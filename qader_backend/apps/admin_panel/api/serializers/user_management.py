import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from django.conf import settings  # Import settings for referral days calculation
from django.utils import timezone  # Import timezone for expiry updates

from apps.users.models import (
    DarkModePrefChoices,
    UserProfile,
    RoleChoices,
    SerialCode,
    GenderChoices,
)
from apps.users.api.serializers import SubscriptionDetailSerializer  # Reuse
from apps.admin_panel.models import AdminPermission  # Import the new model


logger = logging.getLogger(__name__)


# --- Basic User Info Serializer (for nesting) ---
class AdminNestedUserSerializer(serializers.ModelSerializer):
    """Basic User info for nesting in Profile serializers."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",  # Admin can change this
            "is_staff",  # Admin can change this (careful with roles)
            "is_superuser",  # Usually SuperAdmin only
            "date_joined",
            "last_login",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "last_login",
            "is_superuser",  # Superuser status usually managed separately or is read-only
        ]
        extra_kwargs = {
            "is_superuser": {
                "required": False,
                "allow_null": True,
            }  # Don't require in updates
        }


# --- Serializer for Listing Users ---
class AdminUserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users in the admin panel (concise)."""

    user = AdminNestedUserSerializer(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)  # Property on Profile
    level_determined = serializers.BooleanField(read_only=True)  # Property on Profile
    # Include subscription expiry for quick view
    subscription_expires_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
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
        read_only_fields = fields  # List view is primarily read-only


