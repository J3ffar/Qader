from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import SupportTicket, SupportTicketReply

# Assuming a basic user serializer exists, e.g., in apps.users.api.serializers
# If not, define a simple one here or import appropriately.
# from apps.users.api.serializers import UserBasicInfoSerializer # Example import

User = get_user_model()


# Simple User Serializer (replace with actual one if available)
class UserBasicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
        )  # Add 'preferred_name', 'profile_picture_url' if needed


# --- Reply Serializers ---


class SupportTicketReplySerializer(serializers.ModelSerializer):
    """Serializer for displaying ticket replies."""

    user = UserBasicInfoSerializer(read_only=True)

    class Meta:
        model = SupportTicketReply
        fields = ("id", "user", "message", "is_internal_note", "created_at")
        read_only_fields = (
            "id",
            "user",
            "created_at",
            "is_internal_note",
        )  # is_internal_note set by admin


class SupportTicketReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ticket replies (user and admin)."""

    # user and ticket are set in the view's perform_create method
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # Admin can set is_internal_note, user cannot. Logic handled in view/serializer context.
    is_internal_note = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = SupportTicketReply
        fields = (
            "id",
            "message",
            "is_internal_note",
            "user",
        )  # 'ticket' is set in view context

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        # Only allow admins to set is_internal_note
        if not request or not request.user.is_staff:
            if "is_internal_note" in self.fields:
                self.fields["is_internal_note"].read_only = True
                self.fields["is_internal_note"].required = False


# --- Ticket Serializers ---


class SupportTicketListSerializer(serializers.ModelSerializer):
    """Serializer for listing support tickets (user and admin)."""

    user = UserBasicInfoSerializer(read_only=True)
    assigned_to = UserBasicInfoSerializer(read_only=True)
    last_reply_by = serializers.CharField(
        source="last_reply_by_role", read_only=True
    )  # Use property

    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "subject",
            "issue_type",
            "status",
            "priority",
            "user",
            "assigned_to",
            "created_at",
            "updated_at",
            "last_reply_by",
        )
        read_only_fields = fields  # List view is read-only


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing a single support ticket's details."""

    user = UserBasicInfoSerializer(read_only=True)
    assigned_to = UserBasicInfoSerializer(read_only=True)
    replies = SupportTicketReplySerializer(many=True, read_only=True)  # Nested replies

    class Meta:
        model = SupportTicket
        fields = (
            "id",
            "subject",
            "issue_type",
            "description",
            "attachment",
            "status",
            "priority",
            "user",
            "assigned_to",
            "created_at",
            "updated_at",
            "closed_at",
            "replies",
        )
        read_only_fields = fields  # Detail view is read-only by default for users


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new support ticket (user)."""

    # user is set in the view's perform_create method
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # attachment is handled automatically by FileField

    class Meta:
        model = SupportTicket
        fields = ("id", "issue_type", "subject", "description", "attachment", "user")
        read_only_fields = ("id", "user")

    def validate_attachment(self, value):
        # Example validation: Limit file size to 5MB
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(_("Attachment size cannot exceed 5MB."))
        # Add file type validation if needed
        return value


class SupportTicketAdminUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admins to update ticket status, priority, assignment."""

    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_staff=True),
        source="assigned_to",
        required=False,
        allow_null=True,
        write_only=True,
    )
    assigned_to = UserBasicInfoSerializer(read_only=True)  # Display assigned user

    class Meta:
        model = SupportTicket
        fields = ("status", "priority", "assigned_to_id", "assigned_to")
        read_only_fields = ("assigned_to",)  # Display field

    def validate_status(self, value):
        # Optionally add logic here, e.g., ensure closing sets closed_at
        return value
