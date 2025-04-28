from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.models import UserTestAttempt, Question
from apps.study.services import record_single_answer, complete_test_attempt
from apps.study.api.serializers import (
    TestAttemptAnswerSerializer,
    TestAttemptAnswerResponseSerializer,
    TestAttemptCompletionResponseSerializer,
    LevelAssessmentResultSerializer,  # Reuse for level assessment completion
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=[
        "Study & Progress - Tests & Practice"
    ],  # Keep under this tag? Or a new "Attempts" tag?
    summary="Submit Single Answer for Test Attempt",
    description=(
        "Submits an answer for a *single question* within an *ongoing* test attempt "
        "(Level Assessment, Practice, or Simulation). Records the answer, updates proficiency, "
        "and provides immediate feedback. Use the 'complete' endpoint to finalize the test."
    ),
    request=TestAttemptAnswerSerializer,
    responses={
        200: OpenApiResponse(
            response=TestAttemptAnswerResponseSerializer,
            description="Answer recorded successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid input, question not in attempt, attempt not active)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Not Found (Attempt ID or Question ID invalid)."
        ),
    },
)
class TestAttemptAnswerView(generics.GenericAPIView):
    """Handles submission of a single answer for any active test attempt."""

    serializer_class = TestAttemptAnswerSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_object(self):
        """Get the ongoing test attempt, ensuring ownership."""
        attempt_id = self.kwargs.get("attempt_id")
        attempt = get_object_or_404(
            UserTestAttempt,
            pk=attempt_id,
            user=self.request.user,
            status=UserTestAttempt.Status.STARTED,  # Must be ongoing
        )
        return attempt

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = self.get_object()
        except Exception as e:
            # get_object_or_404 raises Http404, handled by DRF.
            # Log if needed, but let DRF handle response.
            logger.warning(
                f"Failed to find active attempt {attempt_id} for user {request.user.id}: {e}"
            )
            # Re-raise or let DRF handle Http404
            raise

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_id = serializer.validated_data["question_id"].id
        try:
            # Fetch the specific question to pass to the service
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question_id": _("Question not found.")})

        try:
            # Call the service function to handle the logic
            result_data = record_single_answer(
                test_attempt=test_attempt,
                question=question,
                answer_data=serializer.validated_data,
            )
            response_serializer = TestAttemptAnswerResponseSerializer(result_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            # Propagate validation errors from the service
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Error recording single answer for attempt {attempt_id}, Q {question_id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while recording the answer.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Complete Test Attempt",
    description=(
        "Finalizes an *ongoing* test attempt (Level Assessment, Practice, or Simulation). "
        "Calculates final scores based on all recorded answers, updates the attempt status to 'Completed', "
        "awards completion points/badges, and updates profile levels if it's a Level Assessment."
    ),
    request=None,  # No request body needed
    responses={
        200: OpenApiResponse(
            response=TestAttemptCompletionResponseSerializer,  # Or LevelAssessmentResultSerializer based on type
            description="Test attempt completed successfully. Final results returned.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., attempt not active or already completed)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt ID invalid)."),
    },
)
class CompleteTestAttemptView(generics.GenericAPIView):
    """Handles the completion and final scoring of any active test attempt."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    # Define response serializer based on attempt type in get method if needed,
    # or use a generic one and let service return appropriate data.
    # serializer_class = TestAttemptCompletionResponseSerializer # Generic default

    def get_object(self):
        """Get the ongoing test attempt, ensuring ownership."""
        attempt_id = self.kwargs.get("attempt_id")
        attempt = get_object_or_404(
            UserTestAttempt.objects.select_related(
                "user", "user__profile"
            ),  # Eager load profile for level assessment
            pk=attempt_id,
            user=self.request.user,
            status=UserTestAttempt.Status.STARTED,  # Must be ongoing
        )
        return attempt

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = self.get_object()
        except Exception as e:
            logger.warning(
                f"Failed to find active attempt {attempt_id} for completion by user {request.user.id}: {e}"
            )
            raise  # Let DRF handle Http404

        try:
            # Call the service function to handle completion logic
            result_data = complete_test_attempt(test_attempt=test_attempt)

            # Choose the appropriate response serializer based on attempt type
            if (
                test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                response_serializer = LevelAssessmentResultSerializer(
                    result_data, context={"request": request}
                )
            else:
                response_serializer = TestAttemptCompletionResponseSerializer(
                    result_data, context={"request": request}
                )

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            # Propagate validation errors from the service
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error completing test attempt {attempt_id}: {e}")
            return Response(
                {"detail": _("An internal error occurred while completing the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Cancel Test Attempt",
    description="Cancels (abandons) an *ongoing* test attempt. Sets status to 'Abandoned' and records end time. No scores are calculated.",
    request=None,  # No request body needed
    responses={
        200: OpenApiResponse(description="Test attempt cancelled successfully."),
        400: OpenApiResponse(description="Bad Request (e.g., attempt not active)."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt ID invalid)."),
    },
)
class CancelTestAttemptView(generics.GenericAPIView):
    """Handles the cancellation (abandonment) of an active test attempt."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_object(self):
        """Get the ongoing test attempt, ensuring ownership."""
        attempt_id = self.kwargs.get("attempt_id")
        attempt = get_object_or_404(
            UserTestAttempt,
            pk=attempt_id,
            user=self.request.user,
            status=UserTestAttempt.Status.STARTED,  # Must be ongoing
        )
        return attempt

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = self.get_object()
        except Exception as e:
            logger.warning(
                f"Failed to find active attempt {attempt_id} for cancellation by user {request.user.id}: {e}"
            )
            raise  # Let DRF handle Http404

        try:
            # Directly update status and end time
            test_attempt.status = UserTestAttempt.Status.ABANDONED
            test_attempt.end_time = timezone.now()
            test_attempt.save(update_fields=["status", "end_time", "updated_at"])
            logger.info(
                f"Test attempt {test_attempt.id} cancelled by user {request.user.id}."
            )
            return Response(
                {"detail": _("Test attempt cancelled.")}, status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.exception(f"Error cancelling test attempt {attempt_id}: {e}")
            return Response(
                {"detail": _("An internal error occurred while cancelling the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