# --- Serializer for User Detail View & Update (Admin) ---
class AdminUserProfileSerializer(serializers.ModelSerializer):
    """Serializer for retrieving/updating user details in the admin panel."""

    user = AdminNestedUserSerializer()  # Allows updating nested user fields
    subscription = SubscriptionDetailSerializer(
        source="*", read_only=True
    )  # Reusing public subscription detail
    # Make subscription_expires_at directly editable by admin
    subscription_expires_at = serializers.DateTimeField(required=False, allow_null=True)
    # serial_code_used might be editable if admin can manually link/unlink, but risky. Keep read-only for now.
    serial_code_used = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True, read_only=True
    )

    # Allow admin to override levels if needed
    current_level_verbal = serializers.FloatField(required=False, allow_null=True)
    current_level_quantitative = serializers.FloatField(required=False, allow_null=True)

    # Allow admin to override some settings
    dark_mode_preference = serializers.ChoiceField(
        choices=DarkModePrefChoices.choices, required=False
    )
    dark_mode_auto_enabled = serializers.BooleanField(required=False)
    dark_mode_auto_time_start = serializers.TimeField(required=False, allow_null=True)
    dark_mode_auto_time_end = serializers.TimeField(required=False, allow_null=True)
    notify_reminders_enabled = serializers.BooleanField(required=False)
    upcoming_test_date = serializers.DateField(required=False, allow_null=True)
    study_reminder_time = serializers.TimeField(required=False, allow_null=True)
    last_visited_study_option = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=100
    )  # Allow admin to reset/set

    # Referral details are read-only calculations
    referral_code = serializers.CharField(read_only=True)  # User's own referral code
    referred_by = serializers.PrimaryKeyRelatedField(
        read_only=True, allow_null=True
    )  # User ID of referrer
    referrals_count = serializers.SerializerMethodField(read_only=True)
    earned_free_days = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "full_name",
            "preferred_name",
            "gender",  # Allow admin override? Yes, required=False
            "grade",  # Allow admin override? Yes, required=False
            "has_taken_qiyas_before",  # Allow admin override? Yes, required=False
            "profile_picture",  # Read-only for update here; separate endpoint for upload
            "role",  # Allow changing role? Careful! Only SuperAdmin should change to ADMIN/SUB_ADMIN.
            "subscription",  # Read-only summary
            "subscription_expires_at",  # Admin editable
            "serial_code_used",  # Keep read-only or add specific handling if needed
            "points",  # Read-only, use adjust-points endpoint
            "current_streak_days",  # Read-only
            "longest_streak_days",  # Read-only
            "last_study_activity_at",  # Read-only
            "current_level_verbal",  # Admin editable
            "current_level_quantitative",  # Admin editable
            "last_visited_study_option",  # Admin editable
            "dark_mode_preference",  # Admin editable
            "dark_mode_auto_enabled",  # Admin editable
            "dark_mode_auto_time_start",  # Admin editable
            "dark_mode_auto_time_end",  # Admin editable
            "notify_reminders_enabled",  # Admin editable
            "upcoming_test_date",  # Admin editable
            "study_reminder_time",  # Admin editable
            "referral_code",  # Read-only
            "referred_by",  # Read-only (shows user ID) - Admin could theoretically change this, but requires specific endpoint/logic. Keep read-only for now.
            "referrals_count",  # Read-only
            "earned_free_days",  # Read-only
            "created_at",
            "updated_at",
        ]
        # Explicitly remove most fields from default read_only_fields to make them editable
        # Rely on permissions to restrict which admins can edit which fields/users
        # For example, Role should likely only be editable by is_superuser=True
        read_only_fields = [
            "profile_picture",
            "points",  # Use specific adjust endpoint
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "referral_code",
            "referred_by",  # Requires specific complex logic if editable
            "created_at",
            "updated_at",
            "referrals_count",
            "earned_free_days",
            "subscription",  # Summary field, not data field
            "serial_code_used",  # Keep read-only for safety
        ]
        extra_kwargs = {
            "gender": {"required": False, "allow_blank": True, "allow_null": True},
            "grade": {"required": False, "allow_blank": True, "allow_null": True},
            "has_taken_qiyas_before": {"required": False, "allow_null": True},
            "last_visited_study_option": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "preferred_name": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            # Role can only be changed by superuser? Handled in view or explicit validation
            "role": {"required": False},
        }

    def get_referrals_count(self, obj: UserProfile) -> int:
        """Calculate the number of users referred by this profile's user."""
        if hasattr(obj, "user") and obj.user:
            # Assuming related_name='referrals_made' on UserProfile.referred_by pointing to User
            # The count is on UserProfile where 'referred_by' is obj.user
            return obj.user.referrals_made.count()
        return 0

    def get_earned_free_days(self, obj: UserProfile) -> int:
        """Calculate free days earned from referrals."""
        referral_count = self.get_referrals_count(obj)
        # Define days per referral in settings or constant
        days_per_referral = getattr(settings, "REFERRAL_BONUS_DAYS", 3)
        return referral_count * days_per_referral

    # Add validation for dark mode auto times
    def validate(self, attrs: dict) -> dict:
        """Validate dark mode auto times if they are being updated."""
        # Check if auto dark mode settings are being updated
        auto_enabled_in_data = "dark_mode_auto_enabled" in attrs
        start_time_in_data = "dark_mode_auto_time_start" in attrs
        end_time_in_data = "dark_mode_auto_time_end" in attrs

        # Only perform validation if auto mode is being explicitly enabled or
        # if both start and end times are provided in the data and auto mode is currently enabled or being enabled.
        # Use getattr with instance fallback for fields not in attrs
        is_enabled = attrs.get(
            "dark_mode_auto_enabled",
            getattr(self.instance, "dark_mode_auto_enabled", False),
        )
        start_time = attrs.get(
            "dark_mode_auto_time_start",
            getattr(self.instance, "dark_mode_auto_time_start", None),
        )
        end_time = attrs.get(
            "dark_mode_auto_time_end",
            getattr(self.instance, "dark_mode_auto_time_end", None),
        )

        if is_enabled and start_time is not None and end_time is not None:
            if start_time >= end_time:
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

    @transaction.atomic  # Ensure User and Profile update together
    def update(self, instance: UserProfile, validated_data: dict) -> UserProfile:
        """Handles updating the UserProfile and its associated User instance."""
        user_data = validated_data.pop("user", None)

        # Handle nested User update if 'user' data is present
        if user_data:
            user_instance: User = instance.user
            # Iterate through user_data and update allowed fields on the User instance
            # Check against fields defined in AdminNestedUserSerializer fields (excluding read_only)
            allowed_user_fields = [
                f
                for f in AdminNestedUserSerializer.Meta.fields
                if f not in AdminNestedUserSerializer.Meta.read_only_fields
            ]
            for attr in allowed_user_fields:
                if attr in user_data:
                    value = user_data[attr]
                    # Add specific checks for sensitive fields if needed (e.g. is_staff, is_superuser)
                    # Role field is handled on UserProfile below, keep is_staff consistent.
                    if attr == "is_staff" and instance.role in [
                        RoleChoices.ADMIN,
                        RoleChoices.SUB_ADMIN,
                    ]:
                        # Automatically set is_staff True if role is admin/sub_admin, prevent setting False via user data
                        if value is False:
                            logger.warning(
                                f"Admin {self.context['request'].user.username} attempted to set is_staff=False for user {instance.user.username} with role {instance.role}. Ignoring."
                            )
                            continue  # Skip setting is_staff to False if role requires it
                        else:
                            user_instance.is_staff = True  # Ensure it's True
                    elif (
                        attr == "is_superuser"
                        and not self.context["request"].user.is_superuser
                    ):
                        logger.warning(
                            f"Admin {self.context['request'].user.username} (not superuser) attempted to change is_superuser for user {instance.user.username}. Ignoring."
                        )
                        continue  # Only superuser can change is_superuser

                    else:
                        setattr(user_instance, attr, value)

            user_instance.save()
            logger.debug(f"Admin updated User fields for user {instance.user.username}")

        # Update UserProfile fields
        # Iterate through validated_data for UserProfile fields
        for attr, value in validated_data.items():
            # Exclude fields that are read-only on the Profile serializer
            if attr in self.Meta.fields and attr not in self.Meta.read_only_fields:
                # Handle specific logic for role change if needed
                if attr == "role":
                    # Ensure is_staff is consistent with role change
                    if value in [RoleChoices.ADMIN, RoleChoices.SUB_ADMIN]:
                        instance.user.is_staff = True
                        instance.user.save(update_fields=["is_staff", "last_login"])
                    elif instance.user.is_staff and value == RoleChoices.STUDENT:
                        instance.user.is_staff = False
                        instance.user.save(update_fields=["is_staff", "last_login"])
                    # Log role changes
                    logger.info(
                        f"Admin {self.context['request'].user.username} changed role for user {instance.user.username} from {instance.role} to {value}"
                    )

                setattr(instance, attr, value)

        instance.save()
        logger.debug(
            f"Admin updated UserProfile fields for user {instance.user.username}"
        )
        return instance


