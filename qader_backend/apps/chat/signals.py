from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from apps.notifications.services import create_notification
from apps.notifications.models import NotificationTypeChoices
from .models import Message, Conversation

User = get_user_model()


@receiver(post_save, sender=Message)
def send_chat_message_notification(sender, instance: Message, created: bool, **kwargs):
    """
    Sends a notification (and potentially an email) when a new chat message is created.
    """
    if created:
        conversation: Conversation = instance.conversation
        message_sender: User = instance.sender
        recipient_user: User = None

        # Determine the recipient (the other user in the conversation)
        if message_sender == conversation.student.user:
            recipient_user = conversation.teacher.user
        elif message_sender == conversation.teacher.user:
            recipient_user = conversation.student.user

        if (
            recipient_user and recipient_user != message_sender
        ):  # Ensure not notifying self

            actor_name = message_sender.get_full_name() or message_sender.username

            # Verb for the in-app notification and email subject
            if conversation.student.user == message_sender:  # Sender is student
                # Recipient is teacher
                notification_verb = _(
                    "sent you a new message in your chat with {student_name}"
                ).format(student_name=actor_name)
                chat_email_subject = _("New message from {student_name}").format(
                    student_name=actor_name
                )
            elif conversation.teacher.user == message_sender:  # Sender is teacher
                # Recipient is student
                notification_verb = _(
                    "sent you a new message in your chat with {teacher_name}"
                ).format(teacher_name=actor_name)
                chat_email_subject = _("New message from {teacher_name}").format(
                    teacher_name=actor_name
                )
            else:  # Should not happen given the conversation structure
                notification_verb = _("sent you a new message")
                chat_email_subject = _("New chat message received")

            # Construct a URL to the conversation.
            # This is an example, adjust the path and parameters as per your frontend routing.
            # Assuming your frontend can handle /chat/<conversation_id>/
            conversation_url = f"/chats/{conversation.id}/"
            # If you have message-specific links:
            # conversation_url = f"/chat/{conversation.id}/#message-{instance.id}"

            create_notification(
                recipient=recipient_user,
                actor=message_sender,
                verb=notification_verb,
                description=instance.content[
                    :200
                ],  # Snippet of the message, adjust length as needed
                target=conversation,
                action_object=instance,
                notification_type=NotificationTypeChoices.CHAT,
                url=conversation_url,
                send_email=True,  # Trigger email sending
                email_subject=chat_email_subject,
                # Using the generic email template; context will fill it.
                # Or you could create specific chat_notification_email.html/txt templates.
                email_body_template_name="emails/generic_notification_email",
                extra_data={  # This data will also be available in the email_context
                    "conversation_id": str(
                        conversation.id
                    ),  # Ensure IDs are strings if using UUIDs
                    "message_id": str(instance.id),
                    "sender_id": str(message_sender.id),
                    "sender_username": message_sender.username,
                    "message_snippet": instance.content[
                        :50
                    ],  # Short snippet for quick view
                },
            )
