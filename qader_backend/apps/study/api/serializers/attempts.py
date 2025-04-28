from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
import logging

from apps.study.models import UserQuestionAttempt, UserTestAttempt, Question
from apps.users.api.serializers import UserProfileSerializer  # For completion response

logger = logging.getLogger(__name__)


# --- Serializers for Incremental Test Attempt Flow ---


class TestAttemptAnswerSerializer(serializers.Serializer):
    """Serializer for submitting a single answer during an ongoing test attempt."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(is_active=True),  # Basic validation
        required=True,
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )
    # Add other flags if needed (used_hint, etc.)
    # used_hint = serializers.BooleanField(default=False, required=False)
    # used_elimination = serializers.BooleanField(default=False, required=False)

    def validate_question_id(self, value):
        """Ensure the question belongs to the specific test attempt (validated in view/service)."""
        # Basic validation happens via PrimaryKeyRelatedField.
        # Specific check against test_attempt.question_ids happens in the service.
        return value

    def validate_selected_answer(self, value):
        """Ensure the selected answer is valid."""
        if value not in UserQuestionAttempt.AnswerChoice.values:
            raise serializers.ValidationError(_("Invalid answer choice."))
        return value


class TestAttemptAnswerResponseSerializer(serializers.Serializer):
    """Response after submitting a single answer."""

    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    feedback_message = serializers.CharField(read_only=True)


class TestAttemptCompletionResponseSerializer(serializers.Serializer):
    """Response after successfully completing a test attempt."""

    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    answered_question_count = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    smart_analysis = serializers.CharField(allow_blank=True)
    message = serializers.CharField()
    # Include profile only if it was updated (level assessment)
    updated_profile = UserProfileSerializer(
        read_only=True, allow_null=True, required=False
    )
