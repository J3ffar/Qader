import logging
from django.http import Http404
from rest_framework import generics, viewsets, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import django_filters
from django_filters.rest_framework import (
    DjangoFilterBackend,
    DateFromToRangeFilter,
    FilterSet,
)
from rest_framework import filters as drf_filters

# from rest_framework.decorators import action # Not used here currently
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, date, datetime, time
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
from ..models import (
    PointLog,
    Badge,
    StudyDayLog,
    UserBadge,
    RewardStoreItem,
    UserRewardPurchase,
)  # Added import
from .serializers import (
    DailyPointSummarySerializer,
    GamificationSummarySerializer,
    BadgeSerializer,
    RewardStoreItemSerializer,
    PointLogSerializer,
    RewardPurchaseResponseSerializer,
    StudyDayLogSerializer,
    UserEarnedBadgeSerializer,
    UserPurchasedItemSerializer,  # Added import
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
    get=extend_schema(
        summary="List My Earned Badges",
        description="Retrieve all badges earned by the current authenticated user, ordered by most recently earned.",
        responses={200: UserEarnedBadgeSerializer(many=True)},
        tags=["Gamification"],
    )
)
class UserEarnedBadgesListView(generics.ListAPIView):
    """
    Lists all badges earned by the authenticated user.
    The response includes details of each badge and the timestamp it was earned.
    Results are ordered by the date earned, with the most recent first.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserEarnedBadgeSerializer
    # Pagination will use global DRF settings if configured, otherwise no pagination.
    # If you want to explicitly disable pagination for this view:
    # pagination_class = None

    def get_queryset(self):
        """
        Returns a queryset of UserBadge instances for the current authenticated user.
        It pre-fetches related Badge data to optimize database queries.
        """
        user = self.request.user
        # Query UserBadge entries for the current user
        # select_related('badge') to efficiently fetch badge details in the same query
        # order_by('-earned_at') to show most recently earned badges first
        return (
            UserBadge.objects.filter(user=user)
            .select_related("badge")
            .order_by("-earned_at")
        )


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
    get=extend_schema(
        summary="List My Purchased Reward Items",
        description="Retrieve a list of all reward items purchased by the current authenticated user.",
        responses={200: UserPurchasedItemSerializer(many=True)},
        tags=["Gamification"],
    )
)
class UserPurchasedItemsListView(generics.ListAPIView):
    """
    Lists all reward store items that the authenticated user has purchased.
    The response includes details of eacf purchase.
    Results are ordered by the most recent purchase first.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserPurchasedItemSerializer

    def get_queryset(self):
        """
        Returns a queryset of UserRewardPurchase instances for the current
        authenticated user. It pre-fetches related RewardStoreItem data
        to optimize database queries.
        """
        user = self.request.user
        return (
            UserRewardPurchase.objects.filter(user=user)
            .select_related("item")
            .order_by("-purchased_at")
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


class StudyDayLogFilter(FilterSet):
    """FilterSet for StudyDayLog."""

    date_range = DateFromToRangeFilter(field_name="study_date")
    year = django_filters.NumberFilter(field_name="study_date", lookup_expr="year")
    month = django_filters.NumberFilter(field_name="study_date", lookup_expr="month")

    class Meta:
        model = StudyDayLog
        fields = [
            "date_range",
            "year",
            "month",
        ]  # Allow filtering by date range, year, month


@extend_schema_view(
    get=extend_schema(
        summary="List Study Days",
        description="Retrieve the list of calendar dates the current authenticated user performed study activities. Supports filtering by date range, year, and month.",
        parameters=[
            OpenApiParameter(
                name="date_range_after",
                description="Start date (YYYY-MM-DD)",
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="date_range_before",
                description="End date (YYYY-MM-DD)",
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="year",
                description="Filter by year (e.g., 2024)",
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="month",
                description="Filter by month (1-12)",
                type=int,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="ordering",
                description="Field to order by (e.g., study_date, -study_date)",
                type=str,
                location=OpenApiParameter.QUERY,
            ),
        ],
        responses={200: StudyDayLogSerializer(many=True)},
        tags=["Gamification"],
    )
)
class StudyDayLogListView(generics.ListAPIView):
    """
    Provides a list of dates on which the user completed study activities.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = StudyDayLogSerializer
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.OrderingFilter,
    ]  # Add OrderingFilter
    filterset_class = StudyDayLogFilter
    ordering_fields = ["study_date"]  # Allow ordering by date
    ordering = ["-study_date"]  # Default ordering

    # Standard DRF pagination will apply based on settings

    def get_queryset(self):
        """Ensure users only see their own study day logs."""
        # Ordering is handled by OrderingFilter and default 'ordering' attribute
        return StudyDayLog.objects.filter(user=self.request.user)


@extend_schema_view(
    get=extend_schema(
        summary="Get Daily Points Summary",
        description=(
            "Retrieve the total points earned/lost by the current user per day "
            "within a specified date range. Results are ordered by date ascending."
        ),
        parameters=[
            OpenApiParameter(
                name="start_date",
                description="Start date (YYYY-MM-DD). If not provided, defaults depend on `range`.",
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="end_date",
                description="End date (YYYY-MM-DD). If not provided, defaults depend on `range`.",
                type=str,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="range",
                description="Predefined range ('today', 'week', 'month', 'year'). Overrides start/end_date if provided.",
                type=str,
                enum=["today", "week", "month", "year"],  # Use enum for allowed values
                location=OpenApiParameter.QUERY,
            ),
            # Pagination parameters are handled automatically by DRF if pagination is enabled
        ],
        responses={200: DailyPointSummarySerializer(many=True)},
        tags=["Gamification"],
    )
)
class DailyPointSummaryView(generics.ListAPIView):
    """
    Provides a daily summary of points earned/lost by the user within a given range.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = DailyPointSummarySerializer
    # Optional: Add pagination if results can be large
    # pagination_class = PageNumberPagination # Or your custom pagination

    def _get_date_range(self):
        """Helper to determine the start and end datetime for filtering."""
        request = self.request
        range_param = request.query_params.get("range")
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")

        now = timezone.now()
        today = now.date()

        start_dt = None
        end_dt = None  # Use datetime for filtering DateTimeField

        if range_param:
            if range_param == "today":
                start_dt = timezone.make_aware(datetime.combine(today, time.min))
                end_dt = start_dt + timedelta(days=1)
            elif range_param == "week":
                start_of_week = today - timedelta(
                    days=today.weekday()
                )  # Monday as start
                # Or use: today - timedelta(days=(today.weekday() + 1) % 7) # Sunday as start
                start_dt = timezone.make_aware(
                    datetime.combine(start_of_week, time.min)
                )
                end_dt = start_dt + timedelta(weeks=1)
            elif range_param == "month":
                start_of_month = today.replace(day=1)
                start_dt = timezone.make_aware(
                    datetime.combine(start_of_month, time.min)
                )
                # Calculate end of month (start of next month)
                next_month = (
                    start_of_month.replace(day=28) + timedelta(days=4)
                ).replace(day=1)
                end_dt = timezone.make_aware(datetime.combine(next_month, time.min))
            elif range_param == "year":
                start_of_year = today.replace(month=1, day=1)
                start_dt = timezone.make_aware(
                    datetime.combine(start_of_year, time.min)
                )
                end_dt = timezone.make_aware(
                    datetime.combine(
                        start_of_year.replace(year=start_of_year.year + 1), time.min
                    )
                )
        else:
            # Use custom start/end dates if range is not specified
            try:
                if start_date_str:
                    start_date = date.fromisoformat(start_date_str)
                    start_dt = timezone.make_aware(
                        datetime.combine(start_date, time.min)
                    )
                else:
                    # Default start: e.g., 30 days ago or beginning of time? Let's default to 30 days.
                    start_date = today - timedelta(days=30)
                    start_dt = timezone.make_aware(
                        datetime.combine(start_date, time.min)
                    )

                if end_date_str:
                    end_date = date.fromisoformat(end_date_str)
                    # Make end_dt exclusive (up to the beginning of the next day)
                    end_dt = timezone.make_aware(
                        datetime.combine(end_date + timedelta(days=1), time.min)
                    )
                else:
                    # Default end: beginning of tomorrow (includes all of today)
                    end_dt = timezone.make_aware(
                        datetime.combine(today + timedelta(days=1), time.min)
                    )

            except ValueError:
                # Handle invalid date format - maybe raise validation error or default
                # For simplicity, we'll default to 'today' range if format is bad
                logger.warning(
                    f"Invalid date format received: start='{start_date_str}', end='{end_date_str}'. Defaulting range."
                )
                start_dt = timezone.make_aware(datetime.combine(today, time.min))
                end_dt = start_dt + timedelta(days=1)

        # Ensure end_dt is always after start_dt
        if start_dt and end_dt and end_dt <= start_dt:
            # Handle invalid range (end before start) - default or raise error
            logger.warning(
                f"End date '{end_dt}' is not after start date '{start_dt}'. Defaulting range."
            )
            start_dt = timezone.make_aware(datetime.combine(today, time.min))
            end_dt = start_dt + timedelta(days=1)

        return start_dt, end_dt

    def get_queryset(self):
        """
        Aggregates PointLog entries by day for the authenticated user
        within the specified date range.
        """
        user = self.request.user
        start_dt, end_dt = self._get_date_range()

        if not start_dt or not end_dt:
            # Should not happen with current logic, but as a safeguard
            return PointLog.objects.none()

        queryset = (
            PointLog.objects.filter(
                user=user,
                timestamp__gte=start_dt,
                timestamp__lt=end_dt,  # Use less than for exclusive end
            )
            .annotate(
                # Truncate timestamp to date
                date=TruncDate("timestamp")
            )
            .values(
                # Group by the truncated date
                "date"
            )
            .annotate(
                # Sum points for each date group
                total_points=Sum("points_change")
            )
            .values(
                # Select the final fields needed for the serializer
                "date",
                "total_points",
            )
            .order_by("date")
        )  # Order by date ascending

        return queryset
