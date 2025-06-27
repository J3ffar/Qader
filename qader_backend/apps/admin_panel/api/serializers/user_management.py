import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)  # Renamed to avoid clash
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone

from apps.users.models import (
    UserProfile,
    RoleChoices,
    SerialCode,
    GenderChoices,
    DarkModePrefChoices,
)
from apps.users.api.serializers import SubscriptionDetailSerializer
from apps.admin_panel.models import AdminPermission

logger = logging.getLogger(__name__)


# --- Basic User Info Serializer (for nesting) ---
class AdminNestedUserSerializer(serializers.ModelSerializer):
    """Basic User info for nesting in Profile serializers."""

    username = serializers.CharField(required=False, validators=[])
    email = serializers.EmailField(required=False, validators=[])

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
        ]
        extra_kwargs = {
            "is_superuser": {
                "required": False,
                "read_only": True,
            },  # Superuser status typically managed by superusers only
            "is_staff": {"required": False},  # Staff status can be influenced by role
            "is_active": {"required": False},
            "email": {"required": False},  # Not always required on update
        }


# --- Serializer for Admin Permission (reused) ---
class AdminPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminPermission
        fields = ["id", "slug", "name", "description"]
        read_only_fields = fields


# --- Brief User Profile Serializer (for Mentees/Mentor display) ---
class BriefUserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "full_name",
            "preferred_name",
            "username",
            "email",
            "role",
        ]  # user_id is the PK of UserProfile
        read_only_fields = fields


# --- Serializer for User Creation (Admin) ---
class AdminUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        label=_("Confirm Password"),
        style={"input_type": "password"},
    )

    # For SUB_ADMIN role
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=AdminPermission.objects.all(),
        many=True,
        write_only=True,
        required=False,  # Only required if role is SUB_ADMIN
        source="admin_permissions",
    )

    # For TEACHER/TRAINER roles - list of student UserProfile IDs
    mentee_ids = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(role=RoleChoices.STUDENT),
        many=True,
        write_only=True,
        required=False,  # Only relevant for teacher/trainer roles
        source="mentees",
    )
    # Make role required for creation
    role = serializers.ChoiceField(choices=RoleChoices.choices, required=True)

    class Meta:
        model = UserProfile
        fields = [
            # User Model Fields (write-only)
            "username",
            "email",
            "password",
            "password_confirm",
            # UserProfile Model Fields
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "role",  # Now required
            # Conditional Write-Only Fields
            "permission_ids",  # For Sub-Admins
            "mentee_ids",  # For Teachers/Trainers
            # Potentially other fields settable on creation like language, etc.
            "language",
            "profile_picture",  # Allow setting on create
        ]
        extra_kwargs = {
            "preferred_name": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "gender": {"required": False, "allow_blank": True, "allow_null": True},
            "grade": {"required": False, "allow_blank": True, "allow_null": True},
            "has_taken_qiyas_before": {"required": False, "allow_null": True},
            "language": {"required": False},
            "profile_picture": {"required": False, "allow_null": True},
        }

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise DRFValidationError(_("A user with that username already exists."))
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise DRFValidationError(_("A user with that email already exists."))
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("password") != attrs.get("password_confirm"):
            raise DRFValidationError(
                {"password_confirm": _("Password fields didn't match.")}
            )

        # Validate role-specific fields
        role = attrs.get("role")
        if role == RoleChoices.SUB_ADMIN and not attrs.get("admin_permissions"):
            # Make permissions optional for sub-admin creation by not raising error
            # Or raise: DRFValidationError({"permission_ids": _("Permissions are required for Sub-Admins.")})
            pass
        if role not in [RoleChoices.TEACHER, RoleChoices.TRAINER] and attrs.get(
            "mentees"
        ):
            raise DRFValidationError(
                {
                    "mentee_ids": _(
                        "Mentees can only be assigned to Teachers or Trainers."
                    )
                }
            )
        if role != RoleChoices.SUB_ADMIN and attrs.get("admin_permissions"):
            raise DRFValidationError(
                {"permission_ids": _("Permissions can only be assigned to Sub-Admins.")}
            )

        # Auto-populate preferred_name
        if attrs.get("full_name") and not attrs.get("preferred_name"):
            attrs["preferred_name"] = attrs["full_name"]

        return attrs

    @transaction.atomic
    def create(self, validated_data: dict) -> UserProfile:
        user_data = {
            "username": validated_data.pop("username"),
            "email": validated_data.pop("email"),
            "password": validated_data.pop("password"),
        }
        validated_data.pop("password_confirm", None)

        role = validated_data.get("role")
        permissions_data = validated_data.pop("admin_permissions", None)
        mentees_data = validated_data.pop("mentees", None)

        # Determine is_staff based on role
        staff_roles = [
            RoleChoices.ADMIN,
            RoleChoices.SUB_ADMIN,
            RoleChoices.TEACHER,
            RoleChoices.TRAINER,
        ]
        user_data["is_staff"] = role in staff_roles
        user_data["is_superuser"] = (
            role == RoleChoices.ADMIN
        )  # Main Admin is also superuser by default in this setup

        try:
            user = User.objects.create_user(**user_data)
        except (
            IntegrityError
        ) as e:  # Should be caught by field validators, but as a fallback
            logger.error(f"IntegrityError during User creation: {e}")
            raise DRFValidationError(
                _(
                    "Failed to create user due to a data conflict (e.g., username/email)."
                )
            )

        # UserProfile is created by a signal. Fetch and update it.
        profile = UserProfile.objects.get(user=user)  # Or user.profile

        # Update profile with remaining validated_data
        for attr, value in validated_data.items():
            setattr(profile, attr, value)
        # Role is already in validated_data and will be set by loop above
        # profile.role = role # Explicitly set role if not covered by loop

        profile.save()  # This will trigger profile's save method including preferred_name logic

        if role == RoleChoices.SUB_ADMIN and permissions_data:
            profile.admin_permissions.set(permissions_data)

        if role in [RoleChoices.TEACHER, RoleChoices.TRAINER] and mentees_data:
            profile.mentees.set(mentees_data)

        logger.info(f"Admin created new user '{user.username}' (Role: {role}).")
        return profile


