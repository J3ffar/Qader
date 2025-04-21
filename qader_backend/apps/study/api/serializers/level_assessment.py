# qader_backend/apps/study/api/serializers/level_assessment.py

import random
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import Question, LearningSection
from apps.users.models import UserProfile
from apps.users.api.serializers import UserProfileSerializer
from apps.learning.api.serializers import QuestionListSerializer
from apps.api.utils import get_user_from_context

# Import only proficiency service if needed
from apps.study.services import update_user_skill_proficiency


logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "DEFAULT_QUESTIONS_LEVEL_ASSESSMENT", 30
)  # Use setting or default
# Point constants handled by gamification signals/services

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
        max_value=100,
        default=DEFAULT_QUESTIONS_LEVEL_ASSESSMENT,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        user = get_user_from_context(self.context)

        # --- Check if level determination is required ---
        # This validation might need adjustment based on whether retakes are allowed.
        # Assuming for now, it prevents starting if already determined.
        try:
            profile = user.profile
            if (
                profile.current_level_verbal is not None
                or profile.current_level_quantitative is not None
            ):
                # Check if level is already set (more reliable than a separate flag)
                # Allow retake? For now, prevent if already set. Add separate endpoint/logic for retake.
                # raise serializers.ValidationError(...) # Disable for now to allow testing
                pass

        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile missing for user ID: {user.id}.")
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
        question_pool_count = Question.objects.filter(
            subsection__section__in=sections, is_active=True
        ).count()

        min_required = self.fields["num_questions"].min_value
        if question_pool_count < min_required:
            raise serializers.ValidationError(
                {
                    "num_questions": [
                        _(
                            "Not enough active questions available ({count}) in the selected sections to start the assessment (minimum {min_req})."
                        ).format(count=question_pool_count, min_req=min_required)
                    ]
                }
            )

        if question_pool_count < num_questions_requested:
            logger.warning(
                f"User {user.id} requested {num_questions_requested} level assessment questions for sections "
                f"{[s.slug for s in sections]}, but only {question_pool_count} active questions are available. Using {question_pool_count}."
            )
            self.context["actual_num_questions"] = question_pool_count
        else:
            self.context["actual_num_questions"] = num_questions_requested

        return data

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        sections = validated_data["sections"]
        num_questions_requested = validated_data["num_questions"]
        actual_num_questions = self.context["actual_num_questions"]

        # --- Question Selection ---
        question_pool_ids = list(
            Question.objects.filter(
                subsection__section__in=sections, is_active=True
            ).values_list("id", flat=True)
        )
        if not question_pool_ids or len(question_pool_ids) < actual_num_questions:
            # This should be caught by validation, but double check
            raise serializers.ValidationError(
                _("Insufficient questions found for selection.")
            )

        selected_question_ids = random.sample(question_pool_ids, actual_num_questions)

        # --- Create Test Attempt ---
        config_snapshot = {
            "sections_requested": [s.slug for s in sections],
            "num_questions_requested": num_questions_requested,
            "actual_num_questions_selected": len(selected_question_ids),
            "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Add type to snapshot
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

        questions_queryset = test_attempt.get_questions_queryset()
        return {
            "attempt_id": test_attempt.id,
            "questions": questions_queryset,
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
    answers = LevelAssessmentAnswerSerializer(many=True, min_length=1)

    def validate(self, data):
        user = get_user_from_context(self.context)
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
            # Added select_related for user__profile
            test_attempt = UserTestAttempt.objects.select_related("user__profile").get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Can only submit 'started'
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            )
        except UserTestAttempt.DoesNotExist:
            # Check if attempt exists but wrong status/type/owner
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                existing_attempt = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                if existing_attempt.status != UserTestAttempt.Status.STARTED:
                    error_msg = _(
                        "This assessment attempt has already been submitted or abandoned."
                    )
                elif (
                    existing_attempt.attempt_type
                    != UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
                ):
                    error_msg = _("This attempt is not a level assessment.")
                else:  # Should not happen if check above passes
                    error_msg = _("Cannot submit this assessment attempt.")
                raise serializers.ValidationError({"non_field_errors": [error_msg]})
            else:
                # Attempt ID is invalid or doesn't belong to user
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Assessment attempt not found or does not belong to you.")
                        ]
                    }
                )
        except UserProfile.DoesNotExist:  # Should user__profile access fail
            logger.error(
                f"UserProfile missing for user {user.id} during assessment submission."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error during submission.")]}
            )

        # --- Validate Submitted Answers ---
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
                            "Incorrect number of answers submitted. Expected {expected}, got {actual}."
                        ).format(
                            expected=len(expected_question_ids),
                            actual=len(submitted_answers_data),
                        )
                    ]
                }
            )

        if submitted_question_ids != expected_question_ids:
            missing = sorted(list(expected_question_ids - submitted_question_ids))
            extra = sorted(list(submitted_question_ids - expected_question_ids))
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = missing
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = extra
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

        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic
    def save(self, **kwargs):
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user
        profile = user.profile  # Assumed to exist from validation

        # --- Fetch questions efficiently ---
        questions_in_attempt = test_attempt.get_questions_queryset()
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records ---
        attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:
                logger.error(
                    f"Question ID {question_id} from submit data not found for test attempt {test_attempt.id}"
                )
                # This should have been caught by validation, but handle defensively
                raise serializers.ValidationError(
                    _("Internal error: Invalid question ID found during submission.")
                )

            is_correct_flag = answer_data["selected_answer"] == question.correct_answer
            attempts_to_create.append(
                UserQuestionAttempt(
                    user=user,
                    question=question,
                    test_attempt=test_attempt,
                    selected_answer=answer_data["selected_answer"],
                    time_taken_seconds=answer_data.get("time_taken_seconds"),
                    mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,  # Set mode correctly
                    is_correct=is_correct_flag,
                )
            )
            # Update proficiency immediately (remains synchronous)
            update_user_skill_proficiency(
                user=user, skill=question.skill, is_correct=is_correct_flag
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
                ).select_related(
                    "question__subsection__section"  # Needed for score calculation
                )
            )
        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for level assessment attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save assessment answers.")]}
            )

        # --- Calculate and Save Scores using model method ---
        test_attempt.calculate_and_save_scores(attempts_for_scoring)

        # --- Mark Test Attempt Complete ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        # Note: completion_points_awarded flag will be set by the signal receiver
        test_attempt.save(update_fields=["status", "end_time", "updated_at"])

        # --- Update User Profile Level Scores ---
        # Moved proficiency update into loop above
        profile.current_level_verbal = test_attempt.score_verbal
        profile.current_level_quantitative = test_attempt.score_quantitative
        # Remove the level_determined flag if using level scores directly
        profile.save(
            update_fields=[
                "current_level_verbal",
                "current_level_quantitative",
                "updated_at",
            ]
        )
        logger.info(
            f"Level assessment attempt {test_attempt.id} completed for user {user.id}. Profile level scores updated."
        )

        # --- Prepare and Return Result Data ---
        # Refresh profile to show latest levels
        profile.refresh_from_db()
        return {
            "attempt_id": test_attempt.id,
            "results": {
                "overall_score": test_attempt.score_percentage,
                "verbal_score": test_attempt.score_verbal,
                "quantitative_score": test_attempt.score_quantitative,
                "proficiency_summary": test_attempt.results_summary,
                "message": _(
                    "Your level assessment is complete. Your personalized learning path is now adjusted!"
                ),
            },
            # Include profile data showing the updated levels
            "updated_profile": profile,
        }


class LevelAssessmentResponseSerializer(serializers.Serializer):
    """Response for starting a level assessment."""

    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(many=True, read_only=True)


class LevelAssessmentResultSerializer(serializers.Serializer):
    """Response for submitting a level assessment."""

    attempt_id = serializers.IntegerField(read_only=True)
    results = serializers.JSONField(read_only=True)
    # Show the profile state AFTER the assessment update
    updated_profile = UserProfileSerializer(read_only=True)
    # Removed points_earned (handled by signal)
