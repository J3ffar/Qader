# qader_backend/apps/admin_panel/api/views/community_management.py

from django.db.models import Count, Prefetch
from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response

# Import models from the community app
from apps.community.models import CommunityPost, CommunityReply

# Import serializers from the community app (reusing them for now)
from apps.community.api.serializers import (
    CommunityPostListSerializer,
    CommunityPostDetailSerializer,
    CommunityPostCreateUpdateSerializer,
    CommunityReplySerializer,
)

# Import filters from the community app (reusing the post filter)
from apps.community.api.filters import CommunityPostFilter


@extend_schema(tags=["Admin Panel - Community Management"])
@extend_schema_view(
    list=extend_schema(
        summary="List All Community Posts",
        description="Retrieve a paginated list of all community posts. Admins can filter, search, and order.",
    ),
    create=extend_schema(
        summary="Create Community Post",
        description="Create a new community post as an administrator (e.g., announcements).",
        request=CommunityPostCreateUpdateSerializer,
        responses={201: CommunityPostCreateUpdateSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve Community Post Details",
        description="Get full details of a specific community post.",
        responses={200: CommunityPostDetailSerializer},
    ),
    update=extend_schema(
        summary="Update Community Post (Full)",
        description="Fully update any existing community post, including pinning and closing.",
        request=CommunityPostCreateUpdateSerializer,
        responses={200: CommunityPostCreateUpdateSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially Update Community Post",
        description="Partially update any existing community post, including pinning and closing.",
        request=CommunityPostCreateUpdateSerializer,
        responses={200: CommunityPostCreateUpdateSerializer},
    ),
    destroy=extend_schema(
        summary="Delete Community Post",
        description="Permanently delete any community post.",
        responses={204: None},
    ),
)
class AdminCommunityPostViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all Community Posts.
    Provides full CRUD capabilities for administrators, including pinning/closing.
    """

    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CommunityPostFilter
    # Admins might want broader search capabilities
    search_fields = [
        "title",
        "content",
        "author__username",
        "author__email",
        "tags__name",
    ]
    # Include admin-controlled fields in ordering
    ordering_fields = [
        "created_at",
        "updated_at",
        "reply_count_annotated",
        "is_pinned",
        "is_closed",
        "author__username",
    ]
    ordering = ["-is_pinned", "-created_at"]  # Default: pinned first, then newest

    def get_queryset(self):
        """
        Return all community posts with necessary annotations and prefetches for admin view.
        """
        return (
            CommunityPost.objects.select_related("author__profile", "section_filter")
            .prefetch_related("tags")
            .annotate(reply_count_annotated=Count("replies"))
            .order_by(*self.ordering)
        )

    def get_serializer_class(self):
        """Return appropriate serializer class based on the action."""
        if self.action == "list":
            return CommunityPostListSerializer
        elif self.action == "retrieve":
            return CommunityPostDetailSerializer
        return CommunityPostCreateUpdateSerializer

    def perform_create(self, serializer):
        """Set the author if not provided (e.g., admin announcement)."""
        # Usually, admin edits user posts, but allow creation too.
        # If author needs setting, it should be done here based on request data or defaults.
        # For simplicity, assume serializer requires necessary fields or handles defaults.
        # Example: Set logged-in admin as author if creating admin posts
        if not serializer.validated_data.get("author"):
            serializer.save(author=self.request.user)
        else:
            serializer.save()  # If author field is part of the request

    def perform_update(self, serializer):
        """
        Allow admins to directly update is_pinned and is_closed.
        The serializer has these as read_only for standard users, so we use
        request.data here specifically for the admin context.
        """
        # Extract potential admin-only fields from request data
        is_pinned_update = self.request.data.get("is_pinned")
        is_closed_update = self.request.data.get("is_closed")

        instance = serializer.instance  # Get instance before saving standard fields

        # Prepare data for update, excluding admin fields initially
        update_data = serializer.validated_data

        # Apply admin-specific field updates directly if provided in request
        update_fields_admin = []
        if is_pinned_update is not None:
            pinned_bool = str(is_pinned_update).lower() in ["true", "1"]
            if instance.is_pinned != pinned_bool:
                instance.is_pinned = pinned_bool
                update_fields_admin.append("is_pinned")

        if is_closed_update is not None:
            closed_bool = str(is_closed_update).lower() in ["true", "1"]
            if instance.is_closed != closed_bool:
                instance.is_closed = closed_bool
                update_fields_admin.append("is_closed")

        # Save the standard validated data via the serializer
        # This handles regular field updates
        serializer.save()  # This updates based on validated_data

        # If admin fields changed, save them separately
        if update_fields_admin:
            # Refresh instance state after serializer.save() if needed
            instance.refresh_from_db(fields=update_fields_admin)
            # Now save only the admin-modified fields
            instance.save(update_fields=update_fields_admin + ["updated_at"])

    # perform_destroy uses the default behavior; IsAdminUser grants permission.


@extend_schema(tags=["Admin Panel - Community Management"])
@extend_schema_view(
    list=extend_schema(
        summary="List All Community Replies",
        description="Retrieve a paginated list of all community replies across all posts. Admins can filter and search.",
    ),
    create=extend_schema(
        summary="Create Community Replies",
        description="Create a new community replies as an administrator.",
        request=CommunityPostCreateUpdateSerializer,
        responses={201: CommunityPostCreateUpdateSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve Community Reply Details",
        description="Get details of a specific community reply.",
        responses={200: CommunityReplySerializer},
    ),
    update=extend_schema(
        summary="Update Community Reply (Full)",
        description="Fully update any existing community reply.",
        request=CommunityReplySerializer,
        responses={200: CommunityReplySerializer},
    ),
    partial_update=extend_schema(
        summary="Partially Update Community Reply",
        description="Partially update any existing community reply.",
        request=CommunityReplySerializer,
        responses={200: CommunityReplySerializer},
    ),
    destroy=extend_schema(
        summary="Delete Community Reply",
        description="Permanently delete any community reply.",
        responses={204: None},
    ),
)
class AdminCommunityReplyViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all Community Replies.
    Provides full CRUD capabilities for administrators.
    """

    serializer_class = CommunityReplySerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["post", "author", "parent_reply"]
    search_fields = ["content", "author__username", "author__email", "post__title"]
    ordering_fields = ["created_at", "updated_at", "author__username", "post__id"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Return all community replies with necessary prefetches/select_related.
        """
        return (
            CommunityReply.objects.select_related(
                "author__profile", "post", "parent_reply"
            )
            .annotate(child_replies_count_annotated=Count("child_replies"))
            .order_by(*self.ordering)
        )

    # No special perform_create/update needed unless admin-specific logic is required
    # Standard ModelViewSet actions with IsAdminUser permission suffice.
