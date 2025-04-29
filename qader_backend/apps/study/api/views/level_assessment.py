from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers import (
    LevelAssessmentStartSerializer,
    UserTestAttemptStartResponseSerializer,  # Use standard response
)

logger = logging.getLogger(__name__)

# --- Level Assessment Views ---


@extend_schema(
    tags=["Study - Level Assessment"],
    summary="Start Level Assessment Test",
    description="Initiates a new level assessment test for the user based on selected sections and number of questions. Returns the attempt ID and the list of questions.",
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=UserTestAttemptStartResponseSerializer,  # Standard start response
            description="Level assessment started successfully. Returns attempt ID and questions.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., ongoing test exists, not enough questions found, invalid sections)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication or Subscription required)."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    """Handles starting a new Level Assessment test."""

    serializer_class = LevelAssessmentStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            # The serializer's create method now handles question fetching and attempt creation
            result_data = serializer.save()  # Returns dict: {'attempt_id', 'questions'}
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during LevelAssessmentStartView post for user {request.user.id}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An internal error occurred while starting the assessment."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the standard response serializer for starting attempts
        response_serializer = UserTestAttemptStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Completion of Level Assessment is handled by the unified UserTestAttemptCompleteView
# Note: Answering questions during Level Assessment is handled by the unified UserTestAttemptAnswerView
