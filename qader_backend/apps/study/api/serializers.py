import random
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Count, Avg, Sum, Case, When, IntegerField, FloatField, Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.conf import settings
import logging

from ..models import UserSkillProficiency, UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import Question, LearningSection, LearningSubSection, Skill
from apps.learning.api.serializers import (
    QuestionListSerializer,
    LearningSubSectionSerializer,  # Used in review serializer
    SkillSerializer,  # Used in review serializer
)
from apps.users.models import UserProfile
from apps.users.api.serializers import UserProfileSerializer

# Import utility functions
from ..utils import (
    get_filtered_questions,
    record_user_study_activity,
    update_user_skill_proficiency,
)

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = 30
DEFAULT_QUESTIONS_TRADITIONAL = 10
RECENT_TESTS_LIMIT = 10
# Proficiency threshold moved to utils


# --- Helper: Get User from Context --- (Keep as is or move to a common API utils)
def _get_user_from_context(context):
    request = context.get("request")
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    logger.error("Authenticated user could not be retrieved from serializer context.")
    raise PermissionDenied(
        _("User not found or not authenticated in serializer context.")
    )


# --- Level Assessment Serializers ---


class LevelAssessmentStartSerializer(serializers.Serializer):
    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSection.objects.all()
        ),
        min_length=1,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        min_value=5,
        max_value=100,  # Enforce reasonable limits
        default=DEFAULT_QUESTIONS_LEVEL_ASSESSMENT,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        user = _get_user_from_context(self.context)

        # --- Check if level determination is required (Based on requirements) ---
        try:
            profile = user.profile
            # The requirement states user MUST determine level first time.
            # This check prevents starting *another* assessment if level is already set,
            # unless a specific "retake" mechanism is implemented.
            if profile.level_determined:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Your level has already been determined. Retake functionality is not yet implemented."
                            )
                        ]
                    }
                )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for authenticated user ID: {user.id}. Check signals/initial setup."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile could not be found.")]}
            )

        # --- Check for existing *ongoing* Level Assessments ---
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "You already have an ongoing level assessment. Please complete or abandon it first."
                        )
                    ]
                }
            )

        # --- Check if enough questions exist ---
        sections = data["sections"]
        num_questions_requested = data["num_questions"]
        # Efficiently count questions
        question_pool_count = Question.objects.filter(
            subsection__section__in=sections, is_active=True
        ).count()

        if question_pool_count < num_questions_requested:
            logger.warning(
                f"User {user.id} requested {num_questions_requested} level assessment questions for sections "
                f"{[s.slug for s in sections]}, but only {question_pool_count} active questions are available."
            )
            # Adjust the number of questions if fewer are available but more than minimum
            if (
                question_pool_count < self.fields["num_questions"].min_value
            ):  # Use defined min_value
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Not enough active questions available in the selected sections to start the assessment."
                            )
                        ]
                    }
                )
            # Store the adjusted count for the create method
            self.context["actual_num_questions"] = question_pool_count
        else:
            self.context["actual_num_questions"] = num_questions_requested

        return data

    def create(self, validated_data):
        user = _get_user_from_context(self.context)
        sections = validated_data["sections"]
        num_questions_requested = validated_data["num_questions"]
        actual_num_questions = self.context[
            "actual_num_questions"
        ]  # Get adjusted count

        # --- Question Selection (Efficiently get IDs) ---
        question_pool_ids = list(
            Question.objects.filter(
                subsection__section__in=sections, is_active=True
            ).values_list("id", flat=True)
        )

        if not question_pool_ids:  # Should be caught by validation, but double-check
            raise serializers.ValidationError(_("No questions found for selection."))

        # Sample the questions using the actual number possible
        selected_question_ids = random.sample(
            question_pool_ids,
            min(
                actual_num_questions, len(question_pool_ids)
            ),  # Ensure sample size <= pool size
        )

        # --- Create Test Attempt ---
        config_snapshot = {
            "sections_requested": [s.slug for s in sections],
            "num_questions_requested": num_questions_requested,
            "actual_num_questions_selected": len(selected_question_ids),
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
                test_configuration=config_snapshot,
                question_ids=selected_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating Level Assessment UserTestAttempt for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the assessment.")]}
            )

        # --- Prepare Response Data ---
        questions_queryset = test_attempt.get_questions_queryset()
        return {
            "attempt_id": test_attempt.id,
            "questions": questions_queryset,  # Pass queryset to response serializer
        }


class LevelAssessmentAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


class LevelAssessmentSubmitSerializer(serializers.Serializer):
    answers = LevelAssessmentAnswerSerializer(
        many=True, min_length=1
    )  # Ensure at least one answer

    def validate(self, data):
        user = _get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = (
            view.kwargs.get("attempt_id") if view and hasattr(view, "kwargs") else None
        )

        if not attempt_id:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Assessment attempt ID missing.")]}
            )

        # --- Fetch and Validate Test Attempt ---
        try:
            # Eager load profile for updates later
            test_attempt = UserTestAttempt.objects.select_related("user__profile").get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Must be ongoing
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Must be correct type
            )
        except UserTestAttempt.DoesNotExist:
            # Check if it exists but status/type is wrong, or if it truly doesn't exist/belong to user
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "This assessment attempt is not active or is not a level assessment."
                            )
                        ]
                    }
                )
            else:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Assessment attempt not found or does not belong to you.")
                        ]
                    }
                )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for user {user.id} during assessment submission."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error.")]}
            )

        # --- Validate Submitted Answers Against Expected Questions ---
        submitted_answers_data = data["answers"]
        submitted_question_ids = {
            answer["question_id"] for answer in submitted_answers_data
        }
        expected_question_ids = set(test_attempt.question_ids)

        if len(submitted_answers_data) != len(expected_question_ids):
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Incorrect number of answers submitted. Expected {}, got {}."
                        ).format(
                            len(expected_question_ids), len(submitted_answers_data)
                        )
                    ]
                }
            )

        if submitted_question_ids != expected_question_ids:
            missing = expected_question_ids - submitted_question_ids
            extra = submitted_question_ids - expected_question_ids
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = sorted(list(missing))
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = sorted(
                    list(extra)
                )
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Mismatch between submitted answers and questions in the assessment attempt."
                        ),
                        error_detail,
                    ]
                }
            )

        # Store validated attempt in context for save method
        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic
    def save(self, **kwargs):
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user
        profile = user.profile  # Assumed to exist from validation

        # --- Fetch questions efficiently ---
        questions_in_attempt = (
            test_attempt.get_questions_queryset()
        )  # Already includes select_related
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records ---
        attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:  # Should not happen if validation passed
                logger.error(
                    f"Question ID {question_id} from submit data not found in fetched questions for test attempt {test_attempt.id}"
                )
                raise serializers.ValidationError(
                    {
                        "answers": _(
                            f"Internal error: Question {question_id} not found during processing."
                        )
                    }
                )

            is_correct_flag = answer_data["selected_answer"] == question.correct_answer

            attempts_to_create.append(
                UserQuestionAttempt(
                    user=user,
                    question=question,
                    test_attempt=test_attempt,
                    selected_answer=answer_data["selected_answer"],
                    time_taken_seconds=answer_data.get("time_taken_seconds"),
                    mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
                    is_correct=is_correct_flag,
                    # attempted_at handled by default
                )
            )

        try:
            created_attempts = UserQuestionAttempt.objects.bulk_create(
                attempts_to_create
            )
            # Important: Need to fetch the created attempts with related question data for scoring
            created_attempt_ids = [attempt.id for attempt in created_attempts]
            attempts_for_scoring = list(
                UserQuestionAttempt.objects.filter(
                    id__in=created_attempt_ids
                ).select_related("question__subsection__section")
            )  # Reload with needed relations

        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for test attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save assessment answers.")]}
            )

        # --- Calculate and Save Scores using model method ---
        test_attempt.calculate_and_save_scores(attempts_for_scoring)

        # --- Mark Test Attempt Complete ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.save(update_fields=["status", "end_time", "updated_at"])

        # --- Update User Profile ---
        profile.current_level_verbal = test_attempt.score_verbal
        profile.current_level_quantitative = test_attempt.score_quantitative
        profile.save(
            update_fields=[
                "current_level_verbal",
                "current_level_quantitative",
                "updated_at",
            ]
        )
        logger.info(
            f"Level assessment attempt {test_attempt.id} completed for user {user.id}. Profile updated."
        )

        # --- Award Points ---
        points_info = record_user_study_activity(
            user=user,
            points_to_add=getattr(
                settings, "POINTS_LEVEL_ASSESSMENT_COMPLETED", 25
            ),  # Example points
            reason_code="LEVEL_ASSESSMENT_COMPLETED",
            description=f"Completed Level Assessment Attempt #{test_attempt.id}",
        )
        # points_info contains updated streak/points, but we don't need it directly for the response here

        # --- Prepare and Return Result Data ---
        profile.refresh_from_db()  # Get final profile state
        return {
            "attempt_id": test_attempt.id,
            "results": {
                "overall_score": test_attempt.score_percentage,
                "verbal_score": test_attempt.score_verbal,
                "quantitative_score": test_attempt.score_quantitative,
                "proficiency_summary": test_attempt.results_summary,  # Get from updated attempt
                "message": _(
                    "Your level assessment is complete. Your personalized learning path is now adjusted!"
                ),
            },
            "updated_profile": profile,  # Pass profile object to response serializer
        }


