from rest_framework import serializers
from typing import TYPE_CHECKING, Dict, Any, Optional

from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)

if TYPE_CHECKING:
    from apps.study.models import UserQuestionAttempt


# --- Learning Structure Serializers ---


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model (basic details)."""

    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description"]
        read_only_fields = fields


class LearningSubSectionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSubSection, optionally including nested skills."""

    class Meta:
        model = LearningSubSection
        fields = ["id", "name", "slug", "description", "order", "is_active"]
        read_only_fields = fields


class LearningSubSectionDetailSerializer(LearningSubSectionSerializer):
    """Serializer for LearningSubSection detail view, including nested skills."""

    skills = SkillSerializer(many=True, read_only=True)

    class Meta(LearningSubSectionSerializer.Meta):
        fields = LearningSubSectionSerializer.Meta.fields + ["skills"]
        read_only_fields = fields


class LearningSectionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSection, including nested subsections."""

    subsections = LearningSubSectionSerializer(many=True, read_only=True)

    class Meta:
        model = LearningSection
        fields = ["id", "name", "slug", "description", "order", "subsections"]
        read_only_fields = fields


class LearningSectionBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for LearningSection (ID, Name, Slug)."""

    class Meta:
        model = LearningSection
        fields = ["id", "name", "slug"]
        read_only_fields = fields


# --- Unified Question Serializer ---


class UserAnswerDetailsSerializer(serializers.Serializer):
    """
    A nested serializer to encapsulate user's attempt-specific details for a question.
    This is not a ModelSerializer and is populated from context.
    """

    selected_choice = serializers.CharField(allow_null=True, read_only=True)
    is_correct = serializers.BooleanField(allow_null=True, read_only=True)
    used_hint = serializers.BooleanField(allow_null=True, read_only=True)
    used_elimination = serializers.BooleanField(allow_null=True, read_only=True)
    revealed_answer = serializers.BooleanField(allow_null=True, read_only=True)
    revealed_explanation = serializers.BooleanField(allow_null=True, read_only=True)


class UnifiedQuestionSerializer(serializers.ModelSerializer):
    """
    A single, unified serializer for the Question model to ensure a consistent
    structure across all API responses.

    It provides:
    - Core question data (text, options, difficulty).
    - Full details (correct answer, explanation) for detail/review views.
    - Rich context via nested subsection and skill objects.
    - Context-aware fields for user-specific data like 'is_starred' and 'user_answer_details'.

    To use context-aware fields, the view must provide context:
    - `is_starred`: Relies on a `user_has_starred` annotation from the queryset.
    - `user_answer_details`: Relies on a `user_attempts_map` in the serializer context,
      which maps question IDs to `UserQuestionAttempt` objects.
      e.g., context={'user_attempts_map': {101: uqa_obj_1, 102: uqa_obj_2}}
    """

    # Use nested serializers for rich, consistent data
    subsection = LearningSubSectionSerializer(read_only=True)
    skill = SkillSerializer(read_only=True, required=False)

    # Reformat options into a more frontend-friendly dictionary
    options = serializers.SerializerMethodField()

    # User-specific flag, populated by queryset annotation for efficiency
    is_starred = serializers.BooleanField(
        source="user_has_starred", read_only=True, default=False
    )

    # User's answer details for this question in a specific test attempt context
    user_answer_details = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            # Core Identification & Content
            "id",
            "question_text",
            "options",  # Frontend-friendly dict of options
            "difficulty",
            "hint",
            "solution_method_summary",
            # Detailed/Sensitive Information (for detail/review views)
            "correct_answer",  # The choice key, e.g., "A"
            "explanation",
            # Relational Context
            "subsection",
            "skill",
            # User-Specific Context
            "is_starred",
            "user_answer_details",  # Contains selected_choice, is_correct, etc.
        ]
        read_only_fields = fields

    def get_options(self, obj: Question) -> Dict[str, str]:
        """Constructs a dictionary of all answer options."""
        return {
            "A": obj.option_a,
            "B": obj.option_b,
            "C": obj.option_c,
            "D": obj.option_d,
        }

    def _get_user_attempt_from_context(
        self, obj: Question
    ) -> Optional["UserQuestionAttempt"]:
        """Helper to safely get the specific UserQuestionAttempt for this question from context."""
        user_attempts_map = self.context.get("user_attempts_map", {})
        return user_attempts_map.get(obj.id)

    def get_user_answer_details(self, obj: Question) -> Optional[Dict[str, Any]]:
        """
        Populates the user's answer details from the context.
        Returns None if no attempt context is provided.
        """
        user_attempt = self._get_user_attempt_from_context(obj)
        if not user_attempt:
            return None

        details_data = {
            "selected_choice": user_attempt.selected_answer,
            "is_correct": (
                user_attempt.is_correct
                if user_attempt.selected_answer is not None
                else None
            ),
            "used_hint": user_attempt.used_hint,
            "used_elimination": user_attempt.used_elimination,
            "revealed_answer": user_attempt.revealed_answer,
            "revealed_explanation": user_attempt.revealed_explanation,
        }
        serializer = UserAnswerDetailsSerializer(instance=details_data)
        return serializer.data

    def to_representation(self, instance: Question) -> Dict[str, Any]:
        """Ensure default=False for is_starred if annotation is missing."""
        ret = super().to_representation(instance)
        # The 'source' attribute handles this, but as a fallback, ensure the key exists.
        ret.setdefault("is_starred", getattr(instance, "user_has_starred", False))
        return ret


# --- Star/Unstar Action Serializer ---


class StarActionSerializer(serializers.Serializer):
    """Minimal serializer for documenting the star/unstar response."""

    status = serializers.ChoiceField(
        choices=["starred", "unstarred", "already starred", "not starred"]
    )

    class Meta:
        fields = ["status"]
