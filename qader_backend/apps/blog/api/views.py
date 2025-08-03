from rest_framework import viewsets, mixins, permissions, status, generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from taggit.models import Tag
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)

from apps.community.api.serializers import (
    TagSerializer,
)  # Import necessary decorators and types

from ..models import BlogPost, BlogAdviceRequest, PostStatusChoices
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogAdviceRequestSerializer,
)
from apps.api.permissions import IsSubscribed


@extend_schema_view(
    list=extend_schema(
        summary="List Published Blog Posts",
        description="Retrieve a paginated list of published blog posts. "
        "Supports filtering by tag slug and searching title/content/tags.",
        parameters=[
            OpenApiParameter(
                name="tag",
                description='Filter posts by tag slug (e.g., "python", "guide").',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            # Search and Ordering are usually automatically detected by spectacular from filter_backends
            # OpenApiParameter(name='search', description='Search term for title, content, or tags.', required=False, type=OpenApiTypes.STR),
            # OpenApiParameter(name='ordering', description='Field to order by (e.g., -published_at).', required=False, type=OpenApiTypes.STR),
        ],
        responses={status.HTTP_200_OK: BlogPostListSerializer(many=True)},
        tags=["Blog"],  # Add tag for grouping in Swagger UI
    ),
    retrieve=extend_schema(
        summary="Retrieve a Blog Post",
        description="Retrieve the full details of a single published blog post by its slug.",
        responses={status.HTTP_200_OK: BlogPostDetailSerializer},
        tags=["Blog"],
    ),
)
class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving published Blog Posts.
    Supports filtering by tags and searching title/content.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = BlogPost.objects.filter(
        status=PostStatusChoices.PUBLISHED
    ).prefetch_related("tags", "author__profile")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = []  # Keep empty as filtering is custom
    search_fields = ["title", "content", "tags__name"]
    ordering_fields = ["published_at", "title", "updated_at"]
    ordering = ["-published_at"]
    lookup_field = "slug"

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
                # Ensure taggit models are available for schema generation too
                from taggit.models import Tag

                tag = Tag.objects.get(slug=tag_slug)
                queryset = queryset.filter(tags=tag)
            except Tag.DoesNotExist:
                queryset = queryset.none()
        return queryset.distinct()


@extend_schema_view(
    create=extend_schema(
        summary="Submit an Advice Request",
        description="Submit a request for specific advice related to studies or the platform. "
        "Requires authentication and an active subscription.",
        request=BlogAdviceRequestSerializer,
        responses={
            status.HTTP_201_CREATED: BlogAdviceRequestSerializer,
            status.HTTP_400_BAD_REQUEST: OpenApiTypes.OBJECT,  # Example: {"description": ["This field is required."]}
            status.HTTP_401_UNAUTHORIZED: None,
            status.HTTP_403_FORBIDDEN: None,
        },
        tags=["Blog"],
    )
)
class BlogAdviceRequestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for creating Blog Advice Requests.
    Requires authentication and active subscription.
    """

    serializer_class = BlogAdviceRequestSerializer
    permission_classes = [IsAuthenticated]
    queryset = BlogAdviceRequest.objects.none()  # Create only


@extend_schema(
    summary="List Used Blog Tags",
    description="Retrieve a list of unique tags currently assigned to one or more *published* blog posts.",
    responses={status.HTTP_200_OK: TagSerializer(many=True)},
    tags=["Blog"],  # Assign to the Blog tag group
)
class BlogTagListView(generics.ListAPIView):
    """
    API view to list all unique tags used in published blog posts.
    """

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Uncomment if you don't want pagination for tags

    def get_queryset(self):
        """
        Return a queryset of Tag objects that are associated with at least
        one published BlogPost.
        """
        # Find IDs of tags used in published posts
        published_post_tag_ids = (
            BlogPost.objects.filter(status=PostStatusChoices.PUBLISHED)
            .values_list("tags", flat=True)
            .distinct()
        )

        # Filter Tag objects by these IDs
        queryset = Tag.objects.filter(pk__in=published_post_tag_ids).order_by("name")
        return queryset


@extend_schema(
    summary="List My Advice Requests",
    description="Retrieve a list of advice requests submitted by the currently authenticated and subscribed user.",
    responses={
        status.HTTP_200_OK: BlogAdviceRequestSerializer(many=True),
        status.HTTP_401_UNAUTHORIZED: None,
        status.HTTP_403_FORBIDDEN: None,
    },
    tags=["Blog"],  # Assign to the Blog tag group
)
class MyBlogAdviceRequestListView(generics.ListAPIView):
    """
    API view to list advice requests submitted by the currently authenticated user.
    Requires authentication and subscription.
    """

    serializer_class = BlogAdviceRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return a queryset filtered to only include requests from the
        currently authenticated user.
        """
        user = self.request.user
        queryset = BlogAdviceRequest.objects.filter(user=user).order_by("-created_at")
        return queryset
