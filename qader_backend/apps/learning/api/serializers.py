from rest_framework import serializers
from typing import TYPE_CHECKING, Dict, Any

from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)

# --- Learning Structure Serializers ---


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model (basic details)."""

    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description"]
        read_only_fields = fields


class LearningSubSectionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSubSection, optionally including nested skills."""

    # Optionally include nested skills - keep this lean for lists if not always needed
    # skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = LearningSubSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            # "skills",  # Uncomment if nested skills are desired in Subsection list/detail views
        ]
        read_only_fields = fields


class LearningSubSectionDetailSerializer(LearningSubSectionSerializer):
    """
    Serializer for LearningSubSection detail view, including nested skills.
    """

    skills = SkillSerializer(many=True, read_only=True)  # Include skills here

    class Meta(LearningSubSectionSerializer.Meta):
        # Inherit fields and add 'skills'
        fields = LearningSubSectionSerializer.Meta.fields + ["skills"]
        read_only_fields = fields


class LearningSectionSerializer(serializers.ModelSerializer):
    """Serializer for LearningSection, optionally including nested subsections."""

    # Optionally include nested subsections - keep this lean for lists if not always needed
    subsections = LearningSubSectionSerializer(many=True, read_only=True)

    class Meta:
        model = LearningSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "subsections",  # Uncomment if nested subsections are desired in Section list/detail views
        ]
        read_only_fields = fields


class LearningSectionBasicSerializer(serializers.ModelSerializer):
    """Basic serializer for LearningSection (ID, Name, Slug)."""

    class Meta:
        model = LearningSection
        fields = ["id", "name", "slug"]
        read_only_fields = fields


# --- Question Serializers ---


class QuestionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Questions. Excludes sensitive information like
    correct answers and full explanations. Optimized for list views.
    """

    # Use SlugRelatedField for performance in lists
    subsection = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    skill = serializers.SlugRelatedField(
        slug_field="slug", read_only=True, required=False  # Skill is nullable
    )
    # Use the 'user_has_starred' annotation added in the ViewSet's get_queryset method
    # This is more efficient than calculating it per-object in the serializer.
    is_starred = serializers.BooleanField(
        source="user_has_starred", read_only=True, default=False
    )

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
            "subsection",  # slug
            "skill",  # slug
            "is_starred",
        ]
        # Ensure all fields are read-only as this is for listing
        read_only_fields = fields

    def to_representation(self, instance: Question) -> Dict[str, Any]:
        """Ensure default=False for is_starred if annotation is missing (e.g., anonymous user)."""
        ret = super().to_representation(instance)
        # Ensure is_starred is present and boolean, defaulting to False
        ret["is_starred"] = getattr(instance, "user_has_starred", False)
        return ret


class QuestionDetailSerializer(QuestionListSerializer):
    """
    Serializer for retrieving a single Question. Includes all details,
    including the correct answer and full explanation. Uses nested serializers
    for related subsection and skill for richer context.
    """

    # Override related fields to use nested serializers for detail view
    subsection = LearningSubSectionSerializer(read_only=True)
    skill = SkillSerializer(read_only=True, required=False)  # Skill is nullable

    class Meta(QuestionListSerializer.Meta):
        # Inherit fields from list serializer and add detail-specific fields
        fields = QuestionListSerializer.Meta.fields + [
            "correct_answer",
            "explanation",
            # Ensure related fields are included if overridden
            "subsection",
            "skill",
        ]
        # Ensure all fields are read-only
        read_only_fields = fields


# --- Star/Unstar Action Serializer (Minimal) ---


class StarActionSerializer(serializers.Serializer):
    """Minimal serializer for documenting the star/unstar response."""

    status = serializers.ChoiceField(
        choices=["starred", "unstarred", "already starred", "not starred"]
    )

    class Meta:
        fields = ["status"]


# Note: UserStarredQuestionSerializer might be useful for admin views, but not needed for basic user star/unstar actions.
