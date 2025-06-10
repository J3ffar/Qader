from typing import List, Optional, Dict, Any
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import (
    PermissionDenied,
    NotFound,
    APIException,
    ValidationError as DRFValidationError,
)
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

from apps.api.permissions import IsSubscribed
from apps.study.models import UserTestAttempt, Question, UserQuestionAttempt
from apps.study.services import study as study_services
from apps.study.api.serializers import traditional as traditional_serializers  # Alias
from apps.study.api.serializers import (
    attempts as attempt_serializers,
)  # Unified answer response
from apps.learning.api.serializers import (
    UnifiedQuestionSerializer,
)  # For question list response
from apps.api.exceptions import UsageLimitExceeded

logger = logging.getLogger(__name__)

# --- Traditional Learning Views ---

# --- Helper Methods (Moved to Service or remain private if simple enough) ---
# These helpers are now largely replaced by service calls or simple get_object_or_404


def _get_active_traditional_attempt(user, attempt_id: int) -> UserTestAttempt:
    """Helper to get the specific active traditional attempt for views."""
    try:
        # Ensure type is Traditional and status is Started
        test_attempt = get_object_or_404(
            UserTestAttempt,
            pk=attempt_id,
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        )
        return test_attempt
    except Http404:
        # Check if exists but wrong type/status
        attempt_exists = UserTestAttempt.objects.filter(
            pk=attempt_id, user=user
        ).first()
        if attempt_exists:
            logger.warning(
                f"User {user.id} attempted traditional action on non-active/non-traditional attempt {attempt_id} (Type: {attempt_exists.attempt_type}, Status: {attempt_exists.status})"
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
        logger.exception(
            f"Error fetching traditional attempt {attempt_id} in helper: {e}"
        )
        raise APIException(_("An error occurred retrieving the session."))


def _get_active_question(question_id: int) -> Question:
    """Helper to get the active question by ID."""
    try:
        # Add select_related if needed by the action (e.g., reveal explanation needs explanation field)
        question = get_object_or_404(Question, pk=question_id, is_active=True)
        return question
    except Http404:
        logger.warning(f"Active question {question_id} not found.")
        raise NotFound(_("Question not found or is inactive."))
    except Exception as e:
        logger.exception(f"Error fetching question {question_id} in helper: {e}")
        raise APIException(_("An error occurred retrieving the question."))


# --- Start View ---
@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Start Traditional Practice Session",
    description="Starts a new traditional practice session, creating a trackable UserTestAttempt record. Can optionally return an initial set of questions based on filters.",
    request=traditional_serializers.TraditionalPracticeStartSerializer,
    responses={
        201: traditional_serializers.TraditionalPracticeStartResponseSerializer,  # Specific start response
        400: OpenApiResponse(
            description="Validation Error (e.g., already active session)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Auth, Subscription, or Usage Limit)."
        ),
    },
)
class TraditionalPracticeStartView(generics.GenericAPIView):
    """Starts a new Traditional Practice session (UserTestAttempt)."""

    serializer_class = traditional_serializers.TraditionalPracticeStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = request.user
            validated_data = serializer.validated_data

            # Call the service function
            result_data = study_services.start_traditional_practice(
                user=user,
                subsections=validated_data.get("subsections", []),
                skills=validated_data.get("skills", []),
                num_questions_initial=validated_data["num_questions"],
                starred=validated_data.get("starred", False),
                not_mastered=validated_data.get("not_mastered", False),
            )

        except (DRFValidationError, UsageLimitExceeded) as e:
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(e, UsageLimitExceeded)
                else status.HTTP_400_BAD_REQUEST
            )
            error_detail = e.detail if hasattr(e, "detail") else str(e)
            return Response({"detail": error_detail}, status=status_code)
        except Exception as e:
            logger.exception(
                f"Unexpected error during TraditionalPracticeStartView post for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while starting the session.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Use the specific response serializer for traditional start
        response_serializer = (
            traditional_serializers.TraditionalPracticeStartResponseSerializer(
                result_data, context=self.get_serializer_context()
            )
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# Note: Answering questions is handled by the unified UserTestAttemptAnswerView


# --- Ad-hoc Question Fetching View ---
@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Fetch Questions for Traditional Practice",
    description=(
        "Retrieves a list of questions for traditional practice based on filters, independent of a specific ongoing attempt. "
        "Supports filtering by subsections, skills, starred, not_mastered, and excluding specific question IDs. Uses limit parameter for count."
    ),
    parameters=[
        OpenApiParameter(
            name="limit",
            description="Max number of questions.",
            type=int,
            default=10,
            required=False,
        ),
        OpenApiParameter(
            name="subsection__slug__in",
            description="Subsection slugs (comma-separated).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="skill__slug__in",
            description="Skill slugs (comma-separated).",
            type=str,
            required=False,
        ),
        OpenApiParameter(
            name="starred",
            description="Filter by starred (`true`/`1`).",
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
            description="Question IDs to exclude (comma-separated ints).",
            type=str,
            required=False,
        ),
    ],
    responses={
        200: UnifiedQuestionSerializer(many=True),
        400: OpenApiResponse(description="Invalid filter parameters."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(description="Permission Denied (Subscription required)."),
    },
)
class TraditionalQuestionListView(generics.ListAPIView):
    """Provides a list of questions for traditional learning based on filters."""

    serializer_class = UnifiedQuestionSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = None  # Use 'limit' parameter instead of standard pagination

    # Helper methods for parsing query params
    def _parse_bool_param(self, param_name: str) -> bool:
        val = self.request.query_params.get(param_name, "").strip().lower()
        return val in ["true", "1", "yes", "on"]

    def _parse_list_param(self, param_name: str) -> Optional[List[str]]:
        val_str = self.request.query_params.get(param_name)
        return [s.strip() for s in val_str.split(",") if s.strip()] if val_str else None

    def _parse_int_list_param(self, param_name: str) -> Optional[List[int]]:
        val_str = self.request.query_params.get(param_name)
        if not val_str:
            return None

        ids = []
        # Split and strip parts first
        parts = [s.strip() for s in val_str.split(",") if s.strip()]
        if not parts:  # Handles cases like val_str = "," or " , , "
            return None

        for part in parts:
            if not part.isdigit():  # Check if the part consists only of digits
                # Raise a validation error specific to this parameter
                raise DRFValidationError(
                    {param_name: [f"Invalid value '{part}'. All IDs must be integers."]}
                )
            try:
                ids.append(int(part))
            except (
                ValueError
            ):  # Should ideally be caught by isdigit, but as a safeguard
                raise DRFValidationError(
                    {param_name: [f"Could not convert '{part}' to an integer."]}
                )
        return ids

    def get_queryset(self):
        user = self.request.user
        limit_str = self.request.query_params.get("limit", "10")
        try:
            limit = int(limit_str)
            limit = max(1, min(limit, 100))  # Ensure reasonable bounds (e.g., 1-100)
        except ValueError:
            limit = 10  # Default if invalid

        try:
            subsections = self._parse_list_param("subsection__slug__in")
            skills = self._parse_list_param("skill__slug__in")
            starred = self._parse_bool_param("starred")
            not_mastered = self._parse_bool_param("not_mastered")
            exclude_ids = self._parse_int_list_param("exclude_ids")

            # Use the central service function to get questions
            return study_services.get_filtered_questions(
                user=user,
                limit=limit,
                subsections=subsections,
                skills=skills,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=exclude_ids,
            )
        except (
            DRFValidationError
        ) as e:  # Catch DRF's DRFValidationError (from _parse_ methods or service)
            # Let DRF's main exception handler convert this to a 400 response
            raise e
        except APIException as e:  # Catch other specific APIExceptions
            logger.error(
                f"APIException fetching traditional questions for user {user.id}: {e}",
                exc_info=True,
            )
            raise e
        except Exception as e:  # Catch any other unexpected errors
            logger.exception(
                f"Unexpected error fetching traditional questions for user {user.id}: {e}"
            )
            # Convert to a generic APIException for a 500 response
            raise APIException(_("An error occurred while fetching questions."))


# --- Traditional Action Views (Hints/Reveals) ---


@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Use Hint (Traditional Mode)",
    description="Retrieves the hint for a specific question within an active traditional practice session and marks that the hint was used.",
    request=None,  # POST request with no body
    responses={
        200: traditional_serializers.HintResponseSerializer,
        400: OpenApiResponse(description="Bad Request."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Attempt or Question ID invalid)."),
    },
)
class TraditionalUseHintView(APIView):
    """Retrieves a hint and marks it as used for a question in an active traditional session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(request.user, attempt_id)
        question = _get_active_question(question_id)

        try:
            # Call service to handle recording the action and potentially fetching hint
            hint_text = study_services.record_traditional_action_and_get_data(
                user=request.user,
                test_attempt=test_attempt,
                question=question,
                action_type="hint",
            )
        except Exception as e:
            logger.exception(
                f"Error recording hint usage for Q:{question_id}, Attempt:{attempt_id}, User:{request.user.id}: {e}"
            )
            raise APIException(
                _("Failed to record hint usage or retrieve hint."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Prepare and Return Response
        response_data = {"question_id": question.id, "hint": hint_text}
        serializer = traditional_serializers.HintResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Mark Elimination Used (Traditional Mode)",
    description="Marks that the user employed an elimination strategy for a specific question within an active traditional practice session.",
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            description="Elimination usage recorded.",
            examples=[
                OpenApiExample(
                    "Success", value={"detail": "Elimination usage recorded."}
                )
            ],
        ),
        400: OpenApiResponse(description="Bad Request."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class TraditionalUseEliminationView(APIView):
    """Marks elimination as used for a question in an active traditional session."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(request.user, attempt_id)
        question = _get_active_question(question_id)

        try:
            # Call service to record the action
            study_services.record_traditional_action_and_get_data(
                user=request.user,
                test_attempt=test_attempt,
                question=question,
                action_type="eliminate",
            )
        except Exception as e:
            logger.exception(
                f"Error recording elimination usage for Q:{question_id}, Attempt:{attempt_id}, User:{request.user.id}: {e}"
            )
            raise APIException(
                _("Failed to record elimination usage."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": _("Elimination usage recorded.")}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Reveal Correct Answer (Traditional Mode)",
    description="Retrieves the correct answer choice for a specific question within an active traditional practice session and marks that the answer was revealed.",
    request=None,  # POST request with no body
    responses={
        200: traditional_serializers.RevealCorrectAnswerResponseSerializer,
        400: OpenApiResponse(description="Bad Request."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class TraditionalRevealAnswerView(APIView):
    """Reveals the correct answer choice and marks it as revealed."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(request.user, attempt_id)
        question = _get_active_question(question_id)

        try:
            # Call service to record action and get data
            correct_answer = study_services.record_traditional_action_and_get_data(
                user=request.user,
                test_attempt=test_attempt,
                question=question,
                action_type="reveal_answer",
            )
        except Exception as e:
            logger.exception(
                f"Error revealing answer for Q:{question_id}, Attempt:{attempt_id}, User:{request.user.id}: {e}"
            )
            raise APIException(
                _("Failed to record action or retrieve answer."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {"question_id": question.id, "correct_answer": correct_answer}
        serializer = traditional_serializers.RevealCorrectAnswerResponseSerializer(
            response_data
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study - Traditional Learning"],
    summary="Reveal Explanation (Traditional Mode)",
    description="Retrieves the explanation for a specific question within an active traditional practice session and marks that the explanation was revealed.",
    request=None,  # POST request with no body
    responses={
        200: traditional_serializers.RevealExplanationResponseSerializer,
        400: OpenApiResponse(description="Bad Request."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class TraditionalRevealExplanationView(APIView):
    """Reveals the explanation and marks it as revealed."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, question_id, *args, **kwargs):
        test_attempt = _get_active_traditional_attempt(request.user, attempt_id)
        question = _get_active_question(
            question_id
        )  # Ensure explanation is loaded if needed

        try:
            # Call service to record action and get data
            explanation = study_services.record_traditional_action_and_get_data(
                user=request.user,
                test_attempt=test_attempt,
                question=question,
                action_type="reveal_explanation",
            )
        except Exception as e:
            logger.exception(
                f"Error revealing explanation for Q:{question_id}, Attempt:{attempt_id}, User:{request.user.id}: {e}"
            )
            raise APIException(
                _("Failed to record action or retrieve explanation."),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response_data = {"question_id": question.id, "explanation": explanation}
        serializer = traditional_serializers.RevealExplanationResponseSerializer(
            response_data
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
