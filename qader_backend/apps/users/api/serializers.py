from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from django.db import transaction, IntegrityError
from django.core.files.images import get_image_dimensions  # For image validation
from django.conf import settings

from rest_framework import serializers
from rest_framework.request import Request  # For type hinting context

from typing import Dict, Any, Optional, Union

from apps.users.utils import generate_unique_username_from_fullname
from ..constants import (
    GenderChoices,
    RoleChoices,
    DarkModePrefChoices,
    SubscriptionTypeChoices,
    SUBSCRIPTION_PLANS_CONFIG,
)
from ..models import (
    PasswordResetOTP,
    UserProfile,
    SerialCode,
)

# Removed unused import: from ..utils import generate_unique_referral_code
# Referral code generation is handled in the model's save method via signal

# --- Define Username Field Properties (from User model) ---
# This ensures consistency with the User model's username field definitions.
_user_username_field = User._meta.get_field("username")
USERNAME_MAX_LENGTH = _user_username_field.max_length
USERNAME_VALIDATORS = (
    _user_username_field.validators
)  # List of validators like ASCIIUsernameValidator

import logging

logger = logging.getLogger(__name__)

# --- Helper Serializers ---


class SimpleUserSerializer(serializers.ModelSerializer):
    """Read-only serializer for basic nested User information."""

    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = fields


class SubscriptionDetailSerializer(serializers.Serializer):
    """Serializer for the nested subscription details (Used in Auth and /me)."""

    is_active = serializers.BooleanField(
        read_only=True,
        source="is_subscribed",
        help_text="Indicates if the user's subscription is currently active.",
    )
    expires_at = serializers.DateTimeField(
        read_only=True,
        source="subscription_expires_at",
        allow_null=True,
        help_text="The date and time when the current subscription expires (UTC).",
    )
    serial_code = serializers.SerializerMethodField(
        read_only=True,
        help_text="The serial code used for the current active subscription, if applicable.",
    )
    account_type = serializers.CharField(
        read_only=True,
        source="get_account_type_display",  # Assumes model method returns display string
        help_text="Display name of the user's current account type (e.g., 'Free Trial', 'Subscribed').",
    )

    def get_serial_code(self, profile: UserProfile) -> Optional[str]:
        """Safely return the code of the last used serial."""
        if profile.serial_code_used and hasattr(profile.serial_code_used, "code"):
            return profile.serial_code_used.code
        return None


class ReferralDetailSerializer(serializers.Serializer):
    """Serializer for the nested referral details as per API docs."""

    code = serializers.CharField(
        read_only=True,
        source="referral_code",
        allow_null=True,
        help_text="The user's unique referral code to share.",
    )
    referrals_count = serializers.SerializerMethodField(
        read_only=True,
        help_text="The number of users who have successfully signed up using this user's referral code.",
    )
    earned_free_days = serializers.SerializerMethodField(
        read_only=True,
        help_text="The total number of free subscription days earned through successful referrals.",
    )

    def get_referrals_count(self, profile: UserProfile) -> int:
        """Calculate the number of users referred by this profile's user."""
        if hasattr(profile, "user") and profile.user:
            return profile.user.referrals_made.count()
        return 0

    def get_earned_free_days(self, profile: UserProfile) -> int:
        """Calculate free days earned from referrals. (Logic needs defining)."""
        referral_count = self.get_referrals_count(profile)
        days_per_referral = getattr(settings, "REFERRAL_BONUS_DAYS", 3)
        return referral_count * days_per_referral


# --- Registration ---


