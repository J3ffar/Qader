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
    # Use the property from the model for consistent author display name
    author_name = serializers.CharField(source="author_display_name", read_only=True)
    # Use the model property directly for the excerpt
    excerpt = serializers.CharField(
        read_only=True
    )  # No 'source' needed if property name matches field name

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
        ]


class BlogPostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for retrieving a single Blog Post detail."""

    tags = TagListSerializerField(read_only=True)
    # Fetch nested author information if needed
    # author = SimpleUserProfileSerializer(source='author.profile', read_only=True) # If author detail needed
    author_name = serializers.CharField(source="author_display_name", read_only=True)

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
        ]
        # read_only_fields = fields # Not needed if all fields listed are read-only by definition/attribute


class BlogAdviceRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating Blog Advice Requests."""

    # Automatically set the user based on the request, not exposed in API input
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # Make problem_type optional in the API request
    problem_type = serializers.CharField(
        max_length=255, required=False, allow_blank=True
    )

    class Meta:
        model = BlogAdviceRequest
        fields = [
            "id",
            "user",  # Included for completeness, but hidden and read-only on input
            "problem_type",
            "description",
            "status",
            "created_at",
            # Exclude admin-managed fields like response_via, related_*
        ]
        read_only_fields = [
            "id",
            "user",  # User is set internally, not by API client input
            "status",
            "created_at",
        ]

    # Optional: Add validation if needed, e.g., ensuring description is not empty
    # def validate_description(self, value):
    #     if not value or len(value.strip()) == 0:
    #         raise serializers.ValidationError(_("Description cannot be empty."))
    #     return value
