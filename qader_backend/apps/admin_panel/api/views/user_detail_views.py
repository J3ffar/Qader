import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, views, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework.exceptions import PermissionDenied, NotFound, APIException
from django_filters.rest_framework import DjangoFilterBackend
from django.http import Http404

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.study.models import UserTestAttempt
from apps.study.api.serializers.statistics import UserStatisticsSerializer
from apps.study.api.serializers.attempts import (
    UserTestAttemptListSerializer,
)
from apps.gamification.api.serializers import PointLogSerializer
from apps.admin_panel.api.permissions import (
    IsAdminUserOrSubAdminWithPermission,
)
from apps.gamification.models import PointLog

logger = logging.getLogger(__name__)
User = get_user_model()


# --- Base View Helper (Optional but Recommended for DRYness) ---
class BaseAdminUserDetailView(generics.GenericAPIView):
    """Base view for admin actions targeting a specific user via user_id in URL."""

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    # required_permissions should be set by subclasses

    def get_target_user(self):
        """Retrieves the target user based on user_id from URL."""
        user_id = self.kwargs.get("user_id")
        try:
            # Select related profile as it's often needed
            user = get_object_or_404(User.objects.select_related("profile"), pk=user_id)
            return user
        except Http404:
            raise NotFound(f"User with ID {user_id} not found.")
        except Exception as e:
            logger.exception(f"Error fetching target user {user_id}: {e}")
            raise APIException("Error retrieving user details.")


# --- Specific Admin User Detail Views ---


@extend_schema(
    tags=["Admin Panel - User Details"],  # New tag for clarity
    summary="Get User Statistics (Admin)",
    description="Retrieve detailed statistics for a specific user, similar to the user-facing stats endpoint.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID of the target user.",
        )
    ],
    responses={
        200: UserStatisticsSerializer,
        400: OpenApiResponse(
            description="Bad Request (e.g., Profile missing for user)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="User not found."),
    },
)
class AdminUserStatisticsView(BaseAdminUserDetailView):
    """Provides aggregated statistics for a specific user (Admin access)."""

    required_permissions = ["view_user_statistics"]  # Define specific permission needed

    def get(self, request, user_id, *args, **kwargs):
        # Permission check is handled by BaseAdminUserDetailView/DRF
        target_user = self.get_target_user()  # Handles 404

        try:
            # Pass the target user into the serializer's context
            serializer = UserStatisticsSerializer(
                instance=target_user,  # Pass user object as instance
                context={"request": request, "target_user": target_user},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except drf_serializers.ValidationError as e:
            # Catch validation errors from the serializer (e.g., profile missing)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Admin: Unexpected error generating statistics for user {user_id} by admin {request.user.id}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred while generating statistics."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Admin Panel - User Details"],
    summary="Get User Test History (Admin)",
    description="Retrieve a paginated list of all test attempts for a specific user.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID of the target user.",
        ),
        OpenApiParameter(
            name="status",
            description="Filter by status (started, completed, abandoned).",
            type=str,
        ),
        OpenApiParameter(
            name="attempt_type",
            description="Filter by type (level_assessment, practice, etc.).",
            type=str,
        ),
        OpenApiParameter(
            name="attempt_type__in",
            description="Filter by multiple types (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="ordering",
            description="Order results (e.g., `-start_time`).",
            type=str,
        ),
        OpenApiParameter(name="page", description="Page number.", type=int),
        OpenApiParameter(name="page_size", description="Results per page.", type=int),
    ],
    responses={
        200: UserTestAttemptListSerializer(many=True),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="User not found."),
    },
)
class AdminUserTestHistoryView(
    generics.ListAPIView
):  # Inherit from ListAPIView for pagination/filtering
    """Provides a paginated list of test attempts for a specific user (Admin access)."""

    serializer_class = UserTestAttemptListSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = [
        "view_user_test_history"
    ]  # Define specific permission needed
    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Add OrderingFilter
    filterset_fields = {
        "status": ["exact", "in"],
        "attempt_type": ["exact", "in"],
        "start_time": ["date__gte", "date__lte"],  # Allow date range filtering
    }
    ordering_fields = [
        "start_time",
        "end_time",
        "score_percentage",
        "status",
        "attempt_type",
    ]
    ordering = ["-start_time"]  # Default ordering

    def get_queryset(self):
        """Filters attempts for the target user specified in the URL."""
        user_id = self.kwargs.get("user_id")
        # Ensure the requesting admin has permission *before* fetching the user
        # The permission class handles this check globally for the view.
        target_user = get_object_or_404(User, pk=user_id)  # Simple lookup here

        return UserTestAttempt.objects.filter(user=target_user).annotate(
            answered_question_count_agg=Count(
                "question_attempts"
            )  # Annotation needed by serializer
        )

    # We override get_queryset, so we don't need get_target_user method here.
    # Need to manually set required_permissions if not using BaseAdminUserDetailView
    def get_permissions(self):
        """Set required permissions for this specific view."""
        # This overrides the default behavior if needed, but setting class attribute is simpler
        self.required_permissions = ["view_user_test_history"]
        return [permission() for permission in self.permission_classes]


@extend_schema(
    tags=["Admin Panel - User Details"],
    summary="Get User Point Log (Admin)",
    description="Retrieve a paginated list of all point transactions for a specific user.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description="ID of the target user.",
        ),
        OpenApiParameter(
            name="reason_code", description="Filter by point reason code.", type=str
        ),
        OpenApiParameter(
            name="reason_code__in",
            description="Filter by multiple reason codes (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="timestamp__date__gte",
            description="Filter by start date (YYYY-MM-DD).",
            type=str,
        ),
        OpenApiParameter(
            name="timestamp__date__lte",
            description="Filter by end date (YYYY-MM-DD).",
            type=str,
        ),
        OpenApiParameter(
            name="ordering", description="Order results (e.g., `-timestamp`).", type=str
        ),
        OpenApiParameter(name="page", description="Page number.", type=int),
        OpenApiParameter(name="page_size", description="Results per page.", type=int),
    ],
    responses={
        200: PointLogSerializer(many=True),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="User not found."),
    },
)
class AdminUserPointLogView(generics.ListAPIView):  # Inherit from ListAPIView
    """Provides a paginated list of point log entries for a specific user (Admin access)."""

    serializer_class = PointLogSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["view_user_point_log"]  # Define specific permission needed
    filter_backends = [DjangoFilterBackend, OrderingFilter]  # Add OrderingFilter
    filterset_fields = {
        "reason_code": ["exact", "in"],
        "timestamp": ["date__gte", "date__lte", "exact"],  # Allow date filtering
    }
    ordering_fields = ["timestamp", "points_change", "reason_code"]
    ordering = ["-timestamp"]  # Default ordering

    def get_queryset(self):
        """Filters point logs for the target user specified in the URL."""
        user_id = self.kwargs.get("user_id")
        target_user = get_object_or_404(User, pk=user_id)
        return PointLog.objects.filter(user=target_user)

    # We override get_queryset, so we don't need get_target_user method here.
    def get_permissions(self):
        """Set required permissions for this specific view."""
        self.required_permissions = ["view_user_point_log"]
        return [permission() for permission in self.permission_classes]
