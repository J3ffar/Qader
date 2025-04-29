from typing import Dict, Optional
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt, Question
from apps.learning.api.serializers import QuestionListSerializer
from apps.users.api.serializers import (
    UserProfileSerializer,
)  # Needed for level assessment completion


logger = logging.getLogger(__name__)

# --- Unified Attempt Serializers ---


class UserTestAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing user test attempts (all types)."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    # Uses the annotated/calculated property from the model/view
    answered_question_count = serializers.IntegerField(read_only=True)
    performance = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "date",
            "status",  # Raw status
            "status_display",  # User-friendly status
            "num_questions",
            "answered_question_count",
            "score_percentage",  # Populated only if completed
            "performance",
        ]
        read_only_fields = fields

    def get_performance(self, obj: UserTestAttempt) -> Optional[Dict[str, float]]:
        """Returns a dictionary of scores if the attempt is completed."""
        if obj.status != UserTestAttempt.Status.COMPLETED:
            return None

        perf = {}
        if obj.score_percentage is not None:
            perf["overall"] = round(obj.score_percentage, 1)
        if obj.score_verbal is not None:
            perf["verbal"] = round(obj.score_verbal, 1)
        if obj.score_quantitative is not None:
            perf["quantitative"] = round(obj.score_quantitative, 1)
        return perf if perf else None


class UserQuestionAttemptBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for representing an answered question within attempt details."""

    question_id = serializers.IntegerField(source="question.id", read_only=True)
    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "question_id",
            "question_text",
            "selected_answer",
            "is_correct",
            "attempted_at",
        ]
        read_only_fields = fields


class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving detailed information about a specific test attempt."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    config_name = serializers.SerializerMethodField(read_only=True)
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    # Uses the annotated/calculated property from the model/view
    answered_question_count = serializers.IntegerField(read_only=True)
    # Shows all questions included in the attempt (useful for FE rendering)
    included_questions = QuestionListSerializer(
        source="get_questions_queryset", many=True, read_only=True
    )
    # Shows questions already answered by the user (for ongoing tests or review)
    # Uses prefetch_related('question_attempts', 'question_attempts__question') in view
    attempted_questions = UserQuestionAttemptBriefSerializer(
        source="question_attempts", many=True, read_only=True
    )
    # Populated only if COMPLETED
    results_summary = serializers.JSONField(read_only=True)
    configuration_snapshot = serializers.JSONField(
        source="test_configuration", read_only=True
    )

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "status",  # Raw status
            "status_display",  # User-friendly status
            "config_name",  # Extracted from configuration snapshot
            "date",  # Alias for start_time
            "start_time",
            "end_time",
            "num_questions",
            "answered_question_count",
            "score_percentage",  # Populated if completed
            "score_verbal",  # Populated if completed
            "score_quantitative",  # Populated if completed
            "included_questions",
            "attempted_questions",
            "results_summary",  # Populated if completed
            "configuration_snapshot",  # The raw config JSON used
        ]
        read_only_fields = fields

    def get_config_name(self, obj: UserTestAttempt) -> str:
        """Extracts a display name from the configuration snapshot."""
        config = obj.test_configuration or {}
        # Handle nested structure from Practice/Simulation tests
        if isinstance(config.get("config"), dict):
            name = config["config"].get("name")
        else:
            # Handle potentially flat structure (e.g., older Level Assessment?)
            name = config.get("name")

        return name or _("Unnamed Test")


class UserTestAttemptStartResponseSerializer(serializers.Serializer):
    """Standard response after starting any type of test attempt."""

    attempt_id = serializers.IntegerField(read_only=True)
    attempt_number_for_type = serializers.IntegerField(
        read_only=True,
        help_text=_(
            "The sequence number of this attempt for this specific test type (e.g., 1st Level Assessment, 3rd Practice Test)."
        ),
    )
    questions = QuestionListSerializer(many=True, read_only=True)


class UserQuestionAttemptSerializer(serializers.Serializer):
    """Serializer for submitting a single answer during ANY ongoing test attempt."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(is_active=True),  # Basic validation
        required=True,
        help_text=_("Primary key of the question being answered."),
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices,
        required=True,
        help_text=_("The answer choice selected by the user (A, B, C, or D)."),
    )
    time_taken_seconds = serializers.IntegerField(
        required=False,
        min_value=0,
        allow_null=True,
        help_text=_("Optional: Time spent on this specific question in seconds."),
    )
    # Add other flags if needed (e.g., hints used)
    # used_hint = serializers.BooleanField(default=False, required=False)
    # used_elimination = serializers.BooleanField(default=False, required=False)

    def validate_question_id(self, value: Question):
        """View/Service layer handles validation against the specific test attempt."""
        # PrimaryKeyRelatedField already validates existence and active status.
        return value

    def validate_selected_answer(self, value: str):
        """Ensures the selected answer is a valid choice."""
        # ChoiceField handles validation against choices. This is redundant but safe.
        if value not in UserQuestionAttempt.AnswerChoice.values:
            raise serializers.ValidationError(_("Invalid answer choice."))
        return value


