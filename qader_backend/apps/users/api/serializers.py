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
from ..constants import (
    GenderChoices,
    RoleChoices,
    DarkModePrefChoices,
    SubscriptionTypeChoices,
    SUBSCRIPTION_PLANS_CONFIG,
)
from ..models import (
    UserProfile,
    SerialCode,
)

# Removed unused import: from ..utils import generate_unique_referral_code
# Referral code generation is handled in the model's save method via signal

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
            validate_password(attrs["password"], user=None)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        """Creates an inactive User and sets the full_name on the profile."""
        email = validated_data["email"]
        password = validated_data["password"]
        full_name = validated_data["full_name"]

        try:
            username = validated_data.get("username", email)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=False,
            )
            profile = user.profile
            profile.full_name = full_name
            profile.save(update_fields=["full_name"])
            logger.info(
                f"Inactive user '{user.username}' created, pending email confirmation."
            )
            return user
        except IntegrityError as e:
            logger.warning(f"IntegrityError during initial signup for {email}: {e}")
            error_msg = str(e).lower()
            if "unique constraint" in error_msg and (
                "username" in error_msg or "email" in error_msg
            ):
                raise serializers.ValidationError(
                    {"email": [_("This email address is already registered.")]}
                )
            else:
                raise serializers.ValidationError(
                    _("Signup failed due to a data conflict.")
                )
        except Exception as e:
            logger.exception(f"Unexpected error during initial signup for {email}: {e}")
            raise serializers.ValidationError(
                _("An unexpected error occurred during signup.")
            )


class CompleteProfileSerializer(serializers.ModelSerializer):
    """Serializer for completing the user profile after email confirmation."""

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
        read_only_fields = (
            "full_name",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "level_determined",
        )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        instance: Optional[UserProfile] = getattr(self, "instance", None)
        if instance and not instance.is_profile_complete:
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


# --- UserProfileSerializer (GET /me/) ---
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the full UserProfile details (/me/)."""

    user = SimpleUserSerializer(read_only=True)
    language = serializers.CharField(source="get_language_display", read_only=True)
    language_code = serializers.CharField(source="language", read_only=True)
    level_determined = serializers.BooleanField(read_only=True)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete", read_only=True
    )
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "user",
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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating allowed user profile fields via PATCH /me/."""

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
