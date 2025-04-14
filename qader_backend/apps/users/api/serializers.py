from django.contrib.auth.models import User
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError as DjangoValidationError  # Avoid name clash
from django.utils.translation import gettext_lazy as _
from django.db import transaction, IntegrityError

from rest_framework import serializers

from ..models import (
    UserProfile,
    SerialCode,
    RoleChoices,
    GenderChoices,
    DarkModePrefChoices,
)
from ..utils import generate_unique_referral_code  # Assuming utils.py for generation

import logging

logger = logging.getLogger(__name__)

# --- Helper Serializers ---


class SerialCodeValidatorSerializer(serializers.Serializer):
    """Validates a serial code's existence, activity, and unused status."""

    serial_code = serializers.CharField(write_only=True, required=True)

    def validate_serial_code(self, value):
        """Check if the serial code is valid and usable."""
        try:
            # Retrieve the code object if valid
            code_instance = SerialCode.objects.get(
                code__iexact=value, is_active=True, is_used=False
            )
            # Return the instance for potential use later, or just the value if only validation needed
            return code_instance  # Return the object
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError(_("Invalid or already used serial code."))
        except Exception as e:
            logger.error(f"Unexpected error validating serial code {value}: {e}")
            raise serializers.ValidationError(_("Error validating serial code."))


# --- Registration ---


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration including profile fields and serial code activation."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},  # Helps OpenAPI display
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

    # Include profile fields required at registration directly
    full_name = serializers.CharField(
        write_only=True, required=True, max_length=255, label=_("Full Name")
    )
    # Make optional fields explicitly optional
    gender = serializers.ChoiceField(
        choices=GenderChoices.choices,
        write_only=True,
        required=False,
        allow_null=True,
        label=_("Gender"),
    )
    preferred_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        max_length=100,
        label=_("Preferred Name"),
    )
    grade = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        max_length=100,
        label=_("Grade"),
    )
    has_taken_qiyas_before = serializers.BooleanField(
        write_only=True, required=False, allow_null=True, label=_("Taken Qiyas Before?")
    )

    class Meta:
        model = User
        # Specify fields from the User model and additional fields needed for registration
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
        )
        # Ensure email is required and unique implicitly via User model
        extra_kwargs = {"email": {"required": True}}

    def validate_serial_code(self, value):
        """Use the helper serializer to validate the code."""
        validator = SerialCodeValidatorSerializer(data={"serial_code": value})
        validator.is_valid(raise_exception=True)
        # Return the validated code string for use in the create method
        return value

    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )
        # You could add more cross-field validation here if needed
        return attrs

    @transaction.atomic  # Ensure user creation, profile update, and code usage are atomic
    def create(self, validated_data):
        """Creates the User, updates Profile, marks SerialCode used, and applies subscription."""
        serial_code_str = validated_data.pop("serial_code")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")  # Not needed for user creation

        # Extract profile data
        profile_data = {
            "full_name": validated_data.pop("full_name"),
            "gender": validated_data.pop("gender", None),
            "preferred_name": validated_data.pop("preferred_name", None),
            "grade": validated_data.pop("grade", None),
            "has_taken_qiyas_before": validated_data.pop(
                "has_taken_qiyas_before", None
            ),
            "role": RoleChoices.STUDENT,  # Explicitly set role for new registration
        }

        try:
            # Create user instance (profile is created via signal)
            user = User.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=password,
            )

            # Update the newly created profile (created by signal)
            profile = user.profile  # Access profile created by signal
            for key, value in profile_data.items():
                if value is not None:  # Only update fields that were provided
                    setattr(profile, key, value)
            # Generate referral code during save if needed (handled in profile.save())
            profile.save()

            # Retrieve and mark serial code used, then apply subscription
            # Use select_for_update to lock the row within the transaction
            serial_code_obj = SerialCode.objects.select_for_update().get(
                code__iexact=serial_code_str, is_active=True, is_used=False
            )

            if serial_code_obj.mark_used(user):
                profile.apply_subscription(serial_code_obj)
                logger.info(
                    f"User {user.username} registered successfully using code {serial_code_obj.code}"
                )
            else:
                # This should ideally not happen if validation passed, but handle defensively
                logger.error(
                    f"Failed to mark serial code {serial_code_str} as used for user {user.username} during registration create."
                )
                raise serializers.ValidationError(
                    _("Failed to process serial code during registration.")
                )

            return user

        except IntegrityError as e:
            # Catch potential unique constraint errors (username, email) not caught by initial validation
            logger.warning(
                f"IntegrityError during registration for {validated_data.get('username')}: {e}"
            )
            if "auth_user_username_key" in str(e):
                raise serializers.ValidationError(
                    {"username": [_("A user with that username already exists.")]}
                )
            if "auth_user_email_key" in str(
                e
            ) or 'unique constraint "auth_user_email"' in str(e):
                raise serializers.ValidationError(
                    {"email": [_("A user with that email already exists.")]}
                )
            raise serializers.ValidationError(
                _("Registration failed due to a database constraint.")
            )
        except SerialCode.DoesNotExist:
            # Defensive: If code became invalid between validation and locking
            logger.error(
                f"Serial code {serial_code_str} became invalid during registration transaction for {validated_data.get('username')}."
            )
            raise serializers.ValidationError(
                _("Serial code became invalid during registration process.")
            )
        except Exception as e:
            # Catch any other unexpected errors during the transaction
            logger.exception(
                f"Unexpected error during registration for {validated_data.get('username')}: {e}"
            )
            raise serializers.ValidationError(
                _("An unexpected error occurred during registration.")
            )


