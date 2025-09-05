from rest_framework import serializers
from apps.learning.models import (
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
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


class AdminQuestionSerializer(serializers.ModelSerializer):
    """Serializer for Admin CRUD on Questions."""

    section = _AdminQuestionSectionSerializer(
        source="subsection.section", read_only=True
    )
    subsection = _AdminQuestionSubSectionSerializer(read_only=True)
    skill = _AdminQuestionSkillSerializer(read_only=True, allow_null=True)
    options = serializers.SerializerMethodField()
    image_url = serializers.ImageField(
        source="image", read_only=True
    )  # MODIFIED: Renamed for clarity
    audio_url = serializers.FileField(
        source="audio_file", read_only=True
    )  # NEW: Read-only audio URL

    total_usage_count = serializers.IntegerField(read_only=True, default=0)
    usage_by_test_type = serializers.SerializerMethodField()

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

    # MODIFIED: Updated write fields for new content types
    image_upload = serializers.ImageField(
        source="image", write_only=True, required=False, allow_null=True
    )
    audio_upload = serializers.FileField(
        source="audio_file", write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "image_url",
            "audio_url",
            "article_title",  # NEW
            "article_content",  # NEW
            "options",
            "difficulty",
            "is_active",
            "correct_answer",
            "explanation",
            "hint",
            "solution_method_summary",
            "section",
            "subsection",
            "skill",
            "total_usage_count",
            "usage_by_test_type",
            "created_at",
            "updated_at",
            # Write-only fields
            "subsection_id",
            "skill_id",
            "image_upload",
            "audio_upload",  # NEW
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
            "image_url",
            "audio_url",
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
            # Make new article fields optional in API
            "article_title": {"required": False, "allow_blank": True},
            "article_content": {"required": False, "allow_blank": True},
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
        # Validate that if a skill is provided, it belongs to the question's subsection
        subsection = attrs.get("subsection")
        skill = attrs.get("skill")
        if subsection and skill and skill.subsection and skill.subsection != subsection:
            raise serializers.ValidationError(
                {
                    "skill_id": f"Skill '{skill.name}' does not belong to the selected subsection '{subsection.name}'."
                }
            )

        # Validate that the model's clean method logic is also enforced here.
        # This gives faster API feedback.
        image = attrs.get("image")
        article_content = attrs.get("article_content")
        audio_file = attrs.get("audio_file")
        content_types = [image, article_content, audio_file]
        filled_content_types = sum(1 for content in content_types if content)
        if filled_content_types > 1:
            raise serializers.ValidationError(
                "A question can only have one type of media content: an image, an article, OR an audio file."
            )

        return attrs