# --- Serializer for Listing Users (Admin) ---
class AdminUserListSerializer(serializers.ModelSerializer):
    user = AdminNestedUserSerializer(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    level_determined = serializers.BooleanField(read_only=True)
    subscription_expires_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",  # Contains user.id (UserProfile PK)
            "full_name",
            "preferred_name",
            "role",
            "points",
            "is_subscribed",
            "subscription_expires_at",
            "level_determined",
            "current_level_verbal",
            "current_level_quantitative",
            "created_at",
        ]
        # Add user_id for easier access to UserProfile pk
        fields.insert(0, "user_id")  # user_id here is UserProfile's PK


# --- Serializer for User Detail View & Update (Admin) ---
class AdminUserProfileSerializer(serializers.ModelSerializer):
    user = AdminNestedUserSerializer()
    subscription = SubscriptionDetailSerializer(source="*", read_only=True)
    subscription_expires_at = serializers.DateTimeField(required=False, allow_null=True)

    referral_code = serializers.CharField(read_only=True)
    referred_by_user = BriefUserProfileSerializer(
        source="referred_by.profile", read_only=True, allow_null=True
    )
    referrals_count = serializers.SerializerMethodField(read_only=True)
    earned_free_days = serializers.SerializerMethodField(read_only=True)

    # For SUB_ADMIN role (permissions)
    admin_permissions = AdminPermissionSerializer(many=True, read_only=True)  # For GET
    permission_ids = serializers.PrimaryKeyRelatedField(
        queryset=AdminPermission.objects.all(),
        source="admin_permissions",  # Source to the actual m2m field
        many=True,
        write_only=True,
        required=False,  # Not required for all roles or updates
        allow_null=True,
    )

    # For STUDENT role (mentor)
    assigned_mentor_details = BriefUserProfileSerializer(
        source="assigned_mentor", read_only=True, allow_null=True
    )
    assigned_mentor_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(
            role__in=[RoleChoices.TEACHER, RoleChoices.TRAINER]
        ),
        source="assigned_mentor",
        write_only=True,
        required=False,
        allow_null=True,
    )

    # For TEACHER/TRAINER roles (mentees)
    mentees_details = BriefUserProfileSerializer(
        source="mentees", many=True, read_only=True
    )  # Mentees is related_name
    mentee_ids = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.filter(role=RoleChoices.STUDENT),
        source="mentees",
        many=True,
        write_only=True,
        required=False,  # Not required for all roles or updates
        allow_null=True,
    )

    class Meta:
        model = UserProfile
        fields = [
            "user_id",  # UserProfile PK
            "user",
            "full_name",
            "preferred_name",
            "gender",
            "grade",
            "has_taken_qiyas_before",
            "profile_picture",
            "role",
            "subscription",
            "subscription_expires_at",
            "serial_code_used",
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "language",
            "current_level_verbal",
            "current_level_quantitative",
            "last_visited_study_option",
            "dark_mode_preference",
            "dark_mode_auto_enabled",
            "dark_mode_auto_time_start",
            "dark_mode_auto_time_end",
            "notify_reminders_enabled",
            "upcoming_test_date",
            "study_reminder_time",
            "referral_code",
            "referred_by_user",
            "referrals_count",
            "earned_free_days",
            # Permissions (for Sub-Admin)
            "admin_permissions",
            "permission_ids",
            # Mentor (for Student)
            "assigned_mentor_details",
            "assigned_mentor_id",
            # Mentees (for Teacher/Trainer)
            "mentees_details",
            "mentee_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "user_id",
            "profile_picture",  # Handle via separate upload endpoint or allow on update
            "points",
            "current_streak_days",
            "longest_streak_days",
            "last_study_activity_at",
            "referral_code",
            "referred_by_user",
            "created_at",
            "updated_at",
            "referrals_count",
            "earned_free_days",
            "subscription",
            "serial_code_used",
            "admin_permissions",
            "assigned_mentor_details",
            "mentees_details",
        ]
        extra_kwargs = {
            "preferred_name": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
            "gender": {"required": False, "allow_blank": True, "allow_null": True},
            "grade": {"required": False, "allow_blank": True, "allow_null": True},
            "has_taken_qiyas_before": {"required": False, "allow_null": True},
            "role": {
                "required": False
            },  # Role change handled with care in view/permissions
            "profile_picture": {"required": False, "allow_null": True},  # Allow update
        }

    def get_referrals_count(self, obj: UserProfile) -> int:
        if hasattr(obj, "user") and obj.user:
            return obj.user.referrals_made.count()
        return 0

    def get_earned_free_days(self, obj: UserProfile) -> int:
        referral_count = self.get_referrals_count(obj)
        days_per_referral = getattr(settings, "REFERRAL_BONUS_DAYS", 3)
        return referral_count * days_per_referral

    def validate(self, attrs: dict) -> dict:
        instance = self.instance  # The UserProfile instance being updated
        user_data = attrs.get("user")

        # --- START: Validation for unique User fields on update ---
        if user_data and instance:
            user_instance = instance.user  # The related User instance

            # Validate username if it's provided in the request
            new_username = user_data.get("username")
            if new_username:
                # Check if a *different* user already has this username
                if (
                    User.objects.filter(username__iexact=new_username)
                    .exclude(pk=user_instance.pk)
                    .exists()
                ):
                    raise DRFValidationError(
                        {
                            "user": {
                                "username": _(
                                    "A user with that username already exists."
                                )
                            }
                        }
                    )

            # Validate email if it's provided in the request
            new_email = user_data.get("email")
            if new_email:
                # Check if a *different* user already has this email
                if (
                    User.objects.filter(email__iexact=new_email)
                    .exclude(pk=user_instance.pk)
                    .exists()
                ):
                    raise DRFValidationError(
                        {"user": {"email": _("A user with that email already exists.")}}
                    )
        # --- END: Validation for unique User fields on update ---

        role_to_be_set = attrs.get("role", instance.role if instance else None)

        # Validate conditional fields based on role
        # Permissions
        if "admin_permissions" in attrs:  # permission_ids source to admin_permissions
            if role_to_be_set != RoleChoices.SUB_ADMIN and attrs.get(
                "admin_permissions"
            ):
                raise DRFValidationError(
                    {"permission_ids": _("Permissions can only be set for Sub-Admins.")}
                )

        # Mentees
        if "mentees" in attrs:  # mentee_ids source to mentees
            if role_to_be_set not in [
                RoleChoices.TEACHER,
                RoleChoices.TRAINER,
            ] and attrs.get("mentees"):
                raise DRFValidationError(
                    {
                        "mentee_ids": _(
                            "Mentees can only be assigned to Teachers or Trainers."
                        )
                    }
                )

        # Mentor
        if "assigned_mentor" in attrs:  # assigned_mentor_id source to assigned_mentor
            if role_to_be_set != RoleChoices.STUDENT and attrs.get("assigned_mentor"):
                raise DRFValidationError(
                    {
                        "assigned_mentor_id": _(
                            "A mentor can only be assigned to Students."
                        )
                    }
                )
            if (
                attrs.get("assigned_mentor") == instance
            ):  # Student cannot be their own mentor
                raise DRFValidationError(
                    {"assigned_mentor_id": _("User cannot be their own mentor.")}
                )

        # Auto-populate preferred_name if full_name is changing and preferred_name is not provided
        full_name = attrs.get("full_name")
        preferred_name = attrs.get("preferred_name")
        if full_name and not preferred_name:
            attrs["preferred_name"] = full_name

        return attrs

    @transaction.atomic
    def update(self, instance: UserProfile, validated_data: dict) -> UserProfile:
        user_data = validated_data.pop("user", None)

        # Handle User model update
        if user_data:
            user_instance: User = instance.user
            # Only superusers can change is_superuser
            if (
                "is_superuser" in user_data
                and not self.context["request"].user.is_superuser
            ):
                user_data.pop("is_superuser")
                logger.warning(
                    f"Non-superuser {self.context['request'].user.username} attempted to change is_superuser for {user_instance.username}. Ignored."
                )

            # Prevent non-superusers from making other users staff unless it's tied to a role they can assign
            if (
                "is_staff" in user_data
                and not self.context["request"].user.is_superuser
            ):
                # This logic is complex as is_staff is also tied to role.
                # The model's save() method handles is_staff based on role.
                # It's safer to let the role change dictate is_staff.
                # We can remove direct 'is_staff' manipulation by non-superusers here if role is also being set.
                # For now, if 'role' is not in validated_data, a non-superuser should not be able to toggle is_staff arbitrarily.
                if (
                    "role" not in validated_data
                ):  # If role is not changing, don't let non-superuser change is_staff
                    user_data.pop("is_staff")
                    logger.warning(
                        f"Non-superuser {self.context['request'].user.username} attempted to directly change is_staff for {user_instance.username} without role change. Ignored."
                    )

            for attr, value in user_data.items():
                setattr(user_instance, attr, value)
            user_instance.save()

        # Handle role-specific M2M/FK updates before general profile update
        # These fields (permissions, mentees, mentor) were sourced correctly
        permissions_data = validated_data.pop("admin_permissions", None)
        mentees_data = validated_data.pop("mentees", None)
        mentor_data = validated_data.pop("assigned_mentor", None)  # This is FK, not M2M

        # Update UserProfile fields
        current_role = instance.role
        new_role = validated_data.get("role", current_role)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Call instance.save() before M2M to ensure instance has PK and role is updated
        # The model's save() method will handle preferred_name, is_staff consistency with role
        instance.save()

        # Post-save M2M/FK updates based on the (potentially new) role
        if new_role == RoleChoices.SUB_ADMIN:
            if (
                permissions_data is not None
            ):  # if key was present, even if null (to clear)
                instance.admin_permissions.set(permissions_data)
        elif (
            instance.admin_permissions.exists()
        ):  # If role changed from SUB_ADMIN, clear perms
            instance.admin_permissions.clear()

        if new_role in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
            if mentees_data is not None:
                instance.mentees.set(mentees_data)
        elif (
            instance.mentees.exists()
        ):  # If role changed from Teacher/Trainer, clear their list of mentees
            # This means students previously assigned to this user will have their 'assigned_mentor' field become null.
            instance.mentees.clear()

        # assigned_mentor is a direct FK on UserProfile, already handled by setattr and instance.save()
        # The model's save() method also clears assigned_mentor if role is not STUDENT.

        logger.info(
            f"Admin '{self.context['request'].user.username}' updated profile for user '{instance.user.username}'."
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
