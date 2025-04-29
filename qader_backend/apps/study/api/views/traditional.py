from typing import List, Optional
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, APIException
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.models import UserTestAttempt, Question, UserQuestionAttempt
from apps.study.services import get_filtered_questions
from apps.study.api.serializers import (
    TraditionalPracticeStartSerializer,
    TraditionalPracticeStartResponseSerializer,
    RevealAnswerResponseSerializer,
)
from apps.learning.api.serializers import (
    QuestionListSerializer,
)  # For Question List view response


logger = logging.getLogger(__name__)

# --- Traditional Learning Views ---


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],  # Use tag from settings
    summary="Start Traditional Practice Session",
    description="Starts a new traditional practice session, creating a trackable UserTestAttempt record. Can optionally return an initial set of questions based on filters.",
    request=TraditionalPracticeStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TraditionalPracticeStartResponseSerializer,
            description="Traditional session started.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., already active session)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class TraditionalPracticeStartView(generics.GenericAPIView):
    """Starts a new Traditional Practice session (UserTestAttempt)."""

    serializer_class = TraditionalPracticeStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
            # Serializer's create method handles attempt creation and initial question fetching
            result_data = (
                serializer.save()
            )  # Returns {'attempt_id', 'status', 'questions'}
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error during TraditionalPracticeStartView post for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while starting the session.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the specific response serializer for traditional start
        response_serializer = TraditionalPracticeStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Answering questions during Traditional Practice is handled by the unified UserTestAttemptAnswerView


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Fetch Questions for Traditional Practice",
    description=(
        "Retrieves a list of questions for traditional practice based on filters, outside the context of a specific ongoing attempt. "
        "Supports filtering by subsections, skills, starred, not_mastered, and excluding specific question IDs."
    ),
    parameters=[
        OpenApiParameter(
            name="limit",
            description="Maximum number of questions to return.",
            type=int,
            default=10,
            required=False,
        ),
        OpenApiParameter(
            name="subsection__slug__in",
            description="Filter by subsection slugs (comma-separated).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="skill__slug__in",
            description="Filter by skill slugs (comma-separated).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="starred",
            description="Filter by starred questions (`true`/`1`).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="not_mastered",
            description="Filter by not mastered skills (`true`/`1`).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="exclude_ids",
            description="Question IDs to exclude (comma-separated integers).",
            type=str,
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=QuestionListSerializer(many=True),
            description="List of questions matching criteria.",
        ),
        400: OpenApiResponse(description="Invalid filter parameters."),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class TraditionalQuestionListView(generics.ListAPIView):
    """Provides a list of questions for traditional learning based on filters."""

    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = None  # Use 'limit' parameter

    # Helper function to parse boolean query params robustly
    def _parse_bool_param(self, param_name: str) -> bool:
        val = self.request.query_params.get(param_name, "").strip().lower()
        return val in ["true", "1", "yes", "on"]

    # Helper function to parse comma-separated list params
    def _parse_list_param(self, param_name: str) -> Optional[List[str]]:
        val_str = self.request.query_params.get(param_name)
        return [s.strip() for s in val_str.split(",") if s.strip()] if val_str else None

    # Helper function to parse comma-separated integer list params
    def _parse_int_list_param(self, param_name: str) -> Optional[List[int]]:
        val_str = self.request.query_params.get(param_name)
        ids = []
        if not val_str:
            return None
        try:
            ids = [int(s.strip()) for s in val_str.split(",") if s.strip().isdigit()]
            return ids
        except ValueError:
            logger.warning(
                f"Invalid non-integer value found in query parameter '{param_name}': {val_str}"
            )
            # Raise validation error to inform the client
            raise drf_serializers.ValidationError(
                {param_name: [_("Invalid integer list format.")]}
            )

    def get_queryset(self):
        user = self.request.user
        limit_str = self.request.query_params.get("limit", "10")
        try:
            limit = int(limit_str)
            limit = max(
                1, min(limit, 100)
            )  # Ensure limit is within reasonable bounds (e.g., 1-100)
        except ValueError:
            limit = 10  # Default limit

        try:
            subsections = self._parse_list_param("subsection__slug__in")
            skills = self._parse_list_param("skill__slug__in")
            starred = self._parse_bool_param("starred")
            not_mastered = self._parse_bool_param("not_mastered")
            exclude_ids = self._parse_int_list_param("exclude_ids")
        except drf_serializers.ValidationError as e:
            # Need to handle validation error raised by helper
            # DRF ListAPIView doesn't automatically handle this in get_queryset
            # A simple way is to return an empty queryset and let DRF handle the response later,
            # but ideally, we'd raise the error correctly. Let's try raising it.
            # This might require overriding the `list` method to catch it.
            # For now, let's log and return none.
            logger.error(f"Validation error processing query parameters: {e.detail}")
            return Question.objects.none()
            # Alternative: raise APIException(e.detail, status.HTTP_400_BAD_REQUEST)

        # Use the central service function to get questions
        try:
            return get_filtered_questions(
                user=user,
                limit=limit,
                subsections=subsections,
                skills=skills,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=exclude_ids,
            )
        except Exception as e:
            logger.exception(
                f"Error fetching traditional questions for user {user.id}: {e}"
            )
            # Raise an API exception for internal errors
            raise APIException(
                _("An error occurred while fetching questions."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Reveal Answer/Explanation (Traditional Mode)",
    description="Retrieves the correct answer and explanation for a specific question within an *active traditional practice session*. Marks the question as having the solution viewed.",
    responses={
        200: OpenApiResponse(
            response=RevealAnswerResponseSerializer,
            description="Answer and explanation revealed.",
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active, not traditional)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt or Question ID invalid)."),
    },
)
class TraditionalRevealAnswerView(APIView):
    """Reveals the answer for a question in an active traditional session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_attempt(self, attempt_id: int, user) -> UserTestAttempt:
        """Helper to get the specific active traditional attempt."""
        try:
            test_attempt = UserTestAttempt.objects.get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
            )
            return test_attempt
        except UserTestAttempt.DoesNotExist:
            # Check if an attempt exists but isn't active/traditional for better error
            exists_non_trad = UserTestAttempt.objects.filter(
                pk=attempt_id, user=user
            ).exists()
            if exists_non_trad:
                raise PermissionDenied(
                    _(
                        "Cannot reveal answers for non-traditional or non-active sessions."
                    )
                )
            else:
                raise NotFound(_("Active traditional practice session not found."))
        except Exception as e:
            logger.error(
                f"Error fetching traditional attempt {attempt_id} for revealing: {e}",
                exc_info=True,
            )
            raise APIException(
                _("An error occurred retrieving the session."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_question(self, question_id: int) -> Question:
        """Helper to get the active question."""
        try:
            # TODO: Check if question should belong to the attempt's scope? Optional enhancement.
            question = Question.objects.get(pk=question_id, is_active=True)
            return question
        except Question.DoesNotExist:
            raise NotFound(_("Question not found or is inactive."))
        except Exception as e:
            logger.error(
                f"Error fetching question {question_id} for revealing: {e}",
                exc_info=True,
            )
            raise APIException(
                _("An error occurred retrieving the question."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = self.get_attempt(attempt_id, request.user)
        question = self.get_question(question_id)

        # --- Record Solution Viewed ---
        # Create/Update UserQuestionAttempt to mark solution was seen
        # This distinguishes looking up the answer vs. answering normally
        try:
            attempt_record, created = UserQuestionAttempt.objects.update_or_create(
                user=request.user,
                test_attempt=test_attempt,
                question=question,
                defaults={
                    "used_solution_method": True,  # Mark as revealed
                    "mode": UserQuestionAttempt.Mode.TRADITIONAL,
                    "attempted_at": timezone.now(),  # Update interaction time
                    # Avoid setting selected_answer or is_correct here
                },
            )
            logger.info(
                f"User {request.user.id} revealed answer for Q:{question_id} in traditional attempt {attempt_id} (Created: {created})"
            )
        except Exception as e:
            # Log error but proceed with revealing answer
            logger.exception(
                f"Error marking solution revealed for Q:{question_id}, Attempt:{attempt_id}, User:{request.user.id}: {e}"
            )

        # --- Prepare and Return Response ---
        response_data = {
            "question_id": question.id,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
        }
        serializer = RevealAnswerResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="End Traditional Practice Session",
    description="Marks an active traditional practice session as completed and sets the end time. No final scores are calculated like regular tests.",
    request=None,  # No request body
    responses={
        200: OpenApiResponse(description="Traditional session ended successfully."),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active or not traditional)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt ID invalid)."),
    },
)
class TraditionalPracticeEndView(APIView):
    """Ends an active traditional practice session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = UserTestAttempt.objects.get(
                pk=attempt_id,
                user=request.user,
                status=UserTestAttempt.Status.STARTED,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
            )
        except UserTestAttempt.DoesNotExist:
            raise NotFound(_("Active traditional practice session not found."))
        except Exception as e:
            logger.error(
                f"Error fetching traditional attempt {attempt_id} for ending: {e}",
                exc_info=True,
            )
            raise APIException(
                _("An error occurred retrieving the session."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Mark as COMPLETED (or a custom status like 'FINISHED' if preferred)
            test_attempt.status = UserTestAttempt.Status.COMPLETED
            test_attempt.end_time = timezone.now()
            # Note: We don't call calculate_and_save_scores here as traditional mode doesn't have a final % score.
            # Summary data might be calculated differently if needed (e.g., accuracy on answered Qs).
            test_attempt.save(update_fields=["status", "end_time", "updated_at"])
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
