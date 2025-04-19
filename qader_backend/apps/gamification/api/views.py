from django.http import Http404
from rest_framework import generics, viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from django.db.models import OuterRef, Subquery, Exists  # For efficient badge checking
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.api.permissions import IsSubscribed  # Assuming this exists
from apps.users.models import UserProfile
from ..models import PointLog, Badge, UserBadge, RewardStoreItem
from .serializers import (
    GamificationSummarySerializer,
    BadgeSerializer,
    RewardStoreItemSerializer,
    PointLogSerializer,
    RewardPurchaseResponseSerializer,
)
from ..services import purchase_reward, PurchaseError


@extend_schema_view(
    get=extend_schema(
        summary="Get Gamification Summary",
        description="Retrieve the current user's points and streak information.",
        responses={200: GamificationSummarySerializer},
        tags=["Gamification"],
    )
)
class GamificationSummaryView(generics.RetrieveAPIView):
    """Provides the user's current points and streak status."""

    permission_classes = [IsAuthenticated]
    serializer_class = GamificationSummarySerializer

    def get_object(self):
        # Retrieve the UserProfile for the current user
        try:
            return UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            # Should not happen for authenticated users if profile creation is enforced
            # Consider creating profile on-the-fly or raising an error
            raise Http404("User profile not found.")


@extend_schema_view(
    list=extend_schema(
        summary="List Badges",
        description="Retrieve all available badges, indicating which ones the current user has earned.",
        responses={200: BadgeSerializer(many=True)},
        tags=["Gamification"],
    )
)
class BadgeListView(generics.ListAPIView):
    """Lists all active badges, indicating which are earned by the user."""

    permission_classes = [IsAuthenticated]
    serializer_class = BadgeSerializer
    pagination_class = None  # Usually don't paginate badges

    def get_queryset(self):
        user = self.request.user
        # Annotate each Badge with whether the current user has earned it
        # Using Subquery is generally more efficient than iterating in serializer
        user_badges = UserBadge.objects.filter(user=user, badge=OuterRef("pk"))
        return (
            Badge.objects.filter(is_active=True)
            .annotate(
                user_earned_badge_id=Subquery(
                    user_badges.values("id")[:1]
                ),  # Get ID if exists
                # Optionally prefetch the earned badge detail if needed more than just existence check
                # This depends on how SerializerMethodField is implemented
            )
            .select_related(None)
            .prefetch_related(None)
        )  # Clear default prefetch/select

    def get_serializer_context(self):
        # Pass request to serializer context to access user
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


@extend_schema_view(
    list=extend_schema(
        summary="List Reward Store Items",
        description="Retrieve items available for purchase with points.",
        responses={200: RewardStoreItemSerializer(many=True)},
        tags=["Gamification"],
    ),
    retrieve=extend_schema(  # Although ReadOnly, standard practice includes retrieve
        summary="Get Reward Store Item Detail",
        description="Retrieve details of a specific reward item.",
        responses={200: RewardStoreItemSerializer},
        tags=["Gamification"],
    ),
)
class RewardStoreItemViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides listing and retrieval of reward store items."""

    permission_classes = [IsAuthenticated]  # Viewable by all authenticated users
    serializer_class = RewardStoreItemSerializer
    queryset = RewardStoreItem.objects.filter(is_active=True)
    pagination_class = None  # Optional: paginate if store becomes large


@extend_schema(
    summary="Purchase Reward Item",
    description="Purchase an item from the reward store using points.",
    request=None,  # No request body needed, item ID is in URL
    responses={
        200: RewardPurchaseResponseSerializer,
        400: OpenApiParameter(
            name="Error Detail",
            description="Reason for failure (e.g., insufficient points).",
        ),
        403: OpenApiParameter(
            name="Error Detail", description="Permission denied (e.g., not subscribed)."
        ),
        404: OpenApiParameter(name="Error Detail", description="Item not found."),
    },
    tags=["Gamification"],
)
class RewardPurchaseView(views.APIView):
    """Handles the purchase of a reward store item."""

    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Only subscribed users can purchase

    def post(self, request, item_id, *args, **kwargs):
        try:
            result = purchase_reward(user=request.user, item_id=item_id)
            serializer = RewardPurchaseResponseSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PurchaseError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RewardStoreItem.DoesNotExist:
            return Response(
                {"detail": _("Reward item not found or is inactive.")},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            # Log unexpected errors
            # logger.exception(f"Unexpected error during reward purchase for user {request.user.id}, item {item_id}")
            return Response(
                {"detail": _("An unexpected error occurred.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema_view(
    list=extend_schema(
        summary="List Point Log History",
        description="Retrieve the current user's history of point transactions.",
        responses={200: PointLogSerializer(many=True)},
        tags=["Gamification"],
    )
)
class PointLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Provides the user's point transaction history."""

    permission_classes = [IsAuthenticated]
    serializer_class = PointLogSerializer

    def get_queryset(self):
        # Return only the logs for the currently authenticated user
        return PointLog.objects.filter(user=self.request.user)
