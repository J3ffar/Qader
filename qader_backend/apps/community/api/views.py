from django.db.models import Count
from rest_framework import viewsets, generics, status
from rest_framework.serializers import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from taggit.models import Tag
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
)


from apps.community.models import CommunityPost, CommunityReply
from apps.community.api.serializers import (
    CommunityPostSerializer,
    CommunityPostListSerializer,
    CommunityPostDetailSerializer,
    CommunityReplySerializer,
    TagSerializer,
)
from apps.community.api.filters import CommunityPostFilter
from apps.api.permissions import IsSubscribed  # Make sure this exists


@extend_schema(tags=["Student Community"])  # Apply tag to all actions in this ViewSet
@extend_schema_view(
    list=extend_schema(
        summary="List Community Posts",
        description="Retrieve a paginated list of community posts. Filter by `post_type`, `section_filter` (slug), `tags` (comma-separated names/slugs), `pinned`. Search fields: `title`, `content`, `author__username`, `tags__name`. Order by `created_at`, `reply_count`.",
    ),
    create=extend_schema(
        summary="Create Community Post",
        description="Create a new post in the community forum. Requires subscription.",
    ),
    retrieve=extend_schema(  # Custom schema for retrieve to show nested paginated replies correctly
        summary="Retrieve Community Post",
        description="Get details of a single community post, including its paginated replies.",
        responses={
            200: CommunityPostDetailSerializer
        },  # Use the detail serializer for schema
    ),
    update=extend_schema(
        summary="Update Community Post",
        description="Update an existing community post (author or admin only).",
    ),
    partial_update=extend_schema(
        summary="Partially Update Community Post",
        description="Partially update an existing community post (author or admin only).",
    ),
    destroy=extend_schema(
        summary="Delete Community Post",
        description="Delete an existing community post (author or admin only).",
    ),
)
class CommunityPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Community Posts.
    Provides list, create, retrieve, update, delete operations.
    Filtering options: `post_type`, `section_filter` (slug), `tags` (comma-separated names/slugs), `pinned`.
    Search fields: `title`, `content`, `author__username`.
    Ordering fields: `created_at`, `reply_count`.
    """

    queryset = (
        CommunityPost.objects.select_related("author__profile", "section_filter")
        .prefetch_related(
            "tags",
            # 'replies' # Pre-fetching all replies might be too heavy here, handle in retrieve
        )
        .annotate(reply_count_annotated=Count("replies", distinct=True))
        .order_by("-is_pinned", "-created_at")
    )  # Default ordering
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Use IsAuthenticated for safety if IsSubscribed not ready
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CommunityPostFilter
    search_fields = ["title", "content", "author__username", "tags__name"]
    ordering_fields = ["created_at", "reply_count"]

    def get_serializer_class(self):
        if self.action == "list":
            return CommunityPostListSerializer
        elif self.action == "retrieve":
            return CommunityPostDetailSerializer
        return CommunityPostSerializer  # For create, update, partial_update

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # Optionally restrict update/delete to author or admin
    def perform_update(self, serializer):
        post = self.get_object()
        is_author = post.author == self.request.user
        is_staff = self.request.user.is_staff  # Check staff status

        # Check permission to edit *at all*
        if not is_author and not is_staff:
            raise PermissionDenied("You do not have permission to edit this post.")

        # Separate logic for admin-only fields
        pinned = serializer.validated_data.pop("is_pinned", None)
        closed = serializer.validated_data.pop("is_closed", None)

        # Save the main data first
        instance = serializer.save()

        # Apply admin-only changes if user is staff and values were provided
        needs_extra_save = False
        if is_staff:
            if pinned is not None and instance.is_pinned != pinned:
                instance.is_pinned = pinned
                needs_extra_save = True
            if closed is not None and instance.is_closed != closed:
                instance.is_closed = closed
                needs_extra_save = True

        # Save again only if admin fields were changed
        if needs_extra_save:
            instance.save(update_fields=["is_pinned", "is_closed", "updated_at"])

    def perform_destroy(self, instance):
        # Clarified permission check
        if instance.author == self.request.user or self.request.user.is_staff:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this post.")

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a post and include paginated replies.
        """
        instance = self.get_object()
        post_serializer = self.get_serializer(instance)
        post_data = post_serializer.data

        # Paginate replies
        reply_queryset = instance.replies.select_related(
            "author__profile", "parent_reply"
        ).order_by(
            "created_at"
        )  # Get replies for this post

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reply_queryset, request, view=self)

        if page is not None:
            reply_serializer = CommunityReplySerializer(
                page, many=True, context={"request": request}
            )
            paginated_replies = paginator.get_paginated_response(
                reply_serializer.data
            ).data
        else:
            # Handle case where pagination is not applied (e.g., no replies or pagination disabled)
            reply_serializer = CommunityReplySerializer(
                reply_queryset, many=True, context={"request": request}
            )
            paginated_replies = {
                "count": reply_queryset.count(),
                "next": None,
                "previous": None,
                "results": reply_serializer.data,
            }

        post_data["replies"] = (
            paginated_replies  # Add paginated replies to the response
        )
        return Response(post_data)


@extend_schema(tags=["Student Community"])
class CommunityReplyListCreateView(generics.ListCreateAPIView):
    """
    List and Create Replies for a specific Community Post.
    Accessed via `/posts/{post_pk}/replies/`.
    """

    serializer_class = CommunityReplySerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_post_object(self):
        """Helper to get the post or raise 404."""
        post_pk = self.kwargs.get("post_pk")
        try:
            post = CommunityPost.objects.get(pk=post_pk)
            return post
        except CommunityPost.DoesNotExist:
            raise NotFound(detail="Post not found.")

    def get_queryset(self):
        post_pk = self.kwargs.get("post_pk")
        return (
            CommunityReply.objects.filter(post_id=post_pk)
            .select_related("author__profile", "parent_reply")
            .order_by("created_at")
        )

    def list(self, request, *args, **kwargs):
        # Check post existence before listing replies
        self.get_post_object()  # This will raise 404 if post not found
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Post existence is checked in perform_create
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Use helper to get post, handles 404
        post = self.get_post_object()

        if post.is_closed and not self.request.user.is_staff:
            raise PermissionDenied(
                "This post is closed and does not accept new replies."
            )

        parent_reply_obj = serializer.validated_data.get("parent_reply")
        if parent_reply_obj and parent_reply_obj.post != post:
            raise ValidationError(
                {"parent_reply_id": "Parent reply does not belong to this post."}
            )

        serializer.save(author=self.request.user, post=post)


@extend_schema(
    tags=["Student Community"],  # Apply tag
    summary="List Community Tags",
    description="Retrieve a list of tags used across all community posts, ordered by popularity (most used first).",
)
class TagListView(generics.ListAPIView):
    """
    List available tags, ordered by usage count (most popular first).
    """

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]  # Allow any authenticated user to see tags

    def get_queryset(self):
        # Annotate with the count of posts using each tag
        return Tag.objects.annotate(
            count=Count("taggit_taggeditem_items")  # Default related name from taggit
        ).order_by(
            "-count"
        )  # Order by most frequently used
