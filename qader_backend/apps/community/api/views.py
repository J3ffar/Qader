from django.db.models import Count, Prefetch, Q
from rest_framework import viewsets, generics, status, mixins
from rest_framework.serializers import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAdminUser, BasePermission
from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from taggit.models import Tag
from rest_framework.decorators import action
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
)
from django.contrib.auth.models import User
from django.utils import timezone

from apps.community.models import CommunityPost, CommunityReply, PartnerRequest
from apps.community.api.serializers import (
    CommunityPartnerSerializer,  # Import new serializer
    CommunityPostCreateUpdateSerializer,
    CommunityPostListSerializer,
    CommunityPostDetailSerializer,
    CommunityReplySerializer,
    TagSerializer,
    PartnerRequestSerializer,
)
from apps.community.api.filters import (
    CommunityPostFilter,
    UserPartnerFilter,
)  # Import new filter
from apps.users.models import AccountTypeChoices
from apps.api.permissions import (
    IsSubscribed,
    IsOwnerOrAdminOrReadOnly,
)
from apps.notifications.services import create_notification
from apps.notifications.models import NotificationTypeChoices
from apps.users.constants import RoleChoices


@extend_schema(
    tags=["Student Community - Partner Search"],
    summary="Search for Study Partners",
    description="Retrieve a paginated list of users who are potential study partners. "
    "All listed users have an active subscription. "
    "Filter by `name` (searches username and full name), `grade`, and `section` (learning section slug).",
    parameters=[
        OpenApiParameter(
            "name",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Search term for the user's full name or username.",
        ),
        OpenApiParameter(
            "grade",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by the user's grade (e.g., 'ثالث ثانوي').",
        ),
        OpenApiParameter(
            "section",
            OpenApiTypes.STR,
            OpenApiParameter.QUERY,
            description="Filter by learning section slug (e.g., 'quantitative', 'verbal').",
        ),
    ],
    responses={200: CommunityPartnerSerializer(many=True)},
)
class PartnerSearchView(generics.ListAPIView):
    """
    Provides a searchable list of potential study partners.

    - Lists only users with an active subscription.
    - Excludes the currently authenticated user from the list.
    - Supports filtering by name and grade.
    """

    serializer_class = CommunityPartnerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserPartnerFilter

    def get_queryset(self):
        """
        - Returns a queryset of `User` objects.
        - Filters for users with an active subscription.
        - Excludes the requesting user.
        - Optimizes by selecting related profile and ordering by recent activity.
        """
        active_subscription_q = Q(
            profile__subscription_expires_at__gte=timezone.now()
        ) | Q(profile__account_type=AccountTypeChoices.PERMANENT)

        return (
            User.objects.select_related("profile")
            .filter(profile__isnull=False, is_active=True)
            .filter(profile__role=RoleChoices.STUDENT)
            .filter(active_subscription_q)
            .exclude(pk=self.request.user.pk)
            .order_by("-last_login", "profile__full_name")
        )


