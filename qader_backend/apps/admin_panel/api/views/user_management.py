import logging
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    MultipleChoiceFilter,
)  # For MultipleChoiceFilter
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from django.db import transaction

from apps.users.models import UserProfile, RoleChoices
from apps.users.utils import send_password_reset_email
from apps.gamification.services import award_points, PointReason
from apps.admin_panel.models import AdminPermission

# from apps.admin_panel.filters import AdminUserProfileFilter # We will define it here or import if separate

from ..serializers.user_management import (
    AdminUserListSerializer,
    AdminUserProfileSerializer,
    AdminUserCreateSerializer,  # New serializer
    AdminPasswordResetRequestSerializer,
    AdminPointAdjustmentSerializer,
    AdminPermissionSerializer,
)
from ..permissions import IsAdminUserOrSubAdminWithPermission

logger = logging.getLogger(__name__)


# --- Filter for User Profiles ---
class AdminUserProfileFilter(FilterSet):
    role = MultipleChoiceFilter(choices=RoleChoices.choices)

    class Meta:
        model = UserProfile
        fields = {  # Using dictionary format for more control over lookup_expr if needed
            "user__username": [
                "exact",
                "icontains",
            ],  # If you want specific username filtering via FilterSet
            "user__email": [
                "exact",
                "icontains",
            ],  # If you want specific email filtering via FilterSet
            "role": ["exact"],  # MultipleChoiceFilter handles this well by default
            "account_type": ["exact"],
            # 'is_subscribed' is a property, cannot be directly filtered by FilterSet without a custom method.
            # Consider filtering on 'subscription_expires_at' (e.g., __isnull=False)
            "user__is_active": ["exact"],
        }


# --- Helper View for Permissions List (remains the same) ---
@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="List all available admin permissions.",
)
class PermissionListView(generics.ListAPIView):
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    serializer_class = AdminPermissionSerializer
    queryset = AdminPermission.objects.all().order_by("name")


