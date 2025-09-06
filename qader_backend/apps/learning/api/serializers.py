from rest_framework import serializers
from typing import TYPE_CHECKING, Dict, Any, Optional

from ..models import (
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
    MediaFile,  # NEW
    Article,  # NEW
    Question,
    UserStarredQuestion,
)

if TYPE_CHECKING:
    from apps.study.models import UserQuestionAttempt


# --- NEW: Test Type Serializer ---


class TestTypeSerializer(serializers.ModelSerializer):
    """Serializer for the TestType model."""

    class Meta:
        model = TestType
        fields = ["id", "name", "slug", "description", "status", "order"]


# --- Learning Structure Serializers (Updated) ---


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model (basic details)."""

    # ADDED: To show the direct parent section
    section_id = serializers.IntegerField(source="section.id", read_only=True)

    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description", "section_id"]  # MODIFIED
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


class LearningSectionBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for LearningSection (ID, Name, Slug)."""

    class Meta:
        model = LearningSection
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class TestTypeBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for TestType."""

    class Meta:
        model = TestType
        fields = ["id", "name", "slug"]
        read_only_fields = fields


class LearningSectionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSection, including nested subsections and parent test type."""

    subsections = LearningSubSectionSerializer(many=True, read_only=True)
    # ADDED: Nest parent TestType info
    test_type = TestTypeBasicSerializer(read_only=True)

    class Meta:
        model = LearningSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "test_type",
            "subsections",
        ]  # MODIFIED
        read_only_fields = fields


# --- NEW: Serializers for Content Libraries ---


class MediaFileSerializer(serializers.ModelSerializer):
    """Read-only serializer for MediaFile objects."""

    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = MediaFile
        fields = ["id", "title", "file_url", "file_type"]


class ArticleSerializer(serializers.ModelSerializer):
    """Read-only serializer for Article objects."""

    class Meta:
        model = Article
        fields = ["id", "title", "content"]


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


# --- MODIFIED: UnifiedQuestionSerializer ---


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

    section = LearningSectionBasicSerializer(
        source="subsection.section", read_only=True
    )

    # Use nested serializers for rich, consistent data
    subsection = LearningSubSectionSerializer(read_only=True)
    # MODIFIED: From single object to a list
    skills = SkillSerializer(many=True, read_only=True)

    # Reformat options into a more frontend-friendly dictionary
    options = serializers.SerializerMethodField()

    # User-specific flag, populated by queryset annotation for efficiency
    is_starred = serializers.BooleanField(
        source="user_has_starred", read_only=True, default=False
    )
    user_answer_details = serializers.SerializerMethodField()

    # NEW: Nested serializers for reusable content
    media_content = MediaFileSerializer(read_only=True)
    article = ArticleSerializer(read_only=True)

    class Meta:
        model = Question
        fields = [
            # Core Identification & Content
            "id",
            "question_text",
            "media_content",  # REPLACES image, audio_url
            "article",  # REPLACES old article field
            "options",
            "difficulty",
            "hint",
            "solution_method_summary",
            # Detailed/Sensitive Information
            "correct_answer",
            "explanation",
            # Relational Context
            "section",
            "subsection",
            "skills",  # MODIFIED: was "skill"
            # User-Specific Context
            "is_starred",
            "user_answer_details",
        ]
        read_only_fields = fields

    def get_options(self, obj: Question) -> Dict[str, str]:
        return {
            "A": obj.option_a,
            "B": obj.option_b,
            "C": obj.option_c,
            "D": obj.option_d,
        }

    def _get_user_attempt_from_context(
        self, obj: Question
    ) -> Optional["UserQuestionAttempt"]:
        user_attempts_map = self.context.get("user_attempts_map", {})
        return user_attempts_map.get(obj.id)

    def get_user_answer_details(self, obj: Question) -> Optional[Dict[str, Any]]:
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
        ret = super().to_representation(instance)
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
