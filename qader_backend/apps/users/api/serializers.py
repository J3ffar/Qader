from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.forms import ValidationError
from django.utils import timezone
from django.db import transaction

from rest_framework import serializers

from ..models import UserProfile, SerialCode, RoleChoices


class SerialCodeValidatorSerializer(serializers.Serializer):
    """Validates a serial code"""

    serial_code = serializers.CharField(write_only=True, required=True)

    def validate_serial_code(self, value):
        try:
            code = SerialCode.objects.get(code=value, is_active=True, is_used=False)
            return code  # Return the object for use in the view/serializer
        except SerialCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or already used serial code.")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    serial_code = serializers.CharField(write_only=True, required=True)

    # Include profile fields required at registration
    full_name = serializers.CharField(write_only=True, required=True)
    gender = serializers.ChoiceField(
        choices=UserProfile.gender.field.choices,
        write_only=True,
        required=False,
        allow_null=True,
    )
    preferred_name = serializers.CharField(
        write_only=True, required=False, allow_null=True
    )
    grade = serializers.CharField(write_only=True, required=False, allow_null=True)
    has_taken_qiyas_before = serializers.BooleanField(
        write_only=True, required=False, allow_null=True
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
        )

    def validate_serial_code(self, value):
        """Use the validator serializer to check the code."""
        validator = SerialCodeValidatorSerializer(data={"serial_code": value})
        validator.is_valid(raise_exception=True)
        # Retrieve the validated SerialCode object from the validator's logic
        # We need the object in the create method, so we fetch it again there or pass it via context
        # Simpler here is to return the code string and re-fetch in create after user is saved.
        return value  # Keep the code string for now

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Password fields didn't match."}
            )
        return attrs

    @transaction.atomic  # Ensure user creation and code usage are atomic
    def create(self, validated_data):
        serial_code_str = validated_data.pop("serial_code")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")  # Remove confirm field

        # Pop profile data
        profile_data = {
            "full_name": validated_data.pop("full_name"),
            "gender": validated_data.pop("gender", None),
            "preferred_name": validated_data.pop("preferred_name", None),
            "grade": validated_data.pop("grade", None),
            "has_taken_qiyas_before": validated_data.pop(
                "has_taken_qiyas_before", None
            ),
        }

        # Create user
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=password,
        )

        # Update profile with provided data (profile created via signal)
        profile = user.profile
        for key, value in profile_data.items():
            if value is not None:  # Only update fields that were provided
                setattr(profile, key, value)
        profile.role = RoleChoices.STUDENT  # Ensure role is student
        profile.save()

        # Retrieve and mark serial code used, apply subscription
        try:
            serial_code_obj = SerialCode.objects.select_for_update().get(
                code=serial_code_str, is_active=True, is_used=False
            )
            if serial_code_obj.mark_used(user):
                profile.apply_subscription(serial_code_obj)
            else:
                # This shouldn't happen if validate_serial_code worked, but handle defensively
                raise serializers.ValidationError("Failed to use serial code.")
        except SerialCode.DoesNotExist:
            # This also shouldn't happen, defensive coding
            raise serializers.ValidationError(
                "Serial code became invalid during registration."
            )

        return user


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for basic User info"""

    class Meta:
        model = User
        fields = ("id", "username", "email")
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model, including nested User info"""

    user = UserSerializer(read_only=True)  # Read-only nested user data
    is_subscribed = serializers.BooleanField(read_only=True)  # From property
    level_determined = serializers.BooleanField(read_only=True)  # From property
    subscription = serializers.SerializerMethodField(read_only=True)
    referral = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        # List all fields to expose via the API (read-only for some)
        fields = (
            "user",
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture",  # 'profile_picture_url' is often preferred
            "role",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",  # Property
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            "created_at",
            "updated_at",  # Usually read-only
            "is_subscribed",  # Property
            "subscription",  # Method field
            "referral",  # Method field
        )
        read_only_fields = (
            "user",
            "role",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",
            "is_subscribed",
            "subscription",
            "referral",
            "created_at",
            "updated_at",
        )
        # Fields users can PATCH on /me/ endpoint
        # Note: profile_picture needs separate handling (e.g., separate endpoint)

    def get_subscription(self, instance):
        return {
            "is_active": instance.is_subscribed,
            "expires_at": instance.subscription_expires_at,
        }

    def get_referral(self, instance):
        # Basic count, calculation logic might be more complex
        referrals_count = UserProfile.objects.filter(referred_by=instance.user).count()
        # Example: 3 free days per referral
        earned_free_days = referrals_count * 3  # This is just an example calculation
        return {
            "code": instance.referral_code,
            "referrals_count": referrals_count,
            "earned_free_days": earned_free_days,  # This might need more robust tracking
        }


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer specifically for updating user profile fields via PATCH /me/"""

    class Meta:
        model = UserProfile
        # List only fields the user is allowed to change
        fields = (
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            # 'profile_picture', # Handle separately
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
        )


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New password fields didn't match."}
            )
        return attrs


class ProfilePictureSerializer(serializers.Serializer):
    profile_picture = serializers.ImageField(required=True)

    def validate_profile_picture(self, image):
        # Optional: Add validation for file size, dimensions, etc.
        max_upload_size = 5 * 1024 * 1024  # 5 MB example limit
        if image.size > max_upload_size:
            raise ValidationError(
                f"Image size cannot exceed {max_upload_size // 1024 // 1024}MB."
            )

        # Optional: Dimension check
        # try:
        #     width, height = get_image_dimensions(image)
        #     # Add dimension checks if needed
        # except Exception:
        #      raise ValidationError("Could not read image dimensions.")

        return image


# --- Password Reset Serializers (Example using built-in Django logic flow) ---


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    # Optional: Allow username too
    # identifier = serializers.CharField(required=True)
    # def validate(self, attrs):
    #     identifier = attrs.get('identifier')
    #     # Check if it's an email or username and find the user
    #     # ... logic to find user ...
    #     if not user:
    #         raise serializers.ValidationError("No user found with that identifier.")
    #     attrs['user'] = user
    #     return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    # Fields depend on the token generation method. Django's default uses uidb64 and token.
    uidb64 = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New password fields didn't match."}
            )
        # Further validation of uidb64/token happens in the view
        return attrs
