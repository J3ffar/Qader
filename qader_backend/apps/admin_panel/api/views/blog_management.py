from rest_framework import viewsets, permissions, mixins
from ..permissions import IsAdminUserOrSubAdminWithPermission
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema_view, extend_schema

from apps.blog.models import BlogPost, BlogAdviceRequest
from ..serializers.blog_management import (
    AdminBlogPostSerializer,
    AdminBlogAdviceRequestSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List Blog Posts", tags=["Admin Panel - Blog"]),
    create=extend_schema(summary="Create Blog Post", tags=["Admin Panel - Blog"]),
    retrieve=extend_schema(summary="Retrieve Blog Post", tags=["Admin Panel - Blog"]),
    update=extend_schema(summary="Update Blog Post", tags=["Admin Panel - Blog"]),
    partial_update=extend_schema(
        summary="Partially Update Blog Post", tags=["Admin Panel - Blog"]
    ),
    destroy=extend_schema(summary="Delete Blog Post", tags=["Admin Panel - Blog"]),
)
class AdminBlogPostViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing Blog Posts (CRUD).
    Requires staff privileges.
    """

    serializer_class = AdminBlogPostSerializer
    permission_classes = [
        IsAdminUserOrSubAdminWithPermission
    ]  # Replace/add custom permissions if needed
    queryset = BlogPost.objects.all().select_related("author").prefetch_related("tags")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "status",
        "author",
        "tags__slug",
    ]  # Allow filtering by status, author ID, tag slug
    search_fields = ["title", "content", "slug", "author__username", "tags__name"]
    ordering_fields = ["created_at", "updated_at", "published_at", "title", "status"]
    ordering = ["-created_at"]
    lookup_field = "slug"  # Or 'pk' if preferred for admin


@extend_schema_view(
    list=extend_schema(
        summary="List Blog Advice Requests", tags=["Admin Panel - Blog"]
    ),
    retrieve=extend_schema(
        summary="Retrieve Blog Advice Request", tags=["Admin Panel - Blog"]
    ),
    update=extend_schema(
        summary="Update Blog Advice Request Status/Links",
        tags=["Admin Panel - Blog"],
    ),
    partial_update=extend_schema(
        summary="Partially Update Blog Advice Request Status/Links",
        tags=["Admin Panel - Blog"],
    ),
    # No destroy by default, admin should typically change status to 'Closed' or 'Published'
)
class AdminBlogAdviceRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Admin ViewSet for viewing and updating Blog Advice Requests.
    Requires staff privileges. Create is handled by users, Delete is omitted (use status).
    """

    serializer_class = AdminBlogAdviceRequestSerializer
    permission_classes = [
        IsAdminUserOrSubAdminWithPermission
    ]  # Replace/add custom permissions if needed
    queryset = BlogAdviceRequest.objects.all().select_related(
        "user__profile",  # Include profile for user_info
        "related_support_ticket",
        "related_blog_post",
    )
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "status",
        "response_via",
        "user",
    ]  # Filter by status, response method, user ID
    search_fields = ["user__username", "user__email", "problem_type", "description"]
    ordering_fields = ["created_at", "updated_at", "status"]
    ordering = ["-created_at"]
    lookup_field = "pk"  # Use PK for advice requests
