import random
from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Exists, Q, OuterRef, Case, When, IntegerField

from apps.learning.models import Question, UserStarredQuestion
from apps.learning.api.serializers import QuestionListSerializer

from .serializers import (
    LevelAssessmentStartSerializer,
    LevelAssessmentSubmitSerializer,
    LevelAssessmentResponseSerializer,
    LevelAssessmentResultSerializer,
    TraditionalLearningAnswerSerializer,
    TraditionalLearningResponseSerializer,
    TestStartSerializer,
    TestStartResponseSerializer,
    UserTestAttemptListSerializer,
    UserTestAttemptDetailSerializer,
    TestSubmitSerializer,
    TestSubmitResponseSerializer,
    TestReviewSerializer,
)
from apps.api.permissions import IsSubscribed  # Import custom permission
from ..models import UserQuestionAttempt, UserSkillProficiency, UserTestAttempt

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


@extend_schema(
    tags=["Study & Progress"],
    summary="Fetch Questions for Traditional Learning",
    description=(
        "Retrieves a list of questions for traditional practice based on specified filters. "
        "Allows filtering by subsections, skills, starred status, or skills the user hasn't mastered. "
        "Use `exclude_ids` to avoid fetching questions already seen in the current frontend session."
    ),
    parameters=[
        OpenApiParameter(
            name="limit",
            description="Maximum number of questions to return.",
            required=False,
            type=int,
            default=10,
        ),
        OpenApiParameter(
            name="subsection__slug__in",
            description="Comma-separated list of subsection slugs to include.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="skill__slug__in",
            description="Comma-separated list of skill slugs to include.",
            required=False,
            type=str,
        ),
        OpenApiParameter(
            name="starred",
            description="Filter by questions starred by the user (`true`).",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="not_mastered",
            description="Filter by questions related to skills the user hasn't mastered (`true`). Requires proficiency tracking.",
            required=False,
            type=bool,
        ),
        OpenApiParameter(
            name="exclude_ids",
            description="Comma-separated list of question IDs to exclude.",
            required=False,
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=QuestionListSerializer(many=True),
            description="Successfully retrieved a list of questions matching the criteria.",
        ),
        400: OpenApiResponse(description="Bad Request - Invalid filter parameters."),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
    },
)
class TraditionalLearningQuestionListView(generics.ListAPIView):
    """
    Provides questions for the Traditional Learning mode based on filters.

    GET /api/v1/study/traditional/questions/
    """

    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    # Define a low proficiency threshold (adjust as needed)
    PROFICIENCY_THRESHOLD = 0.7

    def get_queryset(self):
        """
        Filters the queryset based on query parameters provided in the request.
        """
        user = self.request.user
        queryset = Question.objects.filter(is_active=True).select_related(
            "subsection", "skill"  # Optimize related lookups
        )

        # --- Basic Filters ---
        subsection_slugs = self.request.query_params.get("subsection__slug__in")
        skill_slugs = self.request.query_params.get("skill__slug__in")
        exclude_ids_str = self.request.query_params.get("exclude_ids")

        if subsection_slugs:
            slug_list = [
                slug.strip() for slug in subsection_slugs.split(",") if slug.strip()
            ]
            queryset = queryset.filter(subsection__slug__in=slug_list)

        if skill_slugs:
            slug_list = [
                slug.strip() for slug in skill_slugs.split(",") if slug.strip()
            ]
            queryset = queryset.filter(skill__slug__in=slug_list)

        # --- Starred Filter ---
        # Requires UserStarredQuestion model
        is_starred = self.request.query_params.get("starred", "").lower() == "true"
        if is_starred and UserStarredQuestion:
            # Subquery to check existence
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            queryset = queryset.annotate(
                is_starred_annotation=Exists(starred_subquery)
            ).filter(is_starred_annotation=True)
            # Note: The serializer will also calculate is_starred, this filter ensures ONLY starred are returned.
            # Alternatively, fetch all and let serializer handle display, but filtering is usually better.

        # --- Not Mastered Filter ---
        # Requires UserSkillProficiency model
        not_mastered = (
            self.request.query_params.get("not_mastered", "").lower() == "true"
        )
        if not_mastered and UserSkillProficiency:
            try:
                # Find skills where the user's proficiency is below the threshold
                low_proficiency_skills = UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=self.PROFICIENCY_THRESHOLD
                ).values_list("skill_id", flat=True)

                # Also include skills the user hasn't attempted yet (proficiency record doesn't exist)
                # Get IDs of all skills the user HAS attempted
                attempted_skill_ids = UserSkillProficiency.objects.filter(
                    user=user
                ).values_list("skill_id", flat=True)

                # Filter questions:
                # 1. EITHER the skill is in the low_proficiency list
                # 2. OR the question has a skill AND that skill is NOT in the attempted list
                queryset = queryset.filter(
                    Q(skill_id__in=list(low_proficiency_skills))
                    | (
                        Q(skill__isnull=False)
                        & ~Q(skill_id__in=list(attempted_skill_ids))
                    )
                )
            except Exception as e:
                # Log error if proficiency filtering fails, but don't crash the request
                logger.error(
                    f"Error filtering 'not_mastered' questions for user {user.id}: {e}"
                )

        # --- Exclude IDs ---
        if exclude_ids_str:
            try:
                exclude_ids = [
                    int(id_str.strip())
                    for id_str in exclude_ids_str.split(",")
                    if id_str.strip().isdigit()
                ]
                queryset = queryset.exclude(id__in=exclude_ids)
            except ValueError:
                # Ignore invalid IDs, maybe log a warning
                logger.warning(
                    f"Invalid non-integer value found in exclude_ids: {exclude_ids_str}"
                )

        # --- Limit and Order ---
        limit_str = self.request.query_params.get(
            "limit", "10"
        )  # Default to 10 questions
        try:
            limit = int(limit_str)
            if limit <= 0:
                limit = 10  # Fallback to default if invalid
        except ValueError:
            limit = 10  # Fallback to default

        # Randomize the order and take the limit
        # Using order_by('?') can be inefficient on large tables, especially PostgreSQL.
        # A more performant way for random selection:
        count = queryset.count()
        if count == 0:
            return Question.objects.none()

        num_to_fetch = min(limit, count)

        # Method 1: Efficient random sampling (requires knowing IDs)
        # all_ids = list(queryset.values_list('id', flat=True))
        # random_ids = random.sample(all_ids, num_to_fetch)
        # return Question.objects.filter(id__in=random_ids).select_related('subsection', 'skill') # Re-fetch with select_related

        # Method 2: Using order_by('?') - simpler, but potentially slower
        return queryset.order_by("?")[:num_to_fetch]


