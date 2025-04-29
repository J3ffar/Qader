from typing import List, Optional
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, APIException
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
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
)
from apps.learning.api.serializers import (
    QuestionListSerializer,
)
from apps.study.api.serializers.traditional import (
    HintResponseSerializer,
    RevealCorrectAnswerResponseSerializer,
    RevealExplanationResponseSerializer,
)  # For Question List view response


logger = logging.getLogger(__name__)

# --- Traditional Learning Views ---


# --- Helper Methods (Shared Logic) ---


def _get_active_traditional_attempt(view, attempt_id: int, user) -> UserTestAttempt:
    """Helper to get the specific active traditional attempt for views."""
    try:
        test_attempt = UserTestAttempt.objects.get(
            pk=attempt_id,
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        )
        return test_attempt
    except UserTestAttempt.DoesNotExist:
        exists_non_trad = UserTestAttempt.objects.filter(
            pk=attempt_id, user=user
        ).exists()
        if exists_non_trad:
            logger.warning(
                f"User {user.id} attempted traditional action on non-active/non-traditional attempt {attempt_id}"
            )
            raise PermissionDenied(
                _("This action is only valid for active traditional practice sessions.")
            )
        else:
            logger.warning(
                f"Active traditional attempt {attempt_id} not found for user {user.id}"
            )
            raise NotFound(_("Active traditional practice session not found."))
    except Exception as e:
        logger.error(
            f"Error fetching traditional attempt {attempt_id} in helper: {e}",
            exc_info=True,
        )
        raise APIException(
            _("An error occurred retrieving the session."),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _get_active_question(view, question_id: int) -> Question:
    """Helper to get the active question."""
    try:
        # TODO: Optional: Check if question is within the scope of the attempt's filters?
        question = Question.objects.get(pk=question_id, is_active=True)
        return question
    except Question.DoesNotExist:
        logger.warning(f"Active question {question_id} not found.")
        raise NotFound(_("Question not found or is inactive."))
    except Exception as e:
        logger.error(
            f"Error fetching question {question_id} in helper: {e}", exc_info=True
        )
        raise APIException(
            _("An error occurred retrieving the question."),
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _record_question_attempt_action(
    user, test_attempt: UserTestAttempt, question: Question, updates: dict
):
    """Helper to record an action in UserQuestionAttempt."""
    try:
        defaults = {
            "mode": UserQuestionAttempt.Mode.TRADITIONAL,
            "attempted_at": timezone.now(),  # Update interaction time
            **updates,  # Apply specific action flags (e.g., used_hint=True)
        }
        # Ensure we don't overwrite existing correct answer/selection unless intended
        if "selected_answer" not in defaults:
            defaults["selected_answer"] = None  # Avoid setting if not provided
        if "is_correct" not in defaults:
            defaults["is_correct"] = None  # Avoid setting if not provided

        attempt_record, created = UserQuestionAttempt.objects.update_or_create(
            user=user,
            test_attempt=test_attempt,
            question=question,
            defaults=defaults,
        )
        action_keys = ", ".join(updates.keys())
        logger.info(
            f"Recorded action ({action_keys}) for Q:{question.id}, Attempt:{test_attempt.id}, User:{user.id} (Created: {created})"
        )
        return attempt_record
    except Exception as e:
        action_keys = ", ".join(updates.keys())
        logger.exception(
            f"Error recording action ({action_keys}) for Q:{question.id}, Attempt:{test_attempt.id}, User:{user.id}: {e}"
        )
        # Decide if this should prevent the action (e.g., returning hint)
        # For now, log the error but allow the primary action (like getting hint) to proceed
        # raise APIException(_("Failed to record action."), status.HTTP_500_INTERNAL_SERVER_ERROR) # Option to fail hard
        return None  # Indicate recording failed


@extend_schema(
    tags=["Study - Traditional Learning"],
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
    tags=["Study - Traditional Learning"],
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
    tags=["Study - Traditional Learning"],
    summary="Use Hint (Traditional Mode)",
    description="Retrieves the hint for a specific question within an active traditional practice session and marks that the hint was used for this question attempt.",
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            response=HintResponseSerializer, description="Hint revealed."
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active/traditional)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt or Question ID invalid)."),
    },
)
class TraditionalUseHintView(APIView):
    """Retrieves a hint and marks it as used for a question in an active traditional session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(self, attempt_id, request.user)
        question = _get_active_question(self, question_id)

        # Record the action
        _record_question_attempt_action(
            user=request.user,
            test_attempt=test_attempt,
            question=question,
            updates={"used_hint": True},
        )

        # Prepare and Return Response
        response_data = {
            "question_id": question.id,
            "hint": question.hint,
        }
        serializer = HintResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- NEW: View for using Elimination ---
@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Mark Elimination Used (Traditional Mode)",
    description="Marks that the user employed an elimination strategy for a specific question within an active traditional practice session.",
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            description="Elimination usage recorded successfully.",
            examples=[
                OpenApiExample(
                    "Success", value={"detail": "Elimination usage recorded."}
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., attempt not active/traditional)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt or Question ID invalid)."),
    },
)
class TraditionalUseEliminationView(APIView):
    """Marks elimination as used for a question in an active traditional session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(self, attempt_id, request.user)
        question = _get_active_question(self, question_id)

        # Record the action
        _record_question_attempt_action(
            user=request.user,
            test_attempt=test_attempt,
            question=question,
            updates={"used_elimination": True},
        )

        # Prepare and Return Simple Success Response
        return Response(
            {"detail": _("Elimination usage recorded.")}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Reveal Correct Answer (Traditional Mode)",
    description="Retrieves the correct answer choice (e.g., 'A', 'B') for a specific question within an active traditional practice session and marks that the answer was revealed.",
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            response=RevealCorrectAnswerResponseSerializer,
            description="Correct answer revealed.",
        ),
        400: OpenApiResponse(description="Bad Request."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class TraditionalRevealAnswerView(APIView):
    """Reveals the correct answer choice and marks it as revealed."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(self, attempt_id, request.user)
        question = _get_active_question(self, question_id)

        # Record the specific action
        _record_question_attempt_action(
            user=request.user,
            test_attempt=test_attempt,
            question=question,
            updates={"revealed_answer": True},  # Use the new model field
        )

        # Prepare and Return Response
        response_data = {
            "question_id": question.id,
            "correct_answer": question.correct_answer,
        }
        serializer = RevealCorrectAnswerResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- NEW: View for Revealing Explanation ---
@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Reveal Explanation (Traditional Mode)",
    description="Retrieves the explanation for a specific question within an active traditional practice session and marks that the explanation was revealed.",
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            response=RevealExplanationResponseSerializer,
            description="Explanation revealed.",
        ),
        400: OpenApiResponse(description="Bad Request."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class TraditionalRevealExplanationView(APIView):
    """Reveals the explanation and marks it as revealed."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(self, attempt_id, request.user)
        question = _get_active_question(self, question_id)

        # Record the specific action
        _record_question_attempt_action(
            user=request.user,
            test_attempt=test_attempt,
            question=question,
            updates={"revealed_explanation": True},  # Use the new model field
        )

        # Prepare and Return Response
        response_data = {
            "question_id": question.id,
            "explanation": question.explanation,
        }
        serializer = RevealExplanationResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
