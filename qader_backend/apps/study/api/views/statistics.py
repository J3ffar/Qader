from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils.translation import gettext_lazy as _
from django.utils.dateparse import parse_date
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers.statistics import UserStatisticsSerializer

logger = logging.getLogger(__name__)

# Define allowed aggregation periods for schema and validation
AGGREGATION_PERIOD_CHOICES = ["daily", "weekly", "monthly", "yearly"]


@extend_schema(
    tags=["Study - Statistics & Progress"],
    summary="Retrieve User Statistics with Optional Filtering and Aggregation",
    description=(
        "Fetches aggregated statistics for the authenticated user, including overall progress, "
        "performance breakdown by section/subsection/skill, and recent test history.\n\n"
        "**Filtering Options (Query Parameters):**\n"
        "- `start_date` (YYYY-MM-DD): Filter data from this date (inclusive).\n"
        "- `end_date` (YYYY-MM-DD): Filter data up to this date (inclusive).\n"
        "- `aggregation_period` (string): Group time-series data (like performance trends) "
        f"by a specific period. Allowed values: {', '.join(AGGREGATION_PERIOD_CHOICES)}. "
        "If not provided, trends show individual test attempts."
    ),
    parameters=[
        OpenApiParameter(
            name="start_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Start date for filtering (YYYY-MM-DD).",
        ),
        OpenApiParameter(
            name="end_date",
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            required=False,
            description="End date for filtering (YYYY-MM-DD).",
        ),
        OpenApiParameter(
            name="aggregation_period",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            enum=AGGREGATION_PERIOD_CHOICES,
            description="Period for aggregating time-series data.",
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=UserStatisticsSerializer, description="User statistics data."
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., Invalid date format, invalid aggregation period, User profile missing)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication/Subscription)."
        ),
        500: OpenApiResponse(
            description="Internal Server Error during statistics calculation."
        ),
    },
)
class UserStatisticsView(views.APIView):
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get(self, request, *args, **kwargs):
        start_date_str = request.query_params.get("start_date")
        end_date_str = request.query_params.get("end_date")
        aggregation_period = request.query_params.get("aggregation_period")

        start_date, end_date = None, None

        if start_date_str:
            start_date = parse_date(start_date_str)
            if not start_date:
                return Response(
                    {"detail": _("Invalid start_date format. Use YYYY-MM-DD.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if end_date_str:
            end_date = parse_date(end_date_str)
            if not end_date:
                return Response(
                    {"detail": _("Invalid end_date format. Use YYYY-MM-DD.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if start_date and end_date and start_date > end_date:
            return Response(
                {"detail": _("start_date cannot be after end_date.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if aggregation_period and aggregation_period not in AGGREGATION_PERIOD_CHOICES:
            return Response(
                {
                    "detail": _(
                        f"Invalid aggregation_period. Allowed values are: {', '.join(AGGREGATION_PERIOD_CHOICES)}."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Pass validated parameters to the serializer context
        serializer_context = {
            "request": request,
            "start_date": start_date,
            "end_date": end_date,
            "aggregation_period": aggregation_period,
        }

        try:
            # Note: `instance` is obj for serializer, `obj` for get_... methods
            # For UserStatisticsSerializer, the 'obj' passed to get_... methods is the user instance
            serializer = UserStatisticsSerializer(
                instance=request.user, context=serializer_context
            )
            data = serializer.data
            return Response(data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            logger.warning(
                f"Validation error during statistics generation for user {request.user.id}: {e.detail}"
            )
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error generating statistics for user {request.user.id}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An unexpected error occurred while generating statistics."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
