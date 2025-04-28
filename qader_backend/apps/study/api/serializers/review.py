from rest_framework import serializers
from apps.learning.models import Question
from apps.study.models import UserTestAttempt  # Import UserTestAttempt
from apps.learning.api.serializers import (
    LearningSubSectionSerializer,
    SkillSerializer,
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
            "user_selected_answer",  # Already here
            "is_correct",  # Already here
            "subsection",
            "skill",
            "difficulty",
        ]

    def get_user_selected_answer(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.selected_answer if user_attempt else None

    def get_is_correct(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        # Return explicit True/False, or None if somehow not answered in completed test
        return user_attempt.is_correct if user_attempt else None


class TestReviewSerializer(serializers.Serializer):
    """Response serializer for the test review endpoint."""

    attempt_id = serializers.IntegerField()
    # Optional: Add summary fields from the UserTestAttempt if needed
    # score_percentage = serializers.FloatField(source='attempt.score_percentage', read_only=True)
    review_questions = TestReviewQuestionSerializer(many=True)

    # If you need to pass the attempt object itself for summary fields:
    # def __init__(self, instance=None, **kwargs):
    #     # instance expected to be {'attempt': UserTestAttempt, 'review_questions': QuerySet}
    #     self.attempt = instance.get('attempt') if instance else None
    #     review_questions = instance.get('review_questions') if instance else None
    #     super().__init__(instance={'attempt_id': self.attempt.id if self.attempt else None, 'review_questions': review_questions}, **kwargs)
