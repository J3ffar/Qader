from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.notifications.models import Notification
from apps.notifications.services import bulk_mark_as_read, mark_all_as_read_for_user
from .serializers import NotificationSerializer, NotificationMarkReadInputSerializer

import logging

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Notifications"],
    summary="List User Notifications",
    description=(
        "Retrieves a paginated list of notifications for the authenticated user. "
        "Can be filtered by read status using `?is_read=true` or `?is_read=false`."
    ),
    parameters=[
        OpenApiParameter(
            name="is_read",
            description="Filter by read status (true/false).",
            required=False,
            type=bool,
        )
    ],
)
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    # pagination_class = YourDefaultPaginationClass (if you have one)

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Notification.objects.filter(recipient=user)
            .select_related(
                "actor__profile",  # Assuming actor has a profile for SimpleUserSerializer
                "recipient__profile",
            )
            .prefetch_related(  # For GenericForeignKeys
                "target_content_type", "action_object_content_type"
            )
        )

        is_read_param = self.request.query_params.get("is_read")
        if is_read_param is not None:
            is_read_value = is_read_param.lower() == "true"
            queryset = queryset.filter(is_read=is_read_value)

        return queryset.order_by("-created_at")  # Default ordering is in model Meta


@extend_schema(
    tags=["Notifications"],
    summary="Mark Specified Notifications as Read",
    description="Marks one or more specified notifications as read for the authenticated user.",
)
class NotificationMarkAsReadView(
    generics.GenericAPIView
):  # Changed to GenericAPIView for custom logic
    serializer_class = NotificationMarkReadInputSerializer  # For input validation
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
    description="Deletes a specific notification belonging to the authenticated user.",
)
class NotificationDeleteView(generics.DestroyAPIView):
    serializer_class = NotificationSerializer  # For response schema in docs
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"  # Default

    def get_queryset(self):
        # Ensure users can only delete their own notifications
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
)
class UnreadNotificationCountView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count}, status=status.HTTP_200_OK)
