from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404  # Use get_object_or_404

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
    description=(
        "Initiates a level assessment test for the authenticated, subscribed user. "
        "Validates if the level is already determined or if an assessment is ongoing. "
        "Selects random, active questions based on chosen sections and number."
    ),
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=LevelAssessmentResponseSerializer,  # Use the dedicated response serializer
            description="Assessment started successfully. Returns the new attempt ID and the list of questions for the assessment.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation Error (e.g., level already determined, no active questions found, ongoing assessment exists, invalid input)."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    """
    Handles the request to start a new level assessment test.

    POST /api/v1/study/level-assessment/start/
    """

    serializer_class = LevelAssessmentStartSerializer
    # Permissions applied by DRF before view method is called
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        # Pass request context to the input serializer for validation checks (e.g., user checks)
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # serializer.save() calls the create() method which returns the dictionary:
        # {'attempt_id': id, 'questions': queryset}
        result_data = serializer.save()

        # Serialize the output using the response serializer, PASSING CONTEXT
        # Context is needed by QuestionListSerializer (nested in LevelAssessmentResponseSerializer)
        # to determine 'is_starred' for the current user.
        response_serializer = LevelAssessmentResponseSerializer(
            result_data, context={"request": request}  # Pass context here!
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress"],
    summary="Submit Level Assessment Answers",
    description=(
        "Submits the user's answers for a specific, ongoing level assessment attempt identified by `attempt_id`. "
        "Validates ownership and attempt status. Calculates scores, updates user profile levels, "
        "and marks the assessment as complete."
    ),
    request=LevelAssessmentSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=LevelAssessmentResultSerializer,  # Use the dedicated result serializer
            description="Answers submitted and processed successfully. Returns the attempt ID, final results breakdown, and updated user profile information.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation Error (e.g., invalid answers format, attempt not active, answer/question mismatch, attempt not found or belongs to another user)."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
        404: OpenApiResponse(  # Should technically be caught by serializer validation (400) now
            description="Not Found - The specified assessment attempt ID does not exist (redundant if validation handles it)."
        ),
    },
)
class LevelAssessmentSubmitView(generics.GenericAPIView):
    """
    Handles the submission of answers for a specific level assessment attempt.

    POST /api/v1/study/level-assessment/{attempt_id}/submit/
    """

    serializer_class = LevelAssessmentSubmitSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]  # Base permissions

    # We don't need get_object here because the serializer's validation
    # handles fetching and checking the attempt based on attempt_id from URL kwargs

    def post(self, request, attempt_id, *args, **kwargs):
        # Pass request and view context (including attempt_id from URL) to the serializer
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "view": self},  # 'view' gives access to kwargs
        )
        serializer.is_valid(raise_exception=True)

        # serializer.save() calls the custom processing logic which returns the result dictionary:
        # {'attempt_id': id, 'results': {...}, 'updated_profile': {...}}
        result_data = serializer.save()

        # Serialize the output using the result serializer.
        # Pass context if the nested UserProfileSerializer needs it (e.g., for profile picture URL).
        response_serializer = LevelAssessmentResultSerializer(
            result_data, context={"request": request}  # Pass context here!
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# Add other study-related views here later
# (Traditional Learning Answer, Emergency Mode, Conversation, Tests, Stats etc.)