class LevelAssessmentResponseSerializer(serializers.Serializer):
    """Response for starting a level assessment."""

    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(
        many=True, read_only=True
    )  # Context passed by view


class LevelAssessmentResultSerializer(serializers.Serializer):
    """Response for submitting a level assessment."""

    attempt_id = serializers.IntegerField(read_only=True)
    results = serializers.JSONField(read_only=True)
    updated_profile = UserProfileSerializer(read_only=True)  # Context passed by view


# --- Traditional Learning Serializers ---


class TraditionalLearningAnswerSerializer(serializers.Serializer):
    """Serializer for submitting an answer in Traditional Learning mode."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(is_active=True), required=True
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )
    used_hint = serializers.BooleanField(default=False, required=False)
    used_elimination = serializers.BooleanField(default=False, required=False)
    used_solution_method = serializers.BooleanField(default=False, required=False)

    @transaction.atomic
    def save(self, **kwargs):
        user = _get_user_from_context(self.context)
        question = self.validated_data["question_id"]
        selected_answer = self.validated_data["selected_answer"]

        # --- Determine correctness ---
        is_correct = selected_answer == question.correct_answer

        # --- Create UserQuestionAttempt record ---
        attempt = UserQuestionAttempt.objects.create(
            user=user,
            question=question,
            selected_answer=selected_answer,
            is_correct=is_correct,
            time_taken_seconds=self.validated_data.get("time_taken_seconds"),
            used_hint=self.validated_data.get("used_hint", False),
            used_elimination=self.validated_data.get("used_elimination", False),
            used_solution_method=self.validated_data.get("used_solution_method", False),
            mode=UserQuestionAttempt.Mode.TRADITIONAL,
        )

        # --- Update Profile (Points & Streak) using Utility ---
        points_earned = (
            getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
            if is_correct
            else getattr(settings, "POINTS_TRADITIONAL_INCORRECT", 0)
        )
        reason = "TRADITIONAL_CORRECT" if is_correct else "TRADITIONAL_INCORRECT"
        desc = f"{'Correct' if is_correct else 'Incorrect'} answer for Question #{question.id} (Traditional)"

        profile_updates = record_user_study_activity(
            user=user, points_to_add=points_earned, reason_code=reason, description=desc
        )

        # --- Update User Skill Proficiency using Utility ---
        update_user_skill_proficiency(
            user=user, skill=question.skill, is_correct=is_correct
        )

        # --- Prepare and Return Response Data ---
        return {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points_earned": points_earned,
            "current_total_points": profile_updates["current_total_points"],
            "streak_updated": profile_updates["streak_updated"],
            "current_streak": profile_updates["current_streak"],
        }


class TraditionalLearningResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    points_earned = serializers.IntegerField(read_only=True)
    current_total_points = serializers.IntegerField(read_only=True)
    streak_updated = serializers.BooleanField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)


# --- General Test Serializers ---


class TestConfigSerializer(serializers.Serializer):
    """Validates the 'config' part of the test start request."""

    name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text=_("Optional name for a custom test"),
    )
    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSubSection.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of subsection slugs to include"),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=Skill.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of specific skill slugs to include"),
    )
    num_questions = serializers.IntegerField(
        min_value=1,
        max_value=150,
        required=True,
        help_text=_("Number of questions for the test"),
    )
    starred = serializers.BooleanField(
        default=False, help_text=_("Include only questions starred by the user?")
    )
    not_mastered = serializers.BooleanField(
        default=False,
        help_text=_("Include questions from skills the user hasn't mastered?"),
    )
    full_simulation = serializers.BooleanField(
        default=False, help_text=_("Is this a full timed simulation test?")
    )  # May affect timer/UI

    def validate(self, data):
        if (
            not data.get("subsections")
            and not data.get("skills")
            and not data.get("starred")
        ):
            raise serializers.ValidationError(
                _("Must specify subsections, skills, or filter by starred questions.")
            )
        return data


class TestStartSerializer(serializers.Serializer):
    """Validates the request to start a new test (practice, custom, simulation)."""

    # Make sure choices don't include LEVEL_ASSESSMENT here
    test_type = serializers.ChoiceField(
        choices=[
            (
                UserTestAttempt.AttemptType.PRACTICE,
                UserTestAttempt.AttemptType.PRACTICE.label,
            ),
            (
                UserTestAttempt.AttemptType.SIMULATION,
                UserTestAttempt.AttemptType.SIMULATION.label,
            ),
        ],
        required=True,
    )
    config = TestConfigSerializer(required=True)

    def validate(self, data):
        user = _get_user_from_context(self.context)
        config = data["config"]
        # Check question availability using the utility function (just need count check here)
        # This re-runs the filter logic but ensures validation happens before create
        try:
            question_pool = get_filtered_questions(
                user=user,
                limit=config[
                    "num_questions"
                ],  # Pass limit to get an idea of availability
                subsections=[s.slug for s in config.get("subsections", [])],
                skills=[s.slug for s in config.get("skills", [])],
                starred=config.get("starred", False),
                not_mastered=config.get("not_mastered", False),
                exclude_ids=None,  # No exclusion during validation check
            )
            pool_count = question_pool.count()  # Check count after applying filters

            if pool_count == 0:
                raise serializers.ValidationError(
                    _("No active questions found matching the specified criteria.")
                )
            if pool_count < config["num_questions"]:
                logger.warning(
                    f"User {user.id} requested {config['num_questions']} questions but only {pool_count} available for config {config}. Proceeding with fewer."
                )
                self.context["actual_num_questions"] = pool_count
            else:
                self.context["actual_num_questions"] = config["num_questions"]

        except Exception as e:
            logger.error(
                f"Error validating question availability for TestStartSerializer: {e}"
            )
            raise serializers.ValidationError(
                _("Could not verify question availability.")
            )

        return data

    def create(self, validated_data):
        user = _get_user_from_context(self.context)
        config = validated_data["config"]
        test_type = validated_data["test_type"]
        actual_num_questions = self.context["actual_num_questions"]

        # --- Select Questions using Utility Function ---
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=[s.slug for s in config.get("subsections", [])],
            skills=[s.slug for s in config.get("skills", [])],
            starred=config.get("starred", False),
            not_mastered=config.get("not_mastered", False),
            exclude_ids=None,
        )
        question_ids = list(questions_queryset.values_list("id", flat=True))

        if not question_ids:  # Should be caught by validation
            raise serializers.ValidationError(_("Failed to select questions."))

        # --- Create Test Attempt ---
        config_snapshot = {
            "test_type": test_type,
            "config": {
                **config,  # Spread the validated config dict
                "subsections": [s.slug for s in config.get("subsections", [])],
                "skills": [s.slug for s in config.get("skills", [])],
                "actual_num_questions_selected": len(question_ids),
            },
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=test_type,
                test_configuration=config_snapshot,
                question_ids=question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating UserTestAttempt (Type: {test_type}) for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the test.")]}
            )

        # --- Prepare Response Data ---
        # Reload queryset based on the final selected IDs to pass to serializer
        final_questions_queryset = test_attempt.get_questions_queryset()
        return {
            "attempt_id": test_attempt.id,
            "questions": final_questions_queryset,
        }


class TestStartResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(
        many=True, read_only=True
    )  # Context passed by view


class UserTestAttemptListSerializer(serializers.ModelSerializer):
    test_type = serializers.CharField(
        source="get_attempt_type_display", read_only=True
    )  # Use display name
    num_questions = serializers.IntegerField(read_only=True)  # Use property from model
    date = serializers.DateTimeField(source="start_time", read_only=True)
    performance = serializers.SerializerMethodField()
    attempt_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "date",
            "num_questions",
            "score_percentage",
            "status",
            "performance",
        ]
        read_only_fields = fields

    def get_performance(self, obj):
        perf = {}
        if obj.score_verbal is not None:
            perf["verbal"] = obj.score_verbal
        if obj.score_quantitative is not None:
            perf["quantitative"] = obj.score_quantitative
        return perf if perf else None


class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    config_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)  # Use model property
    questions = QuestionListSerializer(
        source="get_questions_queryset", many=True, read_only=True
    )  # Use method, pass context in view
    results_summary = serializers.JSONField(read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "config_name",
            "date",
            "num_questions",
            "score_percentage",
            "status",
            "questions",
            "results_summary",
        ]
        read_only_fields = fields

    def get_config_name(self, obj):
        config = obj.test_configuration or {}
        return config.get("config", {}).get("name", None)


class TestAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


class TestSubmitSerializer(serializers.Serializer):
    answers = TestAnswerSerializer(many=True, min_length=1)

    def validate(self, data):
        user = _get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = view.kwargs.get("attempt_id") if view else None

        if not attempt_id:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Test attempt ID missing.")]}
            )

        # --- Fetch and Validate Test Attempt ---
        try:
            test_attempt = UserTestAttempt.objects.select_related("user__profile").get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Can only submit 'started' tests
            )
            # Exclude submitting Level Assessment via this endpoint
            if (
                test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Use the level assessment submission endpoint for this attempt."
                            )
                        ]
                    }
                )
        except UserTestAttempt.DoesNotExist:
            # Check if exists but wrong status/owner
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "This test attempt is not active or has already been submitted."
                            )
                        ]
                    }
                )
            else:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Test attempt not found or does not belong to you.")
                        ]
                    }
                )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for user {user.id} during test submission."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error.")]}
            )

        # --- Validate Answers ---
        submitted_answers_data = data["answers"]
        submitted_question_ids = {
            answer["question_id"] for answer in submitted_answers_data
        }
        expected_question_ids = set(test_attempt.question_ids)

        if len(submitted_answers_data) != len(expected_question_ids):
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Incorrect number of answers submitted. Expected {}, got {}."
                        ).format(
                            len(expected_question_ids), len(submitted_answers_data)
                        )
                    ]
                }
            )

        if submitted_question_ids != expected_question_ids:
            missing = expected_question_ids - submitted_question_ids
            extra = submitted_question_ids - expected_question_ids
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = sorted(list(missing))
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = sorted(
                    list(extra)
                )
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Mismatch between submitted answers and questions in the test attempt."
                        ),
                        error_detail,
                    ]
                }
            )

        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic
    def save(self, **kwargs):
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user
        profile = user.profile  # Assumed exists

        # --- Fetch questions ---
        questions_in_attempt = (
            test_attempt.get_questions_queryset()
        )  # Includes select_related
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records and update proficiency ---
        attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:
                continue  # Skip if error somehow

            is_correct = answer_data["selected_answer"] == question.correct_answer

            # Determine mode based on attempt type
            mode = UserQuestionAttempt.Mode.TEST  # Default for practice/simulation

            attempts_to_create.append(
                UserQuestionAttempt(
                    user=user,
                    question=question,
                    test_attempt=test_attempt,
                    selected_answer=answer_data["selected_answer"],
                    is_correct=is_correct,
                    time_taken_seconds=answer_data.get("time_taken_seconds"),
                    mode=mode,
                )
            )
            # Update proficiency immediately after preparing attempt data
            update_user_skill_proficiency(
                user=user, skill=question.skill, is_correct=is_correct
            )

        try:
            created_attempts = UserQuestionAttempt.objects.bulk_create(
                attempts_to_create
            )
            # Fetch attempts with related data needed for scoring
            created_attempt_ids = [attempt.id for attempt in created_attempts]
            attempts_for_scoring = list(
                UserQuestionAttempt.objects.filter(
                    id__in=created_attempt_ids
                ).select_related("question__subsection__section")
            )
        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for test attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save test answers.")]}
            )

        # --- Calculate and Save Scores ---
        test_attempt.calculate_and_save_scores(attempts_for_scoring)

        # --- Mark Test Complete ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.save(update_fields=["status", "end_time", "updated_at"])

        # --- Update Profile (Points & Streak) ---
        profile_updates = record_user_study_activity(
            user=user,
            points_to_add=getattr(settings, "POINTS_TEST_COMPLETED", 10),
            reason_code="TEST_COMPLETED",
            description=f"Completed Test Attempt #{test_attempt.id} ({test_attempt.get_attempt_type_display()})",
        )

        # --- Generate Smart Analysis (Example) ---
        smart_analysis = "Test completed!"
        results_summary = test_attempt.results_summary or {}
        weak_areas = [d["name"] for d in results_summary.values() if d["score"] < 60]
        strong_areas = [d["name"] for d in results_summary.values() if d["score"] >= 85]
        if weak_areas:
            smart_analysis += f" Focus on improving in: {', '.join(weak_areas)}."
        if strong_areas:
            smart_analysis += f" Keep up the great work in: {', '.join(strong_areas)}!"

        # --- Return Results ---
        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.status,
            "score_percentage": test_attempt.score_percentage,
            "score_verbal": test_attempt.score_verbal,
            "score_quantitative": test_attempt.score_quantitative,
            "results_summary": results_summary,
            "smart_analysis": smart_analysis,
            "points_earned": getattr(settings, "POINTS_TEST_COMPLETED", 10),
            "current_total_points": profile_updates["current_total_points"],
        }


class TestSubmitResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    smart_analysis = serializers.CharField()
    points_earned = serializers.IntegerField()
    current_total_points = serializers.IntegerField()


class TestReviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions within the test review response."""

    # Use pre-defined serializers for related fields
    subsection = LearningSubSectionSerializer(read_only=True)
    skill = SkillSerializer(read_only=True)
    user_selected_answer = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "correct_answer",
            "explanation",
            "hint",  # Added hint
            "user_selected_answer",
            "is_correct",
            "subsection",
            "skill",
            "difficulty",  # Added difficulty
        ]

    def get_user_selected_answer(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.selected_answer if user_attempt else None

    def get_is_correct(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.is_correct if user_attempt else None


class TestReviewSerializer(serializers.Serializer):
    """Response serializer for the test review endpoint."""

    attempt_id = serializers.IntegerField()
    review_questions = TestReviewQuestionSerializer(many=True)  # Context passed by view


# --- Statistics Serializers ---


class OverallMasterySerializer(serializers.Serializer):
    """Represents the overall mastery levels."""

    verbal = serializers.FloatField(allow_null=True)
    quantitative = serializers.FloatField(allow_null=True)


class StudyStreaksSerializer(serializers.Serializer):
    """Represents study streak information."""

    current_days = serializers.IntegerField()
    longest_days = serializers.IntegerField()


class ActivitySummarySerializer(serializers.Serializer):
    """Represents overall activity counts."""

    total_questions_answered = serializers.IntegerField()
    total_tests_completed = serializers.IntegerField()


class OverallStatsSerializer(serializers.Serializer):
    """Combines overall statistics."""

    mastery_level = OverallMasterySerializer()
    study_streaks = StudyStreaksSerializer()
    activity_summary = ActivitySummarySerializer()


class SubsectionPerformanceSerializer(serializers.Serializer):
    """Represents performance metrics for a specific subsection."""

    name = serializers.CharField()
    accuracy = serializers.FloatField(allow_null=True)
    attempts = serializers.IntegerField()


class SectionPerformanceSerializer(serializers.Serializer):
    """Represents performance metrics for a main section (Verbal/Quant)."""

    name = serializers.CharField()
    overall_accuracy = serializers.FloatField(allow_null=True)
    subsections = serializers.DictField(child=SubsectionPerformanceSerializer())


class SkillProficiencySummarySerializer(serializers.Serializer):
    """Represents proficiency for a single skill."""

    skill_slug = serializers.SlugField(source="skill.slug")
    skill_name = serializers.CharField(source="skill.name")
    proficiency_score = serializers.FloatField()
    accuracy = serializers.SerializerMethodField()
    attempts = serializers.IntegerField(source="attempts_count")

    def get_accuracy(self, obj):
        if obj.attempts_count > 0:
            # Calculate accuracy directly from counts for consistency
            return round((obj.correct_count / obj.attempts_count * 100), 1)
        return None  # Or 0.0 if preferred


class TestHistorySummarySerializer(serializers.ModelSerializer):
    """Represents a summary of a single completed test attempt for history charts."""

    attempt_id = serializers.IntegerField(source="id")
    date = serializers.DateTimeField(
        source="end_time"
    )  # Use end_time for completed tests
    type = serializers.CharField(source="get_attempt_type_display")
    overall_score = serializers.FloatField(source="score_percentage")
    verbal_score = serializers.FloatField(source="score_verbal")
    quantitative_score = serializers.FloatField(source="score_quantitative")

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "date",
            "type",
            "overall_score",
            "verbal_score",
            "quantitative_score",
        ]


class UserStatisticsSerializer(serializers.Serializer):
    """Serializer for the main user statistics endpoint."""

    overall = serializers.SerializerMethodField()
    performance_by_section = serializers.SerializerMethodField()
    skill_proficiency_summary = serializers.SerializerMethodField()
    test_history_summary = serializers.SerializerMethodField()

    def _get_user_profile_safe(self):
        """Safely retrieves the user profile, returning None on failure."""
        try:
            user = _get_user_from_context(self.context)
            # Cache profile to avoid repeated lookups within one serialization
            if not hasattr(self, "_cached_user_profile"):
                self._cached_user_profile = user.profile
            return self._cached_user_profile
        except Exception as e:  # Catch broader exceptions during profile access
            logger.error(
                f"Statistics: Failed to get profile for user {user.id if 'user' in locals() else 'unknown'}: {e}",
                exc_info=True,
            )
            return None

    def get_overall(self, obj):
        """Gathers overall statistics."""
        profile = self._get_user_profile_safe()
        if profile is None:
            logger.warning(
                "Statistics: Skipping 'overall' calculation due to missing profile."
            )
            return None  # Return None if profile fails

        user = profile.user  # Get user from profile
        try:
            total_questions = UserQuestionAttempt.objects.filter(user=user).count()
            total_tests = UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.COMPLETED
            ).count()

            mastery_data = {
                "verbal": profile.current_level_verbal,
                "quantitative": profile.current_level_quantitative,
            }
            streak_data = {
                "current_days": profile.current_streak_days,
                "longest_days": profile.longest_streak_days,
            }
            activity_data = {
                "total_questions_answered": total_questions,
                "total_tests_completed": total_tests,
            }

            serializer = OverallStatsSerializer(
                {
                    "mastery_level": mastery_data,
                    "study_streaks": streak_data,
                    "activity_summary": activity_data,
                }
            )
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_overall for user {user.id}: {e}"
            )
            return None  # Return None on unexpected error

    def get_performance_by_section(self, obj):
        """Calculates performance aggregated by section and subsection."""
        profile = self._get_user_profile_safe()
        if profile is None:
            logger.warning(
                "Statistics: Skipping 'performance_by_section' calculation due to missing profile."
            )
            return None  # Return None if profile fails

        user = profile.user
        try:
            performance_data = {}
            attempt_aggregates = (
                UserQuestionAttempt.objects.filter(
                    user=user,
                    question__subsection__isnull=False,
                    question__subsection__section__isnull=False,
                )
                .values(
                    "question__subsection__section__slug",
                    "question__subsection__section__name",
                    "question__subsection__slug",
                    "question__subsection__name",
                )
                .annotate(
                    total_attempts=Count("id"),
                    correct_attempts=Sum(
                        Case(
                            When(is_correct=True, then=1),
                            default=0,
                            output_field=IntegerField(),
                        )
                    ),
                )
                .order_by(
                    "question__subsection__section__slug",
                    "question__subsection__slug",
                )
            )

            # Process the aggregated data (same logic as before)
            for aggregate in attempt_aggregates:
                section_slug = aggregate["question__subsection__section__slug"]
                section_name = aggregate["question__subsection__section__name"]
                subsection_slug = aggregate["question__subsection__slug"]
                subsection_name = aggregate["question__subsection__name"]
                attempts = aggregate["total_attempts"]
                correct = aggregate["correct_attempts"]

                if section_slug not in performance_data:
                    performance_data[section_slug] = {
                        "name": section_name,
                        "total_section_attempts": 0,
                        "correct_section_attempts": 0,
                        "subsections": {},
                    }

                subsection_accuracy = (
                    round((correct / attempts * 100), 1) if attempts > 0 else None
                )
                performance_data[section_slug]["subsections"][subsection_slug] = {
                    "name": subsection_name,
                    "accuracy": subsection_accuracy,
                    "attempts": attempts,
                }
                performance_data[section_slug]["total_section_attempts"] += attempts
                performance_data[section_slug]["correct_section_attempts"] += correct

            # Calculate final scores (same logic as before)
            final_performance_data = {}
            for slug, data in performance_data.items():
                total_attempts = data["total_section_attempts"]
                correct_attempts = data["correct_section_attempts"]
                overall_accuracy = (
                    round((correct_attempts / total_attempts * 100), 1)
                    if total_attempts > 0
                    else None
                )

                # Use try-except around nested serializer instantiation
                try:
                    section_serializer = SectionPerformanceSerializer(
                        {
                            "name": data["name"],
                            "overall_accuracy": overall_accuracy,
                            "subsections": data["subsections"],
                        }
                    )
                    section_serializer.is_valid(
                        raise_exception=True
                    )  # Validate nested data
                    final_performance_data[slug] = section_serializer.data
                except Exception as inner_e:
                    logger.exception(
                        f"Statistics: Error serializing section '{slug}' for user {user.id}: {inner_e}"
                    )
                    # Optionally skip this section or return partial data
                    final_performance_data[slug] = {
                        "error": "Failed to serialize section data."
                    }

            return final_performance_data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_performance_by_section for user {user.id}: {e}"
            )
            return None  # Return None on unexpected error

    def get_skill_proficiency_summary(self, obj):
        """Retrieves skill proficiency data."""
        profile = self._get_user_profile_safe()
        if profile is None:
            logger.warning(
                "Statistics: Skipping 'skill_proficiency_summary' calculation due to missing profile."
            )
            return None  # Return None if profile fails

        user = profile.user
        try:
            proficiencies = (
                UserSkillProficiency.objects.filter(user=user, skill__isnull=False)
                .select_related("skill")
                .order_by("-proficiency_score")
            )

            serializer = SkillProficiencySummarySerializer(proficiencies, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_skill_proficiency_summary for user {user.id}: {e}"
            )
            return None  # Return None on unexpected error

    def get_test_history_summary(self, obj):
        """Retrieves a summary of the N most recent completed tests."""
        profile = self._get_user_profile_safe()
        if profile is None:
            logger.warning(
                "Statistics: Skipping 'test_history_summary' calculation due to missing profile."
            )
            return None  # Return None if profile fails

        user = profile.user
        try:
            recent_tests = UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.COMPLETED
            ).order_by("-end_time")[:RECENT_TESTS_LIMIT]

            serializer = TestHistorySummarySerializer(recent_tests, many=True)
            return serializer.data
        except Exception as e:
            logger.exception(
                f"Statistics: Error in get_test_history_summary for user {user.id}: {e}"
            )
            return None  # Return None on unexpected error


# --- Serializers for Emergency Mode, Conversation etc. go here ---
