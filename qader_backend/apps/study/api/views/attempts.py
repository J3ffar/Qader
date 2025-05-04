from rest_framework import generics, status, views, serializers as drf_serializers
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
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Case, When, IntegerField, Count
from django.utils.translation import gettext_lazy as _
from django.http import Http404
import logging
import random

from apps.api.permissions import IsSubscribed
from apps.study.models import UserQuestionAttempt, UserTestAttempt, Question
from apps.study.services import study as study_services
from apps.study.api.serializers import (
    attempts as attempt_serializers,
)  # Use alias for clarity
from apps.users.services import UsageLimiter
from apps.api.exceptions import UsageLimitExceeded

logger = logging.getLogger(__name__)

# --- Unified Test Attempt Views ---


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="List User Test Attempts",
    description=(
        "Retrieves a paginated list of the authenticated user's test attempts (all types). "
        "Supports filtering by `status` (started, completed, abandoned) and `attempt_type` (level_assessment, practice, simulation, traditional). "
        "Supports ordering (e.g., `-start_time`)."
    ),
    parameters=[
        OpenApiParameter(
            name="status", description="Filter by status (e.g., 'completed').", type=str
        ),
        OpenApiParameter(
            name="attempt_type",
            description="Filter by type (e.g., 'practice').",
            type=str,
        ),
        OpenApiParameter(
            name="attempt_type__in",
            description="Filter by multiple types (comma-separated, e.g., 'practice,simulation').",
            type=str,
        ),
        OpenApiParameter(
            name="ordering",
            description="Order results (e.g., '-start_time', 'score_percentage').",
            type=str,
        ),
    ],
    responses={
        200: attempt_serializers.UserTestAttemptListSerializer(many=True),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (e.g., subscription required)."
        ),
    },
)
class UserTestAttemptListView(generics.ListAPIView):
    """Lists all test attempts for the authenticated user, with filtering and ordering."""

    serializer_class = attempt_serializers.UserTestAttemptListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "attempt_type": ["exact", "in"],
    }
    ordering_fields = ["start_time", "end_time", "score_percentage", "status"]
    ordering = ["-start_time"]  # Default ordering

    def get_queryset(self):
        """Filters attempts for the current user and annotates answered count for efficiency."""
        user = self.request.user
        return (
            UserTestAttempt.objects.filter(user=user)
            # Annotate count for serializer/property use
            .annotate(
                answered_question_count_agg=Count("question_attempts")
            ).select_related(
                "user"
            )  # Avoid N+1 if user info needed later
        )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Retrieve Test Attempt Details",
    description="Gets details of a specific test attempt (any type), including status, configuration, included questions, and answers submitted so far. Requires ownership.",
    responses={
        200: attempt_serializers.UserTestAttemptDetailSerializer,
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or no subscription)."
        ),
        404: OpenApiResponse(description="Not Found (Test attempt ID invalid)."),
    },
)
class UserTestAttemptDetailView(generics.RetrieveAPIView):
    """Retrieves details for a specific test attempt owned by the user."""

    serializer_class = attempt_serializers.UserTestAttemptDetailSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    lookup_url_kwarg = "attempt_id"

    def get_queryset(self):
        """Filters for the user's attempts, annotates count, and prefetches related data needed by the serializer."""
        user = self.request.user
        return (
            UserTestAttempt.objects.filter(user=user)
            .select_related("user")  # Needed for permissions/ownership check implicitly
            .prefetch_related(
                # Prefetch answers and their associated questions for 'attempted_questions' field
                "question_attempts",
                "question_attempts__question",
                # Prefetch questions with their details for 'included_questions' field
                # Note: get_questions_queryset() applies its own select_related, but prefetching here
                # might sometimes help Django optimize if the queryset is evaluated multiple times.
                # Test performance impact if needed. Let's rely on get_questions_queryset() for now.
                # 'questions', 'questions__subsection', 'questions__subsection__section', 'questions__skill',
            )
            .annotate(
                answered_question_count_agg=Count("question_attempts")
            )  # Annotation for count
        )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Submit Single Answer",
    description=(
        "Submits an answer for a *single question* within an *ongoing* (`status=started`) test attempt (`{attempt_id}`). "
        "This endpoint is used for all attempt types (Level Assessment, Practice, Simulation, Traditional). "
        "Records the answer, updates proficiency. Immediate feedback (correctness, explanation) is only fully revealed "
        "in the response for Traditional mode or if configured otherwise (service decides)."
    ),
    request=attempt_serializers.UserQuestionAttemptSerializer,
    responses={
        200: attempt_serializers.UserQuestionAttemptResponseSerializer,
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid input, question not part of attempt, attempt not 'started', answer already submitted)."
        ),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Not Found (Attempt ID or Question ID invalid, or attempt not 'started')."
        ),
    },
)
class UserTestAttemptAnswerView(generics.GenericAPIView):
    """Handles submission of a single answer for any active test attempt."""

    serializer_class = attempt_serializers.UserQuestionAttemptSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_object(self) -> UserTestAttempt:
        """Get the ongoing test attempt, ensuring ownership and STARTED status."""
        attempt_id = self.kwargs.get("attempt_id")
        user = self.request.user
        try:
            # Ensure it belongs to the user and is started
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related(
                    "user"
                ),  # Select user for logging/potential use
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,
            )
            return attempt
        except Http404:
            # Check if exists but wrong status/owner for better error message
            try:
                # Check existence and ownership first
                attempt_check = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                # If found, but get_object_or_404 failed, it must be the status mismatch
                logger.warning(
                    f"Attempt {attempt_id} found for user {user.id} but status is not STARTED in {self.__class__.__name__}."
                )
                # Raise NotFound because the *active* attempt wasn't found
                raise NotFound(
                    _("The specified test attempt is not currently active or ongoing.")
                )
            except UserTestAttempt.DoesNotExist:
                # Attempt doesn't exist at all, or doesn't belong to the user
                logger.warning(
                    f"Attempt {attempt_id} not found for user {user.id} in {self.__class__.__name__}."
                )
                # Keep raising NotFound
                raise NotFound(_("Test attempt not found."))
            except Exception as e_inner:  # Catch potential errors in the inner check
                logger.exception(
                    f"Error during existence check in {self.__class__.__name__} get_object for attempt {attempt_id}: {e_inner}"
                )
                raise APIException(
                    _("An error occurred checking the test attempt state.")
                )
        except Exception as e:
            logger.exception(f"Error fetching attempt {attempt_id} in AnswerView: {e}")
            raise APIException(
                _("An error occurred while retrieving the test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles 404/permission implicitly

        serializer = self.get_serializer(data=request.data)
        # Use raise_exception=True for standard DRF error response format
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data[
            "question_id"
        ]  # The validated Question instance

        try:
            # Call the service function to handle the core logic
            result_data = study_services.record_single_answer(
                test_attempt=test_attempt,
                question=question,
                answer_data=serializer.validated_data,
            )
            # Use the standard response serializer
            response_serializer = (
                attempt_serializers.UserQuestionAttemptResponseSerializer(result_data)
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except DRFValidationError as e:
            # Propagate validation errors raised by the service
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Unexpected error recording answer for attempt {attempt_id}, Q {question.id}, User {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("An internal error occurred while recording the answer.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Complete Test Attempt",
    description=(
        "Finalizes an *ongoing* (`status=started`) test attempt (`{attempt_id}`). "
        "Applicable to all types (Level Assessment, Practice, Simulation, Traditional). "
        "For non-Traditional types: calculates scores, updates status, updates profile levels (for Level Assessment), triggers rewards. "
        "For Traditional types: simply marks the session as completed."
    ),
    request=None,  # POST request with no body
    responses={
        200: OpenApiResponse(
            response=attempt_serializers.UserTestAttemptCompletionResponseSerializer,  # Base type, actual response varies
            description=(
                "Test completed. Response contains detailed results for non-Traditional types. "
                "For Traditional type, returns a simple JSON `{'detail': '...'}`."
            ),
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., attempt not 'started', already completed/abandoned)."
        ),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Not Found (Attempt ID invalid or attempt not 'started')."
        ),
    },
)
class UserTestAttemptCompleteView(generics.GenericAPIView):
    """Handles the completion and finalization of ALL types of test attempts."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    # Output serializer determined dynamically based on service response

    def get_object(self) -> UserTestAttempt:
        """Get the ongoing test attempt, ensuring ownership and STARTED status."""
        attempt_id = self.kwargs.get("attempt_id")
        user = self.request.user
        try:
            # Eager load profile for potential level assessment update service call
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user", "user__profile"),
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Must be ongoing
            )
            return attempt
        except Http404:
            # Check if exists but wrong status/owner for better error message
            try:
                attempt_check = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                logger.warning(
                    f"Attempt {attempt_id} found for user {user.id} but status is not STARTED in {self.__class__.__name__}."
                )
                raise NotFound(
                    _("The specified test attempt is not currently active or ongoing.")
                )
            except UserTestAttempt.DoesNotExist:
                logger.warning(
                    f"Attempt {attempt_id} not found for user {user.id} in {self.__class__.__name__}."
                )
                raise NotFound(_("Test attempt not found."))
            except Exception as e_inner:
                logger.exception(
                    f"Error during existence check in {self.__class__.__name__} get_object for attempt {attempt_id}: {e_inner}"
                )
                raise APIException(
                    _("An error occurred checking the test attempt state.")
                )
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
            result_data = study_services.complete_test_attempt(
                test_attempt=test_attempt
            )

            # --- Handle Response based on service output ---
            if "detail" in result_data:
                # Simple response (likely from Traditional completion)
                return Response(result_data, status=status.HTTP_200_OK)
            else:
                # Detailed response for non-Traditional types
                # Determine the correct serializer based on attempt type if needed,
                # or use the generic one if the structure is consistent.
                # The service populates 'updated_profile' for Level Assessment.
                response_serializer = (
                    attempt_serializers.UserTestAttemptCompletionResponseSerializer(
                        result_data, context={"request": request}
                    )
                )
                # Optionally use LevelAssessmentCompletionResponseSerializer for schema clarity
                # if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
                #    response_serializer = attempt_serializers.LevelAssessmentCompletionResponseSerializer(
                #        result_data, context={"request": request}
                #    )

                return Response(response_serializer.data, status=status.HTTP_200_OK)

        except DRFValidationError as e:
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
    request=None,  # POST with no body
    responses={
        200: OpenApiResponse(
            description="Test attempt cancelled successfully.",
            examples=[
                OpenApiExample("Success", value={"detail": "Test attempt cancelled."})
            ],
        ),
        400: OpenApiResponse(description="Bad Request (e.g., attempt not 'started')."),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Not Found (Attempt ID invalid or attempt not 'started')."
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
                UserTestAttempt.objects.select_related("user"),
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Must be ongoing
            )
            return attempt
        except Http404:
            try:
                attempt_check = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                logger.warning(
                    f"Attempt {attempt_id} found for user {user.id} but status is not STARTED in {self.__class__.__name__}."
                )
                raise NotFound(
                    _("The specified test attempt is not currently active or ongoing.")
                )
            except UserTestAttempt.DoesNotExist:
                logger.warning(
                    f"Attempt {attempt_id} not found for user {user.id} in {self.__class__.__name__}."
                )
                raise NotFound(_("Test attempt not found."))
            except Exception as e_inner:
                logger.exception(
                    f"Error during existence check in {self.__class__.__name__} get_object for attempt {attempt_id}: {e_inner}"
                )
                raise APIException(
                    _("An error occurred checking the test attempt state.")
                )
        except Exception as e:
            logger.exception(f"Error fetching attempt {attempt_id} in CancelView: {e}")
            raise APIException(
                _("An error occurred while retrieving the test attempt.")
            )

    def post(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles validation/404

        try:
            # Directly update status and end time - no complex logic needed here
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
    summary="Review Completed Test Attempt",
    description=(
        "Retrieves a detailed question-by-question review for a *completed* (`status=completed`) test attempt (`{attempt_id}`). "
        "Includes user's answer, correct answer, and explanation for each question. Applicable to all attempt types. "
        "Use the `incorrect_only=true` query parameter to fetch only questions the user answered incorrectly (or skipped)."
    ),
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            type=str,
            required=False,
            description="If 'true', '1', or 'yes', return only questions answered incorrectly or skipped.",
        ),
    ],
    responses={
        200: attempt_serializers.UserTestAttemptReviewSerializer,
        400: OpenApiResponse(
            description="Bad Request (e.g., Attempt not 'completed')."
        ),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or not subscribed)."
        ),
        404: OpenApiResponse(
            description="Not Found (Completed test attempt ID invalid)."
        ),
    },
)
class UserTestAttemptReviewView(generics.GenericAPIView):
    """Provides a detailed review of a completed test attempt."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = (
        attempt_serializers.UserTestAttemptReviewSerializer
    )  # For response structure

    def get_object(self) -> UserTestAttempt:
        """Get the test attempt, ensuring ownership and COMPLETED status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Ensure completed status for review
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user").prefetch_related(
                    "question_attempts"
                ),  # Prefetch answers here
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.COMPLETED,  # Must be completed
            )
            return attempt
        except Http404:
            # Check if it exists but has wrong status to give better error
            attempt_exists = UserTestAttempt.objects.filter(
                pk=attempt_id, user=user
            ).first()
            if attempt_exists:
                logger.warning(
                    f"User {user.id} attempted review on non-completed test {attempt_id} (Status: {attempt_exists.status})."
                )
                # Raise 400 Bad Request if not completed
                raise DRFValidationError(
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
        test_attempt = (
            self.get_object()
        )  # Handles validation/404 and prefetching answers

        # --- Fetch all questions for this attempt ---
        all_questions_queryset = test_attempt.get_questions_queryset().prefetch_related(
            "subsection",
            "skill",  # Eager load data needed by review question serializer
        )
        all_question_ids_ordered = list(
            all_questions_queryset.values_list("id", flat=True)
        )  # Get ordered IDs

        # --- Create map of answers (already prefetched) ---
        user_attempts_map = {
            ua.question_id: ua for ua in test_attempt.question_attempts.all()
        }

        # --- Filtering for incorrect only ---
        incorrect_only_param = (
            request.query_params.get("incorrect_only", "").strip().lower()
        )
        incorrect_only = incorrect_only_param in ["true", "1", "yes"]

        review_questions_queryset = all_questions_queryset  # Start with all questions

        if incorrect_only:
            incorrect_or_skipped_question_ids = set()
            for qid in all_question_ids_ordered:
                user_attempt = user_attempts_map.get(qid)
                # Include if attempt exists and is incorrect, OR if attempt doesn't exist (skipped)
                if (user_attempt and user_attempt.is_correct is False) or (
                    user_attempt is None
                ):
                    incorrect_or_skipped_question_ids.add(qid)

            if not incorrect_or_skipped_question_ids:
                review_questions_queryset = (
                    all_questions_queryset.none()
                )  # Return empty if all correct
            else:
                # Filter the main queryset, preserving original order
                review_questions_queryset = all_questions_queryset.filter(
                    pk__in=incorrect_or_skipped_question_ids
                )
                # Ordering is preserved because we filter the already ordered queryset

        # --- Serialize Response ---
        context = (
            self.get_serializer_context()
        )  # Get default context (includes request)
        context["user_attempts_map"] = user_attempts_map
        context["attempt"] = (
            test_attempt  # Pass attempt if serializer needs it (e.g., for summary fields)
        )

        # Prepare data for the main review serializer
        # Pass the filtered+ordered queryset to the 'questions' field
        response_data = {
            "attempt_id": test_attempt.id,
            "questions": review_questions_queryset,
        }
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study - Test Attempts (Core Actions)"],
    summary="Retake Similar Test",
    description=(
        "Starts a *new* test attempt using the same configuration (filters, type, number of questions) as a *previous* attempt (`{attempt_id}`). "
        "Generates a fresh set of questions based on the original criteria, ideally excluding questions from the original attempt. "
        "Checks usage limits before starting. Cannot start if another test is already ongoing. Applicable to all attempt types."
    ),
    request=None,  # POST with no body
    responses={
        201: attempt_serializers.UserTestAttemptStartResponseSerializer,  # Uses the standard start response
        400: OpenApiResponse(
            description="Bad Request (e.g., Ongoing test exists, original config invalid, no suitable questions found)."
        ),
        401: OpenApiResponse(description="Authentication required."),
        403: OpenApiResponse(
            description="Permission Denied (Not owner, not subscribed, or usage limit reached)."
        ),
        404: OpenApiResponse(description="Not Found (Original attempt ID invalid)."),
    },
)
class UserTestAttemptRetakeView(generics.GenericAPIView):
    """Starts a new test attempt based on the configuration of a previous one."""

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = (
        attempt_serializers.UserTestAttemptStartResponseSerializer
    )  # Output matches start response

    def get_object(self) -> UserTestAttempt:
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Allow retake from any status (completed, abandoned etc.)
            original_attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user"), pk=attempt_id, user=user
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

        # Call the service function to handle the complex logic of retake
        try:
            result_data = study_services.retake_test_attempt(
                user=user, original_attempt=original_attempt
            )
        except (
            DRFValidationError,
            UsageLimitExceeded,
        ) as e:  # Now catching DRFValidationError
            status_code = (
                status.HTTP_403_FORBIDDEN
                if isinstance(e, UsageLimitExceeded)
                else status.HTTP_400_BAD_REQUEST
            )
            # DRF ValidationError has .detail, UsageLimitExceeded is just a string
            error_detail = e.detail if isinstance(e, DRFValidationError) else str(e)
            return Response({"detail": error_detail}, status=status_code)
        except Exception as e:
            logger.exception(
                f"Unexpected error during retake of attempt {attempt_id} for user {user.id}: {e}"
            )
            return Response(
                {
                    "detail": _(
                        "An internal error occurred while trying to retake the test."
                    )
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Prepare and Return Response ---
        # The service returns the data needed for the standard start response
        response_serializer = self.get_serializer(
            result_data, context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
