from rest_framework import serializers
from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "slug", "description"]


class LearningSubSectionSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(
        many=True, read_only=True
    )  # Optionally include nested skills

    class Meta:
        model = LearningSubSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "skills",
        ]  # Add 'skills' if needed


class LearningSectionSerializer(serializers.ModelSerializer):
    subsections = LearningSubSectionSerializer(
        many=True, read_only=True
    )  # Optionally include nested subsections

    class Meta:
        model = LearningSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "subsections",
        ]  # Add 'subsections' if needed


# --- Question Serializers ---


class QuestionListSerializer(serializers.ModelSerializer):
    """Serializer for listing questions (excludes answers/explanations)."""

    # Use simple subsection/skill representation for lists
    subsection = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    skill = serializers.SlugRelatedField(slug_field="slug", read_only=True)
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
            "hint",  # Include hint for traditional/emergency modes
            "solution_method_summary",  # Include summary for traditional/emergency
            "difficulty",
            "subsection",
            "skill",
            "is_starred",
        ]
        read_only_fields = fields  # Make all fields read-only for this list view

    def get_is_starred(self, obj):
        """Check if the current user has starred this question."""
        user = self.context.get("request").user
        if user and user.is_authenticated:
            # Efficient check using the reverse relationship defined in models
            return obj.starred_by.filter(pk=user.pk).exists()
            # Alternative (slightly less efficient if not prefeched/annotated):
            # return UserStarredQuestion.objects.filter(user=user, question=obj).exists()
        return False


class QuestionDetailSerializer(QuestionListSerializer):
    """Serializer for retrieving a single question (includes answers/explanations)."""

    # Inherits 'is_starred' and other fields from QuestionListSerializer
    # Use nested serializers for richer subsection/skill info on detail view
    subsection = LearningSubSectionSerializer(read_only=True)
    skill = SkillSerializer(read_only=True)

    class Meta(QuestionListSerializer.Meta):
        # Extend fields from the base class
        fields = QuestionListSerializer.Meta.fields + [
            "correct_answer",
            "explanation",
        ]
        read_only_fields = fields  # Make all fields read-only


# Simple serializer for the star/unstar action if needed
class UserStarredQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStarredQuestion
        fields = ["user", "question", "starred_at"]
