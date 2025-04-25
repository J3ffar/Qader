import logging
from django.contrib.auth.models import User

# Removed send_admin_password_reset_email import - moving to utils
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from django.db import transaction  # Ensure atomicity where needed

from apps.users.models import UserProfile, RoleChoices
from apps.users.utils import send_password_reset_email  # Import from utils
from apps.gamification.services import award_points, PointReason
from apps.admin_panel.models import AdminPermission
from apps.admin_panel.filters import AdminUserProfileFilter  # Import permission model

from ..serializers.user_management import (
    AdminUserListSerializer,
    AdminUserProfileSerializer,
    AdminSubAdminSerializer,
    AdminPasswordResetRequestSerializer,
    AdminPointAdjustmentSerializer,
    AdminPermissionSerializer,  # Import new serializer
)
from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import custom permission

logger = logging.getLogger(__name__)


# --- Helper View for Permissions List ---
@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="List all available admin permissions.",
)
class PermissionListView(generics.ListAPIView):
    """Lists all available granular admin permissions."""

    # Only superusers or main admins should see/assign all permissions
    # Or perhaps sub-admins with a specific 'view_permissions' permission?
    # Let's require main admin/superuser for now.
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    # No specific granular permission slug needed for *this* view,
    # but the permission class itself filters based on base admin role.
    # required_permissions = [] # Can be explicitly empty

    serializer_class = AdminPermissionSerializer
    queryset = AdminPermission.objects.all().order_by("name")
    # No filtering or search needed for a simple list