class InitialSignupSerializer(serializers.ModelSerializer):
    """Serializer for initial user signup (Stage 1)."""

    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(required=True, max_length=255, write_only=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm Password"),
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("email", "full_name", "password", "password_confirm")
        extra_kwargs = {
            "email": {"validators": []},
        }

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive) among active or inactive users."""
        if User.objects.filter(email__iexact=value).exists():
            existing_user = User.objects.filter(email__iexact=value).first()
            if existing_user and not existing_user.is_active:
                raise serializers.ValidationError(
                    _(
                        "This email address is pending confirmation or already registered."
                    )
                )
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password confirmation."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        try:
            validate_password(attrs["password"], user=None)  # Validate password policy
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        """Creates an inactive User, sets username from full_name, and sets full_name on the profile."""
        email = validated_data["email"]
        password = validated_data["password"]
        full_name = validated_data["full_name"]

        # Generate username from full_name, using email as a fallback
        try:
            username = generate_unique_username_from_fullname(full_name, email)
        except ValueError as e:  # Catch error from username generation utility
            logger.error(f"Username generation failed for {full_name}/{email}: {e}")
            raise serializers.ValidationError(
                {
                    "detail": _(
                        "Could not generate a suitable username. Please try a different full name or contact support."
                    )
                }
            )

        try:
            user = User.objects.create_user(
                username=username,  # Use the new generated username
                email=email,
                password=password,
                is_active=False,  # User starts as inactive, activated by email confirmation
            )
            profile = user.profile
            profile.full_name = full_name
            profile.save(update_fields=["full_name"])

            logger.info(
                f"Inactive user '{user.username}' (derived from full_name '{full_name}') created successfully. Email: {email}. Pending email confirmation."
            )
            return user
        except IntegrityError as e:
            logger.error(
                f"IntegrityError during initial signup for email {email} (generated username: {username}): {e}"
            )
            error_msg = str(e).lower()
            # This specific username unique constraint should be rare now due to the utility,
            # but race conditions or flaws in utility could still cause it.
            if "unique constraint" in error_msg and "username" in error_msg:
                logger.critical(
                    f"Username '{username}' (from full_name '{full_name}') caused a unique constraint violation despite generation logic. Possible race condition or utility flaw."
                )
                raise serializers.ValidationError(
                    {
                        "detail": [
                            _(
                                "We encountered an issue creating your username. Please try a slightly different full name or try again later."
                            )
                        ]
                    }
                )
            # Email unique constraint is handled by validate_email, but catch defensively
            elif "unique constraint" in error_msg and "email" in error_msg:
                raise serializers.ValidationError(
                    {"email": [_("This email address is already registered.")]}
                )
            else:
                raise serializers.ValidationError(
                    _("Signup failed due to a data conflict. Please try again.")
                )
        except Exception as e:  # Catch any other unexpected errors
            logger.exception(
                f"Unexpected error during initial signup for {email} (username: {username}): {e}"
            )
            raise serializers.ValidationError(
                _("An unexpected error occurred during signup. Please try again later.")
            )


class CompleteProfileSerializer(serializers.ModelSerializer):
    """Serializer for completing the user profile after email confirmation."""

    # Add username field
    username = serializers.CharField(
        required=False,  # Optional to change if one was auto-generated
        allow_blank=False,  # Usernames cannot be blank if provided
        max_length=USERNAME_MAX_LENGTH,
        # validators=USERNAME_VALIDATORS, # Django's model field validators
        help_text=_(
            "Set or update your username. Must be unique. Allowed characters: letters, digits and './+/-/_' (see below for file content) only."
        ),
    )

    gender = serializers.ChoiceField(
        choices=GenderChoices.choices, required=True, help_text="User's gender."
    )
    language = serializers.ChoiceField(choices=settings.LANGUAGES, required=False)
    grade = serializers.CharField(
        max_length=100,
        required=True,
        help_text="User's current educational grade or level (e.g., 'Grade 11', 'University Freshman').",
    )
    has_taken_qiyas_before = serializers.BooleanField(
        required=True,
        help_text="Indicates whether the user has taken the official Qiyas test before.",
    )
    preferred_name = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Optional: How the user prefers to be called.",
    )
    profile_picture = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text=f"Optional: Upload a profile picture (max {settings.MAX_PROFILE_PIC_SIZE_MB}MB).",
    )
    serial_code = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
        help_text=_("Optional: Enter a serial code to activate a paid subscription."),
    )
    referral_code_used = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )

    profile_picture_url = serializers.SerializerMethodField(
        read_only=True, help_text="URL of the user's profile picture, if uploaded."
    )
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")

    full_name = serializers.CharField(read_only=True)
    points = serializers.IntegerField(read_only=True)
    level_determined = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "username",  # Add username here
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "preferred_name",
            "profile_picture",
            "serial_code",
            "referral_code_used",
            "full_name",
            "language",
            "points",
            "level_determined",
            "profile_picture_url",
            "subscription",
            "referral",
            "current_streak_days",
            "longest_streak_days",
        )
        read_only_fields = (  # username is not read-only here
            "full_name",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "level_determined",
        )

    def validate_username(self, value: str) -> str:
        """
        Validate the username for format (using Django's User model validators) and uniqueness.
        """
        # 1. Apply Django's built-in validators for the username field
        for validator in USERNAME_VALIDATORS:
            try:
                validator(value)
            except DjangoValidationError as e:
                # Convert Django's ValidationError to DRF's for consistent error reporting
                raise serializers.ValidationError(e.messages)

        # 2. Check uniqueness (case-insensitive for user-friendliness in "taken" message)
        # Django's default User model username is often case-sensitive at the DB level,
        # but checking iexact prevents users from creating visually similar usernames
        # like "john" if "John" exists.
        query = User.objects.filter(username__iexact=value)

        current_user = None
        if self.instance and hasattr(self.instance, "user") and self.instance.user:
            current_user = self.instance.user
            # If the username (case-insensitive) is the same as the current user's,
            # it's not a conflict *unless* it's taken by *another* user.
            # This allows changing the case of one's own username, e.g., "MyUser" to "myuser".
            if (
                current_user.username.lower() == value.lower()
            ):  # No change or only case change for self
                # If it's exactly the same, no need to check for uniqueness against self.
                # If only case differs, it's fine as long as new case not taken by OTHERS.
                # The exclude below handles this.
                pass
            query = query.exclude(
                pk=current_user.pk
            )  # Exclude self from uniqueness check

        if query.exists():
            raise serializers.ValidationError(
                _("This username is already taken. Please choose another one.")
            )

        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure the base validate method is called if it exists or if you add one
        # attrs = super().validate(attrs) # If inheriting from a class with a validate method

        instance: Optional[UserProfile] = getattr(self, "instance", None)
        if instance and not instance.is_profile_complete:
            # ... (your existing logic for missing gender, grade, etc.) ...
            required_completion_fields = ["gender", "grade", "has_taken_qiyas_before"]
            missing_fields = []
            for field_name in required_completion_fields:
                is_present_in_attrs = field_name in attrs
                instance_value = getattr(instance, field_name, None)
                if field_name == "has_taken_qiyas_before":
                    has_instance_value = instance_value is not None
                    is_present_in_attrs = attrs.get(field_name) is not None
                else:
                    has_instance_value = bool(instance_value)
                if not is_present_in_attrs and not has_instance_value:
                    missing_fields.append(field_name)
            if missing_fields:
                errors = {
                    field: [_("This field is required to complete your profile.")]
                    for field in missing_fields
                }
                raise serializers.ValidationError(errors)
        return attrs

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        request = self.context.get("request")
        if profile.profile_picture and hasattr(profile.profile_picture, "url"):
            url = profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def validate_serial_code(self, value: Optional[str]) -> Optional[SerialCode]:
        if not value:
            return None
        try:
            code_instance = SerialCode.objects.get(
                code__iexact=value, is_active=True, is_used=False
            )
            return code_instance
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or already used serial code."))
        except Exception as e:
            logger.error(f"Unexpected error validating serial code {value}: {e}")
            raise serializers.ValidationError(_("Error validating serial code."))

    def validate_referral_code_used(self, value: Optional[str]) -> Optional[User]:
        if not value:
            return None
        user = self.context["request"].user
        try:
            profile = UserProfile.objects.select_related("user").get(
                referral_code__iexact=value
            )
            if profile.user == user:
                raise serializers.ValidationError(
                    _("You cannot use your own referral code.")
                )
            return profile.user
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError(_("Invalid referral code provided."))
        except Exception as e:
            logger.error(f"Error validating referral code {value}: {e}")
            raise serializers.ValidationError(_("Error validating referral code."))

    def validate_profile_picture(self, image):
        if image:
            max_upload_size = (
                getattr(settings, "MAX_PROFILE_PIC_SIZE_MB", 5) * 1024 * 1024
            )
            if image.size > max_upload_size:
                raise serializers.ValidationError(
                    _("Image size cannot exceed {size}MB.").format(
                        size=max_upload_size // (1024 * 1024)
                    )
                )
        return image


class MentorInfoSerializer(serializers.ModelSerializer):
    """Basic info for an assigned mentor."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    # full_name is on UserProfile directly

    class Meta:
        model = UserProfile  # The mentor's UserProfile
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "role",
        )  # Add role for clarity
        read_only_fields = fields


