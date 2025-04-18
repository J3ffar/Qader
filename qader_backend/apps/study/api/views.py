from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.db.models import Exists, Q, OuterRef, Case, When, IntegerField

from apps.learning.models import Question  # Keep direct import if needed
from apps.learning.api.serializers import QuestionListSerializer

from ..models import UserQuestionAttempt, UserSkillProficiency, UserTestAttempt
from apps.api.permissions import IsSubscribed
from ..utils import get_filtered_questions  # Import the utility function

# Import all necessary serializers
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
    TestReviewQuestionSerializer,
)

import logging
import random  # Keep for Retake view's sampling

logger = logging.getLogger(__name__)

# --- Level Assessment Views ---


@extend_schema(
    tags=["Study & Progress - Level Assessment"],  # Grouped tag
    summary="Start Level Assessment Test",
    description=(
        "Initiates a level assessment test for the authenticated, subscribed user. "
        "Checks if level is already determined. Requires first-time user or explicit retake. "
        "Selects random, active questions based on chosen sections and number."
    ),
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=LevelAssessmentResponseSerializer,
            description="Assessment started.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., level determined, ongoing assessment, no questions)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication/Subscription)."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    serializer_class = LevelAssessmentStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id': id, 'questions': queryset}
        response_serializer = LevelAssessmentResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress - Level Assessment"],
    summary="Submit Level Assessment Answers",
    description=(
        "Submits answers for a specific, ongoing level assessment. Calculates scores, "
        "updates user profile levels, and marks the assessment complete."
    ),
    request=LevelAssessmentSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=LevelAssessmentResultSerializer,
            description="Submission successful.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., attempt not active, wrong answers)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Not Found (Attempt ID invalid - handled by serializer)."
        ),
    },
)
class LevelAssessmentSubmitView(generics.GenericAPIView):
    serializer_class = LevelAssessmentSubmitSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, *args, **kwargs):
        # Pass view context (which includes URL kwargs like attempt_id) to serializer for validation
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id', 'results', 'updated_profile'}
        response_serializer = LevelAssessmentResultSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# --- Traditional Learning Views ---


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],  # Grouped tag
    summary="Fetch Questions for Traditional Learning",
    description=(
        "Retrieves a list of questions for traditional practice based on filters. "
        "Uses efficient random sampling. Supports filtering by subsections, skills, starred, not_mastered, and excluding IDs."
    ),
    parameters=[
        OpenApiParameter(
            name="limit", description="Max questions.", type=int, default=10
        ),
        OpenApiParameter(
            name="subsection__slug__in",
            description="Subsection slugs (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="skill__slug__in",
            description="Skill slugs (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="starred", description="Filter by starred (`true`).", type=bool
        ),
        OpenApiParameter(
            name="not_mastered",
            description="Filter by not mastered skills (`true`).",
            type=bool,
        ),
        OpenApiParameter(
            name="exclude_ids",
            description="Question IDs to exclude (comma-separated).",
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=QuestionListSerializer(many=True), description="List of questions."
        ),
        400: OpenApiResponse(description="Invalid filter parameters."),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class TraditionalLearningQuestionListView(generics.ListAPIView):
    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    # Remove pagination for this specific endpoint as it uses 'limit' for random fetching
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        limit_str = self.request.query_params.get("limit", "10")
        try:
            limit = int(limit_str)
            if limit <= 0:
                limit = 10
        except ValueError:
            limit = 10

        # Extract filters from query params
        subsection_slugs_str = self.request.query_params.get("subsection__slug__in")
        skill_slugs_str = self.request.query_params.get("skill__slug__in")
        exclude_ids_str = self.request.query_params.get("exclude_ids")

        subsections = (
            [s.strip() for s in subsection_slugs_str.split(",") if s.strip()]
            if subsection_slugs_str
            else None
        )
        skills = (
            [s.strip() for s in skill_slugs_str.split(",") if s.strip()]
            if skill_slugs_str
            else None
        )
        starred = self.request.query_params.get("starred", "").lower() == "true"
        not_mastered = (
            self.request.query_params.get("not_mastered", "").lower() == "true"
        )

        exclude_ids = []
        if exclude_ids_str:
            try:
                exclude_ids = [
                    int(id_str.strip())
                    for id_str in exclude_ids_str.split(",")
                    if id_str.strip().isdigit()
                ]
            except ValueError:
                logger.warning(
                    f"Invalid non-integer value found in exclude_ids: {exclude_ids_str}"
                )

        # Use the utility function
        return get_filtered_questions(
            user=user,
            limit=limit,
            subsections=subsections,
            skills=skills,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=exclude_ids,
        )


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Submit Answer for Traditional Learning",
    description=(
        "Submits an answer for a single question in traditional mode. Records attempt, "
        "calculates correctness, updates points, streak, and proficiency. Returns immediate feedback."
    ),
    request=TraditionalLearningAnswerSerializer,
    responses={
        200: OpenApiResponse(
            response=TraditionalLearningResponseSerializer,
            description="Answer processed successfully.",
        ),
        400: OpenApiResponse(description="Invalid input data."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Question Not Found."
        ),  # Handled by serializer
    },
)
class TraditionalLearningAnswerView(generics.GenericAPIView):
    serializer_class = TraditionalLearningAnswerSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Logic is in the serializer
        response_serializer = TraditionalLearningResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