# --- User Profile Serializers ---


class SimpleUserSerializer(serializers.ModelSerializer):
    """Read-only serializer for basic nested User information."""

    class Meta:
        model = User
        fields = ("id", "username", "email")  # Expose only basic info
        read_only_fields = fields


class SubscriptionDetailSerializer(serializers.Serializer):
    """Serializer for the nested subscription details."""

    is_active = serializers.BooleanField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True, allow_null=True)


class ReferralDetailSerializer(serializers.Serializer):
    """Serializer for the nested referral details."""

    code = serializers.CharField(read_only=True, allow_null=True)
    referrals_count = serializers.IntegerField(read_only=True)
    earned_free_days = serializers.IntegerField(read_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving the full UserProfile details (/me/)."""

    user = SimpleUserSerializer(read_only=True)  # Nested basic user info
    # Properties exposed as read-only fields
    is_subscribed = serializers.BooleanField(
        read_only=True, source="profile.is_subscribed"
    )  # Use source if accessing via user
    level_determined = serializers.BooleanField(
        read_only=True, source="profile.level_determined"
    )
    # Method fields for custom structured output
    subscription = SubscriptionDetailSerializer(
        read_only=True, source="*"
    )  # Pass the whole profile instance
    referral = ReferralDetailSerializer(read_only=True, source="*")
    # Use SerializerMethodField for profile picture URL generation
    profile_picture_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        # List all fields intended to be exposed in the GET /me/ response
        fields = (
            "user",
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture_url",  # Use the method field for URL
            "role",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            # Timestamps might be useful for client-side info
            "created_at",
            "updated_at",
            # Custom structured fields
            "is_subscribed",  # Direct property access is fine too if structure not needed
            "subscription",
            "referral",
        )
        # Most fields are read-only in this view; updates happen via specific serializers/endpoints
        read_only_fields = fields

    def get_profile_picture_url(self, instance):
        request = self.context.get("request")
        if instance.profile_picture and hasattr(instance.profile_picture, "url"):
            # Build absolute URL if request context is available
            if request:
                return request.build_absolute_uri(instance.profile_picture.url)
            return instance.profile_picture.url
        return None

    # Removed get_subscription and get_referral, using source='*' with dedicated serializers now


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer specifically for updating allowed user profile fields via PATCH /me/."""

    # Make fields explicitly optional for PATCH
    full_name = serializers.CharField(required=False, max_length=255)
    preferred_name = serializers.CharField(
        required=False, allow_null=True, max_length=100
    )
    gender = serializers.ChoiceField(
        required=False, allow_null=True, choices=GenderChoices.choices
    )
    grade = serializers.CharField(required=False, allow_null=True, max_length=100)
    has_taken_qiyas_before = serializers.BooleanField(required=False, allow_null=True)
    last_visited_study_option = serializers.CharField(
        required=False, allow_null=True, max_length=100
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
        # List only fields the user is allowed to change via PATCH /me/
        fields = (
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            # 'profile_picture', # Handle profile picture uploads via a separate dedicated endpoint
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
        )


class ProfilePictureSerializer(serializers.ModelSerializer):
    """Serializer for uploading/updating the profile picture."""

    profile_picture = serializers.ImageField(required=True)

    class Meta:
        model = UserProfile
        fields = ("profile_picture",)  # Only handle this field

    def validate_profile_picture(self, image):
        """Optional: Add validation for file size, dimensions, type."""
        max_upload_size = 5 * 1024 * 1024  # Example: 5 MB limit
        if image.size > max_upload_size:
            raise serializers.ValidationError(
                _("Image size cannot exceed {size}MB.").format(
                    size=max_upload_size // 1024 // 1024
                )
            )
        # Add content type check if needed
        # allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        # if image.content_type not in allowed_types:
        #     raise serializers.ValidationError(_("Invalid image file type."))
        return image


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

    def validate_current_password(self, value):
        """Check if the provided current password is correct."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Incorrect current password."))
        return value

    def validate(self, attrs):
        """Check if the new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New password fields didn't match.")}
            )
        # Optional: Check if new password is the same as the old one
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {
                    "new_password": _(
                        "New password cannot be the same as the current password."
                    )
                }
            )
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email."""

    # Allow reset via email OR username for flexibility
    identifier = serializers.CharField(required=True, label=_("Email or Username"))

    def validate_identifier(self, value):
        """Check if a user exists with the given email or username."""
        try:
            user = User.objects.get(Q(email__iexact=value) | Q(username__iexact=value))
            # Store the user object in context or return it if needed by the view directly
            # self.context['user_to_reset'] = user
            return user  # Return the user object
        except User.DoesNotExist:
            # IMPORTANT: Don't reveal if the user exists. Validation passed technically.
            # The view will handle not sending an email.
            pass
        except User.MultipleObjectsReturned:
            # Should not happen with unique constraints, but handle defensively
            logger.error(f"Multiple users found for identifier: {value}")
            pass  # Treat as non-existent for security
        return None  # Indicate user not found (or multiple found)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming the password reset using token and new password."""

    # Fields based on Django's default password reset mechanism
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

    def validate(self, attrs):
        """Check if the new passwords match."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("New password fields didn't match.")}
            )
        # Actual validation of uidb64 and token happens in the view using Django's tools
        return attrs
