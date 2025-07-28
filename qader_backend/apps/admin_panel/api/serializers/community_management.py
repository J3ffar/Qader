from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.db.models import Count

from apps.community.models import CommunityPost, CommunityReply
from apps.users.api.serializers import SimpleUserSerializer  # For read-only nested data


class AdminCommunityReplySerializer(serializers.ModelSerializer):
    """
    Admin serializer for full control over Community Replies.
    """

    author = SimpleUserSerializer(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    # Expose who liked the reply for admin auditing
    likes = SimpleUserSerializer(many=True, read_only=True)

    class Meta:
        model = CommunityReply
        fields = [
            "id",
            "post",
            "author",
            "content",
            "parent_reply",
            "created_at",
            "updated_at",
            "like_count",
            "likes",
        ]
        # Admins can edit the content of any reply
        read_only_fields = [
            "id",
            "post",
            "author",
            "created_at",
            "updated_at",
            "like_count",
            "likes",
        ]


class AdminCommunityPostListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for listing posts. Includes counts for likes and replies.
    """

    author = SimpleUserSerializer(read_only=True)
    reply_count = serializers.IntegerField(
        source="reply_count_annotated", read_only=True
    )
    like_count = serializers.IntegerField(source="like_count_annotated", read_only=True)

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "title",
            "post_type",
            "is_pinned",
            "is_closed",
            "created_at",
            "reply_count",
            "like_count",
            "image",
        ]


class AdminCommunityPostSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Admin serializer for creating and updating posts.
    Provides full control over all fields, including `is_pinned` and `is_closed`.
    """

    author = SimpleUserSerializer(read_only=True)  # Author is set in the view
    tags = TagListSerializerField(required=False)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    # Expose who liked the post for admin auditing
    likes = SimpleUserSerializer(many=True, read_only=True)

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "content",
            "image",
            "section_filter",
            "tags",
            "created_at",
            "updated_at",
            "is_pinned",
            "is_closed",  # <<< CHANGED: These are now writable for admins
            "like_count",
            "likes",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "like_count",
            "likes",
        ]
