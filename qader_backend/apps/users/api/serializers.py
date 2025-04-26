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

from ..models import (
    UserProfile,
    SerialCode,
    RoleChoices,
    GenderChoices,
    DarkModePrefChoices,
    SubscriptionTypeChoices,  # Added just in case needed later
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

    is_active = serializers.BooleanField(read_only=True, source="is_subscribed")
    expires_at = serializers.DateTimeField(
        read_only=True, source="subscription_expires_at", allow_null=True
    )
    # serial_code = serializers.CharField(read_only=True, source="serial_code_used.code", allow_null=True) # Alternative direct source

    # Using SerializerMethodField gives more control if needed
    serial_code = serializers.SerializerMethodField(read_only=True)

    def get_serial_code(self, profile: UserProfile) -> Optional[str]:
        """Safely return the code of the last used serial."""
        # Check if serial_code_used exists and has a code attribute
        if profile.serial_code_used and hasattr(profile.serial_code_used, "code"):
            return profile.serial_code_used.code
        return None


class ReferralDetailSerializer(serializers.Serializer):
    """Serializer for the nested referral details as per API docs."""

    code = serializers.CharField(
        read_only=True, source="referral_code", allow_null=True
    )
    # These fields require calculation, likely using annotations or methods on the model/manager
    referrals_count = serializers.SerializerMethodField(read_only=True)
    earned_free_days = serializers.SerializerMethodField(read_only=True)

    def get_referrals_count(self, profile: UserProfile) -> int:
        """Calculate the number of users referred by this profile's user."""
        # Assumes related_name='referrals_made' on UserProfile.referred_by
        # Ensure the related user exists
        if hasattr(profile, "user") and profile.user:
            return (
                profile.user.referrals_made.count()
            )  # Counts UserProfile objects where referred_by is this user
        return 0

    def get_earned_free_days(self, profile: UserProfile) -> int:
        """Calculate free days earned from referrals. (Logic needs defining)."""
        # Example: 3 free days per referral
        referral_count = self.get_referrals_count(profile)
        days_per_referral = 3  # Define this logic (e.g., in settings)
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
        # Use email as username if username field is not explicitly required
        fields = ("email", "full_name", "password", "password_confirm")
        extra_kwargs = {
            "email": {
                "validators": []
            },  # Remove default uniqueness validator temporarily
        }

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive) among active or inactive users."""
        if User.objects.filter(email__iexact=value).exists():
            # Check if the existing user is inactive and potentially pending confirmation
            existing_user = User.objects.filter(email__iexact=value).first()
            if existing_user and not existing_user.is_active:
                # Optional: Allow re-sending confirmation? Or just block?
                raise serializers.ValidationError(
                    _(
                        "This email address is pending confirmation or already registered."
                    )
                )
            raise serializers.ValidationError(
                _("A user with this email already exists.")
            )
        return value.lower()  # Standardize email to lowercase

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password confirmation."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        # Trigger Django's password validation
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
            # Use email as username if username field is not present/required
            username = validated_data.get("username", email)

            user = User.objects.create_user(
                username=username,  # Use email or provided username
                email=email,
                password=password,
                is_active=False,  # User starts as inactive
            )

            # Access profile created by signal and set full_name
            profile = user.profile  # Profile exists due to signal
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

    # Fields required for completion
    gender = serializers.ChoiceField(choices=GenderChoices.choices, required=True)
    grade = serializers.CharField(max_length=100, required=True)
    has_taken_qiyas_before = serializers.BooleanField(required=True)

    # Optional fields during completion
    preferred_name = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    serial_code = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )
    referral_code_used = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True,
        write_only=True,
    )

    # Explicitly defined fields for response (nested/method)
    # These are automatically included, DO NOT list in Meta.fields
    profile_picture_url = serializers.SerializerMethodField(read_only=True)
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")

    # Read-only representation of model fields also included in the response
    # Define them here if needed, or rely on them being in read_only_fields
    full_name = serializers.CharField(read_only=True)  # Read-only model field
    points = serializers.IntegerField(read_only=True)  # Read-only model field
    # ... add other read-only model fields if needed for the response ...
    level_determined = serializers.BooleanField(read_only=True)  # Read-only property

    class Meta:
        model = UserProfile
        fields = (
            # ---- Writable Model Fields ----
            "gender",  # Required Writeable
            "grade",  # Required Writeable
            "has_taken_qiyas_before",  # Required Writeable
            "preferred_name",  # Optional Writeable
            "profile_picture",  # Optional Writeable
            # ---- Write-Only Fields (Defined Above) ----
            "serial_code",
            "referral_code_used",
            # ---- Read-Only Fields (Explicitly defined above or listed in read_only_fields) ----
            # These are included in the response automatically or via read_only_fields
            "full_name",
            "points",
            "level_determined",
            "profile_picture_url",  # From SerializerMethodField definition
            "subscription",  # From nested serializer definition
            "referral",  # From nested serializer definition
            # Add other model fields if needed for response, ensure they are read-only below
            "current_streak_days",
            "longest_streak_days",
        )
        # List ONLY model fields that should be read-only *through this serializer*
        read_only_fields = (
            "full_name",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "level_determined",
            # Do NOT list subscription, referral, profile_picture_url here as they are not model fields
            # and their read-only status is defined above.
        )

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required fields for completion are provided if profile is not yet complete."""
        instance: Optional[UserProfile] = getattr(self, "instance", None)

        # Only run this check if we have an instance (i.e., during update)
        # and the profile is not already considered complete based on its current state
        # NOTE: We check the instance *before* potential updates from attrs
        if instance and not instance.is_profile_complete:
            # Check if required fields are present in the incoming data (attrs) OR already exist on the instance
            required_completion_fields = ["gender", "grade", "has_taken_qiyas_before"]
            missing_fields = []

            for field_name in required_completion_fields:
                # Check if field is in incoming data OR already has a valid value on the instance
                is_present_in_attrs = field_name in attrs
                instance_value = getattr(instance, field_name, None)

                # Special check for boolean field (None means not set)
                if field_name == "has_taken_qiyas_before":
                    has_instance_value = instance_value is not None
                    is_present_in_attrs = (
                        attrs.get(field_name) is not None
                    )  # Check bool presence
                else:  # For CharField, ChoiceField etc.
                    has_instance_value = bool(
                        instance_value
                    )  # Check if not None or empty string

                if not is_present_in_attrs and not has_instance_value:
                    missing_fields.append(field_name)

            if missing_fields:
                errors = {
                    field: [_("This field is required to complete your profile.")]
                    for field in missing_fields
                }
                raise serializers.ValidationError(errors)

        # Validate referral code against self if needed (though should be handled by validate_referral_code_used)
        # ...

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
        """Validate the serial code if provided."""
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
        """Validate the referral code if provided and return the referring user."""
        if not value:
            return None
        user = self.context["request"].user  # User completing profile
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
        # Re-use validation logic from UserProfileUpdateSerializer if needed
        # ... (add size/dimension/type checks here) ...
        return image

    # No create method needed, this is for updating via PATCH


