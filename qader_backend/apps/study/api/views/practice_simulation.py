from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers import (
    PracticeSimulationStartSerializer,
    UserTestAttemptStartResponseSerializer,  # Use standard response
)

logger = logging.getLogger(__name__)

# --- Practice & Simulation Views ---


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],  # Use tag from settings
    summary="Start Practice or Simulation Test",
    description="Initiates a new Practice or Simulation test based on the provided configuration (filters, number of questions). Returns the attempt ID and the list of questions.",
    request=PracticeSimulationStartSerializer,
    responses={
        201: OpenApiResponse(
            response=UserTestAttemptStartResponseSerializer,  # Standard start response
            description="Practice/Simulation test started successfully. Returns attempt ID and questions.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., ongoing test exists, invalid config, no questions found)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication or Subscription required)."
        ),
    },
)
class PracticeSimulationStartView(generics.GenericAPIView):
    """Handles starting a new Practice or Simulation test."""

    serializer_class = PracticeSimulationStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            # Serializer's create method handles question fetching and attempt creation
            result_data = serializer.save()  # Returns dict: {'attempt_id', 'questions'}
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during PracticeSimulationStartView post for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while starting the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the standard response serializer
        response_serializer = UserTestAttemptStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Completion is handled by the unified UserTestAttemptCompleteView
# Note: Answering questions is handled by the unified UserTestAttemptAnswerView
