import logging
from django.http import Http404
from rest_framework import generics, viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# from rest_framework.decorators import action # Not used here currently
from django.utils.translation import gettext_lazy as _
from django.db.models import (
    OuterRef,
    Subquery,
    Value,
    DateTimeField,
)  # Added Value, DateTimeField
from django.db.models.functions import Coalesce  # To handle null from subquery
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.api.permissions import IsSubscribed  # Use this where appropriate
from apps.users.models import UserProfile
from ..models import PointLog, Badge, UserBadge, RewardStoreItem
from .serializers import (
    GamificationSummarySerializer,
    BadgeSerializer,
    RewardStoreItemSerializer,
    PointLogSerializer,
    RewardPurchaseResponseSerializer,
)
from ..services import purchase_reward, PurchaseError  # Import error classes

logger = logging.getLogger(__name__)
# --- Views ---


@extend_schema_view(
    get=extend_schema(
        summary="Get Gamification Summary",
        description="Retrieve the current user's points and streak information from their profile.",
        responses={200: GamificationSummarySerializer},
        tags=["Gamification"],
    )
)
class GamificationSummaryView(generics.RetrieveAPIView):
    """Provides the user's current points and streak status."""

    permission_classes = [
        IsAuthenticated
    ]  # Any authenticated user can see their summary
    serializer_class = GamificationSummarySerializer

    def get_object(self):
        # Retrieve the UserProfile for the current user.
        # Assumes UserProfile is created via signal when User is created.
        try:
            return self.request.user.profile
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile not found for authenticated user {self.request.user.id}."
            )
            raise Http404(_("User profile not found."))


@extend_schema_view(
    get=extend_schema(
        summary="List Badges",
        description="Retrieve all available badges, indicating which ones the current authenticated user has earned.",
        responses={200: BadgeSerializer(many=True)},
        tags=["Gamification"],  # Already tagged correctly
    )
)
class BadgeListView(generics.ListAPIView):
    """Lists all active badges, annotating which are earned by the user."""

    permission_classes = [IsAuthenticated]  # Any authenticated user can see badges
    serializer_class = BadgeSerializer
    pagination_class = None  # Badges usually aren't numerous enough for pagination

    def get_queryset(self):
        user = self.request.user
        # Annotate each Badge with the timestamp the current user earned it (or null).
        # This is efficient as it performs the check in the database query.
        user_badges = UserBadge.objects.filter(user=user, badge=OuterRef("pk")).values(
            "earned_at"
        )[
            :1
        ]  # Get the earned_at timestamp

        queryset = (
            Badge.objects.filter(is_active=True)
            .annotate(
                user_earned_at=Subquery(
                    user_badges, output_field=DateTimeField(null=True)
                )
            )
            .order_by("name")
        )  # Order consistently

        # Optional: Use Coalesce if you want a default value other than None, but None is fine here
        # .annotate(
        #     user_earned_at=Coalesce(Subquery(user_badges), Value(None, output_field=DateTimeField()))
        # )

        # No need for select/prefetch related unless Badge has FKs to display
        return queryset

    # No need for get_serializer_context if serializer doesn't need request directly


@extend_schema_view(
    list=extend_schema(
        summary="List Reward Store Items",
        description="Retrieve active items available for purchase with points.",
        responses={200: RewardStoreItemSerializer(many=True)},
        tags=["Gamification"],
    ),
    retrieve=extend_schema(
        summary="Get Reward Store Item Detail",
        description="Retrieve details of a specific active reward item.",
        responses={200: RewardStoreItemSerializer},
        tags=["Gamification"],  # Explicitly tag retrieve action
    ),
)
class RewardStoreItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides listing and retrieval of active reward store items."""

    permission_classes = [IsAuthenticated]  # Any authenticated user can view store
    serializer_class = RewardStoreItemSerializer
    queryset = RewardStoreItem.objects.filter(is_active=True)
    pagination_class = None  # Optional: Add pagination if store grows large


@extend_schema(  # Apply schema directly to the APIView class
    tags=["Gamification"],  # Group under Gamification tag
    summary="Purchase Reward Item",
    description="Atomically purchase an item from the reward store using points. Requires active subscription.",
    request=None,  # No request body needed, item ID is in URL path
    responses={
        200: RewardPurchaseResponseSerializer,
        400: OpenApiParameter(  # Use OpenApiParameter for error schema description
            name="Bad Request",
            description="Reason for failure (e.g., 'Insufficient points to purchase this item.', 'Failed to update points balance during purchase.', 'An unexpected error occurred during purchase.').",
            type=str,
            location=OpenApiParameter.QUERY,
        ),
        403: OpenApiParameter(
            name="Forbidden",
            description="Permission denied (e.g., user is not subscribed).",
            type=str,
            location=OpenApiParameter.QUERY,
        ),
        404: OpenApiParameter(
            name="Not Found",
            description="Reward item not found or is inactive.",
            type=str,
            location=OpenApiParameter.QUERY,
        ),
        500: OpenApiParameter(
            name="Server Error",
            description="An unexpected internal server error occurred.",
            type=str,
            location=OpenApiParameter.QUERY,
        ),
    },
)
class RewardPurchaseView(views.APIView):
    """Handles the purchase of a reward store item."""

    permission_classes = [
        IsAuthenticated,
        IsSubscribed,  # Enforce subscription for purchases
    ]

    def post(self, request, item_id: int, *args, **kwargs):
        """Handles POST request to purchase the item specified by item_id."""
        try:
            # Call the service function to handle the logic
            result = purchase_reward(user=request.user, item_id=item_id)
            serializer = RewardPurchaseResponseSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except RewardStoreItem.DoesNotExist:
            # Specific exception for item not found
            return Response(
                {"detail": _("Reward item not found or is inactive.")},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PurchaseError as e:
            # Handle specific purchase errors (e.g., insufficient points)
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Log unexpected errors for debugging
            logger.exception(
                f"Unexpected error during reward purchase for user {request.user.id}, item {item_id}"
            )
            return Response(
                {"detail": _("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    list=extend_schema(
        summary="List Point Log History",
        description="Retrieve the current authenticated user's history of point transactions, ordered by most recent.",
        responses={200: PointLogSerializer(many=True)},
        tags=["Gamification"],
    ),
    retrieve=extend_schema(
        summary="Get Point Log Detail",
        description="Retrieve details of a specific point log entry belonging to the current user.",
        responses={200: PointLogSerializer},
        tags=["Gamification"],  # Explicitly tag retrieve action
    ),
)
class PointLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides the user's point transaction history."""

    permission_classes = [IsAuthenticated]  # User can only see their own log
    serializer_class = PointLogSerializer
    # Default pagination applies from settings

    def get_queryset(self):
        """Ensure users only see their own point logs."""
        # Order by timestamp descending is handled by model Meta ordering
        return PointLog.objects.filter(user=self.request.user)
