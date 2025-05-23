from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache  # Import Django's cache
from django.conf import settings  # Import Django settings
import logging  # It's good practice to log this behavior

from apps.notifications.services import create_notification
from apps.notifications.models import NotificationTypeChoices
from .models import Message, Conversation

User = get_user_model()
logger = logging.getLogger(__name__)


def _get_active_user_cache_key_for_signal(user_id, conversation_id):
    """Helper to generate a consistent cache key, usable in sync context."""
    return f"active_chat_user_{user_id}_conversation_{conversation_id}"


@receiver(post_save, sender=Message)
def send_chat_message_notification(sender, instance: Message, created: bool, **kwargs):
    """
    Sends a notification (and potentially an email) when a new chat message is created,
    unless the recipient is actively connected to this chat.
    """
    if created:
        conversation: Conversation = instance.conversation
        message_sender: User = instance.sender
        recipient_user: User = None

        if message_sender == conversation.student.user:
            recipient_user = conversation.teacher.user
        elif message_sender == conversation.teacher.user:
            recipient_user = conversation.student.user

        if recipient_user and recipient_user != message_sender:
            # Check if the recipient is active in this specific conversation
            active_user_cache_key = _get_active_user_cache_key_for_signal(
                recipient_user.id, conversation.id
            )
            is_recipient_active = cache.get(active_user_cache_key)

            if is_recipient_active:
                logger.info(
                    f"Recipient {recipient_user.username} (ID: {recipient_user.id}) is active "
                    f"in conversation {conversation.id}. Suppressing notification and email for message {instance.id}."
                )
                return  # Skip creating notification and sending email

            # If recipient is not active, proceed to create notification
            actor_name = message_sender.get_full_name() or message_sender.username
            if conversation.student.user == message_sender:
                notification_verb = _(
                    "sent you a new message in your chat with {student_name}"
                ).format(student_name=actor_name)
                chat_email_subject = _("New message from {student_name}").format(
                    student_name=actor_name
                )
            else:  # Sender is teacher
                notification_verb = _(
                    "sent you a new message in your chat with {teacher_name}"
                ).format(teacher_name=actor_name)
                chat_email_subject = _("New message from {teacher_name}").format(
                    teacher_name=actor_name
                )

            conversation_url = f"/chats/{conversation.id}/"

            create_notification(
                recipient=recipient_user,
                actor=message_sender,
                verb=notification_verb,
                description=instance.content[:200],
                target=conversation,
                action_object=instance,
                notification_type=NotificationTypeChoices.CHAT,
                url=conversation_url,
                send_email=True,  # This will now only be effective if the user is NOT active
                email_subject=chat_email_subject,
                email_body_template_name="emails/generic_notification_email",
                extra_data={
                    "conversation_id": str(conversation.id),
                    "message_id": str(instance.id),
                    "sender_id": str(message_sender.id),
                    "sender_username": message_sender.username,
                    "message_snippet": instance.content[:50],
                },
            )
