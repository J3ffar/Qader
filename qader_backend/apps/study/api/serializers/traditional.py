from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.conf import settings
import logging

from apps.study.models import UserQuestionAttempt
from apps.learning.models import Question
from apps.api.utils import get_user_from_context  # Import the helper
from apps.study.services import (  # Import services
    record_user_study_activity,
    update_user_skill_proficiency,
)

logger = logging.getLogger(__name__)

# --- Constants ---
POINTS_TRADITIONAL_CORRECT = getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
POINTS_TRADITIONAL_INCORRECT = getattr(settings, "POINTS_TRADITIONAL_INCORRECT", 0)


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
        user = get_user_from_context(self.context)  # Use helper
        question = self.validated_data["question_id"]
        selected_answer = self.validated_data["selected_answer"]

        # --- Determine correctness ---
        is_correct = selected_answer == question.correct_answer

        # --- Create UserQuestionAttempt record ---
        # Using try-except for robustness, although validation should prevent duplicates
        try:
            attempt = UserQuestionAttempt.objects.create(
                user=user,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct,
                time_taken_seconds=self.validated_data.get("time_taken_seconds"),
                used_hint=self.validated_data.get("used_hint", False),
                used_elimination=self.validated_data.get("used_elimination", False),
                used_solution_method=self.validated_data.get(
                    "used_solution_method", False
                ),
                mode=UserQuestionAttempt.Mode.TRADITIONAL,
            )
        except Exception as e:
            logger.error(
                f"Error creating Traditional UQA for user {user.id}, q {question.id}: {e}"
            )
            # Decide how to handle - maybe raise validation error if it's a duplicate attempt
            # for this specific mode (if constraints allow/require)
            raise serializers.ValidationError(_("Failed to record the attempt."))

        # --- Update Profile (Points & Streak) using Service ---
        points_earned = (
            POINTS_TRADITIONAL_CORRECT if is_correct else POINTS_TRADITIONAL_INCORRECT
        )
        reason = "TRADITIONAL_CORRECT" if is_correct else "TRADITIONAL_INCORRECT"
        desc = f"{'Correct' if is_correct else 'Incorrect'} answer for Question #{question.id} (Traditional)"

        profile_updates = record_user_study_activity(
            user=user, points_to_add=points_earned, reason_code=reason, description=desc
        )

        # --- Update User Skill Proficiency using Service ---
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