@extend_schema(
    tags=["Study & Progress"],
    summary="Submit Answer for Traditional Learning",
    description=(
        "Submits the user's answer for a single question attempted in the traditional learning mode. "
        "Validates the question, records the attempt, calculates correctness, awards points, updates the study streak, "
        "and triggers proficiency updates. Returns immediate feedback including the correct answer and explanation."
    ),
    request=TraditionalLearningAnswerSerializer,
    responses={
        200: OpenApiResponse(
            response=TraditionalLearningResponseSerializer,
            description="Answer processed successfully. Returns correctness, explanation, points, and streak info.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Invalid input data (e.g., invalid question ID, missing fields)."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
        404: OpenApiResponse(
            description="Not Found - The specified question ID does not exist or is inactive."
        ),  # Handled by serializer's PrimaryKeyRelatedField
    },
)
class TraditionalLearningAnswerView(generics.GenericAPIView):
    """
    Handles the submission of an answer in Traditional Learning mode.

    POST /api/v1/study/traditional/answer/
    """

    serializer_class = TraditionalLearningAnswerSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # .save() method in the serializer handles all the logic
        result_data = serializer.save()

        # Use the response serializer for consistent output structure
        response_serializer = TraditionalLearningResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress"],
    summary="List User Test Attempts",
    description="Retrieves a paginated list of the authenticated user's previous test attempts (practice, simulations, custom, level assessments).",
    parameters=[
        OpenApiParameter(name="page", description="Page number", type=int),
        OpenApiParameter(
            name="page_size", description="Number of results per page", type=int
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptListSerializer(many=True),
            description="Paginated list of test attempts.",
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
    },
)
class UserTestAttemptListView(generics.ListAPIView):
    """
    Lists the current user's test attempts.

    GET /api/v1/study/tests/
    """

    serializer_class = UserTestAttemptListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def get_queryset(self):
        """Return attempts belonging to the current authenticated user."""
        user = self.request.user
        # Order by start time, newest first (default ordering in model Meta)
        return UserTestAttempt.objects.filter(user=user)


@extend_schema(
    tags=["Study & Progress"],
    summary="Start New Test",
    description="Initiates a new test (practice, simulation, custom) based on the provided configuration. Selects questions according to the criteria.",
    request=TestStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="Test started successfully. Returns new attempt ID and questions.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation Error (e.g., invalid config, no questions found)."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required or user lacks an active subscription."
        ),
    },
)
class StartTestAttemptView(generics.GenericAPIView):
    """
    Starts a new practice, simulation, or custom test.

    POST /api/v1/study/tests/start/
    """

    serializer_class = TestStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Calls create method in serializer

        response_serializer = TestStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress"],
    summary="Retrieve Test Attempt Details",
    description="Gets the details of a specific test attempt, including its status and associated questions (without answers if ongoing). Requires ownership.",
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptDetailSerializer,
            description="Details of the test attempt.",
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required, user lacks subscription, or user is not the owner."
        ),
        404: OpenApiResponse(
            description="Not Found - Test attempt with the given ID not found."
        ),
    },
)
class UserTestAttemptDetailView(generics.RetrieveAPIView):
    """
    Retrieves details for a specific test attempt owned by the user.

    GET /api/v1/study/tests/{attempt_id}/
    """

    serializer_class = UserTestAttemptDetailSerializer
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Ownership checked in get_queryset
    lookup_field = "pk"  # CORRECT
    lookup_url_kwarg = "attempt_id"

    def get_queryset(self):
        """Ensure only the owner can retrieve the attempt."""
        user = self.request.user
        return UserTestAttempt.objects.filter(user=user)


