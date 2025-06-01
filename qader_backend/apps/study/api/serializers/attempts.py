from typing import Dict, Optional, List
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt, Question
from apps.learning.api.serializers import (
    QuestionListSerializer,
)  # Assumes this is well-defined


logger = logging.getLogger(__name__)

# --- Unified Attempt Listing/Detail Serializers ---


class UserTestAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing user test attempts (all types)."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    date = serializers.DateTimeField(source="start_time", read_only=True)
    # Uses the model property which checks for annotation first
    num_questions = serializers.IntegerField(read_only=True)
    answered_question_count = serializers.IntegerField(read_only=True)
    performance = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "date",
            "status",  # Raw status enum value
            "status_display",  # User-friendly display name
            "num_questions",
            "answered_question_count",
            "score_percentage",  # Populated only if completed
            "performance",  # Detailed scores if completed
        ]
        read_only_fields = fields  # All fields are read-only in list view

    def get_performance(self, obj: UserTestAttempt) -> Optional[Dict[str, float]]:
        """Returns a dictionary of scores if the attempt is completed."""
        if obj.status != UserTestAttempt.Status.COMPLETED:
            return None

        perf = {}
        # Use round() for consistent display, assuming scores are calculated with precision
        if obj.score_percentage is not None:
            perf["overall"] = round(obj.score_percentage, 1)
        if obj.score_verbal is not None:
            perf["verbal"] = round(obj.score_verbal, 1)
        if obj.score_quantitative is not None:
            perf["quantitative"] = round(obj.score_quantitative, 1)
        return perf if perf else None  # Return None if no scores are set


class UserQuestionAttemptBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for representing an answered question within attempt details."""

    question_id = serializers.IntegerField(source="question.id", read_only=True)
    # Assuming Question model has 'question_text' or similar field
    question_text_preview = serializers.CharField(
        source="question.question_text", read_only=True
    )  # Example field

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "question_id",
            "question_text_preview",  # Provide some context
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
    # Use model properties which check for annotations first
    num_questions = serializers.IntegerField(read_only=True)
    answered_question_count = serializers.IntegerField(read_only=True)

    # Shows all questions included in the attempt (relies on view prefetching)
    included_questions = QuestionListSerializer(
        source="get_questions_queryset", many=True, read_only=True
    )

    # Shows questions already answered by the user (relies on view prefetching)
    attempted_questions = UserQuestionAttemptBriefSerializer(
        source="question_attempts", many=True, read_only=True
    )

    results_summary = serializers.JSONField(
        read_only=True
    )  # Populated only if COMPLETED
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
        """Extracts a display name from the configuration snapshot, handling different structures."""
        config = obj.test_configuration or {}
        name = _("Unnamed Test")  # Default

        # Try practice/simulation structure first
        if isinstance(config.get("config"), dict):
            name = config["config"].get("name", name)
        # Try level assessment/traditional structure
        elif isinstance(config, dict):
            # Try common keys used in different start serializers
            name = config.get("name") or config.get("test_name") or name

        return name


# --- Unified Action/Response Serializers ---


class UserTestAttemptStartResponseSerializer(serializers.Serializer):
    """Standard response structure after successfully starting any type of test attempt."""

    attempt_id = serializers.IntegerField(read_only=True)
    attempt_number_for_type = serializers.IntegerField(
        read_only=True,  # Calculated in the service/view
        help_text=_(
            "The sequence number of this attempt for this specific test type (e.g., 1st Level Assessment, 3rd Practice Test)."
        ),
    )
    questions = QuestionListSerializer(many=True, read_only=True)


class UserQuestionAttemptSerializer(serializers.Serializer):
    """Serializer for submitting a single answer during ANY ongoing test attempt."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(
            is_active=True
        ),  # Basic validation: exists and active
        required=True,
        help_text=_("Primary key of the question being answered."),
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices,
        required=True,
        allow_blank=False,  # Must select an answer
        help_text=_("The answer choice selected by the user (A, B, C, or D)."),
    )
    time_taken_seconds = serializers.IntegerField(
        required=False,
        min_value=0,
        allow_null=True,
        help_text=_("Optional: Time spent on this specific question in seconds."),
    )

    def validate_question_id(self, value: Question):
        return value


class UserQuestionAttemptResponseSerializer(serializers.Serializer):
    """Standard response after submitting a single answer."""

    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(
        read_only=True, allow_null=True, required=False
    )
    explanation = serializers.CharField(read_only=True, allow_null=True, required=False)
    feedback_message = serializers.CharField(read_only=True, required=False)


class ScoreSerializer(serializers.Serializer):
    """Serializer for nested score object."""

    overall = serializers.FloatField(allow_null=True, required=False)
    verbal = serializers.FloatField(allow_null=True, required=False)
    quantitative = serializers.FloatField(allow_null=True, required=False)


class BadgeWonSerializer(serializers.Serializer):
    slug = serializers.SlugField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)


class StreakInfoSerializer(serializers.Serializer):
    updated = serializers.BooleanField(read_only=True)
    current_days = serializers.IntegerField(read_only=True)


