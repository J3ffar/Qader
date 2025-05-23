import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from qader_project.settings.base import FRONTEND_BASE_URL

from .models import Conversation, Message
from apps.users.models import (
    UserProfile,
    RoleChoices,
)  # Assuming UserProfile is in users.models
from .api.serializers import ChatMessageSerializer  # Re-use the API serializer

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    def _get_active_user_cache_key(self, user_id, conversation_id):
        """Helper to generate a consistent cache key."""
        return f"active_chat_user_{user_id}_conversation_{conversation_id}"

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.user_profile = await self.get_user_profile(self.user)
        if not self.user_profile:
            await self.close()
            return

        self.conversation_id_param = self.scope["url_route"]["kwargs"].get(
            "conversation_id"
        )
        self.conversation_obj = None

        if self.conversation_id_param:
            self.conversation_obj = await self.get_conversation_by_id_for_teacher(
                self.conversation_id_param, self.user_profile
            )
        elif self.user_profile.role == RoleChoices.STUDENT:
            self.conversation_obj = await self.get_student_conversation(
                self.user_profile
            )
        else:
            await self.close()
            return

        if not self.conversation_obj:
            await self.close()
            return

        self.conversation_id_str = str(self.conversation_obj.id)
        self.room_group_name = f"chat_{self.conversation_id_str}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Mark user as active in this conversation
        active_user_cache_key = self._get_active_user_cache_key(
            self.user.id, self.conversation_id_str
        )
        await database_sync_to_async(cache.set)(
            active_user_cache_key, True, timeout=settings.CHAT_ACTIVE_USER_TIMEOUT
        )

        await self.mark_messages_as_read_on_connect(self.conversation_obj, self.user)

        await self.send(
            text_data=json.dumps(
                {
                    "type": "connection_established",
                    "conversation_id": self.conversation_id_str,
                    "room_group_name": self.room_group_name,
                }
            )
        )

    async def disconnect(self, close_code):
        if (
            hasattr(self, "user")
            and self.user
            and self.user.is_authenticated
            and hasattr(self, "conversation_id_str")
            and self.conversation_id_str
        ):
            # Mark user as inactive by deleting the cache key
            active_user_cache_key = self._get_active_user_cache_key(
                self.user.id, self.conversation_id_str
            )
            await database_sync_to_async(cache.delete)(active_user_cache_key)

        if hasattr(self, "room_group_name") and self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        if not self.conversation_obj:
            await self.send(
                text_data=json.dumps({"error": "Conversation not established."})
            )
            return

        # Refresh user's active status in this conversation upon receiving a message
        # This indicates they are still actively participating.
        active_user_cache_key = self._get_active_user_cache_key(
            self.user.id, self.conversation_id_str
        )
        await database_sync_to_async(cache.set)(
            active_user_cache_key, True, timeout=settings.CHAT_ACTIVE_USER_TIMEOUT
        )

        text_data_json = json.loads(text_data)
        message_content = text_data_json.get("message")

        if not message_content or not message_content.strip():
            await self.send(
                text_data=json.dumps({"error": "Message content cannot be empty."})
            )
            return

        new_message = await self.create_message(
            self.conversation_obj, self.user, message_content
        )

        if not new_message:
            await self.send(text_data=json.dumps({"error": "Failed to save message."}))
            return

        serialized_message = await self.serialize_message_for_broadcast(new_message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": serialized_message,
                "sender_id": self.user.id,
            },
        )

    # Receive message from room group
    async def chat_message(self, event):
        message_data = event["message"]
        sender_id_from_event = event["sender_id"]

        # Add is_own_message based on the current consumer's user
        # This is important because each consumer instance represents one client
        message_data["is_own_message"] = self.user.id == sender_id_from_event

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps({"type": "new_message", "message": message_data})
        )

        # After sending the message to the recipient, if they are connected,
        # and this consumer is the recipient, mark the message as read.
        # This is a bit tricky. A better approach for "seen" status is more complex.
        # For now, rely on the connect/fetch mechanism for read status.
        # If we want instant "read" status, the client receiving the message
        # would send back a "message_read" event.

    @database_sync_to_async
    def get_user_profile(self, user):
        try:
            return UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation_by_id_for_teacher(self, conversation_id, teacher_profile):
        try:
            # Ensure the teacher is actually part of this conversation
            conversation = Conversation.objects.select_related(
                "student__user", "teacher__user"
            ).get(pk=conversation_id, teacher=teacher_profile)
            return conversation
        except Conversation.DoesNotExist:
            return None
        except Exception as e:  # Catch other potential errors
            print(f"Error getting conversation for teacher: {e}")  # Log error
            return None

    @database_sync_to_async
    def get_student_conversation(self, student_profile):
        mentor_profile = student_profile.assigned_mentor
        if not mentor_profile:
            return None
        try:
            conversation, _ = Conversation.get_or_create_conversation(
                student_profile=student_profile, teacher_profile=mentor_profile
            )
            return conversation
        except (ValueError, DjangoPermissionDenied, Conversation.DoesNotExist) as e:
            print(f"Error getting/creating student conversation: {e}")  # Log error
            return None

    @database_sync_to_async
    def create_message(self, conversation, sender, content):
        try:
            message = Message.objects.create(
                conversation=conversation, sender=sender, content=content
            )
            # The message save method should update conversation.updated_at
            return message
        except Exception as e:
            print(f"Error creating message: {e}")  # Log error
            return None

    @database_sync_to_async
    def mark_messages_as_read_on_connect(self, conversation, user):
        """Mark messages as read by this user in this conversation."""
        try:
            updated_count = (
                Message.objects.filter(conversation=conversation, is_read=False)
                .exclude(sender=user)
                .update(
                    is_read=True,  # Removed updated_at here, handled by Message save
                    # read_at=timezone.now() # if you add a read_at field
                )
            )
            # print(f"Marked {updated_count} messages as read for user {user.username} in conv {conversation.id}")
        except Exception as e:
            print(f"Error marking messages as read: {e}")  # Log error

    @database_sync_to_async
    def serialize_message_for_broadcast(self, message_obj):
        # Create a dummy context if your serializer expects 'request'
        # For ChatMessageSerializer, 'is_own_message' is the main concern.
        # We handle 'is_own_message' in the `chat_message` method on the receiving end.
        # So, the context for `is_own_message` during serialization isn't critical here.
        # However, if other fields rely on request (like absolute URLs for images in profiles),
        # you might need a more complete mock.
        class DummyRequest:
            def __init__(self, user):
                self.user = user

            def build_absolute_uri(
                self, path
            ):  # Example if profile_picture_url needs it
                return f"{FRONTEND_BASE_URL}{path}"  # Replace with your actual domain or make it relative

        # Create a context that ChatMessageSerializer might use.
        # The `is_own_message` will be set per-recipient in the `chat_message` handler.
        context = {"request": DummyRequest(user=message_obj.sender)}
        return ChatMessageSerializer(message_obj, context=context).data
