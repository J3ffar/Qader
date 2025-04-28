from rest_framework import (
    generics,
    status,
    serializers as drf_serializers,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django_filters.rest_framework import DjangoFilterBackend  # Import filter backend
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException, NotFound

from django.db.models import Case, When, IntegerField, Count
from django.http import Http404
import logging
import random

from apps.api.permissions import IsSubscribed
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.study.services import get_filtered_questions
from apps.study.api.serializers import (
    TestStartSerializer,
    TestStartResponseSerializer,
    UserTestAttemptListSerializer,
    UserTestAttemptDetailSerializer,
    TestReviewSerializer,
    TestReviewQuestionSerializer,
)

logger = logging.getLogger(__name__)

# --- General Test Attempt Views (Now part of the unified flow) ---


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="List User Test Attempts",
    description="Retrieves a paginated list of the authenticated user's test attempts (Level Assessment, Practice, Simulation). Supports filtering by status and type.",
    parameters=[
        OpenApiParameter(
            name="status",
            description="Filter by status (started, completed, abandoned)",
            type=str,
        ),
        OpenApiParameter(
            name="attempt_type",
            description="Filter by type (level_assessment, practice, simulation)",
            type=str,
        ),
        OpenApiParameter(
            name="attempt_type__in",
            description="Filter by multiple types (comma-separated: practice,simulation)",
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptListSerializer(many=True),
            description="Paginated list.",
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class UserTestAttemptListView(generics.ListAPIView):
    serializer_class = UserTestAttemptListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    filter_backends = [DjangoFilterBackend]  # Add filter backend
    filterset_fields = {  # Define filterable fields
        "status": ["exact"],
        "attempt_type": ["exact", "in"],
    }

    def get_queryset(self):
        # Add annotation for answered count for the serializer
        return (
            UserTestAttempt.objects.filter(user=self.request.user)
            .annotate(
                answered_question_count_agg=Count("question_attempts")  # Annotate count
            )
            .order_by("-start_time")
        )  # Default ordering

    # Override list to pass annotated count to serializer if needed,
    # or adjust serializer to use the annotation directly if source='answered_question_count_agg'.
    # If using source in serializer, no override needed here. Let's assume serializer uses source.
    # def list(self, request, *args, **kwargs): ...


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Start New Test (Practice/Simulation)",
    # ... (keep existing schema description) ...
    request=TestStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="Test started successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid config, ongoing test, no questions found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class StartTestAttemptView(generics.GenericAPIView):
    serializer_class = TestStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        # ... (keep existing post method) ...
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()
        response_serializer = TestStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Retrieve Test Attempt Details",
    description="Gets details of a specific test attempt (any type), including status, configuration, all included questions, and any answers submitted so far for ongoing tests. Requires ownership.",
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
    serializer_class = UserTestAttemptDetailSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    lookup_url_kwarg = "attempt_id"

    def get_queryset(self):
        # Eager load related user question attempts for the serializer
        return (
            UserTestAttempt.objects.filter(user=self.request.user)
            .prefetch_related(
                "question_attempts",  # Prefetch for 'attempted_questions' field
                "question_attempts__question",  # Prefetch question within the attempt for brief serializer
            )
            .annotate(
                answered_question_count=Count(
                    "question_attempts"
                )  # Annotate count for serializer
            )
        )

    # No need to override get_serializer_context if request is passed automatically


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Review Completed Test",
    description="Retrieves a detailed question-by-question review for a *completed* test attempt (any type), including user/correct answers and explanations.",
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            description="If 'true' or '1', return only incorrect questions.",
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=TestReviewSerializer, description="Detailed review questions."
        ),
        400: OpenApiResponse(description="Bad Request (e.g., Attempt not completed)."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class ReviewTestAttemptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = TestReviewSerializer  # For response structure definition

    def get_object(self):
        """Get the test attempt, ensuring ownership and completed status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Ensure completed status
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user"),
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.COMPLETED,  # Must be completed for review
            )
            return attempt
        except Http404:
            # Check if it exists but has wrong status
            exists_wrong_status = (
                UserTestAttempt.objects.filter(pk=attempt_id, user=user)
                .exclude(status=UserTestAttempt.Status.COMPLETED)
                .exists()
            )
            if exists_wrong_status:
                logger.warning(
                    f"User {user.id} attempted review non-completed test {attempt_id}."
                )
                # Raise 400 Bad Request if not completed
                raise drf_serializers.ValidationError(
                    {"detail": _("Cannot review a test attempt that is not completed.")}
                )
            else:
                # If it doesn't exist at all for the user, raise standard 404
                logger.info(
                    f"Completed test attempt {attempt_id} not found for user {user.id} during review."
                )
                raise NotFound(
                    _("Completed test attempt not found.")
                )  # Use DRF's NotFound
        except Exception as e:
            logger.exception(
                f"Unexpected error fetching completed test attempt {attempt_id} for review by user {user.id}: {e}"
            )
            raise APIException(
                _("An error occurred while retrieving test attempt details."),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, attempt_id, *args, **kwargs):
        try:
            test_attempt = self.get_object()
        except (drf_serializers.ValidationError, NotFound) as e:
            # Handle specific errors raised by get_object
            raise e  # Re-raise to let DRF handle status codes
        except Exception as e:
            # Catch other unexpected errors
            raise APIException(
                _("An error occurred."), code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # --- Fetch questions and answers ---
        # Fetch all questions belonging to the attempt, ordered correctly
        all_questions_queryset = test_attempt.get_questions_queryset().prefetch_related(
            "subsection", "skill"  # Eager load for serializer
        )

        # Fetch all user answers for this attempt
        user_attempts_qs = UserQuestionAttempt.objects.filter(
            test_attempt=test_attempt,
            question_id__in=test_attempt.question_ids,  # Redundant check, but safe
        )  # No select_related needed here as map uses id

        # Filter for incorrect only if requested
        incorrect_only_param = request.query_params.get("incorrect_only", "").lower()
        incorrect_only = incorrect_only_param in ["true", "1"]

        user_attempts_map = {ua.question_id: ua for ua in user_attempts_qs}
        review_questions_queryset = all_questions_queryset

        if incorrect_only:
            incorrect_question_ids = {
                ua.question_id for ua in user_attempts_qs if not ua.is_correct
            }
            if not incorrect_question_ids:  # Handle case where all answers are correct
                review_questions_queryset = all_questions_queryset.none()
            else:
                # Filter the main queryset
                review_questions_queryset = all_questions_queryset.filter(
                    pk__in=incorrect_question_ids
                )
                # Reapply original ordering to the filtered set
                filtered_original_ids = [
                    qid
                    for qid in test_attempt.question_ids
                    if qid in incorrect_question_ids
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
                else:
                    review_questions_queryset = (
                        review_questions_queryset.none()
                    )  # Should not happen if incorrect_question_ids is not empty

        # Pass map to serializer context
        context = {"request": request, "user_attempts_map": user_attempts_map}
        # Prepare data for the main review serializer
        response_data = {
            "attempt_id": test_attempt.id,
            "review_questions": review_questions_queryset,
            # Optionally pass the attempt object if serializer needs it
            # "attempt": test_attempt
        }
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Retake Similar Test",
    description="Starts a *new* test attempt using the same configuration as a previous attempt (any type). Generates a fresh set of questions, excluding those in the original attempt if possible.",
    request=None,
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="New similar test started successfully.",
        ),
        400: OpenApiResponse(
            description="Bad Request (Original attempt config invalid or no questions found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Original attempt ID invalid)."),
    },
)
class RetakeSimilarTestAttemptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = TestStartResponseSerializer  # Output matches start response

    def get_object(self):
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        # Allow retake from any status? Yes.
        return get_object_or_404(UserTestAttempt, pk=attempt_id, user=user)

    def post(self, request, attempt_id, *args, **kwargs):
        # ... (Keep most of the existing post logic) ...
        # Ensure validation errors from services/config checks are propagated correctly
        try:
            original_attempt = self.get_object()
        except Http404:
            return Response(
                {"detail": _("Original test attempt not found or not accessible.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # --- Extract and Validate Original Config ---
        original_config_snapshot = original_attempt.test_configuration
        if not isinstance(original_config_snapshot, dict):
            logger.error(
                f"Invalid config snapshot for original attempt {original_attempt.id} during retake."
            )
            raise drf_serializers.ValidationError(
                _("Original test attempt configuration is missing or invalid.")
            )

        # Handle potential variations in snapshot structure
        config_key = "config" if "config" in original_config_snapshot else None
        if (
            config_key is None and "num_questions" in original_config_snapshot
        ):  # Check if config is flat
            original_config_dict = original_config_snapshot
        elif config_key and isinstance(original_config_snapshot.get(config_key), dict):
            original_config_dict = original_config_snapshot[config_key]
        else:
            logger.error(
                f"Could not find valid config dict in snapshot for attempt {original_attempt.id}."
            )
            raise drf_serializers.ValidationError(
                _("Original test attempt configuration format is unrecognized.")
            )

        original_attempt_type = (
            original_config_snapshot.get("test_type") or original_attempt.attempt_type
        )

        num_questions = original_config_dict.get("num_questions")
        sub_slugs = original_config_dict.get("subsections", [])
        skill_slugs = original_config_dict.get("skills", [])
        starred = original_config_dict.get("starred", False)
        not_mastered = original_config_dict.get("not_mastered", False)

        if (
            not num_questions
            or not isinstance(num_questions, int)
            or num_questions <= 0
        ):
            raise drf_serializers.ValidationError(
                _("Invalid or missing 'num_questions' in original configuration.")
            )

        # --- Select New Questions using Service Function ---
        try:
            # Check for active 'started' test first
            if UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.STARTED
            ).exists():
                raise drf_serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "You already have an ongoing test attempt. Please complete or cancel it first."
                            )
                        ]
                    }
                )

            new_questions_queryset = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=original_attempt.question_ids,
            )
            new_question_ids = list(new_questions_queryset.values_list("id", flat=True))

            if len(new_question_ids) < num_questions:
                logger.warning(
                    f"Could not find enough *new* questions for retake of {original_attempt.id}. Trying again including original questions."
                )
                new_questions_queryset_fallback = get_filtered_questions(
                    user=user,
                    limit=num_questions,
                    subsections=sub_slugs,
                    skills=skill_slugs,
                    starred=starred,
                    not_mastered=not_mastered,
                    exclude_ids=None,
                )
                new_question_ids = list(
                    new_questions_queryset_fallback.values_list("id", flat=True)
                )

            if not new_question_ids:
                raise drf_serializers.ValidationError(
                    _("No suitable questions found to generate a similar test.")
                )

            actual_num_to_select = min(num_questions, len(new_question_ids))
            if actual_num_to_select < num_questions:
                logger.warning(
                    f"Only found {actual_num_to_select} questions for retake of {original_attempt.id} (requested {num_questions})."
                )

            final_question_ids = random.sample(new_question_ids, actual_num_to_select)

        except drf_serializers.ValidationError as e:
            raise e  # Re-raise validation errors
        except Exception as e:
            logger.exception(
                f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
            )
            raise drf_serializers.ValidationError(
                _("Failed to select questions for the new test.")
            )

        # --- Create New Test Attempt ---
        new_config_snapshot = original_config_snapshot.copy()
        # Ensure the config dict exists before modifying
        if config_key:
            new_config_snapshot[config_key]["actual_num_questions_selected"] = len(
                final_question_ids
            )
        else:  # If config was flat
            new_config_snapshot["actual_num_questions_selected"] = len(
                final_question_ids
            )

        new_config_snapshot["retake_of_attempt_id"] = original_attempt.id

        try:
            new_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=original_attempt_type,
                test_configuration=new_config_snapshot,
                question_ids=final_question_ids,
                status=UserTestAttempt.Status.STARTED,
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
        response_serializer = self.get_serializer(
            result_data, context={"request": request}
        )

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