# --- Update AuthUserResponseSerializer ---
class AuthUserResponseSerializer(serializers.ModelSerializer):
    """Serializer for the 'user' object in Login/ConfirmEmail responses."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(read_only=True)  # Sourced from profile.full_name
    preferred_name = serializers.CharField(
        read_only=True, allow_null=True
    )  # Sourced from profile.preferred_name
    role = serializers.CharField(read_only=True)  # Sourced from profile.role
    subscription = SubscriptionDetailSerializer(source="*", read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    level_determined = serializers.BooleanField(
        read_only=True
    )  # Sourced from profile.level_determined (property)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete",
        read_only=True,  # Sourced from profile.is_profile_complete (property)
    )

    # --- Added fields as per request ---
    is_super = serializers.BooleanField(
        source="user.is_superuser",
        read_only=True,
        help_text="Indicates if the user is a superuser.",
    )
    is_staff = serializers.BooleanField(
        source="user.is_staff",
        read_only=True,
        help_text="Indicates if the user has staff permissions.",
    )
    points = serializers.IntegerField(
        read_only=True, help_text="User's current gamification points."
    )  # Sourced from profile.points
    current_streak_days = serializers.IntegerField(
        read_only=True, help_text="User's current study streak in days."
    )  # Sourced from profile.current_streak_days
    assigned_mentor = serializers.SerializerMethodField(
        help_text="Information about the student's assigned mentor (if any)."
    )
    mentees_count = serializers.SerializerMethodField(
        help_text="Number of students assigned to this teacher/trainer (if applicable)."
    )
    unread_notifications_count = serializers.IntegerField(
        read_only=True, help_text=_("Number of unread notifications for the user.")
    )

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "username",
            "email",
            "full_name",
            "preferred_name",
            "role",
            "subscription",
            "profile_picture_url",
            "level_determined",
            "profile_complete",
            # --- Added fields to Meta.fields ---
            "is_super",
            "is_staff",
            "points",
            "current_streak_days",
            "assigned_mentor",
            "mentees_count",
            "unread_notifications_count",
        )
        read_only_fields = fields  # This ensures all fields listed above are read-only

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        request: Optional[Request] = self.context.get("request")
        if profile.profile_picture and hasattr(profile.profile_picture, "url"):
            url = profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_assigned_mentor(self, profile: UserProfile) -> Optional[Dict[str, Any]]:
        if profile.role == RoleChoices.STUDENT and profile.assigned_mentor:
            # Pass context (like request) if MentorInfoSerializer needs it
            return MentorInfoSerializer(
                profile.assigned_mentor, context=self.context
            ).data
        return None

    def get_mentees_count(self, profile: UserProfile) -> Optional[int]:
        if profile.role in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
            return profile.mentees.count()  # Uses related_name='mentees'
        return None


# --- UserProfileSerializer (GET /me/) ---
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the full UserProfile details (/me/)."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    is_staff = serializers.BooleanField(source="user.is_staff", read_only=True)
    is_super = serializers.BooleanField(source="user.is_superuser", read_only=True)

    language = serializers.CharField(source="get_language_display", read_only=True)
    language_code = serializers.CharField(source="language", read_only=True)
    level_determined = serializers.BooleanField(read_only=True)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete", read_only=True
    )
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")
    profile_picture_url = serializers.SerializerMethodField()
    assigned_mentor = serializers.SerializerMethodField(
        help_text="Information about the student's assigned mentor (if any)."
    )
    mentees_count = serializers.SerializerMethodField(
        help_text="Number of students assigned to this teacher/trainer (if applicable)."
    )

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "username",
            "email",
            "is_staff",
            "is_super",
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture_url",
            "role",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",
            "profile_complete",
            "language",
            "language_code",
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            "created_at",
            "updated_at",
            "subscription",
            "referral",
            "assigned_mentor",
            "mentees_count",
        )
        read_only_fields = fields

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        request: Optional[Request] = self.context.get("request")
        if profile.profile_picture and hasattr(profile.profile_picture, "url"):
            url = profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

    def get_assigned_mentor(self, profile: UserProfile) -> Optional[Dict[str, Any]]:
        if profile.role == RoleChoices.STUDENT and profile.assigned_mentor:
            # Pass context (like request) if MentorInfoSerializer needs it
            return MentorInfoSerializer(
                profile.assigned_mentor, context=self.context
            ).data
        return None

    def get_mentees_count(self, profile: UserProfile) -> Optional[int]:
        if profile.role in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
            return profile.mentees.count()  # Uses related_name='mentees'
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating allowed user profile fields via PATCH /me/."""

    # Add username field
    username = serializers.CharField(
        required=False,  # Optional to change
        allow_blank=False,
        max_length=USERNAME_MAX_LENGTH,
        # validators=USERNAME_VALIDATORS, # Django's model field validators
        help_text=_(
            "Update your username. Must be unique. Allowed characters: letters, digits and './+/-/_' (see below for file content) only."
        ),
    )

    full_name = serializers.CharField(required=False, max_length=255)
    language = serializers.ChoiceField(choices=settings.LANGUAGES, required=False)
    preferred_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )
    gender = serializers.ChoiceField(
        required=False, allow_blank=True, allow_null=True, choices=GenderChoices.choices
    )
    grade = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )
    has_taken_qiyas_before = serializers.BooleanField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    last_visited_study_option = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )
    dark_mode_preference = serializers.ChoiceField(
        required=False, choices=DarkModePrefChoices.choices
    )
    dark_mode_auto_enabled = serializers.BooleanField(required=False)
    dark_mode_auto_time_start = serializers.TimeField(required=False, allow_null=True)
    dark_mode_auto_time_end = serializers.TimeField(required=False, allow_null=True)
    notify_reminders_enabled = serializers.BooleanField(required=False)
    upcoming_test_date = serializers.DateField(required=False, allow_null=True)
    study_reminder_time = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = (
            "username",  # Add username here
            "full_name",
            "language",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture",
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
        )

    def validate_profile_picture(self, image):
        if image:
            max_upload_size = (
                getattr(settings, "MAX_PROFILE_PIC_SIZE_MB", 5) * 1024 * 1024
            )
            if image.size > max_upload_size:
                raise serializers.ValidationError(
                    _("Image size cannot exceed {size}MB.").format(
                        size=max_upload_size // (1024 * 1024)
                    )
                )
        return image

    def validate_username(self, value: str) -> str:
        """
        Validate the username for format (using Django's User model validators) and uniqueness.
        """
        # 1. Apply Django's built-in validators for the username field
        for validator in USERNAME_VALIDATORS:
            try:
                validator(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.messages)

        # 2. Check uniqueness (case-insensitive for "taken" message)
        query = User.objects.filter(username__iexact=value)

        current_user = None
        if self.instance and hasattr(self.instance, "user") and self.instance.user:
            current_user = self.instance.user
            if (
                current_user.username.lower() == value.lower()
            ):  # No change or only case change for self
                pass
            query = query.exclude(pk=current_user.pk)

        if query.exists():
            raise serializers.ValidationError(
                _("This username is already taken. Please choose another one.")
            )

        return value

    def validate_dark_mode_auto_times(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that start time is before end time if auto mode is enabled."""
        enabled = attrs.get(
            "dark_mode_auto_enabled",
            self.instance.dark_mode_auto_enabled if self.instance else False,
        )
        start = attrs.get(
            "dark_mode_auto_time_start",
            self.instance.dark_mode_auto_time_start if self.instance else None,
        )
        end = attrs.get(
            "dark_mode_auto_time_end",
            self.instance.dark_mode_auto_time_end if self.instance else None,
        )

        if enabled and start and end and start >= end:
            raise serializers.ValidationError(
                {
                    "dark_mode_auto_time_start": _(
                        "Auto dark mode start time must be before end time."
                    ),
                    "dark_mode_auto_time_end": _(
                        "Auto dark mode end time must be after start time."
                    ),
                }
            )
        return attrs

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-field validation for update."""
        attrs = self.validate_dark_mode_auto_times(attrs)
        return attrs


# --- Password Management Serializers ---


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing the current user's password."""

    current_password = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Current Password"),
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        label=_("New Password"),
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm New Password"),
        style={"input_type": "password"},
    )

    def validate_current_password(self, value: str) -> str:
        """Check if the provided current password is correct."""
        user: User = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Incorrect current password."))
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the new passwords match and differ from the current one."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New password fields didn't match.")}
            )
        if self.context["request"].user.check_password(attrs["new_password"]):
            raise serializers.ValidationError(
                {
                    "new_password": _(
                        "New password cannot be the same as the current password."
                    )
                }
            )
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email via email or username."""

    identifier = serializers.CharField(required=True, label=_("Email or Username"))

    def validate_identifier(self, value: str) -> Optional[User]:
        """Check if a user exists with the given email/username (case-insensitive). Returns user or None."""
        try:
            user = User.objects.get(Q(email__iexact=value) | Q(username__iexact=value))
            if not user.is_active:
                logger.warning(f"Password reset requested for inactive user: {value}")
                return None
            return user
        except User.DoesNotExist:
            logger.info(f"Password reset request for non-existent identifier: {value}")
            return None
        except User.MultipleObjectsReturned:
            logger.error(f"Multiple users found for identifier: {value}")
            return None
        except Exception as e:
            logger.exception(f"Error validating password reset identifier {value}: {e}")
            raise serializers.ValidationError(
                _("An error occurred while validating the identifier.")
            )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset using uidb64, token, and new password."""

    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        label=_("New Password"),
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm New Password"),
        style={"input_type": "password"},
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New password fields didn't match.")}
            )
        return attrs


class PasswordResetVerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying an OTP and obtaining a password reset token."""

    identifier = serializers.CharField(
        required=True,
        label=_("Email or Username"),
        help_text=_("The email address or username used to request the OTP."),
    )
    otp = serializers.CharField(
        required=True,
        label=_("OTP Code"),
        min_length=settings.OTP_LENGTH,  # Use OTP_LENGTH from settings
        max_length=settings.OTP_LENGTH,
        style={"input_type": "text"},
        help_text=_("The {otp_length}-digit OTP sent to your email.").format(
            otp_length=settings.OTP_LENGTH
        ),
    )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        identifier = attrs.get("identifier")
        otp_plain = attrs.get("otp")

        try:
            user = User.objects.get(
                Q(email__iexact=identifier.lower().strip())
                | Q(username__iexact=identifier.strip())
            )
            if not user.is_active:
                raise serializers.ValidationError(_("User account is inactive."))
        except User.DoesNotExist:
            raise serializers.ValidationError(_("User with this identifier not found."))
        except User.MultipleObjectsReturned:
            logger.error(
                f"CRITICAL: Multiple users found for identifier '{identifier}' during OTP verification."
            )
            raise serializers.ValidationError(_("Error identifying user account."))

        try:
            # Get the latest, non-fully-used OTP record for this user
            otp_record = PasswordResetOTP.objects.filter(
                user=user,
                is_used=False,  # Not fully used for a password change yet
                otp_expires_at__gt=timezone.now(),  # OTP itself should not be expired
            ).latest("otp_created_at")

            if not otp_record.verify_otp(otp_plain):
                raise serializers.ValidationError(
                    {"otp": _("The OTP provided is invalid or has expired.")}
                )

            # Attach user and otp_record to validated_data for the view
            attrs["user"] = user
            attrs["otp_record"] = otp_record
            return attrs

        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "otp": _(
                        "No active OTP found for this user or it has expired. Please request a new one."
                    )
                }
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during OTP verification for {identifier}: {e}"
            )
            raise serializers.ValidationError(
                _("An error occurred during OTP verification.")
            )


class PasswordResetConfirmOTPSerializer(serializers.Serializer):
    """Serializer for confirming password reset using a reset_token and new password."""

    reset_token = serializers.CharField(
        required=True,
        label=_("Reset Token"),
        help_text=_("The secure token received after OTP verification."),
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        label=_("New Password"),
        style={"input_type": "password"},
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm New Password"),
        style={"input_type": "password"},
    )

    def validate_new_password(self, value):
        # validate_password is already in validators list, but if you need context (like user):
        # For this flow, user is derived from reset_token, so context might be tricky here.
        # The view will handle passing the user to validate_password if needed.
        # For now, relying on the default validator is fine.
        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New password fields didn't match.")}
            )

        plain_reset_token = attrs.get("reset_token")
        hashed_token = PasswordResetOTP()._hash_value(
            plain_reset_token
        )  # Helper to hash

        try:
            # Find the OTP record by the hashed reset token
            # Ensure it's not used and the reset token itself hasn't expired
            otp_record = PasswordResetOTP.objects.get(
                reset_token_hash=hashed_token,
                is_used=False,
                reset_token_expires_at__gt=timezone.now(),
            )
            attrs["otp_record"] = otp_record
            attrs["user"] = otp_record.user  # Get user from the OTP record
            return attrs

        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "reset_token": _(
                        "Invalid or expired reset token. Please verify OTP again."
                    )
                }
            )
        except Exception as e:
            logger.exception(f"Unexpected error validating reset token: {e}")
            raise serializers.ValidationError(
                _("An error occurred while validating the reset token.")
            )


class ApplySerialCodeSerializer(serializers.Serializer):
    """Serializer for validating and applying a new serial code."""

    serial_code = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Serial Code"),
        help_text=_("The new serial code to activate or extend subscription."),
    )

    def validate_serial_code(self, value: str) -> SerialCode:
        """Validate the serial code is active and unused, return the instance."""
        try:
            code_instance = SerialCode.objects.get(
                code__iexact=value, is_active=True, is_used=False
            )
            return code_instance
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or already used serial code."))
        except Exception as e:
            logger.error(
                f"Unexpected error validating serial code {value} for application: {e}"
            )
            raise serializers.ValidationError(_("Error validating serial code."))


class UserRedeemedSerialCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying serial codes redeemed by the current user.
    Exposes only user-relevant, read-only information.
    """

    subscription_type_display = serializers.CharField(
        source="get_subscription_type_display", read_only=True, label=_("Plan Type")
    )
    used_at = serializers.DateTimeField(read_only=True, label=_("Redeemed On"))
    code = serializers.CharField(read_only=True, label=_("Serial Code"))
    duration_days = serializers.IntegerField(read_only=True, label=_("Duration (Days)"))

    class Meta:
        model = SerialCode
        fields = [
            "code",
            "subscription_type_display",
            "duration_days",
            "used_at",
        ]
        read_only_fields = fields


# --- Subscription Plans ---


class SubscriptionPlanSerializer(serializers.Serializer):
    """Serializer for representing available subscription plans."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    requires_code_type = serializers.CharField(read_only=True, allow_null=True)
