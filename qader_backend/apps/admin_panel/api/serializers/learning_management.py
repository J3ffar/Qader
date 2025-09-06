from rest_framework import serializers
from rest_framework.parsers import MultiPartParser # NEW
from apps.learning.models import (
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
    MediaFile, # NEW
    Article,   # NEW
    Question,
)
from django.db.models import Count
from apps.study.models import UserQuestionAttempt, UserTestAttempt


# --- NEW: Serializer for Admin CRUD on TestType ---
class AdminTestTypeSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on TestType."""

    class Meta:
        model = TestType
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "status",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "slug": {"required": False},  # Allow blank slug for auto-generation
        }


class AdminLearningSectionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on LearningSection."""

    # MODIFIED: Add relation to TestType
    test_type_id = serializers.PrimaryKeyRelatedField(
        queryset=TestType.objects.all(), source="test_type", write_only=True
    )
    test_type_name = serializers.CharField(source="test_type.name", read_only=True)

    class Meta:
        model = LearningSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "test_type_id",  # Write
            "test_type_name",  # Read
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "test_type_name"]


class AdminLearningSubSectionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on LearningSubSection."""

    section_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSection.objects.all(), source="section", write_only=True
    )
    section_name = serializers.CharField(source="section.name", read_only=True)
    section_slug = serializers.CharField(source="section.slug", read_only=True)

    # ADDED: Include parent test type for context in read operations
    test_type_name = serializers.CharField(
        source="section.test_type.name", read_only=True
    )

    class Meta:
        model = LearningSubSection
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "order",
            "is_active",  # MODIFIED: Added is_active for admin control
            "section_id",
            "section_name",
            "section_slug",
            "test_type_name",  # Read-only context
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "section_name",
            "section_slug",
            "test_type_name",
        ]


class AdminSkillSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD operations on Skill."""

    # MODIFIED: section_id is now required
    section_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSection.objects.all(), source="section", write_only=True
    )
    section_name = serializers.CharField(source="section.name", read_only=True)

    # MODIFIED: subsection_id is now optional
    subsection_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningSubSection.objects.all(),
        source="subsection",
        write_only=True,
        allow_null=True,  # Allow it to be null
        required=False,  # Don't require it in the payload
    )
    subsection_name = serializers.CharField(
        source="subsection.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",  # MODIFIED: Added is_active
            "section_id",  # Write (Required)
            "section_name",  # Read
            "subsection_id",  # Write (Optional)
            "subsection_name",  # Read
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "section_name",
            "subsection_name",
        ]

    def validate(self, attrs):
        """
        Ensure that if a subsection is provided, it belongs to the specified section.
        """
        section = attrs.get("section")
        subsection = attrs.get("subsection")

        if section and subsection and subsection.section != section:
            raise serializers.ValidationError(
                {
                    "subsection_id": f"The subsection '{subsection.name}' does not belong to the selected section '{section.name}'."
                }
            )
        return attrs


# --- NEW: Admin CRUD Serializers for Content Libraries ---

class AdminMediaFileSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD on the MediaFile library."""
    class Meta:
        model = MediaFile
        fields = ["id", "title", "file", "file_type", "created_at"]
        read_only_fields = ["id", "created_at"]

class AdminArticleSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD on the Article library."""
    class Meta:
        model = Article
        fields = ["id", "title", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


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


# --- MODIFIED: AdminQuestionSerializer ---
class AdminQuestionSerializer(serializers.ModelSerializer):
    # Read-only Nested Representations
    section = _AdminQuestionSectionSerializer(source="subsection.section", read_only=True)
    subsection = _AdminQuestionSubSectionSerializer(read_only=True)
    # MODIFIED: For reading a list of skills
    skills = _AdminQuestionSkillSerializer(many=True, read_only=True, allow_null=True)
    options = serializers.SerializerMethodField()
    
    # NEW: Read-only nested objects for GET
    media_content = AdminMediaFileSerializer(read_only=True)
    article = AdminArticleSerializer(read_only=True)

    total_usage_count = serializers.IntegerField(read_only=True, default=0)
    usage_by_test_type = serializers.SerializerMethodField()

    # Write-only Fields
    subsection_id = serializers.PrimaryKeyRelatedField(queryset=LearningSubSection.objects.all(), source="subsection", write_only=True)
    # MODIFIED: For writing a list of skill IDs
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source="skills", # Link to the 'skills' M2M field on the model
        many=True,      # Accept a list of IDs
        write_only=True,
        required=False, # Allow an empty list
        allow_empty=True
    )
    
    # NEW: Write-only FKs for linking content from libraries
    media_content_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaFile.objects.all(), source="media_content", write_only=True, required=False, allow_null=True
    )
    article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(), source="article", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Question
        fields = [
            # Core Identification & Content
            "id", "question_text",
            # Read-only Nested Content
            "media_content", "article",
            "options", "difficulty", "is_active", "correct_answer", "explanation", "hint",
            "solution_method_summary", "section", "subsection", "skills",
            # Analytics
            "total_usage_count", "usage_by_test_type",
            # Timestamps
            "created_at", "updated_at",
            # Write-only fields
            "subsection_id", "skill_ids", # MODIFIED: was "skill_id"
            "media_content_id", # NEW
            "article_id",       # NEW
            "option_a", "option_b", "option_c", "option_d",
        ]
        read_only_fields = [
            "id", "section", "subsection", "skills", "options", # MODIFIED
            "media_content", "article", # Make the nested objects read-only
            "total_usage_count", "usage_by_test_type", "created_at", "updated_at",
        ]
        extra_kwargs = {
            "option_a": {"write_only": True, "required": True},
            "option_b": {"write_only": True, "required": True},
            "option_c": {"write_only": True, "required": True},
            "option_d": {"write_only": True, "required": True},
        }

    def get_options(self, obj: Question) -> dict:
        return {
            "A": obj.option_a,
            "B": obj.option_b,
            "C": obj.option_c,
            "D": obj.option_d,
        }

    def get_usage_by_test_type(self, obj: Question) -> dict | None:
        # No changes needed here, logic is sound.
        if self.context["view"].action != "retrieve":
            return None
        usage_data = (
            UserQuestionAttempt.objects.filter(question=obj, test_attempt__isnull=False)
            .values("test_attempt__attempt_type")
            .annotate(count=Count("id"))
            .order_by()
        )
        usage_dict = {
            item["test_attempt__attempt_type"]: item["count"]
            for item in usage_data
            if item["test_attempt__attempt_type"]
        }
        all_test_types = UserTestAttempt.AttemptType.values
        for test_type in all_test_types:
            usage_dict.setdefault(test_type, 0)
        return usage_dict

    def validate(self, attrs):
        subsection = attrs.get("subsection")
        # 'skills' will be a list of Skill objects during validation
        skills_list = attrs.get("skills")

        if subsection and skills_list:
            for skill in skills_list:
                # A skill is valid if it has no subsection and matches the section, OR it matches the subsection directly
                is_valid_subsection = (skill.subsection == subsection)
                is_valid_section_only = (skill.subsection is None and skill.section == subsection.section)
                
                if not (is_valid_subsection or is_valid_section_only):
                    raise serializers.ValidationError({
                        "skill_ids": f"Skill '{skill.name}' (ID: {skill.id}) does not belong to the selected classification."
                    })

        # ... (media/article validation is unchanged) ...
        return attrs
