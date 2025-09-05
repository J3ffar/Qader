from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers import practice_simulation as ps_serializers  # Alias
from apps.study.api.serializers import (
    attempts as attempt_serializers,
)  # Unified responses
from apps.study import services as study_services  # Import services
from apps.api.exceptions import UsageLimitExceeded

logger = logging.getLogger(__name__)

# --- Practice & Simulation Views ---


@extend_schema(
    tags=["Study - Tests (Practice & Simulation)"],
    summary="Start Practice or Simulation Test",
    description="Initiates a new Practice or Simulation test based on the provided configuration (filters, number of questions). Returns the attempt ID and the list of questions.",
    request=ps_serializers.PracticeSimulationStartSerializer,
    responses={
        201: attempt_serializers.UserTestAttemptStartResponseSerializer,  # Standard start response
        400: OpenApiResponse(
            description="Validation Error (e.g., ongoing test exists, invalid config, no questions found)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication, Subscription, or Usage Limit reached)."
        ),
    },
)
class PracticeSimulationStartView(generics.GenericAPIView):
    """Handles starting a new Practice or Simulation test."""

    serializer_class = ps_serializers.PracticeSimulationStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = request.user
            validated_data = serializer.validated_data
            config_data = validated_data["config"]  # Nested config

            # Call the service function
            result_data = study_services.start_practice_or_simulation(
                user=user,
                attempt_type=validated_data["test_type"],
                name=config_data.get("name"),
                subsections=config_data.get("subsections", []),
                skills=config_data.get("skills", []),
                num_questions_requested=config_data["num_questions"],
                starred=config_data.get("starred", False),
                not_mastered=config_data.get("not_mastered", False),
            )

        except (ValidationError, UsageLimitExceeded) as e:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(e, UsageLimitExceeded)
                else status.HTTP_400_BAD_REQUEST
            )
            error_detail = e.detail if hasattr(e, "detail") else str(e)
            return Response({"detail": error_detail}, status=status_code)
        except Exception as e:
            logger.exception(
                f"Unexpected error during PracticeSimulationStartView post for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while starting the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the standard response serializer
        response_serializer = (
            attempt_serializers.UserTestAttemptStartResponseSerializer(
                result_data, context=self.get_serializer_context()
            )
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Completion/Answering handled by unified views in attempts.py
