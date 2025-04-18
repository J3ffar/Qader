from rest_framework import serializers
from apps.learning.models import Question
from apps.learning.api.serializers import (
    LearningSubSectionSerializer,  # Used in review serializer
    SkillSerializer,  # Used in review serializer
)

# --- Test Review Serializers ---


class TestReviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions within the test review response."""

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
            "hint",
            "user_selected_answer",
            "is_correct",
            "subsection",
            "skill",
            "difficulty",
        ]

    def get_user_selected_answer(self, obj):
        # Expects 'user_attempts_map' in context: {question_id: UserQuestionAttempt}
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.selected_answer if user_attempt else None

    def get_is_correct(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.is_correct if user_attempt else None


class TestReviewSerializer(serializers.Serializer):
    """Response serializer for the test review endpoint."""

    attempt_id = serializers.IntegerField()
    review_questions = TestReviewQuestionSerializer(many=True)  # Context passed by view
