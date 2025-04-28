from rest_framework import generics, status, views, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.models import UserQuestionAttempt, UserTestAttempt, Question
from apps.study.services import record_single_answer, complete_test_attempt
from apps.study.api.serializers import (
    TestAttemptAnswerSerializer,
    TestAttemptAnswerResponseSerializer,
    TestAttemptCompletionResponseSerializer,
    LevelAssessmentResultSerializer,  # Reuse for level assessment completion
)
from apps.study.api.serializers.attempts import (
    RevealAnswerResponseSerializer,
    TraditionalAttemptStartResponseSerializer,
    TraditionalAttemptStartSerializer,
)

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Start Traditional Practice Session",
    description="Explicitly starts a new traditional practice session, creating a trackable UserTestAttempt record and returning an initial set of questions based on optional filters.",  # Updated description
    request=TraditionalAttemptStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TraditionalAttemptStartResponseSerializer,
            description="Traditional session started with initial questions.",
        ),  # Updated description
        400: OpenApiResponse(
            description="Validation Error (e.g., already active session, invalid filters, failed to get questions)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class StartTraditionalAttemptView(generics.GenericAPIView):
    serializer_class = TraditionalAttemptStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            # The serializer's create method now handles question fetching and attempt creation
            result_data = serializer.save()
        except serializers.ValidationError as e:
            # Handle validation errors raised during question fetching/attempt creation
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Catch other unexpected errors
            logger.exception(
                f"Unexpected error during StartTraditionalAttemptView post: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while starting the session.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the response serializer that includes the questions field
        response_serializer = TraditionalAttemptStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


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


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],  # Group with traditional
    summary="Reveal Answer/Explanation (Traditional Mode Only)",
    description="Retrieves the correct answer and explanation for a specific question within an *active traditional practice session*.",
    responses={
        200: OpenApiResponse(
            response=RevealAnswerResponseSerializer,
            description="Answer/explanation revealed.",
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active, not traditional, question not found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt or Question ID invalid)."),
    },
)
class RevealAnswerView(APIView):  # Use APIView for more control
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get(self, request, attempt_id, question_id, *args, **kwargs):
        # 1. Get the Active Traditional Attempt
        try:
            test_attempt = UserTestAttempt.objects.get(
                pk=attempt_id,
                user=request.user,
                status=UserTestAttempt.Status.STARTED,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,  # MUST be traditional
            )
        except UserTestAttempt.DoesNotExist:
            # Provide more specific error messages
            exists_non_trad = UserTestAttempt.objects.filter(
                pk=attempt_id, user=request.user, status=UserTestAttempt.Status.STARTED
            ).exists()
            if exists_non_trad:
                raise PermissionDenied(
                    _("Cannot reveal answers during non-traditional test attempts.")
                )
            else:
                raise NotFound(_("Active traditional practice session not found."))
        except Exception as e:
            logger.error(
                f"Error fetching traditional attempt {attempt_id} for revealing: {e}",
                exc_info=True,
            )
            raise  # Re-raise unexpected errors

        # 2. Get the Question
        try:
            # Optionally check if question is *supposed* to be part of this session based on filters?
            # For simplicity now, just check if it exists.
            question = Question.objects.get(pk=question_id, is_active=True)
        except Question.DoesNotExist:
            raise NotFound(_("Question not found."))

        # 3. Record that the solution was viewed (Optional but useful)
        # This helps distinguish between getting it wrong vs looking up the answer
        UserQuestionAttempt.objects.update_or_create(
            user=request.user,
            test_attempt=test_attempt,
            question=question,
            defaults={
                "used_solution_method": True,  # Mark as revealed
                "mode": UserQuestionAttempt.Mode.TRADITIONAL,
                # Update attempted_at if revealing counts as interaction?
                # "attempted_at": timezone.now(),
            },
        )
        logger.info(
            f"User {request.user.id} revealed answer for Q:{question_id} in traditional attempt {attempt_id}"
        )

        # 4. Prepare and Return Response
        response_data = {
            "question_id": question.id,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            # Add hints here if your Question model has them
        }
        serializer = RevealAnswerResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],  # Group with traditional
    summary="End Traditional Practice Session",
    description="Gracefully ends an active traditional practice session, marking it as completed (or finished) and setting the end time.",
    request=None,
    responses={
        200: OpenApiResponse(description="Traditional session ended successfully."),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active or not traditional)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt ID invalid)."),
    },
)
class EndTraditionalAttemptView(APIView):  # Use APIView or GenericAPIView
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = UserTestAttempt.objects.get(
                pk=attempt_id,
                user=request.user,
                status=UserTestAttempt.Status.STARTED,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,  # MUST be traditional
            )
        except UserTestAttempt.DoesNotExist:
            raise NotFound(_("Active traditional practice session not found."))
        except Exception as e:
            logger.error(
                f"Error fetching traditional attempt {attempt_id} for ending: {e}",
                exc_info=True,
            )
            raise

        try:
            # Mark as COMPLETED (or a custom 'FINISHED' status if you add one)
            test_attempt.status = UserTestAttempt.Status.COMPLETED
            test_attempt.end_time = timezone.now()
            # Call calculate_scores if you want summary data, but it won't calculate overall score %
            # test_attempt.calculate_and_save_scores(test_attempt.question_attempts.all())
            test_attempt.save(
                update_fields=["status", "end_time", "updated_at"]
            )  # Add scores/summary if calculated
            logger.info(
                f"Ended traditional practice session {test_attempt.id} for user {request.user.id}"
            )
            return Response(
                {"detail": _("Traditional practice session ended.")},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception(f"Error ending traditional attempt {attempt_id}: {e}")
            return Response(
                {"detail": _("An error occurred while ending the session.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