# --- Update AuthUserResponseSerializer ---
class AuthUserResponseSerializer(serializers.ModelSerializer):
    """Serializer for the 'user' object in Login/ConfirmEmail responses."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(read_only=True)
    preferred_name = serializers.CharField(read_only=True, allow_null=True)
    role = serializers.CharField(read_only=True)
    subscription = SubscriptionDetailSerializer(source="*", read_only=True)
    profile_picture_url = serializers.SerializerMethodField()
    level_determined = serializers.BooleanField(read_only=True)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete", read_only=True
    )  # <-- ADDED

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
            "profile_complete",  # <-- ADDED
        )
        read_only_fields = fields

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        # ... (implementation remains the same) ...
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
    level_determined = serializers.BooleanField(read_only=True)
    profile_complete = serializers.BooleanField(
        source="is_profile_complete", read_only=True
    )  # <-- ADDED
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "user",
            # Basic Info
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture_url",
            "role",
            # Gamification/Progress
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            # Learning Level
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",
            "profile_complete",  # <-- ADDED
            # Settings
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            # Timestamps & Relations
            "created_at",
            "updated_at",
            "subscription",
            "referral",
        )
        read_only_fields = fields

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        # ... (implementation remains the same) ...
        request: Optional[Request] = self.context.get("request")
        if profile.profile_picture and hasattr(profile.profile_picture, "url"):
            url = profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating allowed user profile fields via PATCH /me/."""

    # Explicitly list allowed fields and make them optional for PATCH
    full_name = serializers.CharField(required=False, max_length=255)
    preferred_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )
    gender = serializers.ChoiceField(
        required=False, allow_blank=True, allow_null=True, choices=GenderChoices.choices
    )  # Allow blank
    grade = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )
    has_taken_qiyas_before = serializers.BooleanField(required=False, allow_null=True)
    profile_picture = serializers.ImageField(
        required=False, allow_null=True
    )  # Handles image upload
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

    # Exclude fields user shouldn't update directly
    # e.g., role, points, streak, levels, subscription, referral code

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
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
        """Validate uploaded profile picture (size, dimensions, type)."""
        if image:  # Only validate if an image is provided
            max_upload_size = (
                settings.MAX_PROFILE_PIC_SIZE_MB * 1024 * 1024
                if hasattr(settings, "MAX_PROFILE_PIC_SIZE_MB")
                else 5 * 1024 * 1024
            )  # Default 5MB
            if image.size > max_upload_size:
                raise serializers.ValidationError(
                    _("Image size cannot exceed {size}MB.").format(
                        size=max_upload_size // (1024 * 1024)
                    )
                )

            # Optional: Validate image dimensions
            # min_width, min_height = 100, 100
            # max_width, max_height = 2000, 2000
            # try:
            #     width, height = get_image_dimensions(image)
            #     if not (min_width <= width <= max_width and min_height <= height <= max_height):
            #          raise serializers.ValidationError(
            #              _("Image dimensions must be between {min_w}x{min_h} and {max_w}x{max_h} pixels.").format(
            #                   min_w=min_width, min_h=min_height, max_w=max_width, max_h=max_height
            #               )
            #          )
            # except Exception:
            #      raise serializers.ValidationError(_("Could not read image dimensions. Invalid image file?"))

            # Optional: Validate content type (more reliable than extension)
            # allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            # if image.content_type not in allowed_types:
            #      raise serializers.ValidationError(_("Invalid image file type. Allowed types: JPG, PNG, WEBP."))

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
        # Add other cross-field validations if needed
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
        # Check if new password is the same as the old one
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
            # Case-insensitive lookup using Q objects
            user = User.objects.get(Q(email__iexact=value) | Q(username__iexact=value))
            if not user.is_active:
                logger.warning(f"Password reset requested for inactive user: {value}")
                return None  # Treat inactive user as non-existent for reset purpose
            return user  # Return the user object for the view
        except User.DoesNotExist:
            # Don't reveal user existence in error message
            logger.info(f"Password reset request for non-existent identifier: {value}")
            return None  # Validation technically passes, user just not found
        except User.MultipleObjectsReturned:
            # Should not happen with unique constraints, but handle defensively
            logger.error(f"Multiple users found for identifier: {value}")
            return None  # Treat as non-existent for security
        except Exception as e:
            logger.exception(f"Error validating password reset identifier {value}: {e}")
            raise serializers.ValidationError(
                _("An error occurred while validating the identifier.")
            )  # User-facing generic error


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
        # uidb64 and token validity are checked in the view using Django's tools
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
            # Use __iexact for case-insensitivity matching user input behavior
            code_instance = SerialCode.objects.get(
                code__iexact=value, is_active=True, is_used=False
            )
            return code_instance  # Return the object for use in the view's logic
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or already used serial code."))
        except Exception as e:
            logger.error(
                f"Unexpected error validating serial code {value} for application: {e}"
            )
            raise serializers.ValidationError(_("Error validating serial code."))

    # Note: The actual application logic (marking used, updating profile) happens in the View
    # to ensure atomicity and access to the request.user.


# --- Subscription Plans ---


class SubscriptionPlanSerializer(serializers.Serializer):
    """Serializer for representing available subscription plans."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    duration_days = serializers.IntegerField(read_only=True)
    requires_code_type = serializers.CharField(read_only=True, allow_null=True)
