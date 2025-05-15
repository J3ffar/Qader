from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from ..models import (
    BlogPost,
    BlogAdviceRequest,
)

# Assuming this exists for author info and is lightweight
# from apps.users.api.serializers import SimpleUserSerializer


class BlogPostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for listing Blog Posts (concise)."""

    tags = TagListSerializerField(read_only=True)
    author_name = serializers.CharField(source="author_display_name", read_only=True)
    excerpt = serializers.CharField(read_only=True)
    image = serializers.ImageField(read_only=True, allow_null=True, use_url=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "author_name",
            "published_at",
            "excerpt",
            "tags",
            "image",
        ]


class BlogPostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for retrieving a single Blog Post detail."""

    tags = TagListSerializerField(read_only=True)
    author_name = serializers.CharField(source="author_display_name", read_only=True)
    image = serializers.ImageField(read_only=True, allow_null=True, use_url=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "author_name",
            "content",
            "published_at",
            "tags",
            "created_at",
            "updated_at",
            "image",
        ]


class BlogAdviceRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating Blog Advice Requests."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    problem_type = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    class Meta:
        model = BlogAdviceRequest
        fields = [
            "id",
            "user",
            "problem_type",
            "description",
            "status",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "created_at",
        ]

    # Optional: Add validation if needed, e.g., ensuring description is not empty
    # def validate_description(self, value):
    #     if not value or len(value.strip()) == 0:
    #         raise serializers.ValidationError(_("Description cannot be empty."))
    #     return value
