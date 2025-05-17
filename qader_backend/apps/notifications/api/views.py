from rest_framework import (
    generics,
    views,
    status,
    serializers as drf_serializers,
)  # Alias for clarity
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,  # For simple response structures
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes  # For parameter types

from apps.notifications.models import Notification
from apps.notifications.services import bulk_mark_as_read, mark_all_as_read_for_user
from .serializers import NotificationSerializer, NotificationMarkReadInputSerializer

import logging

logger = logging.getLogger(__name__)

# --- Define Reusable Error Responses for Notifications API Docs ---
# (Could be in a shared module like apps.api.openapi_schemas if used across apps)
NOTIFICATION_API_COMMON_ERRORS = {
    status.HTTP_400_BAD_REQUEST: OpenApiResponse(
        description="Bad Request: Invalid input data. Check response body for details.",
        response=inline_serializer(
            name="NotificationValidationErrorResponse",
            fields={
                "field_name": drf_serializers.ListField(
                    child=drf_serializers.CharField(), required=False
                ),
                "detail": drf_serializers.CharField(required=False),
            },
        ),
        examples=[
            OpenApiExample(
                "Field Error Example",
                value={"notification_ids": ["This field is required."]},
            ),
            OpenApiExample(
                "Non-Field Error Example",
                value={"detail": "Invalid operation parameter."},
            ),
        ],
    ),
    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
        description="Unauthorized: Authentication credentials were not provided or are invalid.",
        response=inline_serializer(
            name="NotificationUnauthorizedResponse",
            fields={"detail": drf_serializers.CharField()},
        ),
        examples=[
            OpenApiExample(
                "Auth Required Example",
                value={"detail": "Authentication credentials were not provided."},
            )
        ],
    ),
    status.HTTP_403_FORBIDDEN: OpenApiResponse(
        description="Forbidden: You do not have permission to perform this action.",
        response=inline_serializer(
            name="NotificationForbiddenResponse",
            fields={"detail": drf_serializers.CharField()},
        ),
        examples=[
            OpenApiExample(
                "Permission Denied Example",
                value={"detail": "You do not have permission to perform this action."},
            )
        ],
    ),
    status.HTTP_404_NOT_FOUND: OpenApiResponse(
        description="Not Found: The requested resource could not be found.",
        response=inline_serializer(
            name="NotificationNotFoundResponse",
            fields={"detail": drf_serializers.CharField()},
        ),
        examples=[
            OpenApiExample(
                "Not Found Example", value={"detail": "Notification not found."}
            )
        ],
    ),
}


@extend_schema(
    tags=["Notifications"],
    summary="List User Notifications",
    description=(
        "Retrieves a paginated list of notifications for the authenticated user. "
        "Notifications are ordered by creation date (most recent first). "
        "Can be filtered by read status using the `is_read` query parameter."
    ),
    parameters=[
        OpenApiParameter(
            name="is_read",
            description="Filter by read status. `true` for read, `false` for unread. If omitted, all notifications are returned.",
            required=False,
            type=OpenApiTypes.BOOL,  # Use OpenApiTypes for clarity
        ),
        OpenApiParameter(  # Standard pagination parameter
            name="page",
            description="A page number within the paginated result set.",
            required=False,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(  # Standard pagination parameter
            name="page_size",
            description="Number of results to return per page.",
            required=False,
            type=OpenApiTypes.INT,
        ),
    ],
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=NotificationSerializer(many=True),  # Use the actual serializer
            description="Successfully retrieved list of notifications.",
        ),
        status.HTTP_401_UNAUTHORIZED: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_401_UNAUTHORIZED
        ],
    },
)
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    # Ensure pagination_class is set in REST_FRAMEWORK defaults or here
    # pagination_class = YourDefaultPaginationClass

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Notification.objects.filter(recipient=user)
            .select_related("actor__profile", "recipient__profile")
            .prefetch_related("target_content_type", "action_object_content_type")
        )

        is_read_param = self.request.query_params.get("is_read")
        if is_read_param is not None:
            is_read_value = is_read_param.lower() == "true"
            queryset = queryset.filter(is_read=is_read_value)

        return queryset.order_by("-created_at")


@extend_schema(
    tags=["Notifications"],
    summary="Mark Specified Notifications as Read",
    description="Marks one or more specified notifications as read for the authenticated user.",
    request=NotificationMarkReadInputSerializer,  # Use the input serializer for request body
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="MarkAsReadSuccessResponse",
                fields={"detail": drf_serializers.CharField()},
            ),
            description="Successfully marked specified notifications as read.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"detail": "3 notification(s) marked as read."},
                )
            ],
        ),
        status.HTTP_400_BAD_REQUEST: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_400_BAD_REQUEST
        ],
        status.HTTP_401_UNAUTHORIZED: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_401_UNAUTHORIZED
        ],
    },
)
class NotificationMarkAsReadView(generics.GenericAPIView):
    serializer_class = NotificationMarkReadInputSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data["notification_ids"]
        updated_count = bulk_mark_as_read(request.user, notification_ids)

        return Response(
            {"detail": _(f"{updated_count} notification(s) marked as read.")},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Notifications"],
    summary="Mark All Notifications as Read",
    description="Marks all unread notifications as read for the authenticated user.",
    request=None,  # No request body
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="MarkAllAsReadSuccessResponse",
                fields={"detail": drf_serializers.CharField()},
            ),
            description="Successfully marked all unread notifications as read.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"detail": "5 unread notification(s) marked as read."},
                )
            ],
        ),
        status.HTTP_401_UNAUTHORIZED: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_401_UNAUTHORIZED
        ],
    },
)
class NotificationMarkAllAsReadView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        updated_count = mark_all_as_read_for_user(request.user)
        return Response(
            {"detail": _(f"{updated_count} unread notification(s) marked as read.")},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["Notifications"],
    summary="Delete a Notification",
    description="Deletes a specific notification belonging to the authenticated user. The notification is identified by its ID in the URL path.",
    parameters=[
        OpenApiParameter(
            name="pk",
            description="The primary key of the notification to delete.",
            required=True,
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,  # Indicate it's a path parameter
        )
    ],
    responses={
        status.HTTP_204_NO_CONTENT: OpenApiResponse(
            description="Notification deleted successfully. No content returned."
        ),
        status.HTTP_401_UNAUTHORIZED: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_401_UNAUTHORIZED
        ],
        status.HTTP_403_FORBIDDEN: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_403_FORBIDDEN
        ],  # If trying to delete other's notification
        status.HTTP_404_NOT_FOUND: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_404_NOT_FOUND
        ],
    },
)
class NotificationDeleteView(generics.DestroyAPIView):
    # serializer_class = NotificationSerializer # Not strictly needed for DELETE response schema if 204
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def perform_destroy(self, instance):
        logger.info(
            f"User {self.request.user.id} deleting notification ID {instance.id}."
        )
        super().perform_destroy(instance)


@extend_schema(
    tags=["Notifications"],
    summary="Get Unread Notifications Count",
    description="Retrieves the count of unread notifications for the authenticated user.",
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=inline_serializer(
                name="UnreadCountResponse",
                fields={"unread_count": drf_serializers.IntegerField()},
            ),
            description="Successfully retrieved the count of unread notifications.",
            examples=[OpenApiExample("Count Example", value={"unread_count": 12})],
        ),
        status.HTTP_401_UNAUTHORIZED: NOTIFICATION_API_COMMON_ERRORS[
            status.HTTP_401_UNAUTHORIZED
        ],
    },
)
class UnreadNotificationCountView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)