@extend_schema(tags=["Student Community"])
@extend_schema_view(
    list=extend_schema(
        summary="List Community Posts",
        description="Retrieve a paginated list of community posts. Filter by `post_type`, `section_filter` (slug), `tags` (comma-separated names/slugs), `pinned`. Search fields: `title`, `content`, `author__username`, `tags__name`. Order by `created_at` (default descending), `reply_count`.",
        parameters=[
            OpenApiParameter(
                "post_type",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                enum=CommunityPost.PostType.values,
            ),
            OpenApiParameter(
                "section_filter",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Slug of the learning section.",
            ),
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Comma-separated tag names/slugs.",
            ),
            OpenApiParameter("pinned", OpenApiTypes.BOOL, OpenApiParameter.QUERY),
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Search term for title, content, author, tags.",
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Order by fields: created_at, -created_at, reply_count, -reply_count.",
            ),
        ],
    ),
    create=extend_schema(
        summary="Create Community Post",
        description="Create a new post in the community forum. Requires an active subscription.",
        request=CommunityPostCreateUpdateSerializer,
        responses={201: CommunityPostCreateUpdateSerializer},
    ),
    retrieve=extend_schema(
        summary="Retrieve Community Post",
        description="Get details of a single community post, including its paginated replies.",
        responses={200: CommunityPostDetailSerializer},
    ),
    update=extend_schema(
        summary="Update Community Post (Full)",
        description="Fully update an existing community post. Requires ownership or admin privileges.",
        request=CommunityPostCreateUpdateSerializer,
        responses={200: CommunityPostCreateUpdateSerializer},
    ),
    partial_update=extend_schema(
        summary="Partially Update Community Post",
        description="Partially update an existing community post. Requires ownership or admin privileges. Admins can update `is_pinned` and `is_closed`.",
        request=CommunityPostCreateUpdateSerializer,
        responses={200: CommunityPostCreateUpdateSerializer},
    ),
    destroy=extend_schema(
        summary="Delete Community Post",
        description="Delete an existing community post. Requires ownership or admin privileges.",
        responses={204: None},
    ),
    toggle_like=extend_schema(
        summary="Toggle Like on Post",
        description="Toggles the like status for the current user on a specific post.",
        request=None,
        responses={
            200: {
                "description": "Like status toggled successfully.",
                "examples": {
                    "application/json": {
                        "status": "like toggled",
                        "liked": True,
                    }
                },
            }
        },
    ),
)
class CommunityPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Community Posts (CRUD operations).

    Ensures users are subscribed and handles ownership/admin permissions for write actions.
    Provides filtering, searching, and ordering.
    Retrieval includes paginated replies.

    Adheres to SOLID:
    - SRP: Manages request/response cycle for Community Posts. Delegates serialization.
    - OCP: Extendable via custom actions or overriding methods.
    - DIP: Depends on abstractions (QuerySet, Serializers, Permissions).
    """

    queryset = CommunityPost.objects.all()  # Base queryset, refined in get_queryset
    permission_classes = [IsAuthenticated, IsSubscribed, IsOwnerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CommunityPostFilter
    search_fields = ["title", "content", "author__username", "tags__name"]
    # Default ordering is defined in the model's Meta, but explicit here for clarity
    ordering_fields = [
        "created_at",
        "reply_count_annotated",
    ]  # Use annotated field name
    ordering = ["-is_pinned", "-created_at"]  # Default ordering

    def get_queryset(self):
        """
        Optimize queryset for the specific action.
        Select related authors/sections and prefetch tags.
        Annotate reply count for ordering and serialization.
        """
        queryset = (
            CommunityPost.objects.select_related(
                "author__profile",  # Optimize fetching author profile data
                "section_filter",
            )
            .prefetch_related(
                "tags",  # Optimize fetching tags
                # Prefetching replies here can be heavy for list view, handle in retrieve
            )
            .annotate(
                reply_count_annotated=Count(
                    "replies", distinct=True
                ),  # Efficiently count replies
                like_count_annotated=Count(
                    "likes", distinct=True
                ),  # Add this annotation
            )
        )

        # Further optimization: Only prefetch replies for detail view if needed
        # if self.action == 'retrieve':
        #     # This might still be too much if replies are numerous; pagination in retrieve is safer.
        #     queryset = queryset.prefetch_related('replies__author__profile')

        return queryset.order_by(*self.ordering)  # Apply default or requested ordering

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "list":
            # Here we specify that ONLY the 'list' action requires just authentication.
            # You could also use [AllowAny()] to make it public.
            permission_classes = [IsAuthenticated]
        else:
            # For all other actions (create, accept, reject, etc.),
            # we require the user to be authenticated AND subscribed.
            permission_classes = [IsAuthenticated, IsSubscribed]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Return appropriate serializer class based on the action."""
        if self.action == "list":
            return CommunityPostListSerializer
        elif self.action == "retrieve":
            return CommunityPostDetailSerializer
        # Use the same serializer for create, update, partial_update
        return CommunityPostCreateUpdateSerializer

    def perform_create(self, serializer):
        """Set the author automatically when creating a post."""
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Override create to use the Detail serializer for the response.
        """
        # Use the default serializer for validation and saving
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        self.perform_create(write_serializer)
        instance = write_serializer.instance

        # Use the Detail serializer to create the response payload
        read_serializer = CommunityPostDetailSerializer(
            instance, context=self.get_serializer_context()
        )

        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        Override update to use the Detail serializer for the response.
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Use the default serializer for validation and saving
        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        write_serializer.is_valid(raise_exception=True)
        self.perform_update(write_serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been used, we need to
            # forcibly refresh the instance from the database.
            instance = self.get_object()

        # Use the Detail serializer to create the response payload
        read_serializer = CommunityPostDetailSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(read_serializer.data)

    # The update method now handles both full and partial updates.
    # We no longer need a separate perform_update, but we keep it for admin logic.
    def perform_update(self, serializer):
        """
        Handle updates, allowing admins to modify 'is_pinned' and 'is_closed'.
        Standard users can only update fields defined as writable in the serializer
        if they are the author.
        """
        # Permissions are checked by IsOwnerOrAdminOrReadOnly before this method is called.

        # Extract potential admin-only fields from request data *before* validation
        # We use request.data because they are read-only in the serializer itself
        is_pinned_update = self.request.data.get("is_pinned")
        is_closed_update = self.request.data.get("is_closed")

        # Save the instance with regular validated data first
        instance = serializer.save()

        # Check if the user is staff and if admin fields need updating
        if self.request.user.is_staff:
            update_fields = []
            if is_pinned_update is not None:
                # Convert potential string ('true'/'false') to boolean
                pinned_bool = str(is_pinned_update).lower() in ["true", "1"]
                if instance.is_pinned != pinned_bool:
                    instance.is_pinned = pinned_bool
                    update_fields.append("is_pinned")

            if is_closed_update is not None:
                closed_bool = str(is_closed_update).lower() in ["true", "1"]
                if instance.is_closed != closed_bool:
                    instance.is_closed = closed_bool
                    update_fields.append("is_closed")

            # Save again only if admin fields were changed
            if update_fields:
                instance.save(update_fields=update_fields + ["updated_at"])

    # perform_destroy uses the default behavior, relying on IsOwnerOrAdminOrReadOnly

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a post and include its paginated replies.
        Overrides the default retrieve to add reply pagination.
        """
        instance = self.get_object()  # Handles 404 if not found
        post_serializer = self.get_serializer(instance)
        post_data = post_serializer.data

        # --- Paginate Replies ---
        # Efficiently fetch replies for the current post
        reply_queryset = (
            instance.replies.select_related(
                "author__profile", "parent_reply"  # Select parent for ID access
            )
            .prefetch_related(
                # Prefetch children count if needed often, or use annotation
                # Prefetch('child_replies') # Less efficient than count usually
            )
            .annotate(child_replies_count_annotated=Count("child_replies"))
            .order_by("created_at")
        )  # Standard chronological order for replies

        # Use the view's pagination settings
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(reply_queryset, request, view=self)

        if page is not None:
            # Serialize the current page of replies
            reply_serializer = CommunityReplySerializer(
                page, many=True, context=self.get_serializer_context()
            )
            # Get the paginated response structure (includes count, next, previous)
            paginated_replies = paginator.get_paginated_response(
                reply_serializer.data
            ).data
        else:
            # Handle cases where pagination is disabled or no replies exist
            reply_serializer = CommunityReplySerializer(
                reply_queryset, many=True, context=self.get_serializer_context()
            )
            paginated_replies = {
                "count": reply_queryset.count(),
                "next": None,
                "previous": None,
                "results": reply_serializer.data,
            }
        # --- End Paginate Replies ---

        # Add the paginated replies under the 'replies' key in the response
        post_data["replies"] = paginated_replies
        return Response(post_data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def toggle_like(self, request, pk=None):
        """Toggles the like status for the current user on a post."""
        post = self.get_object()
        user = request.user

        if user in post.likes.all():
            post.likes.remove(user)
            liked = False
        else:
            post.likes.add(user)
            liked = True

        return Response({"status": "like toggled", "liked": liked})


@extend_schema(
    tags=["Student Community"],
    summary="List/Create Replies",
    description="List replies for a specific post (`/posts/{post_pk}/replies/`) or create a new reply for that post. Requires subscription.",
)
@extend_schema_view(
    get=extend_schema(
        description="List replies for post with ID `post_pk`. Replies are paginated.",
        responses={
            200: CommunityReplySerializer(many=True)
        },  # Note: Actual response is paginated
    ),
    post=extend_schema(
        description="Create a new reply for post with ID `post_pk`. Can optionally specify `parent_reply_id` for threading.",
        request=CommunityReplySerializer,
        responses={201: CommunityReplySerializer},
    ),
)
class CommunityReplyListCreateView(generics.ListCreateAPIView):
    """
    API view to list replies for a specific post or create a new reply.
    """

    serializer_class = CommunityReplySerializer
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Must be subscribed to read/write replies
    # Inherits pagination class from settings

    # def get_permissions(self):
    #     """
    #     Instantiates and returns the list of permissions that this view requires,
    #     based on the request method.
    #     """
    #     # For a 'list' request (GET), maybe you only require authentication
    #     if self.request.method == "GET":
    #         permission_classes = [IsAuthenticated]
    #     # For a 'create' request (POST), you require authentication AND subscription
    #     else:  # This covers POST, OPTIONS, etc.
    #         permission_classes = [IsAuthenticated, IsSubscribed]

    #     return [permission() for permission in permission_classes]

    def get_post_object(self):
        """Helper method to retrieve the associated CommunityPost or raise NotFound."""
        post_pk = self.kwargs.get("post_pk")
        try:
            # Fetch post with select_related for author check if needed later
            post = CommunityPost.objects.select_related("author").get(pk=post_pk)
            return post
        except CommunityPost.DoesNotExist:
            raise NotFound(detail=f"Community Post with ID {post_pk} not found.")

    def get_queryset(self):
        """Return replies belonging to the specified post, ordered by creation."""
        post = self.get_post_object()  # Ensures post exists before querying replies
        return (
            post.replies.select_related("author__profile", "parent_reply")
            .annotate(child_replies_count_annotated=Count("child_replies"))
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        """
        Set the author and associate the reply with the correct post.
        Validate parent reply belongs to the same post and check if post is closed.
        """
        post = self.get_post_object()  # Retrieve the post instance

        # Prevent replying to closed posts (unless user is admin)
        if post.is_closed and not self.request.user.is_staff:
            raise PermissionDenied(
                "This post is closed and does not accept new replies."
            )

        # Validate parent reply contextually
        parent_reply_obj = serializer.validated_data.get("parent_reply")
        if parent_reply_obj and parent_reply_obj.post != post:
            raise ValidationError(
                {"parent_reply_id": _("Parent reply does not belong to this post.")}
            )

        serializer.save(author=self.request.user, post=post)


@extend_schema(
    tags=["Student Community"],
    summary="List Community Tags",
    description="Retrieve a list of tags used across community posts, ordered by popularity (highest usage count first).",
    responses={200: TagSerializer(many=True)},
)
class TagListView(generics.ListAPIView):
    """
    Provides a list of tags used in the Community app, ordered by frequency.
    """

    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]  # Allow any logged-in user to see tags

    def get_queryset(self):
        """
        Return Tag objects annotated with their usage count in CommunityPost,
        ordered by count descending.
        """
        # Using distinct=True with Count on the reverse generic relation
        # Requires careful checking of the Taggit internals or specific testing.
        # A safer approach might be to filter TaggedItem for the correct ContentType.
        # Assuming CommunityPost is the only model using tags for simplicity here.
        # If other models use tags, filtering by ContentType is necessary.
        # from django.contrib.contenttypes.models import ContentType
        # post_content_type = ContentType.objects.get_for_model(CommunityPost)

        return (
            Tag.objects.annotate(
                # Use taggit_taggeditem_items which is the default related_name
                # Filter by content_type if necessary:
                # count=Count('taggit_taggeditem_items', filter=Q(taggit_taggeditem_items__content_type=post_content_type))
                count=Count("taggit_taggeditem_items")
            )
            .filter(count__gt=0)
            .order_by("-count", "name")
        )  # Order by count, then name alphabetically


class IsRequestRecipient(BasePermission):
    """
    Permission to only allow the recipient of a request to modify it.
    """

    message = "You do not have permission to perform this action."

    def has_object_permission(self, request, view, obj):
        return obj.to_user == request.user


@extend_schema(
    tags=["Student Community - Partner Requests"],
    summary="Manage Study Partner Requests",
    description="Create, view, accept, or reject study partner requests.",
)
class PartnerRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing partner requests.
    - `create`: Send a new partner request to a user.
    - `list`: View your sent and received requests.
    - `accept`: (Action) Accept a received request.
    - `reject`: (Action) Reject a received request.
    """

    serializer_class = PartnerRequestSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "list":
            # Here we specify that ONLY the 'list' action requires just authentication.
            # You could also use [AllowAny()] to make it public.
            permission_classes = [IsAuthenticated]
        else:
            # For all other actions (create, accept, reject, etc.),
            # we require the user to be authenticated AND subscribed.
            permission_classes = [IsAuthenticated, IsSubscribed]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Return requests where the user is either the sender or the recipient.
        Filter by direction (sent/received).
        """
        user = self.request.user
        direction = self.request.query_params.get("direction", None)

        base_query = PartnerRequest.objects.filter(
            Q(from_user=user) | Q(to_user=user)
        ).select_related("from_user__profile", "to_user__profile")

        if direction == "sent":
            return base_query.filter(from_user=user)
        elif direction == "received":
            return base_query.filter(to_user=user)

        return base_query

    def perform_create(self, serializer):
        """Set the sender automatically and send a notification."""
        instance = serializer.save(from_user=self.request.user)

        # Send notification to the recipient
        create_notification(
            recipient=instance.to_user,
            actor=instance.from_user,
            verb=_("sent you a study partner request"),
            target=instance,
            notification_type=NotificationTypeChoices.COMMUNITY_PARTNER,
            url=f"/communstudy/study-community/partner_search?tab=received",  # Example frontend URL
            send_email=True,
        )

    @extend_schema(
        summary="Accept a Partner Request",
        description="Accept a pending partner request that was sent to you.",
        responses={200: PartnerRequestSerializer()},
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsRequestRecipient],
    )
    def accept(self, request, pk=None):
        partner_request = self.get_object()
        if partner_request.status != PartnerRequest.StatusChoices.PENDING:
            return Response(
                {"detail": "This request is not pending and cannot be accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partner_request.status = PartnerRequest.StatusChoices.ACCEPTED
        partner_request.save(update_fields=["status", "updated_at"])

        # Notify the original sender that their request was accepted
        create_notification(
            recipient=partner_request.from_user,
            actor=partner_request.to_user,
            verb=_("accepted your study partner request"),
            target=partner_request,
            notification_type=NotificationTypeChoices.COMMUNITY_PARTNER,
            url=f"/study/study-community/partner_search?tab=sent",  # Example frontend URL
            send_email=True,
        )

        serializer = self.get_serializer(partner_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Reject a Partner Request",
        description="Reject a pending partner request that was sent to you.",
        responses={200: PartnerRequestSerializer()},
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsRequestRecipient],
    )
    def reject(self, request, pk=None):
        partner_request = self.get_object()
        if partner_request.status != PartnerRequest.StatusChoices.PENDING:
            return Response(
                {"detail": "This request is not pending and cannot be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        partner_request.status = PartnerRequest.StatusChoices.REJECTED
        partner_request.save(update_fields=["status", "updated_at"])

        serializer = self.get_serializer(partner_request)
        return Response(serializer.data, status=status.HTTP_200_OK)