class UserTestAttemptCompletionResponseSerializer(serializers.Serializer):
    """
    Standard response after successfully completing a non-Traditional test attempt
    (Practice, Simulation, Level Assessment).
    """

    attempt_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    score = ScoreSerializer(read_only=True, allow_null=True, required=False)
    results_summary = serializers.JSONField(required=False, read_only=True)
    answered_question_count = serializers.IntegerField(read_only=True)
    total_questions = serializers.IntegerField(read_only=True)
    correct_answers_in_test_count = serializers.IntegerField(
        read_only=True,
        default=0,
        help_text=_("Number of questions answered correctly in this test."),
    )
    smart_analysis = serializers.CharField(
        allow_blank=True, allow_null=True, required=False, read_only=True
    )
    points_from_test_completion_event = serializers.IntegerField(
        read_only=True,
        default=0,
        help_text=_(
            "Points earned from completing the test, streak bonuses, and badges awarded at completion."
        ),
    )
    points_from_correct_answers_this_test = serializers.IntegerField(
        read_only=True,
        default=0,
        help_text=_(
            "Points earned from correctly answering questions during this specific test attempt."
        ),
    )
    badges_won = BadgeWonSerializer(many=True, read_only=True, default=list)
    streak_info = StreakInfoSerializer(read_only=True, required=False)

    def create(self, validated_data):
        raise NotImplementedError("This serializer cannot create data.")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer cannot update data.")


# --- Review Serializers ---
class UserTestAttemptReviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for a single question within the review context of a completed attempt."""

    question_id = serializers.IntegerField(source="id", read_only=True)
    question_text = serializers.CharField(read_only=True)
    options = serializers.SerializerMethodField()
    correct_answer_choice = serializers.CharField(
        source="correct_answer", read_only=True
    )  # e.g., 'A'
    explanation = serializers.CharField(read_only=True, allow_null=True)
    subsection_name = serializers.CharField(
        source="subsection.name", read_only=True, allow_null=True
    )
    skill_name = serializers.CharField(
        source="skill.name", read_only=True, allow_null=True
    )

    user_selected_choice = serializers.SerializerMethodField()  # e.g., 'B' or None
    user_is_correct = serializers.SerializerMethodField()
    used_hint = serializers.SerializerMethodField()
    used_elimination = serializers.SerializerMethodField()
    revealed_answer = serializers.SerializerMethodField()
    revealed_explanation = serializers.SerializerMethodField()

    class Meta:
        model = Question  # Make sure Question is imported from apps.learning.models
        fields = [
            "question_id",
            "question_text",
            "options",  # This will be a dict {"A": "text a", "B": "text b", ...}
            "user_selected_choice",  # The letter 'A', 'B', 'C', or 'D' the user picked
            "correct_answer_choice",  # The correct letter 'A', 'B', 'C', or 'D'
            "user_is_correct",
            "explanation",
            "subsection_name",
            "skill_name",
            "used_hint",
            "used_elimination",
            "revealed_answer",
            "revealed_explanation",
        ]
        read_only_fields = fields

    def get_options(self, obj: Question) -> Dict[str, str]:
        """Constructs a dictionary of all answer options for the question."""
        return {
            "A": obj.option_a,
            "B": obj.option_b,
            "C": obj.option_c,
            "D": obj.option_d,
        }

    def _get_user_attempt_from_context(
        self, obj: Question  # obj is the Question instance
    ) -> Optional[UserQuestionAttempt]:
        """Helper to safely get the specific UserQuestionAttempt for this question from context."""
        user_attempts_map = self.context.get("user_attempts_map", {})
        # The key in user_attempts_map is the question_id
        return user_attempts_map.get(obj.id)

    def get_user_selected_choice(self, obj: Question) -> Optional[str]:
        """Gets the user's selected answer choice (e.g., 'A', 'B') for this question."""
        user_attempt = self._get_user_attempt_from_context(obj)
        # user_attempt is an instance of UserQuestionAttempt
        # selected_answer on UserQuestionAttempt stores 'A', 'B', etc.
        return user_attempt.selected_answer if user_attempt else None

    def get_user_is_correct(self, obj: Question) -> Optional[bool]:
        """Gets whether the user's answer was correct from context."""
        user_attempt = self._get_user_attempt_from_context(obj)
        return (
            user_attempt.is_correct
            if user_attempt and user_attempt.selected_answer is not None
            else None  # If not answered, correctness is None
        )

    def get_used_hint(self, obj: Question) -> Optional[bool]:
        user_attempt = self._get_user_attempt_from_context(obj)
        return (
            user_attempt.used_hint if user_attempt else None
        )  # Default to None if no attempt

    def get_used_elimination(self, obj: Question) -> Optional[bool]:
        user_attempt = self._get_user_attempt_from_context(obj)
        return user_attempt.used_elimination if user_attempt else None

    def get_revealed_answer(self, obj: Question) -> Optional[bool]:
        user_attempt = self._get_user_attempt_from_context(obj)
        return user_attempt.revealed_answer if user_attempt else None

    def get_revealed_explanation(self, obj: Question) -> Optional[bool]:
        user_attempt = self._get_user_attempt_from_context(obj)
        return user_attempt.revealed_explanation if user_attempt else None


class UserTestAttemptReviewSerializer(serializers.Serializer):
    """Serializer for the overall test review response."""

    attempt_id = serializers.IntegerField(read_only=True)
    questions = UserTestAttemptReviewQuestionSerializer(many=True, read_only=True)

    # These fields will source data from the 'attempt' object passed in the instance data
    score_percentage = serializers.FloatField(
        source="attempt.score_percentage", read_only=True, allow_null=True
    )
    score_verbal = serializers.FloatField(
        source="attempt.score_verbal", read_only=True, allow_null=True
    )
    score_quantitative = serializers.FloatField(
        source="attempt.score_quantitative", read_only=True, allow_null=True
    )
    results_summary = serializers.JSONField(
        source="attempt.results_summary",
        read_only=True,
        allow_null=True,  # Allow null if not present
    )

    def create(self, validated_data):
        raise NotImplementedError("This serializer cannot create data.")

    def update(self, instance, validated_data):
        raise NotImplementedError("This serializer cannot update data.")
