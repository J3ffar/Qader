from django.db.models import Count
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.parsers import (
    MultiPartParser,
)

# Import models from the community app
from apps.community.models import CommunityPost, CommunityReply

from apps.admin_panel.api.serializers.community_management import (
    AdminCommunityPostSerializer,
    AdminCommunityPostListSerializer,
    AdminCommunityReplySerializer,
)

# Import filters from the community app (reusing the post filter)
from apps.community.api.filters import CommunityPostFilter
from ..permissions import IsAdminUserOrSubAdminWithPermission


@extend_schema(tags=["Admin Panel - Community Management"])
@extend_schema_view(
    list=extend_schema(summary="[Admin] List All Community Posts"),
    create=extend_schema(summary="[Admin] Create Community Post"),
    retrieve=extend_schema(summary="[Admin] Retrieve Community Post"),
    update=extend_schema(summary="[Admin] Update Community Post (Full)"),
    partial_update=extend_schema(summary="[Admin] Partially Update Community Post"),
    destroy=extend_schema(summary="[Admin] Delete Community Post"),
)
class AdminCommunityPostViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all Community Posts.
    Provides full CRUD capabilities for administrators, including pinning/closing.
    """

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    parser_classes = [MultiPartParser]  # <<< CHANGED: Allow file uploads
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CommunityPostFilter
    search_fields = [
        "title",
        "content",
        "author__username",
        "author__email",
        "tags__name",
    ]
    # <<< CHANGED: Added like_count for ordering
    ordering_fields = [
        "created_at",
        "updated_at",
        "reply_count_annotated",
        "like_count_annotated",
        "is_pinned",
        "is_closed",
        "author__username",
    ]
    ordering = ["-is_pinned", "-created_at"]

    def get_queryset(self):
        """
        Return all community posts with necessary annotations and prefetches for admin view.
        """
        # <<< CHANGED: Added annotation for likes and prefetched the relation
        return (
            CommunityPost.objects.select_related("author__profile", "section_filter")
            .prefetch_related("tags", "likes__profile")
            .annotate(
                reply_count_annotated=Count("replies", distinct=True),
                like_count_annotated=Count("likes", distinct=True),
            )
            .order_by(*self.ordering)
        )

    def get_serializer_class(self):
        """Return appropriate serializer class based on the action."""
        # <<< CHANGED: Using new admin-specific serializers
        if self.action == "list":
            return AdminCommunityPostListSerializer
        # Use the full serializer for all other actions (create, retrieve, update)
        return AdminCommunityPostSerializer

    def get_permissions(self):
        """Set required permissions based on the action."""
        self.required_permissions = ["api_manage_community"]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """Set the author to the currently logged-in admin."""
        # <<< CHANGED: Simplified to always use the request user
        serializer.save(author=self.request.user)

    # <<< CHANGED: The complex perform_update is NO LONGER NEEDED.
    # The new AdminCommunityPostSerializer handles is_pinned and is_closed
    # as regular writable fields, so the default ModelViewSet behavior is sufficient.


@extend_schema(tags=["Admin Panel - Community Management"])
@extend_schema_view(
    list=extend_schema(summary="[Admin] List All Community Replies"),
    retrieve=extend_schema(summary="[Admin] Retrieve Community Reply"),
    update=extend_schema(summary="[Admin] Update Community Reply (Full)"),
    partial_update=extend_schema(summary="[Admin] Partially Update Community Reply"),
    destroy=extend_schema(summary="[Admin] Delete Community Reply"),
)
class AdminCommunityReplyViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing all Community Replies.
    Provides full CRUD for administrators, but creation is disabled as replies
    should be created in context of a post.
    """

    # <<< CHANGED: Using the new admin reply serializer
    serializer_class = AdminCommunityReplySerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    http_method_names = [
        "get",
        "put",
        "patch",
        "delete",
        "head",
        "options",
    ]  # No 'post'
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["post", "author", "parent_reply"]
    search_fields = ["content", "author__username", "author__email", "post__title"]
    # <<< CHANGED: Added like_count for ordering
    ordering_fields = [
        "created_at",
        "updated_at",
        "author__username",
        "post__id",
        "like_count_annotated",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Return all community replies with necessary prefetches/select_related.
        """
        # <<< CHANGED: Added annotation for likes and prefetched the relation
        return (
            CommunityReply.objects.select_related(
                "author__profile", "post", "parent_reply"
            )
            .prefetch_related("likes__profile")
            .annotate(like_count_annotated=Count("likes", distinct=True))
            .order_by(*self.ordering)
        )

    def get_permissions(self):
        """Set required permissions based on the action."""
        self.required_permissions = ["api_manage_community"]
        return [permission() for permission in self.permission_classes]
