from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from apps.study.models import EmergencyModeSession, UserQuestionAttempt

# --- Serializer for Starting Emergency Mode ---


class EmergencyModeStartSerializer(serializers.Serializer):
    """Serializer for validating input when starting emergency mode."""

    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)
    available_time_hours = serializers.IntegerField(
        required=False, min_value=1, max_value=24
    )
    focus_areas = serializers.ListField(
        child=serializers.ChoiceField(choices=["verbal", "quantitative"]),
        required=False,
        max_length=2,
    )


class EmergencyModeStartResponseSerializer(serializers.Serializer):
    """Serializer for the response after starting emergency mode."""

    session_id = serializers.IntegerField()
    suggested_plan = (
        serializers.JSONField()
    )  # Contains focus_skills, recommended_questions, quick_review_topics


# --- Serializer for Updating Emergency Mode Session ---


class EmergencyModeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating calm mode or sharing status."""

    class Meta:
        model = EmergencyModeSession
        fields = ["calm_mode_active", "shared_with_admin"]


class EmergencyModeSessionSerializer(serializers.ModelSerializer):
    """Serializer for representing the Emergency Mode Session details."""

    user = serializers.StringRelatedField()  # Or a nested User serializer

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
            "shared_with_admin",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "reason",
            "suggested_plan",
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ]


# --- Serializer for Answering Questions in Emergency Mode ---


class EmergencyModeAnswerSerializer(serializers.Serializer):
    """Serializer for validating an answer submitted in emergency mode."""

    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    session_id = serializers.IntegerField(required=True)  # To verify context


class EmergencyModeAnswerResponseSerializer(serializers.Serializer):
    """Serializer for the response after submitting an answer."""

    question_id = serializers.IntegerField()
    is_correct = serializers.BooleanField(allow_null=True)  # Null if couldn't determine
    correct_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices
    )
    explanation = serializers.CharField(allow_blank=True, allow_null=True)
    points_earned = serializers.IntegerField(default=0)  # Typically 0 in emergency mode
    feedback = serializers.JSONField()
