from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.conf import settings
from django.contrib.auth import get_user_model
from ..models import (
    BlogPost,
    BlogAdviceRequest,
)

User = get_user_model()

class BlogAuthorSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying public author information in blog posts.
    """

    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    preferred_name = serializers.CharField(
        source="profile.preferred_name", read_only=True, allow_null=True
    )
    profile_picture_url = serializers.SerializerMethodField()
    bio = serializers.CharField(source="profile.bio", read_only=True, allow_null=True)
    linkedin_url = serializers.URLField(
        source="profile.linkedin_url", read_only=True, allow_null=True
    )
    twitter_url = serializers.URLField(
        source="profile.twitter_url", read_only=True, allow_null=True
    )
    facebook_url = serializers.URLField(
        source="profile.facebook_url", read_only=True, allow_null=True
    )
    instagram_url = serializers.URLField(
        source="profile.instagram_url", read_only=True, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "full_name",
            "preferred_name",
            "profile_picture_url",
            "bio",
            "linkedin_url",
            "twitter_url",
            "facebook_url",
            "instagram_url",
        )

    def get_profile_picture_url(self, obj) -> str | None:
        """
        Returns the absolute URL for the user's profile picture.
        """
        request = self.context.get("request")
        if (
            hasattr(obj, "profile")
            and obj.profile.profile_picture
            and hasattr(obj.profile.profile_picture, "url")
        ):
            url = obj.profile.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class BlogPostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for listing Blog Posts (concise)."""

    tags = TagListSerializerField(read_only=True)
    author = BlogAuthorSerializer(read_only=True)
    excerpt = serializers.CharField(read_only=True)
    image = serializers.ImageField(read_only=True, allow_null=True, use_url=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "author",
            "published_at",
            "excerpt",
            "tags",
            "image",
        ]


class BlogPostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for retrieving a single Blog Post detail."""

    tags = TagListSerializerField(read_only=True)
    author = BlogAuthorSerializer(read_only=True)
    image = serializers.ImageField(read_only=True, allow_null=True, use_url=True)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "author",
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