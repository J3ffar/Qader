from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.study.models import EmergencyModeSession, UserQuestionAttempt, EmergencySupportRequest
from apps.learning.api.serializers import UnifiedQuestionSerializer  # Assumed location

# --- NEW: Nested Serializers for a Detailed Plan ---


class TargetSkillSerializer(serializers.Serializer):
    """Represents a target skill in the emergency plan."""

    slug = serializers.CharField()
    name = serializers.CharField()
    reason = serializers.CharField()
    current_proficiency = serializers.FloatField(allow_null=True)
    subsection_name = serializers.CharField()


class QuickReviewTopicSerializer(serializers.Serializer):
    """Represents a quick review topic in the emergency plan."""

    slug = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField(allow_null=True)


class SuggestedPlanSerializer(serializers.Serializer):
    """A detailed, structured representation of the generated emergency plan."""

    focus_area_names = serializers.ListField(child=serializers.CharField())
    estimated_duration_minutes = serializers.IntegerField(allow_null=True)
    recommended_question_count = serializers.IntegerField()
    target_skills = TargetSkillSerializer(many=True)
    quick_review_topics = QuickReviewTopicSerializer(many=True)
    motivational_tips = serializers.ListField(child=serializers.CharField())


# --- UPDATED: Response Serializer for Starting Emergency Mode ---


class EmergencyModeStartSerializer(serializers.Serializer):
    """Serializer for validating input when starting emergency mode."""

    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    available_time_hours = serializers.IntegerField(
        required=False, min_value=1, max_value=24, allow_null=True
    )
    focus_areas = serializers.ListField(
        child=serializers.ChoiceField(choices=["verbal", "quantitative"]),
        required=False,
        max_length=2,
    )


class EmergencyModeStartResponseSerializer(serializers.Serializer):
    """Serializer for the structured response after starting emergency mode."""

    session_id = serializers.IntegerField(read_only=True)
    suggested_plan = SuggestedPlanSerializer(read_only=True)


# --- UPDATED: Answer Serializer (simpler) ---


class EmergencyModeAnswerSerializer(serializers.Serializer):
    """
    Serializer for validating an answer submitted in an emergency session.
    The session_id is now sourced from the URL.
    """

    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )


# --- Session and Completion Serializers ---


class EmergencyModeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating calm mode status."""

    class Meta:
        model = EmergencyModeSession
        fields = ["calm_mode_active"]


class EmergencyModeSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for representing the Emergency Mode Session details.
    """

    user = serializers.StringRelatedField()
    suggested_plan = SuggestedPlanSerializer(read_only=True)

    class Meta:
        model = EmergencyModeSession
        fields = [
            "id",
            "user",
            "reason",
            "suggested_plan",
            "calm_mode_active",
            "start_time",
            "end_time",
            "overall_score",
            "verbal_score",
            "quantitative_score",
            "results_summary",
            "ai_feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EmergencyModeAnswerResponseSerializer(serializers.Serializer):
    """Serializer for the response after submitting an answer."""

    question_id = serializers.IntegerField()
    is_correct = serializers.BooleanField(allow_null=True)
    correct_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices
    )
    explanation = serializers.CharField(allow_blank=True, allow_null=True)
    feedback = serializers.CharField()  # Simple text feedback is enough for calm mode


class EmergencyModeCompleteResponseSerializer(serializers.Serializer):
    """
    Serializer for the detailed response after completing an emergency session.
    This provides the frontend with all necessary data for the results screen.
    """

    session_id = serializers.IntegerField()
    overall_score = serializers.FloatField()
    verbal_score = serializers.FloatField()
    quantitative_score = serializers.FloatField()
    results_summary = serializers.JSONField()
    ai_feedback = serializers.CharField()
    answered_question_count = serializers.IntegerField()
    correct_answers_count = serializers.IntegerField()


# <<< --- NEW SERIALIZER --- >>>
class EmergencySupportRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and validating a new EmergencySupportRequest.
    The `user` and `session` fields will be populated from the view context.
    """
    class Meta:
        model = EmergencySupportRequest
        fields = [
            "id",
            "problem_type",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]