# --- Unified User Management ViewSet ---
@extend_schema_view(
    list=extend_schema(
        tags=["Admin Panel - User Management"], summary="List All Users"
    ),
    create=extend_schema(
        tags=["Admin Panel - User Management"], summary="Create New User"
    ),
    retrieve=extend_schema(
        tags=["Admin Panel - User Management"], summary="Retrieve User Details"
    ),
    update=extend_schema(
        tags=["Admin Panel - User Management"], summary="Update User (Full)"
    ),
    partial_update=extend_schema(
        tags=["Admin Panel - User Management"], summary="Update User (Partial)"
    ),
    destroy=extend_schema(
        tags=["Admin Panel - User Management"], summary="Delete User (SuperAdmin Only)"
    ),
)
class AdminUserViewSet(viewsets.ModelViewSet):  # Changed from ReadOnlyModelViewSet
    """
    Admin viewset for listing, creating, retrieving, updating, and deleting User Profiles.
    """

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    queryset = (
        UserProfile.objects.select_related(
            "user", "assigned_mentor__user", "referred_by__profile"
        )
        .prefetch_related("admin_permissions", "mentees__user", "user__referrals_made")
        .all()
        .order_by("-user__date_joined")
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AdminUserProfileFilter  # Use the defined filter class
    search_fields = [
        "user__username",
        "user__email",
        "full_name",
        "preferred_name",
    ]  # For SearchFilter
    ordering_fields = [
        "user__date_joined",
        "user__last_login",
        "points",
        "full_name",
        "user__username",
        "role",
        "subscription_expires_at",
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return AdminUserListSerializer
        elif self.action == "create":
            return AdminUserCreateSerializer
        # For retrieve, update, partial_update
        return AdminUserProfileSerializer

    def get_permissions(self):
        if self.action == "list":
            self.required_permissions = ["view_users"]
        elif self.action == "create":
            self.required_permissions = ["create_users"]  # New permission slug needed
        elif self.action == "retrieve":
            self.required_permissions = ["view_user_data"]
        elif self.action in ["update", "partial_update"]:
            self.required_permissions = ["edit_users"]
        elif self.action == "destroy":
            # For destroy, require 'api_manage_users' permission.
            # The superuser check within the destroy method will still apply.
            self.required_permissions = ["api_manage_users"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        # Role validation for creation (who can create whom)
        request_user = self.request.user
        requested_role = serializer.validated_data.get("role")

        if (
            not request_user.is_superuser
            and request_user.profile.role != RoleChoices.ADMIN
        ):
            # Sub-Admins or other staff roles creating users
            if requested_role in [RoleChoices.ADMIN, RoleChoices.SUB_ADMIN]:
                raise PermissionDenied(
                    _("You do not have permission to create Admin or Sub-Admin users.")
                )
            # Potentially restrict sub-admins to only create students, or teachers within their scope
            # For now, 'create_users' permission allows creating non-admin/sub-admin roles.

        user_profile = serializer.save()
        logger.info(
            f"Admin '{request_user.username}' created user '{user_profile.user.username}' with role '{user_profile.role}'."
        )

    def perform_update(self, serializer):
        request_user = self.request.user
        instance = serializer.instance  # UserProfile instance being updated
        requested_role_change = (
            "role" in serializer.validated_data
            and serializer.validated_data["role"] != instance.role
        )
        target_role_is_privileged = instance.role in [
            RoleChoices.ADMIN,
            RoleChoices.SUB_ADMIN,
        ] or (
            requested_role_change
            and serializer.validated_data["role"]
            in [RoleChoices.ADMIN, RoleChoices.SUB_ADMIN]
        )

        if not request_user.is_superuser:
            # Prevent non-superusers from editing Admins/Sub-Admins
            if (
                instance.role in [RoleChoices.ADMIN, RoleChoices.SUB_ADMIN]
                and instance.user != request_user
            ):
                raise PermissionDenied(
                    _(
                        "You do not have permission to edit Admin or Sub-Admin users other than yourself (if applicable)."
                    )
                )
            # Prevent non-superusers from promoting users to Admin/Sub-Admin
            if requested_role_change and serializer.validated_data["role"] in [
                RoleChoices.ADMIN,
                RoleChoices.SUB_ADMIN,
            ]:
                raise PermissionDenied(
                    _("You do not have permission to assign Admin or Sub-Admin roles.")
                )

        serializer.save()
        logger.info(
            f"Admin '{request_user.username}' updated user '{instance.user.username}'."
        )

    def destroy(self, request, *args, **kwargs):
        instance: UserProfile = self.get_object()
        user_to_delete = instance.user  # Get the User model instance
        username_log = user_to_delete.username
        user_id_log = user_to_delete.id

        # Only Superusers can delete users
        if not request.user.is_superuser:
            # Also, prevent admins from deleting themselves if that's a requirement
            # if instance.user == request.user:
            #     raise PermissionDenied(_("You cannot delete your own account."))
            raise PermissionDenied(_("Only superusers can delete users."))

        # Deleting the User object will cascade and delete the UserProfile.
        with transaction.atomic():
            user_to_delete.delete()

        logger.warning(
            f"SuperAdmin '{request.user.username}' DELETED user '{username_log}' (ID: {user_id_log})."
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# Remove AdminSubAdminViewSet, as its functionality is merged into AdminUserViewSet.

# --- Specific Admin Action Views (AdminPasswordResetView, AdminPointAdjustmentView) ---
# These can remain the same as they operate on specific actions via user_id.
# Ensure their 'required_permissions' align with your new permission model.
# (Keep AdminPasswordResetView and AdminPointAdjustmentView as they were)


@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Trigger Password Reset for User (Admin)",
    description="Sends a password reset email to the specified user ID.",
)
class AdminPasswordResetView(generics.GenericAPIView):
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["reset_user_password"]
    # serializer_class = AdminPasswordResetRequestSerializer # Not strictly needed if user_id is from URL

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH
            )
        ],
        request=None,  # No request body needed
    )
    def post(self, request, user_id):  # user_id here refers to User.pk
        target_user = get_object_or_404(User, pk=user_id)
        requesting_user_profile = getattr(request.user, "profile", None)

        # Security: Prevent sub-admins from resetting passwords of Admins or other Sub-Admins (unless superuser)
        if not request.user.is_superuser:
            target_profile = getattr(target_user, "profile", None)
            if target_profile and target_profile.role in [
                RoleChoices.ADMIN,
                RoleChoices.SUB_ADMIN,
            ]:
                # Allow resetting own password if they are a sub-admin (covered by general permission)
                # But prevent resetting *other* admins/sub-admins
                if target_user != request.user:
                    logger.warning(
                        f"User '{request.user.username}' attempted to reset password for admin/sub-admin '{target_user.username}'. Denied."
                    )
                    raise PermissionDenied(
                        _(
                            "You do not have permission to reset the password for this user type."
                        )
                    )

        if send_password_reset_email(target_user, context={"admin_initiated": True}):
            logger.info(
                f"Admin '{request.user.username}' triggered password reset for user '{target_user.username}'."
            )
            return Response(
                {"detail": _("Password reset email sent successfully.")},
                status=status.HTTP_200_OK,
            )
        else:
            logger.error(
                f"Failed to send password reset email for user '{target_user.username}' by admin '{request.user.username}'."
            )
            return Response(
                {"detail": _("Failed to send password reset email.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Adjust User Points (Admin)",
)
class AdminPointAdjustmentView(generics.GenericAPIView):
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["manage_user_points"]
    serializer_class = AdminPointAdjustmentSerializer

    def post(self, request, user_id):  # user_id here refers to User.pk
        target_user_profile = get_object_or_404(
            UserProfile.objects.select_related("user"), user_id=user_id
        )
        target_user = target_user_profile.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        points_change = serializer.validated_data["points_change"]
        reason = serializer.validated_data["reason"]

        try:
            success = award_points(
                user=target_user,
                points_change=points_change,
                reason_code=PointReason.ADMIN_ADJUSTMENT,
                description=f"Admin adjustment: {reason}",
                related_object=request.user,  # Admin performing action
            )
            if success:
                target_user_profile.refresh_from_db()
                logger.info(
                    f"Admin '{request.user.username}' adjusted points for user '{target_user.username}' by {points_change}. New total: {target_user_profile.points}. Reason: {reason}"
                )
                return Response(
                    {
                        "detail": _("Points adjusted successfully."),
                        "user_id": target_user.id,
                        "new_total_points": target_user_profile.points,
                    },
                    status=status.HTTP_200_OK,
                )
            else:  # Should be rare if award_points is robust
                raise DRFValidationError(
                    _("Failed to adjust points due to an internal issue.")
                )
        except Exception as e:
            logger.exception(
                f"Error adjusting points for {target_user.username} by {request.user.username}: {e}"
            )
            # Convert non-DRF exceptions to DRFValidationError for consistent API response
            if not isinstance(e, DRFValidationError):
                raise DRFValidationError(str(e))
            raise e
