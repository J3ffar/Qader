from rest_framework import generics, status, views, serializers as drf_serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, APIException
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Case, When, IntegerField
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.http import Http404
import logging
import random

from apps.api.permissions import IsSubscribed
from apps.study.models import UserQuestionAttempt, UserTestAttempt, Question
from apps.study.services.study import (
    record_single_answer,
    complete_test_attempt,
    get_filtered_questions,
)  # Import services
from apps.study.api.serializers import (  # Import consolidated serializers
    UserTestAttemptListSerializer,
    UserTestAttemptDetailSerializer,
    UserQuestionAttemptSerializer,
    UserQuestionAttemptResponseSerializer,
    UserTestAttemptCompletionResponseSerializer,
    LevelAssessmentCompletionResponseSerializer,  # For specific Level Assessment completion response
    UserTestAttemptReviewSerializer,
    UserTestAttemptReviewQuestionSerializer,
    UserTestAttemptStartResponseSerializer,  # For Retake response
)
from apps.users.services import UsageLimiter
from apps.api.exceptions import UsageLimitExceeded


logger = logging.getLogger(__name__)

# --- Unified Test Attempt Views ---


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="List Test Attempts",  # More concise
    description=(
        "Retrieves a paginated list of the authenticated user's test attempts (all types: Level Assessment, Practice, Simulation, Traditional). "
        "Supports filtering by `status` (started, completed, abandoned) and `attempt_type` (level_assessment, practice, simulation, traditional). "
        "Use query parameters like `status=completed` or `attempt_type__in=practice,simulation`."
    ),
    parameters=[
        OpenApiParameter(name="status", description="Filter by status.", type=str),
        OpenApiParameter(name="attempt_type", description="Filter by type.", type=str),
        OpenApiParameter(
            name="attempt_type__in",
            description="Filter by multiple types (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="ordering",
            description="Order results (e.g., `-start_time`).",
            type=str,
        ),
        OpenApiParameter(
            name="page", description="Page number for pagination.", type=int
        ),
        OpenApiParameter(
            name="page_size", description="Number of results per page.", type=int
        ),
    ],
    responses={
        200: UserTestAttemptListSerializer(many=True),  # Simplified response definition
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (e.g., user not subscribed)."
        ),
    },
)
class UserTestAttemptListView(generics.ListAPIView):
    """Lists all test attempts for the authenticated user, with filtering."""

    serializer_class = UserTestAttemptListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    filter_backends = [
        DjangoFilterBackend,
    ]  # Add OrderingFilter
    filterset_fields = {
        "status": ["exact"],
        "attempt_type": ["exact", "in"],
    }
    ordering_fields = [
        "start_time",
        "end_time",
        "score_percentage",
        "status",
    ]  # Fields allowed for ordering
    ordering = ["-start_time"]  # Default ordering

    def get_queryset(self):
        """Filters attempts for the current user and annotates answered count."""
        user = self.request.user
        return (
            UserTestAttempt.objects.filter(user=user).annotate(
                answered_question_count_agg=Count(
                    "question_attempts"
                )  # Use specific name for annotation
            )
            # The serializer will use 'answered_question_count' which maps to the model property,
            # which in turn uses this annotation if available.
        )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Retrieve Test Attempt Details",
    description="Gets details of a specific test attempt (any type), including status, configuration, included questions, and answers submitted so far. Requires ownership.",
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptDetailSerializer,
            description="Test attempt details.",
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or no subscription)."
        ),
        404: OpenApiResponse(description="Not Found (Test attempt ID invalid)."),
    },
)
class UserTestAttemptDetailView(generics.RetrieveAPIView):
    """Retrieves details for a specific test attempt owned by the user."""

    serializer_class = UserTestAttemptDetailSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    lookup_url_kwarg = "attempt_id"

    def get_queryset(self):
        """
        Filters for the user's attempts and prefetches related data needed by the serializer.
        Annotates answered question count.
        """
        user = self.request.user
        return (
            UserTestAttempt.objects.filter(user=user)
            .select_related(
                "user"
            )  # Select user if needed by permissions/logic downstream
            .prefetch_related(
                "question_attempts",  # For 'attempted_questions' field list
                "question_attempts__question",  # For data within UserQuestionAttemptBriefSerializer
            )
            .annotate(
                answered_question_count_agg=Count(
                    "question_attempts"
                )  # Annotation for count
            )
        )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Submit Single Answer for Test Attempt",
    description=(
        "Submits an answer for a *single question* within an *ongoing* (`status=started`) test attempt (`{attempt_id}`). "
        "This endpoint is used for Level Assessment, Practice, Simulation, **and** Traditional modes. "
        "Records the answer, updates proficiency (if applicable). "
        "Immediate feedback (correctness, explanation) is only fully revealed in the response for Traditional mode."
        # Clarified mode usage
    ),
    request=UserQuestionAttemptSerializer,
    responses={
        200: UserQuestionAttemptResponseSerializer,
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid input, question not part of attempt, attempt not 'started', answer already submitted for this question in this attempt)."
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Attempt ID or Question ID invalid, or attempt is not 'started'."
        ),
    },
)
class UserTestAttemptAnswerView(generics.GenericAPIView):
    """Handles submission of a single answer for any active test attempt."""

    serializer_class = UserQuestionAttemptSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_object(self) -> UserTestAttempt:
        """Get the ongoing test attempt, ensuring ownership and STARTED status."""
        attempt_id = self.kwargs.get("attempt_id")
        user = self.request.user
        try:
            # Ensure it belongs to the user and is started
            attempt = get_object_or_404(
                UserTestAttempt,
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,
            )
            return attempt
        except Http404:
            logger.warning(
                f"Attempt {attempt_id} not found or not active for user {user.id} in AnswerView."
            )
            raise NotFound(_("Active test attempt not found or not accessible."))
        except Exception as e:
            logger.exception(f"Error fetching attempt {attempt_id} in AnswerView: {e}")
            raise APIException(
                _("An error occurred while retrieving the test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles 404/permission implicitly

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data[
            "question_id"
        ]  # The validated Question instance

        try:
            # Call the service function to handle the core logic
            result_data = record_single_answer(
                test_attempt=test_attempt,
                question=question,
                answer_data=serializer.validated_data,
            )
            response_serializer = UserQuestionAttemptResponseSerializer(result_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except drf_serializers.ValidationError as e:
            # Propagate validation errors raised by the service
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Error recording answer for attempt {attempt_id}, Q {question.id}, User {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while recording the answer.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Complete Test Attempt (All Types)",  # Updated summary
    description=(
        "Finalizes an *ongoing* (`status=started`) test attempt (`{attempt_id}`). "
        "Applicable to Level Assessment, Practice, Simulation, and Traditional types. "  # Updated description
        "For non-Traditional types, calculates final scores, updates status, updates profile levels (for Level Assessment), and triggers rewards."
        "For Traditional types, simply marks the session as completed and sets the end time (returns a simple success message)."
    ),
    request=None,
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptCompletionResponseSerializer,  # Base type for non-traditional
            description=(
                "Test completed. Response structure contains detailed results for non-Traditional types "
                "(see `LevelAssessmentCompletionResponseSerializer` schema for specifics on Level Assessment). "
                "For Traditional type, returns a simple JSON object like `{'detail': 'Traditional practice session ended.'}`."
            ),
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., attempt not 'started', already completed)."
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Attempt ID invalid or attempt not 'started'."
        ),
    },
)
class UserTestAttemptCompleteView(generics.GenericAPIView):
    """Handles the completion and finalization of ALL types of test attempts."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    # Output serializer is determined dynamically in post()

    def get_object(self) -> UserTestAttempt:
        """Get the ongoing test attempt, ensuring ownership and STARTED status."""
        attempt_id = self.kwargs.get("attempt_id")
        user = self.request.user
        try:
            # Eager load profile for potential level assessment update (for non-traditional)
            # No longer need to filter out traditional type here.
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user", "user__profile"),
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Must be ongoing
            )
            # Removed the check preventing traditional attempts here
            return attempt
        except Http404:
            logger.warning(
                f"Attempt {attempt_id} not found or not active for user {user.id} in CompleteView."
            )
            raise NotFound(_("Active test attempt not found or not accessible."))
        except Exception as e:
            logger.exception(
                f"Error fetching attempt {attempt_id} in CompleteView: {e}"
            )
            raise APIException(
                _("An error occurred while retrieving the test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles validation/404

        try:
            # Call the service function to handle completion logic for ALL types
            result_data = complete_test_attempt(test_attempt=test_attempt)

            # --- Handle Response based on service output ---
            if "detail" in result_data:
                # This indicates a simple response, likely from Traditional completion
                return Response(result_data, status=status.HTTP_200_OK)
            else:
                # This is a detailed response for non-Traditional types
                response_serializer = None
                if (
                    test_attempt.attempt_type
                    == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
                    and result_data.get("updated_profile")
                ):
                    response_serializer = LevelAssessmentCompletionResponseSerializer(
                        result_data, context={"request": request}
                    )
                else:
                    response_serializer = UserTestAttemptCompletionResponseSerializer(
                        result_data, context={"request": request}
                    )

                return Response(response_serializer.data, status=status.HTTP_200_OK)

        except drf_serializers.ValidationError as e:
            # Propagate validation errors from the service (e.g., attempt not started)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Error completing test attempt {attempt_id} for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while completing the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Cancel Test Attempt",
    description="Cancels (abandons) an *ongoing* (`status=started`) test attempt (`{attempt_id}`). Sets status to 'Abandoned'. No scores are calculated. Applicable to all attempt types.",
    request=None,
    responses={
        200: OpenApiResponse(description="Test attempt cancelled successfully."),
        400: OpenApiResponse(description="Bad Request (e.g., attempt not 'started')."),
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Attempt ID invalid or attempt not 'started'."
        ),
    },
)
class UserTestAttemptCancelView(generics.GenericAPIView):
    """Handles the cancellation (abandonment) of any active test attempt."""

    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_object(self) -> UserTestAttempt:
        """Get the ongoing test attempt, ensuring ownership and STARTED status."""
        attempt_id = self.kwargs.get("attempt_id")
        user = self.request.user
        try:
            attempt = get_object_or_404(
                UserTestAttempt,
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Must be ongoing
            )
            return attempt
        except Http404:
            logger.warning(
                f"Attempt {attempt_id} not found or not active for user {user.id} in CancelView."
            )
            raise NotFound(_("Active test attempt not found or not accessible."))
        except Exception as e:
            logger.exception(f"Error fetching attempt {attempt_id} in CancelView: {e}")
            raise APIException(
                _("An error occurred while retrieving the test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles validation/404

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
            logger.exception(
                f"Error cancelling test attempt {attempt_id} for user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while cancelling the test.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Review Completed Test",
    description=(
        "Retrieves a detailed question-by-question review for a *completed* (`status=completed`) test attempt (`{attempt_id}`). "
        "Includes user's answer, correct answer, and explanation for each question. "
        "Use the `incorrect_only=true` query parameter to fetch only questions the user answered incorrectly. Applicable to all attempt types."
    ),
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            description="If 'true', return only incorrectly answered questions.",
            type=str,
            required=False,
        ),
    ],
    responses={
        200: UserTestAttemptReviewSerializer,
        400: OpenApiResponse(
            description="Bad Request (e.g., Attempt not 'completed')."
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Completed test attempt with the given ID not found."
        ),
    },
)
class UserTestAttemptReviewView(generics.GenericAPIView):
    """Provides a detailed review of a completed test attempt."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = UserTestAttemptReviewSerializer  # For response structure

    def get_object(self) -> UserTestAttempt:
        """Get the test attempt, ensuring ownership and COMPLETED status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Ensure completed status for review
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user"),  # Select user if needed
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.COMPLETED,  # Must be completed
            )
            return attempt
        except Http404:
            # Check if it exists but has wrong status to give better error
            exists_wrong_status = UserTestAttempt.objects.filter(
                pk=attempt_id, user=user
            ).exists()
            if exists_wrong_status:
                logger.warning(
                    f"User {user.id} attempted review non-completed test {attempt_id}."
                )
                # Raise 400 Bad Request if not completed
                raise drf_serializers.ValidationError(
                    {"detail": _("Cannot review a test attempt that is not completed.")}
                )
            else:
                logger.info(
                    f"Completed test attempt {attempt_id} not found for user {user.id} during review."
                )
                raise NotFound(_("Completed test attempt not found."))
        except Exception as e:
            logger.exception(
                f"Unexpected error fetching completed test attempt {attempt_id} for review by user {user.id}: {e}"
            )
            raise APIException(
                _("An error occurred while retrieving test attempt details.")
            )

    def get(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = self.get_object()
        except (drf_serializers.ValidationError, NotFound) as e:
            raise e  # Re-raise specific validation/not found errors
        except Exception as e:
            raise APIException(
                _("An error occurred retrieving the attempt."),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Fetch questions and answers for review ---
        # Get base queryset of all questions in the attempt, ordered correctly
        all_questions_queryset = test_attempt.get_questions_queryset().prefetch_related(
            "subsection", "skill"  # Eager load data needed by review serializer
        )

        # Get all user answers for this specific attempt
        user_attempts_qs = UserQuestionAttempt.objects.filter(
            test_attempt=test_attempt,
            # question_id__in=test_attempt.question_ids, # Ensure association (already implied by test_attempt FK)
        )

        # Create a map for quick lookup in the serializer
        user_attempts_map = {ua.question_id: ua for ua in user_attempts_qs}

        # --- Filtering for incorrect only ---
        incorrect_only_param = request.query_params.get("incorrect_only", "").lower()
        incorrect_only = incorrect_only_param in ["true", "1", "yes"]

        review_questions_queryset = all_questions_queryset  # Start with all questions

        if incorrect_only:
            # Find IDs of questions answered incorrectly by the user in this attempt
            incorrect_question_ids = {
                ua.question_id
                for ua in user_attempts_map.values()
                if ua.is_correct == False  # Explicitly check for False
            }
            # Also include questions that were part of the attempt but *never answered*? (Policy decision)
            # answered_ids = set(user_attempts_map.keys())
            # unanswered_ids = set(test_attempt.question_ids) - answered_ids
            # target_ids = incorrect_question_ids.union(unanswered_ids)
            target_ids = incorrect_question_ids  # Let's only include explicitly incorrect for now

            if not target_ids:
                # Handle case where all answers were correct (or no answers submitted)
                review_questions_queryset = all_questions_queryset.none()
            else:
                # Filter the main queryset
                review_questions_queryset = all_questions_queryset.filter(
                    pk__in=target_ids
                )
                # Reapply original ordering if needed (important for consistency)
                original_ordered_ids = test_attempt.question_ids
                filtered_original_ids = [
                    qid for qid in original_ordered_ids if qid in target_ids
                ]

                if filtered_original_ids:
                    preserved_order = Case(
                        *[
                            When(pk=pk, then=pos)
                            for pos, pk in enumerate(filtered_original_ids)
                        ],
                        output_field=IntegerField(),
                    )
                    review_questions_queryset = review_questions_queryset.order_by(
                        preserved_order
                    )
                # If filtered_original_ids is empty (shouldn't happen if target_ids not empty), order doesn't matter

        # --- Serialize Response ---
        # Pass the attempt object and the map to the serializer context
        context = (
            self.get_serializer_context()
        )  # Get default context (includes request)
        context["user_attempts_map"] = user_attempts_map
        context["attempt"] = test_attempt  # Pass attempt if serializer needs it

        # Prepare data for the main review serializer
        response_data = {
            "attempt_id": test_attempt.id,
            "questions": review_questions_queryset,  # Pass the filtered+ordered queryset
            # Add other attempt summary data if needed in the response
        }
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Retake Similar Test",
    description=(
        "Starts a *new* test attempt using the same configuration (filters, type, number of questions) as a *previous* attempt (`{attempt_id}`). "
        "Generates a fresh set of questions based on the original criteria, ideally excluding questions from the original attempt (but may include them if necessary). "
        "Checks for usage limits before starting. Cannot start if another test is already ongoing."
        " Applicable to all attempt types."
    ),
    request=None,
    responses={
        201: UserTestAttemptStartResponseSerializer,  # Uses the standard start response
        400: OpenApiResponse(
            description="Bad Request (e.g., Ongoing test exists, original config invalid, no suitable questions found)."
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner, not subscribed, or usage limit reached)."
        ),  # Added usage limit note
        404: OpenApiResponse(
            description="Original attempt with the given ID not found."
        ),
    },
)
class UserTestAttemptRetakeView(generics.GenericAPIView):
    """Starts a new test attempt based on the configuration of a previous one."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = (
        UserTestAttemptStartResponseSerializer  # Output matches start response
    )

    def get_object(self) -> UserTestAttempt:
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Allow retake from any status (completed, abandoned, maybe even started?)
            original_attempt = get_object_or_404(
                UserTestAttempt, pk=attempt_id, user=user
            )
            return original_attempt
        except Http404:
            logger.warning(
                f"Original attempt {attempt_id} not found for user {user.id} during retake."
            )
            raise NotFound(_("Original test attempt not found or not accessible."))
        except Exception as e:
            logger.exception(
                f"Error fetching original attempt {attempt_id} for retake: {e}"
            )
            raise APIException(
                _("An error occurred while retrieving the original test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        original_attempt = self.get_object()  # Handles 404/permissions
        user = request.user

        # --- Check for Existing Active Test ---
        if UserTestAttempt.objects.filter(
            user=user, status=UserTestAttempt.Status.STARTED
        ).exists():
            raise drf_serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Please complete or cancel your ongoing test before starting a new one."
                        )
                    ]
                }
            )

        # --- Extract and Validate Original Config ---
        original_config_snapshot = original_attempt.test_configuration
        if not isinstance(original_config_snapshot, dict):
            logger.error(
                f"Invalid config snapshot for original attempt {original_attempt.id} during retake."
            )
            raise drf_serializers.ValidationError(
                {"detail": _("Original test configuration is missing or invalid.")}
            )

        # Determine original type and config dict (handle different snapshot structures)
        original_attempt_type = (
            original_config_snapshot.get("test_type") or original_attempt.attempt_type
        )
        if not original_attempt_type:
            logger.error(
                f"Cannot determine attempt type for retake from original attempt {original_attempt.id}"
            )
            raise drf_serializers.ValidationError(
                {"detail": _("Could not determine the type of the original test.")}
            )

        if isinstance(original_config_snapshot.get("config"), dict):
            original_config_dict = original_config_snapshot["config"]
        elif (
            "num_questions_requested" in original_config_snapshot
            or "num_questions" in original_config_snapshot
        ):  # Assume flat structure for older assessment/traditional
            original_config_dict = original_config_snapshot
        else:
            logger.error(
                f"Could not find valid config dict in snapshot for attempt {original_attempt.id} during retake."
            )
            raise drf_serializers.ValidationError(
                {"detail": _("Original test configuration format is unrecognized.")}
            )

        # Extract parameters needed for question fetching
        num_questions = original_config_dict.get(
            "num_questions"
        ) or original_config_dict.get(
            "num_questions_requested"
        )  # Handle different key names
        sub_slugs = original_config_dict.get("subsections") or original_config_dict.get(
            "subsections_requested", []
        )
        skill_slugs = original_config_dict.get("skills") or original_config_dict.get(
            "skills_requested", []
        )
        starred = original_config_dict.get("starred") or original_config_dict.get(
            "starred_requested", False
        )
        not_mastered = original_config_dict.get(
            "not_mastered"
        ) or original_config_dict.get("not_mastered_requested", False)

        if (
            not num_questions
            or not isinstance(num_questions, int)
            or num_questions <= 0
        ):
            raise drf_serializers.ValidationError(
                {
                    "detail": _(
                        "Invalid or missing 'num_questions' in original configuration."
                    )
                }
            )
        if not isinstance(sub_slugs, list):
            sub_slugs = []
        if not isinstance(skill_slugs, list):
            skill_slugs = []

        try:
            limiter = UsageLimiter(user)
            # 1. Check if allowed to start this type of attempt
            limiter.check_can_start_test_attempt(original_attempt_type)

            # 2. Check and cap number of questions for the *new* attempt
            max_allowed_questions = limiter.get_max_questions_per_attempt()
            if (
                max_allowed_questions is not None
                and num_questions > max_allowed_questions
            ):
                logger.info(
                    f"User {user.id} retake attempt for {original_attempt.id} capped from {num_questions} to {max_allowed_questions} questions due to plan limits."
                )
                capped_num_questions = (
                    max_allowed_questions  # Update the number to fetch
                )

        except UsageLimitExceeded as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            return Response(
                {"detail": "Could not verify account limits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Select New Questions ---
        try:
            # First, try to exclude questions from the original attempt
            new_questions_queryset = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=original_attempt.question_ids,  # Exclude original questions
            )
            new_question_ids = list(new_questions_queryset.values_list("id", flat=True))
            ids_count = len(new_question_ids)

            # Fallback: If not enough *new* questions found, try again *including* original ones
            if ids_count < num_questions:
                logger.warning(
                    f"Could not find {num_questions} *new* questions for retake of {original_attempt.id} (found {ids_count}). Trying again including original questions."
                )
                new_questions_queryset_fallback = get_filtered_questions(
                    user=user,
                    limit=num_questions,
                    subsections=sub_slugs,
                    skills=skill_slugs,
                    starred=starred,
                    not_mastered=not_mastered,
                    exclude_ids=None,  # No exclusion
                )
                new_question_ids = list(
                    new_questions_queryset_fallback.values_list("id", flat=True)
                )
                ids_count = len(new_question_ids)

            if ids_count == 0:
                # If still no questions found even with fallback, it's an issue
                raise drf_serializers.ValidationError(
                    {
                        "detail": _(
                            "No suitable questions found to generate a similar test based on the original criteria."
                        )
                    }
                )

            # Ensure we don't try to sample more than available
            actual_num_to_select = min(num_questions, ids_count)
            if actual_num_to_select < num_questions:
                logger.warning(
                    f"Only found {actual_num_to_select} total questions for retake of {original_attempt.id} (requested {num_questions}). Using available questions."
                )

            # Randomly sample from the final pool
            final_question_ids = random.sample(new_question_ids, actual_num_to_select)

        except drf_serializers.ValidationError as e:
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.exception(
                f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
            )
            raise drf_serializers.ValidationError(
                {"detail": _("Failed to select questions for the new test.")}
            )

        # --- Create New Test Attempt ---
        # Create a new snapshot, marking it as a retake
        new_config_snapshot = original_config_snapshot.copy()  # Start with original
        new_config_snapshot["retake_of_attempt_id"] = original_attempt.id
        # Update the actual selected count in the appropriate place
        if isinstance(new_config_snapshot.get("config"), dict):
            new_config_snapshot["config"]["actual_num_questions_selected"] = len(
                final_question_ids
            )
        else:
            new_config_snapshot["actual_num_questions_selected"] = len(
                final_question_ids
            )
        # Ensure test_type is correct
        new_config_snapshot["test_type"] = original_attempt_type

        try:
            new_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=original_attempt_type,  # Use determined type
                test_configuration=new_config_snapshot,
                question_ids=final_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
            logger.info(
                f"Started retake (New Attempt: {new_attempt.id}) of original attempt {original_attempt.id} for user {user.id}."
            )
        except Exception as e:
            logger.exception(
                f"Error creating retake UserTestAttempt for user {user.id} (original: {original_attempt.id}): {e}"
            )
            raise drf_serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the new similar test.")]}
            )

        # --- Prepare and Return Response ---
        final_questions_queryset = new_attempt.get_questions_queryset()
        result_data = {
            "attempt_id": new_attempt.id,
            "questions": final_questions_queryset,
        }
        # Use the standard start response serializer
        response_serializer = self.get_serializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
