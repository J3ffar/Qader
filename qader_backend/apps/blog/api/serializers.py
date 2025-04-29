from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from ..models import BlogPost, BlogAdviceRequest, PostStatusChoices
from apps.users.api.serializers import (
    SimpleUserSerializer,
)  # Assuming this exists for author info


class BlogPostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for listing Blog Posts (concise)."""

    tags = TagListSerializerField(read_only=True)
    # Use the property from the model for consistent author display name
    author_name = serializers.CharField(source="author_display_name", read_only=True)
    excerpt = serializers.CharField(read_only=True)  # Use the model property

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
        read_only_fields = fields  # This serializer is read-only

    def get_excerpt(self, obj: BlogPost) -> str:
        """Call the model's get_excerpt method."""
        # You can optionally specify the word count here if needed,
        # otherwise it uses the model method's default (30).
        return obj.get_excerpt()


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
            "author_name",  # Changed from 'author'
            "published_at",
            "content",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields  # This serializer is read-only


class BlogAdviceRequestSerializer(serializers.ModelSerializer):
    """Serializer for creating Blog Advice Requests."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BlogAdviceRequest
        fields = [
            "id",  # Read-only field returned after creation
            "user",
            "problem_type",
            "description",
            "status",  # Read-only, set by default
            "created_at",  # Read-only
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
        ]  # Explicitly mark read-only fields


# --- Admin Serializers (Example - these would live in admin_panel app) ---
# class AdminBlogPostSerializer(TaggitSerializer, serializers.ModelSerializer):
#     """ Admin Serializer for full CRUD on Blog Posts """
#     tags = TagListSerializerField(required=False)
#     author = serializers.PrimaryKeyRelatedField(
#         queryset=User.objects.filter(is_staff=True),
#         required=False, allow_null=True # Assign author explicitly
#     )

#     class Meta:
#         model = BlogPost
#         fields = [
#             "id", "author", "title", "slug", "content", "status",
#             "published_at", "tags", "created_at", "updated_at"
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]
#         extra_kwargs = {
#             'slug': {'required': False, 'allow_blank': True} # Slug can be auto-generated
#         }

# class AdminBlogAdviceRequestSerializer(serializers.ModelSerializer):
#     """ Admin Serializer for managing Blog Advice Requests """
#     user = serializers.CharField(source='user.username', read_only=True) # Display username

#     class Meta:
#         model = BlogAdviceRequest
#         fields = [
#             "id", "user", "problem_type", "description", "status",
#             "response_via", "related_support_ticket", "related_blog_post",
#             "created_at", "updated_at"
#         ]
#         read_only_fields = ["id", "user", "problem_type", "description", "created_at", "updated_at"]
#         # Admin can only update status and links
