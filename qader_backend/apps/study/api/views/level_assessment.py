from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers import level_assessment as la_serializers  # Alias
from apps.study.api.serializers import (
    attempts as attempt_serializers,
)  # Unified responses
from apps.study.services import study as study_services
from apps.api.exceptions import UsageLimitExceeded

logger = logging.getLogger(__name__)

# --- Level Assessment Views ---


@extend_schema(
    tags=["Study - Level Assessment"],
    summary="Start Level Assessment Test",
    description="Initiates a new level assessment test for the user based on selected sections and number of questions. Returns the attempt ID and the list of questions.",
    request=la_serializers.LevelAssessmentStartSerializer,
    responses={
        201: attempt_serializers.UserTestAttemptStartResponseSerializer,  # Standard start response
        400: OpenApiResponse(
            description="Validation Error (e.g., ongoing test exists, invalid sections, insufficient questions)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication, Subscription, or Usage Limit reached)."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    """Handles starting a new Level Assessment test."""

    serializer_class = la_serializers.LevelAssessmentStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = request.user
            validated_data = serializer.validated_data

            # Call the service function to handle the logic
            result_data = study_services.start_level_assessment(
                user=user,
                sections=validated_data["sections"],
                num_questions_requested=validated_data["num_questions"],
            )

        except (ValidationError, UsageLimitExceeded) as e:
            # Handle specific known errors (validation, limits)
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(e, UsageLimitExceeded)
                else status.HTTP_400_BAD_REQUEST
            )
            error_detail = e.detail if hasattr(e, "detail") else str(e)
            return Response({"detail": error_detail}, status=status_code)
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
        response_serializer = (
            attempt_serializers.UserTestAttemptStartResponseSerializer(
                result_data, context=self.get_serializer_context()
            )
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Completion/Answering handled by unified views in attempts.py
