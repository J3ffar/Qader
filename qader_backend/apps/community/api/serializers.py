from rest_framework import serializers
from taggit.models import Tag
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.utils.translation import gettext_lazy as _
from django.db.models import (
    Count,
)  # Needed if we annotate count in TagListView queryset
from django.contrib.auth.models import User  # Import the User model
from django.db.models import Q

from apps.community.models import CommunityPost, CommunityReply, PartnerRequest
from apps.learning.models import LearningSection  # Import the actual model

# --- Nested Serializers (Assume these exist and are correctly defined) ---
from apps.users.api.serializers import SimpleUserSerializer
from apps.learning.api.serializers import (
    LearningSectionBasicSerializer,
)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag objects, potentially including usage count."""

    # Assumes 'count' is annotated onto the queryset in the TagListView
    count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Tag
        fields = ["id", "name", "slug", "count"]
        read_only_fields = ["id", "name", "slug", "count"]


# NEW SERIALIZER FOR PARTNER SEARCH
class CommunityPartnerSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users as potential study partners in the community.
    """

    full_name = serializers.CharField(source="profile.full_name", read_only=True)
    grade = serializers.CharField(source="profile.grade", read_only=True)
    profile_picture = serializers.ImageField(
        source="profile.profile_picture", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "grade",
            "profile_picture",
        ]


