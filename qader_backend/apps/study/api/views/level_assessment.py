from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers.level_assessment import (  # Import specific serializers
    LevelAssessmentStartSerializer,
    LevelAssessmentSubmitSerializer,
    LevelAssessmentResponseSerializer,
    LevelAssessmentResultSerializer,
)

logger = logging.getLogger(__name__)

# --- Level Assessment Views ---


@extend_schema(
    tags=["Study & Progress - Level Assessment"],
    summary="Start Level Assessment Test",
    description=(
        "Initiates a level assessment test for the authenticated, subscribed user. "
        "Checks for ongoing assessments. Requires first-time user or explicit retake mechanism (TBD). "
        "Selects random, active questions based on chosen sections and number."
    ),
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=LevelAssessmentResponseSerializer,
            description="Assessment started.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., level determined, ongoing assessment, no questions)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication/Subscription)."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    serializer_class = LevelAssessmentStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id': id, 'questions': queryset}
        response_serializer = LevelAssessmentResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress - Level Assessment"],
    summary="Submit Level Assessment Answers",
    description=(
        "Submits answers for a specific, ongoing level assessment. Calculates scores, "
        "updates user profile levels, marks level as determined, and marks the assessment complete."
    ),
    request=LevelAssessmentSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=LevelAssessmentResultSerializer,
            description="Submission successful.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., attempt not active, wrong answers, profile missing)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Not Found (Attempt ID invalid or doesn't belong to user)."
        ),  # Raised by serializer validation
    },
)
class LevelAssessmentSubmitView(generics.GenericAPIView):
    serializer_class = LevelAssessmentSubmitSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    # No queryset needed, validation happens in serializer

    def post(self, request, attempt_id, *args, **kwargs):
        # Pass view context (includes URL kwargs like attempt_id) to serializer for validation
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id', 'results', 'updated_profile'}
        response_serializer = LevelAssessmentResultSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)
