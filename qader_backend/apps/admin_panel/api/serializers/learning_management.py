from rest_framework import serializers
from apps.learning.models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
)
from django.db.models import Count
from apps.study.models import UserQuestionAttempt, UserTestAttempt


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


class _AdminQuestionSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSection
        fields = ["id", "name", "slug"]


class _AdminQuestionSubSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningSubSection
        fields = ["id", "name", "slug"]


class _AdminQuestionSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "slug"]


# --- Main Admin Question Serializer ---


class AdminQuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Admin CRUD on Questions.
    - Read: Provides a detailed, nested view similar to the user-facing API.
    - Write: Uses simple primary key IDs for relationships.
    - Analytics: Includes question usage counts.
    """

    # --- Read-only Nested Representations (for GET requests) ---
    section = _AdminQuestionSectionSerializer(
        source="subsection.section", read_only=True
    )
    subsection = _AdminQuestionSubSectionSerializer(read_only=True)
    skill = _AdminQuestionSkillSerializer(read_only=True, allow_null=True)
    options = serializers.SerializerMethodField()
    image = serializers.ImageField(
        read_only=True
    )  # Image is read-only here, write is handled below

    # --- Analytics Fields (Read-only) ---
    total_usage_count = serializers.IntegerField(read_only=True, default=0)
    usage_by_test_type = serializers.SerializerMethodField()

    # --- Write-only Fields (for POST/PUT/PATCH requests) ---
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
    # Allows image uploads on create/update
    image_upload = serializers.ImageField(
        source="image", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Question
        fields = [
            # Core Identification & Content
            "id",
            "question_text",
            "image",  # Read URL
            "options",
            "difficulty",
            "is_active",
            "correct_answer",
            "explanation",
            "hint",
            "solution_method_summary",
            # Relational Context (Read-only)
            "section",
            "subsection",
            "skill",
            # Analytics (Read-only)
            "total_usage_count",
            "usage_by_test_type",
            # Timestamps
            "created_at",
            "updated_at",
            # Write-only fields
            "subsection_id",
            "skill_id",
            "image_upload",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
        ]
        read_only_fields = [
            "id",
            "section",
            "subsection",
            "skill",
            "options",
            "image",
            "total_usage_count",
            "usage_by_test_type",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "option_a": {"write_only": True, "required": True},
            "option_b": {"write_only": True, "required": True},
            "option_c": {"write_only": True, "required": True},
            "option_d": {"write_only": True, "required": True},
        }

    def get_options(self, obj: Question) -> dict:
        """Constructs a dictionary of all answer options."""
        return {
            "A": obj.option_a,
            "B": obj.option_b,
            "C": obj.option_c,
            "D": obj.option_d,
        }

    def get_usage_by_test_type(self, obj: Question) -> dict | None:
        """
        Calculates question usage broken down by test type.
        This method is only executed for 'retrieve' actions to prevent N+1 queries.
        """
        # Only calculate this complex field for single-object detail views.
        if self.context["view"].action != "retrieve":
            return None

        # Query UserQuestionAttempt, filter by the current question and where a test_attempt exists
        usage_data = (
            UserQuestionAttempt.objects.filter(question=obj, test_attempt__isnull=False)
            .values(
                "test_attempt__attempt_type"  # Group by the attempt type from the related UserTestAttempt
            )
            .annotate(count=Count("id"))
            .order_by()
        )  # Ungroup to prevent default ordering issues

        # Format the result into the desired dictionary
        # {'level_assessment': 10, 'practice': 50, ...}
        usage_dict = {
            item["test_attempt__attempt_type"]: item["count"]
            for item in usage_data
            if item["test_attempt__attempt_type"]
        }

        # Ensure all possible test types are present in the response, even if count is 0
        all_test_types = UserTestAttempt.AttemptType.values
        for test_type in all_test_types:
            usage_dict.setdefault(test_type, 0)

        return usage_dict

    def validate(self, attrs):
        """Ensure skill belongs to the chosen subsection during write operations."""
        # This validation only runs on write (create/update) because 'subsection' and 'skill'
        # are only present in `attrs` during those operations.
        subsection = attrs.get("subsection")
        skill = attrs.get("skill")

        if subsection and skill and skill.subsection != subsection:
            raise serializers.ValidationError(
                {
                    "skill_id": f"Skill '{skill.name}' does not belong to the selected subsection '{subsection.name}'."
                }
            )
        return attrs