class CommunityReplySerializer(serializers.ModelSerializer):
    """
    Serializer for reading and creating Community Replies.
    Handles nested author data and parent reply linking.

    Adheres to SRP: Focuses on serializing/deserializing Reply data.
    Adheres to ISP: Provides fields relevant to a reply.
    """

    author = SimpleUserSerializer(read_only=True)
    # Use PrimaryKeyRelatedField for write operations, linking by ID
    parent_reply_id = serializers.PrimaryKeyRelatedField(
        queryset=CommunityReply.objects.all(),
        source="parent_reply",  # Link to the model field
        write_only=True,  # Only used for input validation/linking
        required=False,
        allow_null=True,  # Allow top-level replies
        help_text=_("ID of the parent reply being responded to (for threading)."),
    )
    # Include parent_reply_id in read output for frontend convenience
    parent_reply_read_id = serializers.PrimaryKeyRelatedField(
        read_only=True,
        source="parent_reply",
        help_text=_("ID of the parent reply being responded to (for threading)."),
    )
    # Assumes annotation or property exists on the model/queryset
    child_replies_count = serializers.IntegerField(read_only=True, required=False)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = CommunityReply
        fields = [
            "id",
            "author",
            "content",
            "created_at",
            "updated_at",
            "post",  # Included for context, usually read-only
            "parent_reply_id",  # Write-only field for input
            "parent_reply_read_id",  # Read-only representation of parent ID
            "child_replies_count",
            "like_count",
            "is_liked_by_user",
        ]
        # Fields that are set automatically or shouldn't be changed directly by user input
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "post",
            "parent_reply_read_id",
            "child_replies_count",
            "like_count",
            "is_liked_by_user",
        ]
        # Note: 'content' is writable

    def get_is_liked_by_user(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.likes.filter(pk=user.pk).exists()
        return False

    def validate_parent_reply_id(self, value):
        """
        Ensure the parent reply (if provided) belongs to the same post
        as the new reply will belong to. This validation happens slightly
        late but is necessary. The view performs a more robust check.
        """
        # This validation is partially redundant with the view's check,
        # but provides early feedback if possible.
        # The actual post context is only available in the view's perform_create.
        # We can only check if the parent_reply exists here.
        if value and not CommunityReply.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError(_("Parent reply not found."))
        return value


class CommunityPostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Serializer for listing Community Posts (summary view).
    Optimized for list views with excerpts and counts.
    """

    author = SimpleUserSerializer(read_only=True)
    tags = TagListSerializerField(read_only=True)
    # Expects 'reply_count_annotated' from the view's queryset annotation
    reply_count = serializers.IntegerField(
        source="reply_count_annotated", read_only=True
    )
    # Expects 'content_excerpt' property on the model or annotation
    content_excerpt = serializers.CharField(read_only=True)
    # Use basic serializer for related section in list view
    section_filter = LearningSectionBasicSerializer(read_only=True)
    like_count = serializers.IntegerField(source="likes.count", read_only=True)
    is_liked_by_user = serializers.SerializerMethodField()

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "section_filter",  # Show basic related section info
            "content_excerpt",
            "image",
            "reply_count",
            "like_count",
            "is_liked_by_user",
            "created_at",
            "tags",
            "is_pinned",
            "is_closed",
        ]
        # All fields are typically read-only in a list summary
        read_only_fields = fields

    def get_is_liked_by_user(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.likes.filter(pk=user.pk).exists()
        return False


class CommunityPostCreateUpdateSerializer(
    TaggitSerializer, serializers.ModelSerializer
):
    """
    Serializer for creating and updating Community Posts.
    Includes writable fields like content, title, tags, etc.
    Admin-only fields (is_pinned, is_closed) are handled in the view logic.
    """

    # Author is set automatically in the view
    author = SimpleUserSerializer(read_only=True)
    # Tags are writable via TagListSerializerField
    tags = TagListSerializerField(required=False)
    # Allow setting section_filter via its slug on create/update
    section_filter = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=LearningSection.objects.all(),
        required=False,
        allow_null=True,
        help_text=_(
            "Slug of the learning section to associate this post with (optional)."
        ),
    )

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
            # Admin controlled fields are read-only here, handled in view's perform_update
            "is_pinned",
            "is_closed",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "is_pinned",  # Prevent non-admins from setting via serializer
            "is_closed",  # Prevent non-admins from setting via serializer
        ]

    def validate_post_type(self, value):
        """Ensure the provided post_type is a valid choice."""
        if value not in CommunityPost.PostType.values:
            raise serializers.ValidationError(_("Invalid post type selected."))
        # Potentially add logic here: e.g., only admins can create 'competition' posts?
        # request = self.context.get('request')
        # if value == CommunityPost.PostType.COMPETITION and (not request or not request.user.is_staff):
        #     raise serializers.ValidationError(_("Only administrators can create competition posts."))
        return value

    def validate_title(self, value):
        """Ensure title is provided for certain post types if required."""
        # Example validation: Require title for 'discussion' or 'tip' posts
        post_type = self.initial_data.get("post_type")
        if (
            post_type in [CommunityPost.PostType.DISCUSSION, CommunityPost.PostType.TIP]
            and not value
        ):
            raise serializers.ValidationError(
                _("A title is required for this post type.")
            )
        return value


class CommunityPostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """
    Serializer for retrieving a single Community Post with full details.
    Replies are handled separately with pagination in the view's retrieve method.
    """

    author = SimpleUserSerializer(read_only=True)
    tags = TagListSerializerField(read_only=True)
    section_filter = LearningSectionBasicSerializer(read_only=True)
    reply_count = serializers.IntegerField(
        source="reply_count_annotated", read_only=True
    )

    class Meta:
        model = CommunityPost
        fields = [
            "id",
            "author",
            "post_type",
            "title",
            "content",  # Full content for detail view
            "section_filter",
            "created_at",
            "updated_at",
            "tags",
            "is_pinned",
            "is_closed",
            "reply_count",
        ]
        # Detail view is typically read-only for standard users
        read_only_fields = fields


# NEW SERIALIZER FOR PARTNER REQUESTS
class PartnerRequestSerializer(serializers.ModelSerializer):
    """Serializer for viewing and creating Partner Requests."""

    from_user = SimpleUserSerializer(read_only=True)
    to_user = SimpleUserSerializer(read_only=True)
    # Writable field to specify the recipient when creating a request
    to_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="to_user",
        write_only=True,
        label=_("Recipient User ID"),
    )

    class Meta:
        model = PartnerRequest
        fields = [
            "id",
            "from_user",
            "to_user",
            "to_user_id",  # For writing
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_user",
            "to_user",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        from_user = self.context["request"].user
        to_user = attrs.get("to_user")

        if from_user == to_user:
            raise serializers.ValidationError(
                _("You cannot send a partner request to yourself.")
            )

        # Check for an existing pending request
        if PartnerRequest.objects.filter(
            from_user=from_user,
            to_user=to_user,
            status=PartnerRequest.StatusChoices.PENDING,
        ).exists():
            raise serializers.ValidationError(
                _("You already have a pending request with this user.")
            )

        # Check for an existing accepted relationship (bi-directional)
        if PartnerRequest.objects.filter(
            (
                Q(from_user=from_user, to_user=to_user)
                | Q(from_user=to_user, to_user=from_user)
            ),
            status=PartnerRequest.StatusChoices.ACCEPTED,
        ).exists():
            raise serializers.ValidationError(
                _("You are already partners with this user.")
            )

        return attrs
