# qader_backend/apps/admin_panel/api/serializers/learning_management.py

from rest_framework import serializers
from apps.learning.models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
)


class AdminLearningSectionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on LearningSection."""

    class Meta:
        model = LearningSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "created_at",
            "updated_at",
        ]
        # Slug is auto-generated if blank, but allow admin override
        read_only_fields = ["id", "created_at", "updated_at"]


class AdminSkillSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on Skill."""

    # Represent related subsection by its ID for writes, include name for reads.
    subsection_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSubSection.objects.all(), source="subsection", write_only=True
    )
    subsection_name = serializers.CharField(source="subsection.name", read_only=True)
    subsection_slug = serializers.CharField(source="subsection.slug", read_only=True)

    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "subsection_id",  # Write
            "subsection_name",  # Read
            "subsection_slug",  # Read
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subsection_name",
            "subsection_slug",
        ]


class AdminLearningSubSectionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on LearningSubSection."""

    # Represent related section by its ID for writes, include name for reads.
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSection.objects.all(), source="section", write_only=True
    )
    section_name = serializers.CharField(source="section.name", read_only=True)
    section_slug = serializers.CharField(source="section.slug", read_only=True)
    # Optionally show skills related to this subsection (read-only)
    # skills = AdminSkillSerializer(many=True, read_only=True)

    class Meta:
        model = LearningSubSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "section_id",  # Write
            "section_name",  # Read
            "section_slug",  # Read
            # "skills", # Uncomment if needed for detail view
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "section_name",
            "section_slug",
            "skills",
        ]
        extra_kwargs = {
            "slug": {"required": False},  # Allow blank slug for auto-generation
        }

    def validate(self, attrs):
        """Ensure name is unique within the section if provided."""
        section = attrs.get("section")
        name = attrs.get("name")
        instance = self.instance  # Needed for updates

        if section and name:
            query = LearningSubSection.objects.filter(section=section, name=name)
            if instance:
                query = query.exclude(pk=instance.pk)
            if query.exists():
                raise serializers.ValidationError(
                    {
                        "name": f"A sub-section with this name already exists in the '{section.name}' section."
                    }
                )
        return attrs


class AdminQuestionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on Question."""

    # Represent related objects by ID for writes, include names/slugs for reads.
    subsection_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSubSection.objects.all(), source="subsection", write_only=True
    )
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source="skill",
        allow_null=True,
        required=False,
        write_only=True,
    )
    subsection_slug = serializers.CharField(source="subsection.slug", read_only=True)
    skill_slug = serializers.CharField(
        source="skill.slug", read_only=True, allow_null=True
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
            "correct_answer",  # Admins need to set this
            "explanation",  # Admins need to set this
            "hint",
            "solution_method_summary",
            "difficulty",
            "is_active",  # Admins need to control activation
            "subsection_id",  # Write
            "skill_id",  # Write
            "subsection_slug",  # Read
            "skill_slug",  # Read
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "subsection_slug",
            "skill_slug",
        ]

    def validate_correct_answer(self, value):
        """Ensure correct_answer is one of the allowed choices."""
        if value not in Question.CorrectAnswerChoices.values:
            raise serializers.ValidationError(
                f"Invalid choice. Must be one of {Question.CorrectAnswerChoices.labels}."
            )
        return value

    def validate(self, attrs):
        """Ensure skill belongs to the chosen subsection."""
        subsection = attrs.get("subsection")
        skill = attrs.get("skill")

        if subsection and skill and skill.subsection != subsection:
            raise serializers.ValidationError(
                {
                    "skill_id": f"Skill '{skill.name}' does not belong to the selected subsection '{subsection.name}'."
                }
            )
        return attrs