class UserQuestionAttemptResponseSerializer(serializers.Serializer):
    """Standard response after submitting a single answer."""

    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    # Correct answer/explanation only revealed based on mode (handled by service)
    correct_answer = serializers.CharField(read_only=True, allow_null=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    feedback_message = serializers.CharField(read_only=True)


class UserTestAttemptCompletionResponseSerializer(serializers.Serializer):
    """Standard response after successfully completing a test attempt (Practice, Sim, Level Assessment)."""

    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    answered_question_count = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    smart_analysis = serializers.CharField(allow_blank=True, allow_null=True)
    message = serializers.CharField()
    # Include profile only if it was updated (level assessment - populated by service)
    updated_profile = UserProfileSerializer(
        read_only=True, allow_null=True, required=False
    )


# --- Review Serializers ---


class UserTestAttemptReviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for a single question within the review context."""

    user_answer = serializers.SerializerMethodField()
    user_is_correct = serializers.SerializerMethodField()
    # Basic question details from QuestionListSerializer can be inherited or duplicated
    question_id = serializers.IntegerField(source="id", read_only=True)
    question_text = serializers.CharField(read_only=True)
    choices = serializers.JSONField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    subsection_name = serializers.CharField(
        source="subsection.name", read_only=True, allow_null=True
    )
    skill_name = serializers.CharField(
        source="skill.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Question
        fields = [
            "question_id",
            "question_text",
            "choices",
            "user_answer",  # Added
            "correct_answer",
            "user_is_correct",  # Added
            "explanation",
            "subsection_name",
            "skill_name",
        ]
        read_only_fields = fields

    def get_user_answer(self, obj: Question) -> Optional[str]:
        """Gets the user's selected answer for this question from context."""
        user_attempts_map = self.context.get("user_attempts_map", {})
        user_attempt = user_attempts_map.get(obj.id)
        return user_attempt.selected_answer if user_attempt else None

    def get_user_is_correct(self, obj: Question) -> Optional[bool]:
        """Gets whether the user's answer was correct from context."""
        user_attempts_map = self.context.get("user_attempts_map", {})
        user_attempt = user_attempts_map.get(obj.id)
        # Return None if the user didn't answer this question in the attempt
        return (
            user_attempt.is_correct
            if user_attempt and user_attempt.selected_answer is not None
            else None
        )


class UserTestAttemptReviewSerializer(serializers.Serializer):
    """Serializer for the overall test review response."""

    attempt_id = serializers.IntegerField(read_only=True)
    # Field name changed from 'review_questions' to match context data key
    questions = UserTestAttemptReviewQuestionSerializer(many=True, read_only=True)
    # Optionally include overall summary data again if needed
    # score_percentage = serializers.FloatField(source="attempt.score_percentage", read_only=True, allow_null=True)
    # ... other summary fields ...

    def create(self, validated_data):
        # This serializer is read-only, used for response structuring.
        raise NotImplementedError("This serializer cannot be used to create data.")

    def update(self, instance, validated_data):
        # This serializer is read-only, used for response structuring.
        raise NotImplementedError("This serializer cannot be used to update data.")