@extend_schema(
    tags=["Study & Progress"],
    summary="Submit Test Answers",
    description="Submits answers for an ongoing test attempt. Calculates score, updates status, awards points, updates proficiency.",
    request=TestSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=TestSubmitResponseSerializer,
            description="Test submitted successfully. Returns final results and analysis.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation Error (e.g., already submitted, wrong answers, invalid data)."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required, user lacks subscription, or user is not the owner."
        ),
        404: OpenApiResponse(
            description="Not Found - Test attempt with the given ID not found."
        ),
    },
)
class SubmitTestAttemptView(generics.GenericAPIView):
    """
    Handles the submission of answers for a specific test attempt.

    POST /api/v1/study/tests/{attempt_id}/submit/
    """

    serializer_class = TestSubmitSerializer
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Ownership checked in serializer validation

    def post(self, request, attempt_id, *args, **kwargs):
        # Pass request and view context (for attempt_id) to serializer
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Serializer handles processing

        response_serializer = TestSubmitResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress"],
    summary="Review Completed Test",
    description="Retrieves a detailed question-by-question review for a *completed* test attempt, including user answers, correct answers, and explanations.",
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            description="If true, return only incorrectly answered questions.",
            type=bool,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=TestReviewSerializer, description="Detailed review questions."
        ),
        400: OpenApiResponse(description="Bad Request - Attempt is not completed."),
        403: OpenApiResponse(
            description="Forbidden - Authentication required, user lacks subscription, or user is not the owner."
        ),
        404: OpenApiResponse(
            description="Not Found - Test attempt with the given ID not found."
        ),
    },
)
class ReviewTestAttemptView(generics.GenericAPIView):
    """
    Provides a detailed review of a completed test attempt.

    GET /api/v1/study/tests/{attempt_id}/review/
    """

    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Ownership checked in get_object
    serializer_class = TestReviewSerializer  # For response serialization

    def get_object(self):
        """Get the test attempt, ensuring ownership and completion status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        attempt = get_object_or_404(UserTestAttempt, pk=attempt_id, user=user)

        if attempt.status != UserTestAttempt.Status.COMPLETED:
            # Use DRF's validation error mechanism for a 400 response
            raise serializers.ValidationError(
                _("Cannot review an ongoing or abandoned test attempt.")
            )
        return attempt

    def get(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles 404, ownership, and status check

        # Fetch questions associated with the attempt
        questions_queryset = test_attempt.get_questions_queryset().select_related(
            "subsection", "skill"
        )

        # Fetch user's answers for these questions within this attempt
        user_attempts_queryset = UserQuestionAttempt.objects.filter(
            test_attempt=test_attempt,
            question_id__in=test_attempt.question_ids,  # Ensure we only get attempts for this test
        )

        # Filter by incorrect_only if requested
        incorrect_only = (
            request.query_params.get("incorrect_only", "").lower() == "true"
        )
        if incorrect_only:
            incorrect_question_ids = user_attempts_queryset.filter(
                is_correct=False
            ).values_list("question_id", flat=True)
            questions_queryset = questions_queryset.filter(
                id__in=list(incorrect_question_ids)
            )
            # Re-apply ordering if filtering changes it significantly
            preserved_order = Case(
                *[
                    When(pk=pk, then=pos)
                    for pos, pk in enumerate(test_attempt.question_ids)
                    if pk in incorrect_question_ids
                ],
                output_field=IntegerField(),
            )
            questions_queryset = questions_queryset.order_by(preserved_order)

        # Create a map for faster lookup in the serializer
        user_attempts_map = {
            attempt.question_id: attempt for attempt in user_attempts_queryset
        }

        # Prepare context for the review question serializer
        context = {
            "request": request,
            "user_attempts_map": user_attempts_map,
        }

        # Serialize the data for the response
        response_data = {
            "attempt_id": test_attempt.id,
            "review_questions": questions_queryset,  # Pass the queryset
        }
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress"],
    summary="Retake Similar Test",
    description="Starts a *new* test attempt using the same configuration as a previous attempt. Generates a fresh set of questions.",
    request=None,  # No request body needed
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="New similar test started successfully. Returns new attempt ID and questions.",
        ),
        400: OpenApiResponse(
            description="Bad Request - Original attempt has no valid configuration."
        ),
        403: OpenApiResponse(
            description="Forbidden - Authentication required, user lacks subscription, or user is not the owner of the original attempt."
        ),
        404: OpenApiResponse(
            description="Not Found - Original test attempt with the given ID not found."
        ),
    },
)
class RetakeSimilarTestAttemptView(generics.GenericAPIView):
    """
    Starts a new test attempt based on the configuration of a previous one.

    POST /api/v1/study/tests/{attempt_id}/retake-similar/
    """

    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Ownership checked in get_object
    serializer_class = TestStartResponseSerializer  # We reuse the response serializer

    def get_object(self):
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        # No status check needed here, can retake completed or even abandoned? (Decide policy)
        return get_object_or_404(UserTestAttempt, pk=attempt_id, user=user)

    def post(self, request, attempt_id, *args, **kwargs):
        original_attempt = self.get_object()

        # --- Extract and Validate Original Config ---
        original_config_snapshot = original_attempt.test_configuration
        if (
            not isinstance(original_config_snapshot, dict)
            or "config" not in original_config_snapshot
        ):
            raise serializers.ValidationError(
                _("Original test attempt configuration is missing or invalid.")
            )

        original_config_dict = original_config_snapshot["config"]
        original_attempt_type = (
            original_config_snapshot.get("test_type") or original_attempt.attempt_type
        )  # Get type

        # --- Re-validate the config data (use TestConfigSerializer logic if possible) ---
        # Need to convert slugs back to objects for validation if using the serializer directly
        # Simpler approach: manually extract and check required fields
        num_questions = original_config_dict.get("num_questions")
        sub_slugs = original_config_dict.get("subsections", [])
        skill_slugs = original_config_dict.get("skills", [])
        starred = original_config_dict.get("starred", False)
        not_mastered = original_config_dict.get("not_mastered", False)

        if not num_questions:
            raise serializers.ValidationError(
                _("Original configuration missing 'num_questions'.")
            )
        if not sub_slugs and not skill_slugs and not starred:
            raise serializers.ValidationError(
                _(
                    "Original configuration must specify subsections, skills, or starred filter."
                )
            )

        # --- Select New Questions using the same logic as TestStartSerializer ---
        # Define a low proficiency threshold (adjust as needed)
        PROFICIENCY_THRESHOLD = 0.7
        user = request.user

        question_filters = Q(is_active=True)
        if sub_slugs:
            question_filters &= Q(subsection__slug__in=sub_slugs)
        if skill_slugs:
            question_filters &= Q(skill__slug__in=skill_slugs)
        if starred:
            starred_ids = UserStarredQuestion.objects.filter(user=user).values_list(
                "question_id", flat=True
            )
            question_filters &= Q(id__in=list(starred_ids))
        if not_mastered and UserSkillProficiency:
            try:
                low_prof = UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=PROFICIENCY_THRESHOLD
                ).values_list("skill_id", flat=True)
                attempted = UserSkillProficiency.objects.filter(user=user).values_list(
                    "skill_id", flat=True
                )
                not_mastered_filter = Q(skill_id__in=list(low_prof)) | (
                    Q(skill__isnull=False) & ~Q(skill_id__in=list(attempted))
                )
                question_filters &= not_mastered_filter
            except Exception as e:
                logger.error(
                    f"Error applying 'not_mastered' filter during retake for user {user.id}: {e}"
                )

        question_pool_query = Question.objects.filter(question_filters).exclude(
            id__in=original_attempt.question_ids
        )  # Exclude original questions
        question_pool_ids = list(question_pool_query.values_list("id", flat=True))
        pool_count = len(question_pool_ids)

        if pool_count == 0:
            # Maybe try without excluding original questions as a fallback?
            question_pool_query_fallback = Question.objects.filter(question_filters)
            question_pool_ids = list(
                question_pool_query_fallback.values_list("id", flat=True)
            )
            pool_count = len(question_pool_ids)
            if pool_count == 0:
                raise serializers.ValidationError(
                    _("No suitable questions found to generate a similar test.")
                )

        actual_num_questions = min(num_questions, pool_count)
        if actual_num_questions == 0:
            raise serializers.ValidationError(
                _("Could not select any questions for the new test.")
            )

        new_question_ids = random.sample(question_pool_ids, actual_num_questions)

        # --- Create New Test Attempt ---
        # Update config snapshot for the new attempt
        new_config_snapshot = (
            original_config_snapshot.copy()
        )  # Shallow copy is fine for dict
        new_config_snapshot["config"][
            "actual_num_questions_selected"
        ] = actual_num_questions
        # Add reference to original attempt? Optional.
        # new_config_snapshot['retake_of_attempt_id'] = original_attempt.id

        try:
            new_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=original_attempt_type,  # Use the original attempt type
                test_configuration=new_config_snapshot,  # Use the copied/updated config
                question_ids=new_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating retake UserTestAttempt for user {user.id} (original: {original_attempt.id}): {e}"
            )
            raise serializers.ValidationError(
                _("Failed to start the new similar test.")
            )

        # --- Prepare and Return Response ---
        questions_queryset = new_attempt.get_questions_queryset()
        result_data = {
            "new_attempt_id": new_attempt.id,
            "message": _(
                "New test started based on the configuration of attempt #{}."
            ).format(original_attempt.id),
            "questions": questions_queryset,
        }

        # Need to serialize slightly differently than TestStartResponseSerializer expects input
        response_data = {
            "attempt_id": result_data["new_attempt_id"],
            "questions": result_data["questions"],
        }

        # Manually add the message to the serialized data if not part of the serializer
        final_response_data = self.get_serializer(
            response_data, context={"request": request}
        ).data
        final_response_data["message"] = result_data["message"]
        final_response_data["new_attempt_id"] = result_data[
            "new_attempt_id"
        ]  # Ensure ID is present

        return Response(final_response_data, status=status.HTTP_201_CREATED)


# Add other study-related views here later
# (Emergency Mode, Conversation, Tests, Stats etc.)
