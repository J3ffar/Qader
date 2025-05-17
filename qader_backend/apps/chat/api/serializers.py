from rest_framework import serializers
from django.contrib.auth import get_user_model
from typing import Dict, Optional


# Adjust the import path if your BriefUserProfileSerializer is elsewhere
# Assuming it's in users.api.serializers as per your project structure.
# If apps.users.api.serializers imports from admin_panel.api.serializers, ensure no circular dependency.
# For now, let's define a simple one here if it's problematic.
# from apps.users.api.serializers import BriefUserProfileSerializer
# Placeholder if import is complex:
class SimpleProfileSerializer(
    serializers.Serializer
):  # Replace with your actual BriefUserProfileSerializer
    user_id = serializers.IntegerField(source="pk")
    full_name = serializers.CharField()
    username = serializers.CharField(source="user.username")
    email = serializers.EmailField(source="user.email")
    role = serializers.CharField()


from apps.users.models import UserProfile  # For type hinting
from ..models import Conversation, Message

User = get_user_model()


class ChatMessageSerializer(serializers.ModelSerializer):
    # Use your BriefUserProfileSerializer here if available and working
    sender_profile = SimpleProfileSerializer(source="sender.profile", read_only=True)
    is_own_message = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            # 'conversation', # Usually not needed in message list, implied by context
            "sender",
            "sender_profile",
            "content",
            "timestamp",
            "is_read",
            "is_own_message",
        ]
        read_only_fields = [
            "id",
            "sender",
            "sender_profile",
            "timestamp",
            "is_own_message",
        ]

    def get_is_own_message(self, obj: Message) -> bool:
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return obj.sender == request.user
        return False


class CreateMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["content"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


class ChatConversationSerializer(serializers.ModelSerializer):
    # Use your BriefUserProfileSerializer here
    student_profile = SimpleProfileSerializer(source="student", read_only=True)
    teacher_profile = SimpleProfileSerializer(source="teacher", read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_message_count_for_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "student_profile",
            "teacher_profile",
            "created_at",
            "updated_at",  # This is effectively last_message_time
            "last_message",
            "unread_message_count_for_user",
        ]

    def get_last_message(self, obj: Conversation) -> Optional[Dict]:
        last_msg = obj.messages.order_by("-timestamp").first()
        if last_msg:
            return ChatMessageSerializer(last_msg, context=self.context).data
        return None

    def get_unread_message_count_for_user(self, obj: Conversation) -> int:
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            # Count messages in this conversation not sent by the current user and are unread
            return (
                obj.messages.filter(is_read=False).exclude(sender=request.user).count()
            )
        return 0