# --- Admin Permission Serializer ---
class AdminPermissionSerializer(serializers.ModelSerializer):
    """Serializer for listing available admin permissions."""

    class Meta:
        model = AdminPermission
        fields = ["id", "slug", "name", "description"]
        read_only_fields = fields


# --- Serializer for Sub-Admin Creation/Update ---
class AdminSubAdminSerializer(serializers.ModelSerializer):
    """Serializer for creating and managing Sub-Admin accounts."""

    # User fields required for creation, write-only
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    # Password confirmation, write-only
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm Password"),
        style={"input_type": "password"},
    )

    # Permissions field - Read/Write ManyToManyField
    admin_permissions = AdminPermissionSerializer(
        many=True, read_only=True
    )  # Display permissions on GET
    # Use PrimaryKeyRelatedField for writing (list of permission IDs)
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=AdminPermission.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    # Nested serializer to display user info after creation/update (read-only)
    user = AdminNestedUserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",  # Read-only display after action
            "username",  # Write-only input
            "email",  # Write-only input
            "password",  # Write-only input
            "password_confirm",  # Write-only input
            "full_name",  # Required profile field
            "preferred_name",  # Optional profile field
            "gender",  # Optional profile field
            "role",  # Read-only, should be SUB_ADMIN
            "profile_picture",  # Read-only for now
            "admin_permissions",  # Read-only display of granted permissions
            "permission_ids",  # Write-only field for setting permissions
        ]
        read_only_fields = [
            "user",
            "role",
            "profile_picture",
            "admin_permissions",
        ]

    def validate(self, attrs: dict) -> dict:
        """Validate password confirmation and password complexity."""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )

        # Manually trigger password validation here
        # This applies AUTH_PASSWORD_VALIDATORS
        try:
            # Pass None for the user object during creation validation
            validate_password(attrs["password"], user=None)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})

        return attrs

    def validate_username(self, value: str) -> str:
        """Ensure username is unique (case-insensitive)."""
        # Check uniqueness excluding the current instance user during updates
        query = User.objects.filter(username__iexact=value)
        if self.instance and hasattr(self.instance, "user"):
            query = query.exclude(pk=self.instance.user.pk)
        if query.exists():
            raise serializers.ValidationError(
                _("A user with that username already exists.")
            )
        return value

    def validate_email(self, value: str) -> str:
        """Ensure email is unique (case-insensitive)."""
        # Check uniqueness excluding the current instance user during updates
        query = User.objects.filter(email__iexact=value)
        if self.instance and hasattr(self.instance, "user"):
            query = query.exclude(pk=self.instance.user.pk)
        if query.exists():
            raise serializers.ValidationError(
                _("A user with that email already exists.")
            )
        return value

    @transaction.atomic
    def create(self, validated_data: dict) -> UserProfile:
        """Creates User, gets the auto-created Profile, and updates it."""

        # Pop user/profile/permission fields that need specific handling
        username = validated_data.pop("username")
        email = validated_data.pop("email")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)  # Remove confirm password
        permission_ids = validated_data.pop(
            "permission_ids", []
        )  # List of permission IDs

        # Remaining items in validated_data are for the UserProfile
        # We only expect fields defined as editable in the serializer's fields
        profile_data = validated_data

        try:
            # 1. Create the User instance.
            #    This action *should* trigger a signal (or default ORM behavior)
            #    to automatically create the related UserProfile immediately.
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,  # Sub-admins must be staff
                is_superuser=False,
            )

            # 2. Retrieve the UserProfile instance that was *just* created
            #    automatically when the user was saved.
            #    Access it via the reverse relationship: user.profile
            #    We use select_for_update within the transaction to lock the profile row
            #    in case there's another process somehow trying to touch it (less likely here, but good practice).
            try:
                profile = UserProfile.objects.select_for_update().get(user=user)
            except UserProfile.DoesNotExist:
                # This case indicates the signal/auto-creation failed.
                # Log a critical error as this is unexpected setup failure.
                logger.critical(
                    f"UserProfile signal/auto-creation failed for new user {user.username} (ID: {user.id}) during sub-admin creation."
                )
                # Clean up the created User if possible, or raise a specific error
                # user.delete() # Consider deleting the user if profile is essential
                raise serializers.ValidationError(
                    _("Failed to create user profile automatically. Contact support.")
                )

            # 3. Update the attributes of the existing profile instance
            #    with the data provided in the serializer's validated_data.
            #    Ensure we only set fields allowed for creation/update via this serializer.
            #    The 'role' field is explicitly set for sub-admin creation.
            profile.role = RoleChoices.SUB_ADMIN  # Explicitly set the role

            # Iterate through the remaining profile_data and set attributes on the profile
            # Only set fields that are actually defined in the serializer's Meta fields
            # and are expected to be provided for a SUB_ADMIN creation.
            allowed_profile_fields = [
                f.name for f in self.Meta.model._meta.fields if f.name in profile_data
            ]
            for attr in allowed_profile_fields:
                # Exclude fields that should NOT be set directly like points, timestamps, etc.
                # The `profile_data` here should only contain 'full_name', 'preferred_name', 'gender' etc.
                # based on the `validated_data` after popping user/permission fields.
                # It's generally safe to set these basic profile fields.
                setattr(profile, attr, profile_data[attr])

            # 4. Save the updated profile instance.
            profile.save(
                update_fields=[
                    "role",
                    "full_name",
                    "preferred_name",
                    "gender",
                    "updated_at",
                ]
            )  # Explicitly update changed fields

            # 5. Assign granular permissions
            if permission_ids:
                # Ensure permission_ids are AdminPermission instances before setting
                # The PrimaryKeyRelatedField should return instances, but defensive check doesn't hurt.
                valid_permissions = [
                    p for p in permission_ids if isinstance(p, AdminPermission)
                ]
                profile.admin_permissions.set(valid_permissions)
            else:
                profile.admin_permissions.clear()  # Ensure no default permissions if none provided

            # Log the successful creation and permissions assignment
            assigned_slugs = [p.slug for p in profile.admin_permissions.all()]
            logger.info(
                f"Admin '{self.context['request'].user.username}' created sub-admin '{user.username}' (ID: {user.id}) with role {profile.role} and permissions: {assigned_slugs}."
            )

            # 6. Return the profile instance
            return profile

        # Catch IntegrityError for User creation (username/email unique)
        # These should ideally be caught by validate_username/validate_email first,
        # but catching here provides a fallback if something unexpected happens.
        except IntegrityError as e:
            logger.warning(f"IntegrityError creating sub-admin {username}: {e}")
            error_msg = str(e).lower()
            if "unique constraint" in error_msg:
                if "username" in error_msg:
                    raise serializers.ValidationError(
                        {"username": [_("A user with that username already exists.")]}
                    )
                elif "email" in error_msg:
                    raise serializers.ValidationError(
                        {"email": [_("A user with that email already exists.")]}
                    )
            # Re-raise if it's an unexpected IntegrityError
            raise serializers.ValidationError(
                _("Error creating sub-admin account due to a data conflict.")
            )
        except Exception as e:
            # Catch any other unexpected exceptions during the creation process
            logger.exception(f"Unexpected error creating sub-admin {username}: {e}")
            raise serializers.ValidationError(
                _("An unexpected error occurred during sub-admin creation.")
            )

    @transaction.atomic
    def update(self, instance: UserProfile, validated_data: dict) -> UserProfile:
        """Updates User and UserProfile fields for a sub-admin."""
        user_instance: User = instance.user

        # Handle User field updates (username, email, password)
        username = validated_data.pop("username", None)
        email = validated_data.pop("email", None)
        password = validated_data.pop(
            "password", None
        )  # Handle password separately if needed
        validated_data.pop("password_confirm", None)  # Remove confirm
        permission_ids = validated_data.pop("permission_ids", None)  # Permissions list

        if username is not None:
            if (
                User.objects.filter(username__iexact=username)
                .exclude(pk=user_instance.pk)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"username": _("A user with that username already exists.")}
                )
            user_instance.username = username

        if email is not None:
            if (
                User.objects.filter(email__iexact=email)
                .exclude(pk=user_instance.pk)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"email": _("A user with that email already exists.")}
                )
            user_instance.email = email

        # Password change should ideally be a separate action for clarity and logging
        # If allowing here:
        # if password:
        #     user_instance.set_password(password)
        #     logger.info(f"Admin {self.context['request'].user.username} changed password for sub-admin {user_instance.username} via update endpoint.")
        #     # Consider requiring re-authentication or notifying the user

        user_instance.save()
        logger.debug(
            f"Admin updated User fields for sub-admin {user_instance.username}"
        )

        # Update UserProfile fields
        # Explicitly handle profile fields allowed in Meta
        profile_fields = [
            "full_name",
            "preferred_name",
            "gender",
        ]  # Add other profile fields allowed for sub-admins
        for field in profile_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        # Update granular permissions
        if permission_ids is not None:  # Check if the field was provided in the request
            instance.admin_permissions.set(permission_ids)
            logger.info(
                f"Admin '{self.context['request'].user.username}' updated permissions for sub-admin '{instance.user.username}' to: {[p.slug for p in permission_ids]}."
            )

        instance.save()
        logger.debug(
            f"Admin updated UserProfile fields for sub-admin {user_instance.username}"
        )

        return instance


# --- Serializer for Admin Password Reset Request ---
# This serializer remains largely the same, it validates the input identifier
# The view will handle the logic of finding the user and calling the email utility
class AdminPasswordResetRequestSerializer(serializers.Serializer):
    """Serializer to identify the user for admin-initiated password reset."""

    identifier = serializers.CharField(
        required=True,
        write_only=True,
        help_text=_("Username or Email of the user to reset password for."),
    )
    # user = serializers.HiddenField(default=None, write_only=True) # Don't need HiddenField if view handles lookup

    # Validation happens in the view or a dedicated service to avoid leaking user existence


# --- Serializer for Admin Point Adjustment ---
# This serializer remains the same
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
    # reason_code = serializers.ChoiceField(choices=[(code, code) for code in PointReason.ADMIN_ADJUSTMENT_CODES], required=False)

    def validate_points_change(self, value):
        if value == 0:
            # Allow zero if there's a reason, maybe? Current validation prevents.
            # If admin wants to log a reason without changing points, they can't.
            # Keep current validation for now as it's 'adjustment'.
            raise serializers.ValidationError(_("Points change cannot be zero."))
        return value
