from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.study.models import (
    UserTestAttempt,
    UserQuestionAttempt,
    TestDefinition,
    UserSkillProficiency,
    update_skill_proficiency_for_attempt,
)
from apps.learning.models import Question, LearningSection
from apps.users.models import UserProfile


# --- Serializers for Level Assessment ---


class LevelAssessmentStartRequestSerializer(serializers.Serializer):
    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSection.objects.all(),
            error_messages={
                "does_not_exist": _("Invalid section slug: {value}."),
                "invalid": _("Invalid section slug type."),
            },
        ),
        required=True,
        min_length=1,
        help_text=_("List of section slugs (e.g., ['verbal', 'quantitative'])"),
    )
    num_questions = serializers.IntegerField(
        required=False,
        default=30,
        min_value=5,  # Set a reasonable minimum
        max_value=100,  # Set a reasonable maximum
        help_text=_("Number of questions for the assessment (default: 30)"),
    )

    def validate_sections(self, value):
        if not value:
            raise serializers.ValidationError(
                _("At least one section must be selected.")
            )
        # You could add more validation, e.g., ensure 'verbal' and 'quantitative' are valid if needed
        return value


class QuestionForAssessmentSerializer(serializers.ModelSerializer):
    """
    Serializer for questions shown during an assessment/test.
    Excludes sensitive fields like correct_answer and explanation.
    Includes is_starred for potential UI elements.
    """

    subsection = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    skill = serializers.SlugRelatedField(
        slug_field="slug", read_only=True, allow_null=True
    )
    is_starred = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            "hint",
            "solution_method_summary",
            "difficulty",
            "subsection",
            "skill",
            "is_starred",
            # DO NOT INCLUDE: 'correct_answer', 'explanation'
        ]

    def get_is_starred(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.starred_by_users.filter(pk=user.pk).exists()
        return False


class LevelAssessmentSubmitAnswerSerializer(serializers.Serializer):
    """Serializer for a single answer within the submission payload."""

    question_id = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())
    selected_answer = serializers.ChoiceField(
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, default=0
    )


class LevelAssessmentSubmitRequestSerializer(serializers.Serializer):
    """Serializer for the entire submission payload."""

    answers = serializers.ListField(
        child=LevelAssessmentSubmitAnswerSerializer(), allow_empty=False
    )

    def validate(self, data):
        """
        Ensure the submission corresponds to the questions in the UserTestAttempt.
        """
        attempt = self.context.get("attempt")
        if not attempt:
            # This should be set in the view context
            raise serializers.ValidationError(
                _("Test attempt context is missing."), code="context_missing"
            )

        # Fetch questions associated with this attempt (more robust than just checking count)
        # This requires linking questions to the attempt, e.g., via UserQuestionAttempt creation stub, or storing question IDs in attempt.configuration
        # For now, let's assume the attempt knows its questions (e.g., stored in configuration['question_ids'])
        expected_question_ids = set(attempt.configuration.get("question_ids", []))
        submitted_question_ids = {
            answer["question_id"].id for answer in data["answers"]
        }

        if len(data["answers"]) != len(expected_question_ids):
            raise serializers.ValidationError(
                _("Incorrect number of answers submitted for this attempt."),
                code="answer_count_mismatch",
            )

        if submitted_question_ids != expected_question_ids:
            raise serializers.ValidationError(
                _("Submitted answers do not match the questions in this assessment."),
                code="question_mismatch",
            )

        # Check for duplicate answers
        if len(submitted_question_ids) != len(data["answers"]):
            raise serializers.ValidationError(
                _("Duplicate answers submitted for the same question."),
                code="duplicate_answer",
            )

        return data


# --- Serializer for the Result ---
class UserProfileLevelSerializer(serializers.ModelSerializer):
    """Minimal profile info showing updated levels."""

    class Meta:
        model = UserProfile
        fields = [
            "current_level_verbal",
            "current_level_quantitative",
            "level_determined",
        ]


class LevelAssessmentResultSerializer(serializers.ModelSerializer):
    """Serializer to show the results after submitting."""

    results = serializers.JSONField(source="results_summary", read_only=True)
    updated_profile = UserProfileLevelSerializer(
        source="user.userprofile", read_only=True
    )
    attempt_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = ["attempt_id", "results", "updated_profile"]
