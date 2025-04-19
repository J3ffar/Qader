import logging
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from decouple import config

from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAdminUser  # Requires is_staff=True

# from rest_framework.permissions import IsSuperUser # If needed for stricter actions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.users.models import UserProfile, RoleChoices
from apps.gamification.services import award_points, PointReason

# from apps.users.utils import send_password_reset_email # TODO: Refactor email logic here
from ..serializers.user_management import (
    AdminUserListSerializer,
    AdminUserProfileSerializer,
    AdminSubAdminSerializer,
    AdminPasswordResetRequestSerializer,
    AdminPointAdjustmentSerializer,
)

# from ..permissions import IsSuperAdminOrSubAdminWithPermission # TODO: Implement custom permissions

logger = logging.getLogger(__name__)


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
)
class AdminUserViewSet(
    viewsets.ReadOnlyModelViewSet
):  # Primarily read-only for safety, use PATCH on detail for edits
    """
    Admin viewset for listing and retrieving User Profiles.
    Updates are handled via the detail view's PATCH method.
    """

    permission_classes = [IsAdminUser]  # Base permission: must be staff
    queryset = (
        UserProfile.objects.select_related("user").all().order_by("-user__date_joined")
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "user__is_active": ["exact"],
        "role": ["exact"],
        "user__date_joined": ["gte", "lte", "exact"],
        "subscription_expires_at": ["isnull", "gte", "lte"],
    }
    search_fields = ["user__username", "user__email", "full_name"]
    ordering_fields = [
        "user__date_joined",
        "user__last_login",
        "points",
        "full_name",
        "user__username",
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return AdminUserListSerializer
        # Use the detail serializer for retrieve, update, partial_update
        return AdminUserProfileSerializer

    # Allow PATCH for updating user details via the detail route (e.g., /admin/users/{user_id}/)
    def get_allowed_methods(self):
        """Allow PATCH on detail view."""
        methods = super().get_allowed_methods()
        if self.action in ["retrieve", "update", "partial_update"]:
            methods.append("PATCH")
        return methods

    def update(self, request, *args, **kwargs):
        # Note: The update logic is handled by RetrieveUpdateDestroyAPIView parent class
        # using the AdminUserProfileSerializer's update method.
        # We just need to allow the PATCH method.
        partial = kwargs.pop("partial", True)  # Force partial update for PATCH
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        logger.info(
            f"Admin {request.user.username} updated profile for user ID {instance.user.id}"
        )
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()  # Calls serializer.update()

    # If you need to allow DELETING users (use with extreme caution!)
    # Add 'destroy' method and potentially check for superuser status.
    # def destroy(self, request, *args, **kwargs):
    #     if not request.user.is_superuser:
    #         return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
    #     instance = self.get_object()
    #     user_id = instance.user.id
    #     self.perform_destroy(instance.user) # Delete the User, profile cascades
    #     logger.warning(f"Admin {request.user.username} DELETED user ID {user_id}")
    #     return Response(status=status.HTTP_204_NO_CONTENT)


# --- Sub-Admin Management ViewSet ---
# TODO: Add permission checking based on a 'permissions' field on UserProfile model
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

    permission_classes = [
        IsAdminUser
    ]  # TODO: Replace/augment with IsSuperAdminOrSubAdminWithPermission('manage_subadmins')
    serializer_class = AdminSubAdminSerializer
    queryset = (
        UserProfile.objects.select_related("user")
        .filter(role=RoleChoices.SUB_ADMIN)
        .order_by("-user__date_joined")
    )
    # Add filtering/searching if needed
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["user__username", "user__email", "full_name"]
    ordering_fields = ["user__date_joined", "full_name", "user__username"]

    def perform_create(self, serializer):
        profile = serializer.save()  # Serializer handles User and Profile creation
        logger.info(
            f"Admin {self.request.user.username} created sub-admin {profile.user.username}"
        )

    def perform_update(self, serializer):
        profile = serializer.save()
        logger.info(
            f"Admin {self.request.user.username} updated sub-admin {profile.user.username}"
        )

    def perform_destroy(self, instance: UserProfile):
        user_id = instance.user.id
        username = instance.user.username
        # Delete the User object; the UserProfile will cascade delete
        instance.user.delete()
        logger.warning(
            f"Admin {self.request.user.username} DELETED sub-admin {username} (ID: {user_id})"
        )


# --- Specific Admin Action Views ---


# TODO: Refactor email sending logic into a reusable function in apps/users/utils.py
@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Trigger Password Reset for User (Admin)",
    description="Sends a password reset email to the specified user ID.",
)
def send_admin_password_reset_email(user: User):
    """Sends the password reset email. (Refactor Target)"""
    try:
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_url = config(
            "PASSWORD_RESET_URL", default="https://example.com/reset-password-confirm"
        )
        reset_link = f"{frontend_url}/{uidb64}/{token}/"

        context = {
            "email": user.email,
            "username": user.username,
            "reset_link": reset_link,
            "site_name": "Qader Platform",
            "user": user,
        }
        subject = render_to_string("emails/password_reset_subject.txt", context).strip()
        html_body = render_to_string("emails/password_reset_body.html", context)
        text_body = render_to_string("emails/password_reset_body.txt", context)

        msg = EmailMultiAlternatives(
            subject, text_body, settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(
            f"Admin-initiated password reset email sent successfully to {user.email}"
        )
        return True
    except Exception as e:
        logger.exception(
            f"Error sending admin-initiated password reset email to {user.email}: {e}"
        )
        return False


class AdminPasswordResetView(generics.GenericAPIView):
    """Triggers a password reset email for a specific user."""

    permission_classes = [IsAdminUser]  # TODO: Add specific sub-admin permission check
    serializer_class = AdminPasswordResetRequestSerializer

    def post(self, request, user_id):
        target_user = get_object_or_404(User, pk=user_id)

        # Optional: Check if admin has permission to reset this user's password
        # (e.g., superadmin can reset anyone, sub-admin can reset students only?)
        # if not has_permission_to_reset(request.user, target_user):
        #     return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        if send_admin_password_reset_email(target_user):
            return Response(
                {"detail": _("Password reset email sent successfully.")},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": _("Failed to send password reset email.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Admin Panel - User Management"],
    summary="Adjust User Points (Admin)",
    description="Adds or subtracts points from a specified user's account.",
)
class AdminPointAdjustmentView(generics.GenericAPIView):
    """Allows Admin to add or subtract points from a user's account."""

    permission_classes = [
        IsAdminUser
    ]  # TODO: Add specific sub-admin permission check ('can_adjust_points')
    serializer_class = AdminPointAdjustmentSerializer

    def post(self, request, user_id):
        target_user = get_object_or_404(
            User.objects.select_related("profile"), pk=user_id
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        points_change = serializer.validated_data["points_change"]
        reason = serializer.validated_data["reason"]

        try:
            success = award_points(
                user=target_user,
                points_change=points_change,
                reason_code=PointReason.ADMIN_ADJUSTMENT,
                description=f"Admin adjustment: {reason} (Admin: {request.user.username})",
                related_object=request.user,  # Log which admin performed the action
            )
            if success:
                target_user.profile.refresh_from_db()  # Get updated points total
                logger.info(
                    f"Admin {request.user.username} adjusted points for {target_user.username} by {points_change}. New total: {target_user.profile.points}"
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
                # award_points logs the specific error
                return Response(
                    {"detail": _("Failed to adjust points.")},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.exception(
                f"Unexpected error during admin point adjustment by {request.user.username} for user {target_user.username}: {e}"
            )
            return Response(
                {"detail": _("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