# --- General Test Attempt Views ---


@extend_schema(
    tags=["Study & Progress - Tests"],  # Grouped tag
    summary="List User Test Attempts",
    description="Retrieves a paginated list of the authenticated user's previous test attempts (practice, simulations, level assessments).",
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
    # Default pagination applies

    def get_queryset(self):
        # Model Meta defines default ordering by -start_time
        return UserTestAttempt.objects.filter(user=self.request.user)


@extend_schema(
    tags=["Study & Progress - Tests"],
    summary="Start New Test (Practice/Simulation)",
    description="Initiates a new practice or simulation test based on the provided configuration. Selects questions according to criteria.",
    request=TestStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="Test started successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid config, no questions found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class StartTestAttemptView(generics.GenericAPIView):
    serializer_class = TestStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id', 'questions': queryset}
        response_serializer = TestStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress - Tests"],
    summary="Retrieve Test Attempt Details",
    description="Gets details of a specific test attempt (any type), including status and associated questions (no answers if ongoing). Requires ownership.",
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
        return UserTestAttempt.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        # Pass request context for nested QuestionListSerializer
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


@extend_schema(
    tags=["Study & Progress - Tests"],
    summary="Submit Test Answers (Practice/Simulation)",
    description="Submits answers for an ongoing practice or simulation test. Calculates score, updates status, points, proficiency.",
    request=TestSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=TestSubmitResponseSerializer,
            description="Test submitted successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., already submitted, wrong answers)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class SubmitTestAttemptView(generics.GenericAPIView):
    serializer_class = TestSubmitSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, attempt_id, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Logic handled in serializer
        response_serializer = TestSubmitResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Tests"],
    summary="Review Completed Test",
    description="Retrieves a detailed question-by-question review for a *completed* test attempt (any type), including user/correct answers and explanations.",
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            description="If true, return only incorrect questions.",
            type=bool,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=TestReviewSerializer, description="Detailed review questions."
        ),
        400: OpenApiResponse(
            description="Bad Request (Attempt not completed)."
        ),  # Raised by get_object
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class ReviewTestAttemptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = TestReviewSerializer  # For response structure

    def get_object(self):
        """Get the test attempt, ensuring ownership and completion status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        # Ensure attempt exists, belongs to user, and is completed
        attempt = get_object_or_404(
            UserTestAttempt.objects.select_related(
                "user"
            ),  # Select user if needed later
            pk=attempt_id,
            user=user,
        )
        if attempt.status != UserTestAttempt.Status.COMPLETED:
            raise serializers.ValidationError(
                _("Cannot review an ongoing or abandoned test attempt.")
            )
        return attempt

    def get(self, request, attempt_id, *args, **kwargs):
        test_attempt = self.get_object()  # Handles 404, ownership, status check

        # Fetch questions associated with the attempt (ordered)
        questions_queryset = (
            test_attempt.get_questions_queryset()
        )  # Includes select_related

        # Fetch user's answers for these questions within this attempt
        user_attempts = UserQuestionAttempt.objects.filter(
            test_attempt=test_attempt,
            question_id__in=test_attempt.question_ids,
        )

        # --- Filter by incorrect_only if requested ---
        incorrect_only = (
            request.query_params.get("incorrect_only", "").lower() == "true"
        )
        if incorrect_only:
            incorrect_map = {
                attempt.question_id: attempt
                for attempt in user_attempts
                if not attempt.is_correct
            }
            # Filter the main questions queryset based on keys from the incorrect map
            questions_queryset = questions_queryset.filter(pk__in=incorrect_map.keys())
            # Reapply ordering based on the *filtered* set of original IDs
            filtered_original_ids = [
                qid for qid in test_attempt.question_ids if qid in incorrect_map
            ]
            preserved_order = Case(
                *[
                    When(pk=pk, then=pos)
                    for pos, pk in enumerate(filtered_original_ids)
                ],
                output_field=IntegerField(),
            )
            questions_queryset = questions_queryset.order_by(preserved_order)
            user_attempts_map = incorrect_map  # Use the filtered map
        else:
            # Create a map for all attempts for faster lookup in the serializer
            user_attempts_map = {
                attempt.question_id: attempt for attempt in user_attempts
            }

        # Prepare context for the review question serializer
        context = {"request": request, "user_attempts_map": user_attempts_map}

        # Prepare data structure for the response serializer
        response_data = {
            "attempt_id": test_attempt.id,
            "review_questions": questions_queryset,  # Pass queryset
        }
        # Use the TestReviewSerializer for the final output
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Tests"],
    summary="Retake Similar Test",
    description="Starts a *new* test attempt using the same configuration as a previous attempt (any type). Generates a fresh set of questions, excluding those in the original attempt if possible.",
    request=None,  # No request body
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
    # Reuse TestStartResponseSerializer as the output structure is the same (attempt_id, questions)
    serializer_class = TestStartResponseSerializer

    def get_object(self):
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        # Allow retake from any status? Or only completed? Let's allow from any for flexibility.
        return get_object_or_404(UserTestAttempt, pk=attempt_id, user=user)

    def post(self, request, attempt_id, *args, **kwargs):
        original_attempt = self.get_object()
        user = request.user

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
        )

        # --- Extract parameters for question filtering ---
        num_questions = original_config_dict.get("num_questions")
        sub_slugs = original_config_dict.get("subsections", [])
        skill_slugs = original_config_dict.get("skills", [])
        starred = original_config_dict.get("starred", False)
        not_mastered = original_config_dict.get("not_mastered", False)

        if not num_questions:
            raise serializers.ValidationError(
                _("Original configuration missing 'num_questions'.")
            )
        # Basic check: Ensure at least one filter criterion exists
        if (
            not sub_slugs and not skill_slugs and not starred and not not_mastered
        ):  # Added not_mastered here
            logger.warning(
                f"Retake attempt for {original_attempt.id} triggered with no primary filter criteria (subsections, skills, starred, not_mastered). Relying on active questions only."
            )
            # Allow proceeding, will select from all active questions if this happens

        # --- Select New Questions using Utility Function ---
        # Try to exclude original questions first
        new_questions_queryset = get_filtered_questions(
            user=user,
            limit=num_questions,
            subsections=sub_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=original_attempt.question_ids,  # Exclude original set
        )
        new_question_ids = list(new_questions_queryset.values_list("id", flat=True))

        # Fallback: If no *new* questions found matching criteria, try including originals
        if not new_question_ids or len(new_question_ids) < num_questions:
            logger.warning(
                f"Could not find enough *new* questions for retake of attempt {original_attempt.id}. Trying again including original questions."
            )
            new_questions_queryset_fallback = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=None,  # Allow original questions this time
            )
            new_question_ids = list(
                new_questions_queryset_fallback.values_list("id", flat=True)
            )

        # Check if *any* questions could be selected
        if not new_question_ids:
            raise serializers.ValidationError(
                _(
                    "No suitable questions found to generate a similar test, even including originals."
                )
            )

        # Ensure we don't request more than available
        actual_num_questions = min(num_questions, len(new_question_ids))
        if actual_num_questions < num_questions:
            logger.warning(
                f"Only found {actual_num_questions} questions for retake of attempt {original_attempt.id} (requested {num_questions})."
            )
            # Need to resize the sample if fewer were found than requested
            final_question_ids = random.sample(new_question_ids, actual_num_questions)
        else:
            final_question_ids = random.sample(
                new_question_ids, num_questions
            )  # Sample the requested number

        # --- Create New Test Attempt ---
        new_config_snapshot = original_config_snapshot.copy()
        new_config_snapshot["config"]["actual_num_questions_selected"] = len(
            final_question_ids
        )
        new_config_snapshot["retake_of_attempt_id"] = (
            original_attempt.id
        )  # Add reference

        try:
            new_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=original_attempt_type,  # Use original type
                test_configuration=new_config_snapshot,
                question_ids=final_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating retake UserTestAttempt for user {user.id} (original: {original_attempt.id}): {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the new similar test.")]}
            )

        # --- Prepare and Return Response ---
        final_questions_queryset = new_attempt.get_questions_queryset()
        result_data = {
            "attempt_id": new_attempt.id,
            "questions": final_questions_queryset,
        }
        # Add extra message for clarity
        response_data = self.get_serializer(
            result_data, context={"request": request}
        ).data
        response_data["message"] = _(
            "New test started based on the configuration of attempt #{}."
        ).format(original_attempt.id)
        # Ensure ID is present if serializer structure changes
        response_data["new_attempt_id"] = new_attempt.id

        return Response(response_data, status=status.HTTP_201_CREATED)


# --- Placeholder Views for other features ---
# class EmergencyModeStartView(generics.GenericAPIView): ...
# class EmergencyModeUpdateView(generics.GenericAPIView): ...
# class EmergencyModeAnswerView(generics.GenericAPIView): ...
# class ConversationStartView(generics.GenericAPIView): ...
# class ConversationMessageView(generics.GenericAPIView): ...
# class StatisticsView(views.APIView): ...
# class SaveLastVisitedOptionView(generics.UpdateAPIView): ...
