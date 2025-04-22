from rest_framework import serializers
from taggit.models import Tag
from taggit.serializers import TagListSerializerField, TaggitSerializer

from apps.community.models import CommunityPost, CommunityReply
from apps.users.api.serializers import SimpleUserSerializer  # Assuming this exists
from apps.learning.api.serializers import (
    LearningSectionBasicSerializer,
)  # Assuming this exists
from apps.api.permissions import IsSubscribed  # Import your permission
from apps.learning.models import (
    LearningSection,
)  # Helper for nested pagination


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag objects."""

    count = serializers.IntegerField(read_only=True)  # Assuming annotated in view

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "count"]


class CommunityReplySerializer(serializers.ModelSerializer):
    """Serializer for CommunityReply."""

    author = SimpleUserSerializer(read_only=True)
    parent_reply_id = serializers.PrimaryKeyRelatedField(
        queryset=CommunityReply.objects.all(),
        source="parent_reply",
        write_only=True,
        required=False,
        allow_null=True,
    )
    child_replies_count = serializers.IntegerField(
        read_only=True
    )  # Can be annotated or property

    class Meta:
        model = CommunityReply
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
            "post",
            "parent_reply_id",
            "parent_reply",
            "child_replies_count",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "post",
            "parent_reply",
            "child_replies_count",
        ]

    # Override to exclude 'parent_reply' from response if needed, it's read_only now
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Show parent_reply_id in response for easier frontend handling
        representation["parent_reply_id"] = instance.parent_reply_id
        representation.pop("parent_reply", None)  # Remove bulky nested parent object
        return representation


class CommunityPostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for listing Community Posts."""

    author = SimpleUserSerializer(read_only=True)
    tags = TagListSerializerField(required=False)
    reply_count = serializers.IntegerField(
        read_only=True
    )  # Must be annotated in queryset
    content_excerpt = serializers.CharField(
        read_only=True
    )  # Must be annotated or property

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "content_excerpt",
            "reply_count",
            "created_at",
            "tags",
            "is_pinned",
            "is_closed",
            "section_filter",  # Keep section filter slug/id for filtering context
        ]
        read_only_fields = [
            "id",
            "author",
            "reply_count",
            "created_at",
            "is_pinned",
            "is_closed",
            "content_excerpt",
        ]


class CommunityPostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for creating/updating Community Posts."""

    author = SimpleUserSerializer(read_only=True)
    tags = TagListSerializerField(required=False)
    section_filter = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=LearningSection.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "content",
            "section_filter",
            "tags",
            "created_at",
            "updated_at",
            "is_pinned",
            "is_closed",  # Include but make admin-only editable in view
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "is_pinned",
            "is_closed",
        ]

    def validate_post_type(self, value):
        if value not in CommunityPost.PostType.values:
            raise serializers.ValidationError(_("Invalid post type selected."))
        return value


class CommunityPostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Serializer for retrieving a single Community Post with details."""

    author = SimpleUserSerializer(read_only=True)
    tags = TagListSerializerField(
        read_only=True
    )  # Tags usually read-only on detail view
    section_filter = LearningSectionBasicSerializer(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)  # Annotated
    # Replies will be added manually in the view using pagination
    # We define a placeholder field for documentation purposes

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "content",
            "section_filter",
            "created_at",
            "updated_at",
            "tags",
            "is_pinned",
            "is_closed",
            "reply_count",
        ]
        read_only_fields = fields  # Detail view is read-only by default for users
