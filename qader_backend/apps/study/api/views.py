from rest_framework import generics, status, permissions, serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.study.models import (
    UserTestAttempt,
    TestDefinition,
    UserQuestionAttempt,
    update_skill_proficiency_for_attempt,
)
from apps.learning.models import Question, LearningSection
from apps.api.permissions import (
    IsSubscribed,
    IsOwnerOfTestAttempt,
    HasDeterminedLevel,
)
from apps.users.models import UserProfile

from .serializers import (
    LevelAssessmentStartRequestSerializer,
    QuestionForAssessmentSerializer,
    LevelAssessmentSubmitRequestSerializer,
    LevelAssessmentResultSerializer,
)


class StartLevelAssessmentView(generics.GenericAPIView):
    """
    Starts a new Level Assessment test for the logged-in user.

    Selects random questions based on the chosen sections and count.
    Returns the test attempt ID and the list of questions (without answers).
    """

    serializer_class = LevelAssessmentStartRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsSubscribed]

    @extend_schema(
        tags=["Study & Progress"],
        summary="Start Level Assessment Test",
        description="Initiates a level assessment test. Requires an active subscription.",
        request=LevelAssessmentStartRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=QuestionForAssessmentSerializer,
                description="Assessment started successfully. Returns attempt ID and questions.",
            ),
            400: OpenApiResponse(
                description="Bad Request (e.g., invalid input, level already determined and retake not allowed - future)."
            ),
            403: OpenApiResponse(description="Forbidden (e.g., not subscribed)."),
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        user = request.user
        profile = user.userprofile

        # Optional: Add logic to prevent starting if already determined, unless retaking explicitly
        # if profile.level_determined and not request.data.get('retake', False):
        #     raise PermissionDenied(_("Level already determined. Retake option not implemented yet."))

        selected_sections = validated_data["sections"]
        num_questions = validated_data["num_questions"]

        # --- Fetch Questions ---
        # Simple random selection across specified sections
        # More sophisticated: balance questions per subsection/skill/difficulty
        question_queryset = Question.objects.filter(
            subsection__section__in=selected_sections, is_active=True
        ).order_by(
            "?"
        )  # Random order - potentially slow on large tables

        # Ensure we don't request more questions than available
        available_questions = question_queryset.count()
        if available_questions < num_questions:
            # Decide: raise error or take all available? Let's take available.
            num_questions = available_questions
            if num_questions < 5:  # Arbitrary minimum needed
                raise ValidationError(
                    _(
                        "Not enough active questions available in the selected sections to start the assessment."
                    )
                )

        questions = list(question_queryset[:num_questions])
        question_ids = [q.id for q in questions]

        # --- Create Test Attempt ---
        try:
            # Assuming a single, predefined TestDefinition for level assessment
            level_assessment_def = TestDefinition.objects.get(
                slug="initial-level-assessment",
                test_type=TestDefinition.TestType.LEVEL_ASSESSMENT,
            )
        except TestDefinition.DoesNotExist:
            # Consider creating it if it doesn't exist, or raising an error
            # For now, let's assume it must be created via admin/fixtures
            raise NotFound(
                _("Level Assessment definition not found. Please contact support.")
            )
        except TestDefinition.MultipleObjectsReturned:
            # This indicates a configuration issue
            raise NotFound(
                _(
                    "Multiple Level Assessment definitions found. Please contact support."
                )
            )

        attempt_config = {
            "type": "level_assessment",
            "sections": [s.slug for s in selected_sections],
            "num_questions": num_questions,
            "question_ids": question_ids,  # Store the exact questions used
        }

        # Use transaction to ensure attempt and related data are created atomically
        with transaction.atomic():
            attempt = UserTestAttempt.objects.create(
                user=user,
                test_definition=level_assessment_def,
                configuration=attempt_config,
                status=UserTestAttempt.Status.STARTED,
            )

            # Pre-create UserQuestionAttempt entries if needed later for validation,
            # or rely solely on configuration['question_ids'] stored above.
            # Storing IDs in config is simpler for now.

        # --- Serialize Response ---
        question_serializer = QuestionForAssessmentSerializer(
            questions, many=True, context={"request": request}
        )
        response_data = {
            "attempt_id": attempt.id,
            "questions": question_serializer.data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class SubmitLevelAssessmentView(generics.GenericAPIView):
    """
    Submits the answers for a specific Level Assessment test attempt.

    Calculates scores, updates user profile levels and skill proficiencies.
    Returns the final results.
    """

    serializer_class = LevelAssessmentSubmitRequestSerializer
    permission_classes = [
        permissions.IsAuthenticated,
        IsSubscribed,
        IsOwnerOfTestAttempt,
    ]

    def get_object(self):
        """
        Retrieves the UserTestAttempt based on the URL pk, ensuring correct type and status.
        Also checks object-level permissions.
        """
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Ensure it's the correct type and hasn't been completed yet
            obj = UserTestAttempt.objects.select_related(
                "user__userprofile", "test_definition"
            ).get(
                pk=attempt_id,
                # test_definition__test_type=TestDefinition.TestType.LEVEL_ASSESSMENT, # Could enforce this
                status=UserTestAttempt.Status.STARTED,  # Can only submit 'started' attempts
            )
        except UserTestAttempt.DoesNotExist:
            raise NotFound(_("Assessment attempt not found or already submitted."))

        # Check permissions (IsOwnerOfTestAttempt)
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        tags=["Study & Progress"],
        summary="Submit Level Assessment Answers",
        description="Submits answers for an ongoing level assessment attempt. Calculates results and updates user profile.",
        request=LevelAssessmentSubmitRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=LevelAssessmentResultSerializer,
                description="Assessment submitted successfully. Returns calculated results and updated profile levels.",
            ),
            400: OpenApiResponse(
                description="Bad Request (e.g., validation errors like wrong number of answers)."
            ),
            403: OpenApiResponse(
                description="Forbidden (e.g., not owner, not subscribed)."
            ),
            404: OpenApiResponse(
                description="Not Found (e.g., invalid attempt ID or already submitted)."
            ),
        },
    )
    def post(self, request, attempt_id, *args, **kwargs):
        attempt = self.get_object()  # Get attempt and check permissions

        serializer = self.get_serializer(
            data=request.data,
            context={
                "attempt": attempt,
                "request": request,
            },  # Pass attempt to serializer context
        )
        serializer.is_valid(raise_exception=True)
        submitted_answers = serializer.validated_data["answers"]

        # Use a transaction to ensure all updates happen together
        with transaction.atomic():
            question_attempt_list = []
            questions_cache = {
                q.id: q
                for q in Question.objects.filter(
                    id__in=[a["question_id"].id for a in submitted_answers]
                )
            }

            for answer_data in submitted_answers:
                question = questions_cache.get(answer_data["question_id"].id)
                if not question:
                    # Should be caught by serializer validation, but double-check
                    continue

                is_correct = answer_data["selected_answer"] == question.correct_answer

                user_question_attempt = UserQuestionAttempt(
                    user=request.user,
                    question=question,
                    test_attempt=attempt,
                    selected_answer=answer_data["selected_answer"],
                    is_correct=is_correct,  # Set automatically in model save or here
                    time_taken_seconds=answer_data.get("time_taken_seconds", 0),
                    mode=UserQuestionAttempt.Mode.TEST,  # Use 'TEST' mode
                )
                question_attempt_list.append(user_question_attempt)

            # Bulk create for efficiency
            UserQuestionAttempt.objects.bulk_create(question_attempt_list)

            # --- Calculate Scores and Update Attempt ---
            # Reload attempt to ensure question_attempts related manager is updated after bulk_create
            attempt.refresh_from_db()
            attempt.calculate_scores()  # This method now updates scores, summary, status, end_time
            attempt.save()

            # --- Update User Profile ---
            profile = attempt.user.userprofile
            profile.current_level_verbal = attempt.score_verbal
            profile.current_level_quantitative = attempt.score_quantitative
            profile.level_determined = True
            profile.save(
                update_fields=[
                    "current_level_verbal",
                    "current_level_quantitative",
                    "level_determined",
                    "updated_at",
                ]
            )

            # --- Update Skill Proficiency (Can be slow, consider async task) ---
            # Fetch attempts again to ensure they are linked
            created_attempts = UserQuestionAttempt.objects.filter(test_attempt=attempt)
            unique_skill_ids = set(
                created_attempts.exclude(question__skill__isnull=True).values_list(
                    "question__skill_id", flat=True
                )
            )

            # This recalculates proficiency based on *all* history for the skill, triggered by this test
            for skill_id in unique_skill_ids:
                skill_attempts = UserQuestionAttempt.objects.filter(
                    user=request.user, question__skill_id=skill_id
                )
                proficiency, created = UserSkillProficiency.objects.get_or_create(
                    user=request.user, skill_id=skill_id
                )
                total_attempts = skill_attempts.count()
                correct_attempts = skill_attempts.filter(is_correct=True).count()
                proficiency.attempts_count = total_attempts
                proficiency.correct_count = correct_attempts
                if total_attempts > 0:
                    proficiency.proficiency_score = correct_attempts / total_attempts
                else:
                    proficiency.proficiency_score = 0.0
                proficiency.save()

        # --- Serialize and Return Results ---
        result_serializer = LevelAssessmentResultSerializer(attempt)
        return Response(result_serializer.data, status=status.HTTP_200_OK)
