from datetime import timedelta
from django.utils import timezone
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


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration including profile fields and serial code activation."""

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
    serial_code = serializers.CharField(
        write_only=True, required=True, label=_("Serial Code")
    )

    # Profile fields required at registration
    full_name = serializers.CharField(
        write_only=True, required=True, max_length=255, label=_("Full Name")
    )
    gender = serializers.ChoiceField(
        choices=GenderChoices.choices,
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        label=_("Gender"),  # Allow blank string too
    )
    preferred_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
        label=_("Preferred Name"),
    )
    grade = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
        label=_("Grade"),
    )
    has_taken_qiyas_before = serializers.BooleanField(
        write_only=True, required=False, allow_null=True, label=_("Taken Qiyas Before?")
    )

    # Field for referral code (optional)
    referral_code_used = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
        label=_("Referral Code (Optional)"),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "serial_code",
            "full_name",
            "gender",
            "preferred_name",
            "grade",
            "has_taken_qiyas_before",
            "referral_code_used",  # Added referral code field
        )
        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
            # Add validators for username format if needed
        }

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive)."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with that email already exists.")
            )
        return value

    def validate_username(self, value: str) -> str:
        """Ensure username is unique (case-insensitive)."""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                _("A user with that username already exists.")
            )
        # Add custom username syntax validation if needed
        return value

    def validate_serial_code(self, value: str) -> SerialCode:
        """Validate the serial code is active and unused, return the instance."""
        try:
            # Use __iexact for case-insensitivity matching user input behavior
            code_instance = SerialCode.objects.get(
                code__iexact=value, is_active=True, is_used=False
            )
            return code_instance  # Return the object for use in create()
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or already used serial code."))
        except Exception as e:
            logger.error(f"Unexpected error validating serial code {value}: {e}")
            raise serializers.ValidationError(
                _("Error validating serial code.")
            )  # Generic error

    def validate_referral_code_used(self, value: Optional[str]) -> Optional[User]:
        """Validate the referral code if provided and return the referring user."""
        if not value:
            return None  # Optional field
        try:
            # Find the profile (and thus user) with this referral code
            profile = UserProfile.objects.select_related("user").get(
                referral_code__iexact=value
            )
            # Ensure the referrer is not the user themselves (though unlikely at registration)
            # This validation might be better placed in the main validate() method
            return profile.user  # Return the referring user object
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError(_("Invalid referral code provided."))
        except Exception as e:
            logger.error(f"Error validating referral code {value}: {e}")
            raise serializers.ValidationError(_("Error validating referral code."))

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate password confirmation and cross-field logic."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )

        # Example: Prevent self-referral (though username isn't known here yet)
        # This type of check might need adjustment based on flow
        # if 'referral_code_used' in attrs and 'username' in attrs:
        #    referring_user = attrs.get('referral_code_used') # This holds the User object now
        #    if referring_user and referring_user.username == attrs['username']:
        #         raise serializers.ValidationError({"referral_code_used": _("Cannot refer yourself.")})

        return attrs

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> User:
        """Creates User, Profile, marks SerialCode used, applies subscription & referral."""

        # Pop fields not directly part of User model creation
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)  # Remove confirm password
        serial_code_obj = validated_data.pop(
            "serial_code"
        )  # Already validated instance
        referring_user = validated_data.pop(
            "referral_code_used", None
        )  # Optional User object

        # Pop profile data - keep only User fields in validated_data for create_user
        profile_data = {
            "full_name": validated_data.pop("full_name"),
            "gender": validated_data.pop("gender", None),
            "preferred_name": validated_data.pop("preferred_name", None),
            "grade": validated_data.pop("grade", None),
            "has_taken_qiyas_before": validated_data.pop(
                "has_taken_qiyas_before", None
            ),
            "role": RoleChoices.STUDENT,  # Default role
            "referred_by": referring_user,  # Add referring user if present
        }

        try:
            # Create the user instance
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=password,
                # Note: is_active defaults to True in create_user
            )

            # Update the profile created by the signal
            profile = user.profile  # Access profile created by signal
            for key, value in profile_data.items():
                # Ensure we don't overwrite existing referral_code if signal generated it
                if key == "referral_code" and profile.referral_code:
                    continue
                # Set attribute only if provided or non-None (handle blank strings carefully if needed)
                if value is not None:
                    setattr(profile, key, value)

            # Save profile *before* applying subscription to ensure referred_by is set if needed
            profile.save()

            # Mark serial code used (using the validated object) and apply subscription
            # Re-fetch with select_for_update to prevent race conditions within the transaction
            serial_code_to_use = SerialCode.objects.select_for_update().get(
                pk=serial_code_obj.pk
            )

            if serial_code_to_use.mark_used(user):
                profile.apply_subscription(serial_code_to_use)
            else:
                # This indicates a potential race condition or logic error if validation passed
                logger.error(
                    f"Failed to mark serial code {serial_code_to_use.code} as used for user {user.username} within transaction."
                )
                raise serializers.ValidationError(
                    _(
                        "Failed to process serial code during registration. Please try again."
                    )
                )  # User-facing error

            # Handle referral reward application (e.g., grant free days to referrer)
            # This might be better handled by a separate signal on UserProfile save or SerialCode usage
            if referring_user:
                try:
                    # Example: Add 3 free days to the referrer
                    referrer_profile = referring_user.profile
                    days_to_add = 3  # TODO: Get from settings
                    current_expiry = (
                        referrer_profile.subscription_expires_at or timezone.now()
                    )
                    new_expiry = current_expiry + timedelta(days=days_to_add)
                    referrer_profile.subscription_expires_at = new_expiry
                    referrer_profile.save(
                        update_fields=["subscription_expires_at", "updated_at"]
                    )
                    logger.info(
                        f"Granted {days_to_add} referral bonus days to user {referring_user.username}"
                    )
                    # TODO: Consider creating a PointLog entry or notification for the referrer
                except UserProfile.DoesNotExist:
                    logger.error(
                        f"Could not find profile for referring user {referring_user.username} to grant bonus."
                    )
                except Exception as e:
                    logger.exception(
                        f"Error granting referral bonus to {referring_user.username}: {e}"
                    )

            logger.info(
                f"User '{user.username}' registered successfully using code '{serial_code_to_use.code}'."
            )
            return user

        # Keep existing specific error handling
        except IntegrityError as e:
            logger.warning(
                f"IntegrityError during registration for {validated_data.get('username')}: {e}"
            )
            # Check specific constraint names if possible (depends on DB backend)
            error_msg = str(e).lower()
            if "unique constraint" in error_msg and "username" in error_msg:
                raise serializers.ValidationError(
                    {"username": [_("A user with that username already exists.")]}
                )
            elif "unique constraint" in error_msg and "email" in error_msg:
                raise serializers.ValidationError(
                    {"email": [_("A user with that email already exists.")]}
                )
            else:
                raise serializers.ValidationError(
                    _(
                        "Registration failed due to a data conflict. Please check your input."
                    )
                )
        except SerialCode.DoesNotExist:
            logger.error(
                f"Serial code {serial_code_obj.code} became invalid during registration transaction for {validated_data.get('username')}."
            )
            raise serializers.ValidationError(
                _("Serial code became invalid during registration. Please try again.")
            )
        except Exception as e:
            logger.exception(
                f"Unexpected error during registration create for {validated_data.get('username')}: {e}"
            )
            raise serializers.ValidationError(
                _("An unexpected error occurred during registration.")
            )


# --- User Profile Serializers ---


class AuthUserResponseSerializer(serializers.ModelSerializer):
    """Serializer for the 'user' object in Login/Register responses (based on UserProfile)."""

    id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    full_name = serializers.CharField(read_only=True)
    preferred_name = serializers.CharField(
        read_only=True, allow_null=True
    )  # Ensure null is allowed if blank=True in model
    role = serializers.CharField(read_only=True)

    subscription = SubscriptionDetailSerializer(
        source="*", read_only=True
    )  # Pass profile to nested serializer
    profile_picture_url = serializers.SerializerMethodField()
    level_determined = serializers.BooleanField(read_only=True)  # From profile property

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
        )
        read_only_fields = fields

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        """Generate absolute profile picture URL if available."""
        request: Optional[Request] = self.context.get("request")
        if profile.profile_picture and hasattr(profile.profile_picture, "url"):
            url = profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url  # Return relative URL if no request context
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the full UserProfile details (/me/)."""

    # Expose user fields directly or via nested serializer
    # Option 1: Direct fields (requires source='user.fieldname')
    # id = serializers.IntegerField(source="user.id", read_only=True)
    # username = serializers.CharField(source="user.username", read_only=True)
    # email = serializers.EmailField(source="user.email", read_only=True)
    # date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)

    # Option 2: Nested User Serializer (cleaner)
    user = SimpleUserSerializer(read_only=True)

    level_determined = serializers.BooleanField(read_only=True)
    subscription = SubscriptionDetailSerializer(read_only=True, source="*")
    referral = ReferralDetailSerializer(read_only=True, source="*")  # Added source='*'
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = (
            "user",  # Use nested user object
            # Basic Info
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture_url",  # Use method field
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
            "updated_at",  # Profile timestamps
            "subscription",
            "referral",
            # Removed redundant user fields covered by nested 'user' object
        )
        read_only_fields = fields  # All fields read-only for GET /me/

    def get_profile_picture_url(self, profile: UserProfile) -> Optional[str]:
        """Generate absolute profile picture URL."""
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
