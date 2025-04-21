# qader_backend/apps/study/api/serializers/traditional.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.conf import settings
import logging

from apps.study.models import UserQuestionAttempt
from apps.learning.models import Question
from apps.api.utils import get_user_from_context

# Import proficiency service only
from apps.study.services import update_user_skill_proficiency

logger = logging.getLogger(__name__)

# --- Constants ---
# Point constants are now handled in gamification signals/services

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

    @transaction.atomic  # Keep transaction for attempt creation and proficiency update
    def save(self, **kwargs):
        user = get_user_from_context(self.context)
        question = self.validated_data["question_id"]
        selected_answer = self.validated_data["selected_answer"]

        # --- Determine correctness ---
        is_correct = selected_answer == question.correct_answer

        # --- Create UserQuestionAttempt record ---
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
            raise serializers.ValidationError(_("Failed to record the attempt."))

        # --- Update User Skill Proficiency using Service ---
        # This remains synchronous within the request
        update_user_skill_proficiency(
            user=user, skill=question.skill, is_correct=is_correct
        )

        # --- Prepare and Return Response Data ---
        # Return feedback, but not the exact points/streak which are updated by async signals.
        return {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "feedback_message": _("Answer processed."),  # Generic feedback
        }


class TraditionalLearningResponseSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    feedback_message = serializers.CharField(read_only=True)
    # Removed point/streak fields as they are handled by signals
