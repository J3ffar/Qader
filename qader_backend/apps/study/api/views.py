from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _

from .serializers import (
    LevelAssessmentStartSerializer,
    LevelAssessmentSubmitSerializer,
    LevelAssessmentResponseSerializer,
    LevelAssessmentResultSerializer,
)
from apps.api.permissions import IsSubscribed  # Import custom permission
from ..models import UserTestAttempt

import logging

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Study & Progress"],
    summary="Start Level Assessment Test",
    description="Initiates a level assessment test for the authenticated user. Requires an active subscription. Selects random questions based on chosen sections and number.",
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=LevelAssessmentResponseSerializer,
            description="Assessment started successfully, returns attempt ID and questions.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation error (e.g., level already determined, no questions found, ongoing assessment exists)."
        ),
        403: OpenApiResponse(
            description="Forbidden - User does not have an active subscription."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    """
    POST /api/v1/study/level-assessment/start/
    """

    serializer_class = LevelAssessmentStartSerializer
    permission_classes = [IsSubscribed]

    def post(self, request, *args, **kwargs):
        context = {"request": request, "view": self}

        serializer = self.get_serializer(
            data=request.data, context=context  # Pass context to input serializer
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # .save() calls create() which returns dict

        # Serialize the output using the response serializer
        # *** FIX: Pass the context here as well ***
        response_serializer = LevelAssessmentResponseSerializer(
            result_data, context=context
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress"],
    summary="Submit Level Assessment Answers",
    description="Submits the user's answers for a specific level assessment attempt. Calculates scores, updates user profile levels, and marks the assessment as complete.",
    request=LevelAssessmentSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=LevelAssessmentResultSerializer,
            description="Answers submitted and processed successfully. Returns final results and updated profile info.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation error (e.g., incorrect answers format, attempt already completed, answer/question mismatch)."
        ),
        403: OpenApiResponse(
            description="Forbidden - User does not own this assessment attempt or lacks subscription."
        ),
        404: OpenApiResponse(
            description="Not Found - The specified assessment attempt ID does not exist."
        ),
    },
)
class LevelAssessmentSubmitView(generics.GenericAPIView):
    """
    POST /api/v1/study/level-assessment/{attempt_id}/submit/
    """

    serializer_class = LevelAssessmentSubmitSerializer
    permission_classes = [
        IsSubscribed,
    ]  # Object permission checked in serializer/view

    def post(self, request, attempt_id, *args, **kwargs):
        # Basic check if attempt exists before passing to serializer validation
        # More robust check (owner, status) happens within the serializer's validate method
        try:
            # Basic check if attempt exists before passing to serializer validation
            # More robust check (owner, status) happens within the serializer's validate method
            UserTestAttempt.objects.get(pk=attempt_id)
        except UserTestAttempt.DoesNotExist:
            return Response(
                {"detail": _("Assessment attempt not found.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # .save() calls custom logic

        # Serialize the output using the result serializer
        response_serializer = LevelAssessmentResultSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# Add other study-related views here later
# (Traditional Learning Answer, Emergency Mode, Conversation, Tests, Stats etc.)
