from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.users.models import UserProfile, RoleChoices, SerialCode
from apps.users.api.serializers import SubscriptionDetailSerializer  # Reuse if possible
from apps.gamification.services import PointReason  # To use reason codes


# --- Basic User Info Serializer (for nesting) ---
class AdminNestedUserSerializer(serializers.ModelSerializer):
    """Basic User info for nesting in Profile serializers."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
        ]  # Admin might change is_active/is_staff


# --- Serializer for Listing Users ---
class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users in the admin panel (concise)."""

    user = AdminNestedUserSerializer(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    level_determined = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",  # Contains id, username, email, is_active etc.
            "full_name",
            "role",
            "points",
            "is_subscribed",
            "subscription_expires_at",
            "level_determined",
            "current_level_verbal",
            "current_level_quantitative",
            "created_at",
        ]
        # Most fields are read-only in the list view
        read_only_fields = fields


# --- Serializer for User Detail View & Update (Admin) ---
class AdminUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving/updating user details in the admin panel."""

    user = (
        AdminNestedUserSerializer()
    )  # Allows updating nested user fields like is_active
    subscription = SubscriptionDetailSerializer(
        source="*", read_only=True
    )  # Reusing public subscription detail
    # Include fields an admin might want to see or edit
    # Add referral details for viewing
    referrals_count = serializers.SerializerMethodField(read_only=True)
    earned_free_days = serializers.SerializerMethodField(
        read_only=True
    )  # Example calculation

    class Meta:
        model = UserProfile
        fields = [
            "user",  # Allows updating nested user fields like is_active, email?
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture",  # Read-only, use a separate endpoint if admin needs to upload
            "role",  # Allow changing role
            "subscription",  # Read-only summary from SubscriptionDetailSerializer
            "subscription_expires_at",  # Allow admin override/extension? Careful!
            "serial_code_used",  # Allow admin to link/unlink a code? Careful!
            "points",  # Read-only, use adjust-points endpoint
            "current_streak_days",  # Read-only
            "longest_streak_days",  # Read-only
            "last_study_activity_at",  # Read-only
            "current_level_verbal",  # Allow admin override?
            "current_level_quantitative",  # Allow admin override?
            "last_visited_study_option",  # Read-only
            "dark_mode_preference",  # Allow admin override?
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            "referral_code",  # Read-only
            "referred_by",  # Read-only (shows user ID)
            "referrals_count",  # Read-only
            "earned_free_days",  # Read-only
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "profile_picture",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "referral_code",
            "referred_by",
            "created_at",
            "updated_at",
            "referrals_count",
            "earned_free_days",
            "subscription",
        ]

    def get_referrals_count(self, obj):
        # Count users who were referred by this profile's user
        return obj.user.referrals_made.count()

    def get_earned_free_days(self, obj):
        # Example calculation: 3 free days per referral
        # You might store this explicitly or calculate dynamically
        return self.get_referrals_count(obj) * 3

    @transaction.atomic  # Ensure User and Profile update together
    def update(self, instance: UserProfile, validated_data):
        # Handle nested User update if 'user' data is present
        user_data = validated_data.pop("user", None)
        if user_data:
            user_instance = instance.user
            # Update user fields (e.g., email, is_active)
            for attr, value in user_data.items():
                # Avoid updating password here; use specific endpoints
                if attr != "password":
                    setattr(user_instance, attr, value)
            user_instance.save()

        # Update UserProfile fields
        # Prevent direct update of read-only fields just in case
        for attr, value in validated_data.items():
            if attr not in self.Meta.read_only_fields:
                setattr(instance, attr, value)

        instance.save()
        return instance


# --- Serializer for Sub-Admin Creation/Update ---
# Note: Requires adding a 'permissions' field to UserProfile or a separate model
# For now, this focuses on basic user creation with the 'sub_admin' role.
class AdminSubAdminSerializer(serializers.ModelSerializer):
    """Serializer for creating and managing Sub-Admin accounts."""

    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    # permissions = serializers.MultipleChoiceField(choices=...) # Requires model changes

    # Nested serializer to display user info after creation/update
    user = AdminNestedUserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",  # Read-only display after action
            "username",  # Write-only input
            "email",  # Write-only input
            "password",  # Write-only input
            "full_name",  # Required profile field
            "preferred_name",
            "gender",
            "role",  # Should be pre-set or validated to 'sub_admin' in the view
            # Add 'permissions' field here when model is updated
            "profile_picture",  # Read-only for now
        ]
        read_only_fields = [
            "user",
            "role",
            "profile_picture",
        ]  # Role is set by the view

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                _("A user with that username already exists.")
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                _("A user with that email already exists.")
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        # Pop user fields to create User first
        username = validated_data.pop("username")
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        # permission_data = validated_data.pop('permissions', None) # Handle when available

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,  # Sub-admins should have staff access
            is_superuser=False,
        )

        # Create the profile linked to the user
        profile = UserProfile.objects.create(
            user=user,
            role=RoleChoices.SUB_ADMIN,  # Set the role explicitly
            full_name=validated_data.get("full_name"),
            preferred_name=validated_data.get("preferred_name"),
            gender=validated_data.get("gender"),
            # ... set other profile defaults if needed ...
        )

        # Handle permissions assignment here when the model supports it
        # if permission_data: profile.permissions.set(permission_data)

        return profile  # Return the profile instance

    @transaction.atomic
    def update(self, instance: UserProfile, validated_data):
        # Pop user fields to update User if necessary
        username = validated_data.pop("username", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop(
            "password", None
        )  # Allow password change? Or separate endpoint?
        # permission_data = validated_data.pop('permissions', None)

        user = instance.user
        if username and user.username != username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                raise serializers.ValidationError(
                    {"username": _("A user with that username already exists.")}
                )
            user.username = username
        if email and user.email != email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                raise serializers.ValidationError(
                    {"email": _("A user with that email already exists.")}
                )
            user.email = email
        if password:  # Consider if password change should be allowed here
            user.set_password(password)
            # Maybe force re-login?
        user.save()

        # Update profile fields
        instance.full_name = validated_data.get("full_name", instance.full_name)
        instance.preferred_name = validated_data.get(
            "preferred_name", instance.preferred_name
        )
        instance.gender = validated_data.get("gender", instance.gender)
        # Handle permissions update when available
        # if permission_data is not None: instance.permissions.set(permission_data)

        instance.save()
        return instance


# --- Serializer for Admin Password Reset Request ---
class AdminPasswordResetRequestSerializer(serializers.Serializer):
    """Serializer to identify the user for password reset."""

    identifier = serializers.CharField(
        required=True,
        write_only=True,
        help_text=_("Username or Email of the user to reset password for."),
    )
    user = serializers.HiddenField(default=None)  # To store the found user object

    def validate_identifier(self, value):
        try:
            # Try finding by email first, then username
            user = User.objects.filter(email__iexact=value).first()
            if not user:
                user = User.objects.filter(username__iexact=value).first()

            if not user:
                # Don't raise ValidationError here for security, handle in view
                # We return None if not found
                return None
            return user  # Return the user object if found
        except Exception:
            # Should not happen with standard User model, but good practice
            return None


# --- Serializer for Admin Point Adjustment ---
class AdminPointAdjustmentSerializer(serializers.Serializer):
    """Serializer for admin adjusting user points."""

    points_change = serializers.IntegerField(
        required=True,
        help_text=_("Number of points to add (positive) or subtract (negative)."),
    )
    reason = serializers.CharField(
        max_length=255,
        required=True,
        help_text=_(
            "Reason for the point adjustment (will be logged and may be shown to user)."
        ),
    )
    # Optionally add a reason_code dropdown if you have predefined admin reasons
    # reason_code = serializers.ChoiceField(choices=[(code, code) for code in PointReason.ADMIN_ADJUSTMENT_CODES], required=False)

    def validate_points_change(self, value):
        if value == 0:
            raise serializers.ValidationError(_("Points change cannot be zero."))
        return value
