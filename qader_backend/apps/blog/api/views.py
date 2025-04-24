from rest_framework import viewsets, mixins, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from taggit.models import Tag  # Import Tag for filtering

from ..models import BlogPost, BlogAdviceRequest, PostStatusChoices
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogAdviceRequestSerializer,
)
from apps.api.permissions import IsSubscribed  # Import subscription permission


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving published Blog Posts.
    Supports filtering by tags and searching title/content.
    """

    permission_classes = [
        IsAuthenticatedOrReadOnly
    ]  # Allow anyone to read, auth needed for other methods (none defined here)
    queryset = BlogPost.objects.filter(
        status=PostStatusChoices.PUBLISHED
    ).prefetch_related("tags", "author__profile")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = (
        []
    )  # No specific model fields exposed for direct filtering by default
    search_fields = [
        "title",
        "content",
        "tags__name",
    ]  # Search in title, content, and tag names
    ordering_fields = ["published_at", "title", "updated_at"]
    ordering = ["-published_at"]  # Default ordering
    lookup_field = "slug"  # Use slug for retrieving posts

    def get_serializer_class(self):
        if self.action == "list":
            return BlogPostListSerializer
        return BlogPostDetailSerializer

    def get_queryset(self):
        """Allow filtering by tag slug in the query parameters"""
        queryset = super().get_queryset()
        tag_slug = self.request.query_params.get("tag", None)
        if tag_slug:
            try:
                tag = Tag.objects.get(slug=tag_slug)
                queryset = queryset.filter(tags=tag)
            except Tag.DoesNotExist:
                # Return empty queryset if tag doesn't exist to avoid errors
                queryset = queryset.none()
        return (
            queryset.distinct()
        )  # Use distinct because searching tags might duplicate results


class BlogAdviceRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for creating Blog Advice Requests.
    Requires authentication and active subscription.
    """

    serializer_class = BlogAdviceRequestSerializer
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Must be logged in and subscribed
    queryset = (
        BlogAdviceRequest.objects.none()
    )  # Only allows creation, no listing/retrieval here

    # perform_create is automatically handled by setting user = HiddenField(default=...) in serializer
    # def perform_create(self, serializer):
    #     serializer.save(user=self.request.user)

    # No list, retrieve, update, or destroy actions are enabled by default
