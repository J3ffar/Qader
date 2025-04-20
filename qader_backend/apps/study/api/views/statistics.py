from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers.statistics import (
    UserStatisticsSerializer,
)  # Import specific serializer

logger = logging.getLogger(__name__)

# --- Statistics View ---


@extend_schema(
    tags=["Study & Progress - Statistics"],
    summary="Retrieve User Statistics",
    description=(
        "Fetches aggregated statistics for the authenticated user, including overall progress, "
        "performance breakdown by section/subsection/skill, and recent test history."
    ),
    responses={
        200: OpenApiResponse(
            response=UserStatisticsSerializer, description="User statistics data."
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., User profile missing - error raised by serializer)."
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
    """
    Provides aggregated statistics for the authenticated user's study progress.
    """

    permission_classes = [IsAuthenticated, IsSubscribed]

    def get(self, request, *args, **kwargs):
        # The serializer calculates everything based on the user in the request context
        try:
            serializer = UserStatisticsSerializer(
                instance=request.user, context={"request": request}
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