# --- User Management ViewSet (All Users) ---
@extend_schema_view(
    list=extend_schema(
        tags=["Admin Panel - User Management"], summary="List All Users (Admin)"
    ),
    retrieve=extend_schema(
        tags=["Admin Panel - User Management"], summary="Retrieve User Details (Admin)"
    ),
    partial_update=extend_schema(
        tags=["Admin Panel - User Management"], summary="Update User Details (Admin)"
    ),
    destroy=extend_schema(
        tags=["Admin Panel - User Management"], summary="Delete User (SuperAdmin Only)"
    ),  # Added destroy schema
)
class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset for listing, retrieving, updating, and deleting User Profiles.
    Requires appropriate admin or sub-admin permissions.
    """

    # Use custom permission class. Define required permissions per action.
    permission_classes = [IsAdminUserOrSubAdminWithPermission]

    # Define required permissions for standard actions
    # Overridden in methods using @action or by checking self.action
    # This is more explicit on methods below.

    queryset = (
        UserProfile.objects.select_related("user")
        .prefetch_related("user__referrals_made")  # Prefetch referred_by count source
        .all()
        .order_by("-user__date_joined")
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AdminUserProfileFilter
    search_fields = ["user__username", "user__email", "full_name", "preferred_name"]
    ordering_fields = [
        "user__date_joined",
        "user__last_login",
        "points",
        "full_name",
        "user__username",
        "current_level_verbal",
        "current_level_quantitative",
        "subscription_expires_at",
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return AdminUserListSerializer
        # Use the detail serializer for retrieve, update, partial_update
        return AdminUserProfileSerializer

    def get_permissions(self):
        """Instantiates and returns the list of permissions that this view requires."""
        # Define required permissions based on action
        if self.action == "list":
            self.required_permissions = [
                "view_users"
            ]  # Sub-admins need this to list users
        elif self.action == "retrieve":
            self.required_permissions = [
                "view_users",
                "view_user_data",
            ]  # Need more specific perm to see details? Or combine? Let's use view_user_data for details.
            # Or maybe: ['view_users'] is enough, and view_user_data is for a deeper drilldown endpoint?
            # Let's stick to view_user_data for the detail view /admin/users/{id}/
            self.required_permissions = ["view_user_data"]
        elif self.action in ["update", "partial_update"]:
            self.required_permissions = [
                "edit_users"
            ]  # Sub-admins need this to edit users
        elif self.action == "destroy":
            # Only superusers should be able to delete users
            if not self.request.user.is_superuser:
                raise PermissionDenied("Only superusers can delete users.")
            self.required_permissions = []  # Superuser doesn't need granular perm check
        else:
            self.required_permissions = []  # Default, deny unless handled

        return [permission() for permission in self.permission_classes]

    # The update/partial_update methods are inherited and use the serializer's update() method.
    # We just need to ensure the PATCH method is allowed in the router config or here.
    # DefaultRouter allows PATCH on detail view for ModelViewSet if serializer is writeable.
    # ReadOnlyModelViewSet doesn't include update/partial_update by default.
    # We need to explicitly add these methods or change the base class if allowing more.
    # Let's override the methods to add permission check and logging.

    @extend_schema(
        tags=["Admin Panel - User Management"], summary="Update User Details (Admin)"
    )
    def update(self, request, *args, **kwargs):
        """Handles PUT requests to update a user profile."""
        # get_permissions() is called before the method, handling the primary check
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=False
        )  # Use partial=False for PUT
        serializer.is_valid(raise_exception=True)

        # Ensure role changes require superuser? Add validation here or in serializer.
        if (
            "role" in serializer.validated_data
            and serializer.validated_data["role"] != instance.role
        ):
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can change user roles.")

        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied, clear the cache to force re-fetch
            # This ensures relationships like referrals_made are up-to-date in the response
            instance._prefetched_objects_cache = {}

        logger.info(
            f"Admin '{request.user.username}' (ID: {request.user.id}) updated profile for user '{instance.user.username}' (ID: {instance.user.id})"
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Admin Panel - User Management"],
        summary="Partially Update User Details (Admin)",
    )
    def partial_update(self, request, *args, **kwargs):
        """Handles PATCH requests to partially update a user profile."""
        # get_permissions() is called before the method
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )  # Use partial=True for PATCH
        serializer.is_valid(raise_exception=True)

        # Ensure role changes require superuser?
        if (
            "role" in serializer.validated_data
            and serializer.validated_data["role"] != instance.role
        ):
            if not request.user.is_superuser:
                raise PermissionDenied("Only superusers can change user roles.")

        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}  # Clear cache

        logger.info(
            f"Admin '{request.user.username}' (ID: {request.user.id}) partially updated profile for user '{instance.user.username}' (ID: {instance.user.id})"
        )
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()  # Calls serializer.update()

    # Add the destroy method for deleting users (SuperAdmin only)
    @extend_schema(
        tags=["Admin Panel - User Management"], summary="Delete User (SuperAdmin Only)"
    )
    def destroy(self, request, *args, **kwargs):
        """Handles DELETE requests to delete a user."""
        # Permission check is handled in get_permissions()
        instance: UserProfile = self.get_object()
        user_id = instance.user.id
        username = instance.user.username

        # Perform the deletion (deleting User cascades to UserProfile)
        with transaction.atomic():  # Ensure atomicity
            instance.user.delete()

        logger.warning(
            f"SuperAdmin '{request.user.username}' (ID: {request.user.id}) DELETED user '{username}' (ID: {user_id})"
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Sub-Admin Management ViewSet ---
@extend_schema_view(
    list=extend_schema(
        tags=["Admin Panel - User Management"], summary="List Sub-Admins (Admin)"
    ),
    create=extend_schema(
        tags=["Admin Panel - User Management"], summary="Create Sub-Admin (Admin)"
    ),
    retrieve=extend_schema(
        tags=["Admin Panel - User Management"],
        summary="Retrieve Sub-Admin Details (Admin)",
    ),
    update=extend_schema(
        tags=["Admin Panel - User Management"], summary="Update Sub-Admin (Admin)"
    ),
    partial_update=extend_schema(
        tags=["Admin Panel - User Management"],
        summary="Partially Update Sub-Admin (Admin)",
    ),
    destroy=extend_schema(
        tags=["Admin Panel - User Management"], summary="Delete Sub-Admin (Admin)"
    ),
)
class AdminSubAdminViewSet(viewsets.ModelViewSet):
    """Admin viewset for managing Sub-Admin accounts."""

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    serializer_class = AdminSubAdminSerializer

    queryset = (
        UserProfile.objects.select_related("user")
        .prefetch_related(
            "admin_permissions"
        )  # Prefetch permissions for detail/list view
        .filter(role=RoleChoices.SUB_ADMIN)
        .order_by("-user__date_joined")
    )
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["user__username", "user__email", "full_name"]
    ordering_fields = ["user__date_joined", "full_name", "user__username"]

    def get_permissions(self):
        """Instantiates and returns the list of permissions that this view requires."""
        # Define required permissions based on action
        if self.action == "list":
            # Anyone with 'view_sub_admins' can list
            self.required_permissions = ["view_sub_admins"]
        elif self.action == "create":
            # Only SuperAdmins or specific admins can create sub-admins
            # Assumes IsAdminUserOrSubAdminWithPermission handles superuser implicitly
            self.required_permissions = ["create_sub_admins"]
        elif self.action in ["retrieve", "update", "partial_update"]:
            # Only admins with 'edit_sub_admins' can view/edit details
            self.required_permissions = ["edit_sub_admins"]
        elif self.action == "destroy":
            # Only admins with 'delete_sub_admins' can delete
            self.required_permissions = ["delete_sub_admins"]
        else:
            self.required_permissions = []  # Default, deny

        return [permission() for permission in self.permission_classes]

    # perform_create, perform_update, perform_destroy handle logging correctly


# --- Specific Admin Action Views ---


@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Trigger Password Reset for User (Admin)",
    description="Sends a password reset email to the specified user ID.",
)
class AdminPasswordResetView(generics.GenericAPIView):
    """Triggers a password reset email for a specific user."""

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["reset_user_password"]  # Specific permission needed
    serializer_class = AdminPasswordResetRequestSerializer  # Used for identifying user by identifier *within the view*, not URL

    # Overriding POST to use user_id from URL
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="The ID of the user to reset password for.",
            )
        ],
        request=None,  # Request body is not needed as user_id is in path
        responses={
            200: {"detail": "message"},
            404: {"detail": "Not found"},
            403: {"detail": "Permission denied"},
        },
    )
    def post(self, request, user_id):
        # get_permissions() is called before this method

        # Ensure the user exists
        target_user = get_object_or_404(User, pk=user_id)

        # Double-check permission if needed (e.g., admin shouldn't reset password of *another* admin)
        # Example check: Prevent sub-admin from resetting password of main admin or other sub-admins
        if (
            target_user.is_staff
            and request.user != target_user
            and not request.user.is_superuser
        ):
            # Check if the target user is an admin/sub-admin and current user is NOT superuser
            target_profile = getattr(target_user, "profile", None)
            if target_profile and target_profile.role in [
                RoleChoices.ADMIN,
                RoleChoices.SUB_ADMIN,
            ]:
                logger.warning(
                    f"Admin '{request.user.username}' (ID: {request.user.id}) attempted to reset password for admin user '{target_user.username}' (ID: {target_user.id}). Permission denied."
                )
                raise PermissionDenied(
                    "You do not have permission to reset the password for this type of user."
                )

        # Call the moved utility function
        if send_password_reset_email(
            target_user, context={"admin_initiated": True}
        ):  # Add context flag if needed
            logger.info(
                f"Admin '{request.user.username}' (ID: {request.user.id}) triggered password reset email for user '{target_user.username}' (ID: {target_user.id})"
            )
            return Response(
                {"detail": _("Password reset email sent successfully.")},
                status=status.HTTP_200_OK,
            )
        else:
            logger.error(
                f"Admin '{request.user.username}' (ID: {request.user.id}) failed to send password reset email for user '{target_user.username}' (ID: {target_user.id})"
            )
            return Response(
                {"detail": _("Failed to send password reset email.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Note: The AdminPasswordResetRequestSerializer is not directly used by this view's POST method with user_id in the URL.
# If the requirement was to identify the user by username/email in the *request body* instead of URL ID,
# then a different view structure (like the original serializer + post method) would be needed,
# and the lookup would happen within the view's post method using the serializer's data.
# Given the URL structure, the serializer is only for documentation purposes here, or if a different endpoint used it.
# Let's update the URL config to reflect it takes user_id.
# The serializer would be useful for an endpoint like /admin/users/reset-password/ (without id in URL).


@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Adjust User Points (Admin)",
    description="Adds or subtracts points from a specified user's account.",
)
class AdminPointAdjustmentView(generics.GenericAPIView):
    """Allows Admin to add or subtract points from a user's account."""

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["manage_user_points"]  # Specific permission needed
    serializer_class = AdminPointAdjustmentSerializer

    def post(self, request, user_id):
        # get_permissions() is called before this method
        target_user = get_object_or_404(
            User.objects.select_related("profile"), pk=user_id
        )

        # Add object-level permission check if sub-admins should only adjust points for *certain* users
        # E.g., if a school admin can only adjust points for students in their school.
        # This would require implementing has_object_permission in IsAdminUserOrSubAdminWithPermission
        # and adding required_object_permissions = ['manage_user_points'] here.
        # For now, assume permission applies to all users visible to the admin type.

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        points_change = serializer.validated_data["points_change"]
        reason = serializer.validated_data["reason"]

        try:
            # Call the award_points service
            # Ensure related_object is the *admin* user performing the action for logging
            success = award_points(
                user=target_user,
                points_change=points_change,
                reason_code=PointReason.ADMIN_ADJUSTMENT,
                description=f"Admin adjustment: {reason}",  # Reason should be logged
                # metadata={
                #     "admin_user_id": request.user.id,
                #     "admin_username": request.user.username,
                #     "admin_reason": reason,
                # },  # Add admin context to metadata
                related_object=target_user.profile,  # Log the user profile being adjusted
            )

            if success:
                target_user.profile.refresh_from_db()  # Get updated points total
                logger.info(
                    f"Admin '{request.user.username}' (ID: {request.user.id}) adjusted points for user '{target_user.username}' (ID: {target_user.id}) by {points_change}. New total: {target_user.profile.points}. Reason: {reason}"
                )
                return Response(
                    {
                        "detail": _("Points adjusted successfully."),
                        "user_id": target_user.id,
                        "username": target_user.username,
                        "points_change": points_change,
                        "new_total_points": target_user.profile.points,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # award_points service should return False on failure and log the reason
                # If the service returns False without raising an exception, it's a service-level issue.
                logger.error(
                    f"Admin '{request.user.username}' (ID: {request.user.id}) failed to adjust points for user '{target_user.username}' (ID: {target_user.id}) by {points_change}. Reason: {reason}. award_points service returned False."
                )
                return Response(
                    {"detail": _("Failed to adjust points.")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            # Catch any unexpected exceptions during the process
            logger.exception(
                f"Unexpected error during admin point adjustment by '{request.user.username}' (ID: {request.user.id}) for user '{target_user.username}' (ID: {target_user.id}): {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred during point adjustment.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
