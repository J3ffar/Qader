from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Exists, Q, OuterRef

from apps.learning.models import Question, UserStarredQuestion
from apps.learning.api.serializers import QuestionListSerializer

from .serializers import (
    LevelAssessmentStartSerializer,
    LevelAssessmentSubmitSerializer,
    LevelAssessmentResponseSerializer,
    LevelAssessmentResultSerializer,
    TraditionalLearningAnswerSerializer,
    TraditionalLearningResponseSerializer,
)
from apps.api.permissions import IsSubscribed  # Import custom permission
from ..models import UserSkillProficiency, UserTestAttempt

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


# Add other study-related views here later
# (Emergency Mode, Conversation, Tests, Stats etc.)
