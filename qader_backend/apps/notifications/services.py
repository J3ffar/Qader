from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Optional, Any, Dict
import logging

from apps.notifications.tasks import dispatch_notification_email_task
from qader_project.settings.base import FRONTEND_BASE_URL

from .models import Notification, NotificationTypeChoices

User = get_user_model()
logger = logging.getLogger(__name__)


@transaction.atomic
def create_notification(
    recipient: User,
    verb: str,
    actor: Optional[User] = None,
    description: Optional[str] = None,
    target: Optional[Any] = None,
    action_object: Optional[Any] = None,
    notification_type: str = NotificationTypeChoices.INFO,
    url: Optional[str] = FRONTEND_BASE_URL,
    extra_data: Optional[Dict[str, Any]] = None,
    send_email: bool = False,
    email_subject: Optional[str] = None,
    email_body_template_name: Optional[str] = None,
    # send_realtime: bool = True, # For future WebSocket integration
) -> Optional[Notification]:
    """
    Creates and saves a notification, optionally triggering an email.

    Args:
        recipient: The user who will receive the notification.
        verb: A short string describing the action (e.g., "commented on", "earned").
        actor: The user who performed the action (optional).
        description: A more detailed message for the notification (optional).
        target: The primary object related to the notification (optional).
        action_object: A secondary object related to the action (optional).
        notification_type: The type of notification (from NotificationTypeChoices).
        url: A URL the user can click to see more details (optional).
        extra_data: A dictionary for any additional data for frontend/logic.
        send_email: If True, an email notification will be dispatched.
        email_subject: Custom subject for the email. If None, a default will be used.
        email_body_template_name: Custom template name for email body. If None, a default will be used.
        # send_realtime: If True, attempt to send a real-time update (future).

    Returns:
        The created Notification object or None if an error occurred.
    """

    # Prevent self-notifications for certain actions if desired.
    # Example: if actor and recipient are the same, and type is 'COMMUNITY_REPLY' on own post.
    # This logic can be more sophisticated based on specific needs.
    # if actor == recipient and verb == _("replied to your post"): # Example
    #     logger.debug(f"Skipping self-notification for {actor.username} on their own post reply.")
    #     return None

    try:
        notification_data = {
            "recipient": recipient,
            "actor": actor,
            "verb": verb,
            "description": description,
            "notification_type": notification_type,
            "url": url,
            "data": extra_data,
        }

        if target:
            if not hasattr(target, "pk"):
                logger.error(f"Target object {target} does not have a pk attribute.")
                return None
            notification_data["target_content_type"] = (
                ContentType.objects.get_for_model(target._meta.model)
            )  # Ensure using actual model
            notification_data["target_object_id"] = str(target.pk)
        if action_object:
            if not hasattr(action_object, "pk"):
                logger.error(
                    f"Action object {action_object} does not have a pk attribute."
                )
                return None
            notification_data["action_object_content_type"] = (
                ContentType.objects.get_for_model(action_object._meta.model)
            )
            notification_data["action_object_object_id"] = str(action_object.pk)

        notification = Notification.objects.create(**notification_data)

        logger.info(
            f"Notification created for User ID {recipient.id}: "
            f"Actor ID {actor.id if actor else 'System'}, Verb '{verb}', Type '{notification_type}'"
        )

        # TODO: Future - Real-time push via WebSockets (e.g., Django Channels)
        # if send_realtime:
        #     from .tasks import send_realtime_notification_task # Example Celery task
        #     send_realtime_notification_task.delay(notification.id)

        if send_email and recipient.email:
            try:
                # Prepare context for the email template
                email_context = {
                    "recipient_name": recipient.get_full_name() or recipient.username,
                    "verb": verb,
                    "actor_name": (
                        actor.get_full_name() or actor.username
                        if actor
                        else _("System")
                    ),
                    "description": description,
                    "target_name": str(target) if target else None,
                    "action_object_name": str(action_object) if action_object else None,
                    "url": url,  # This should be the relative path, SITE_BASE_URL will be prepended in task
                }
                if extra_data:
                    email_context.update(
                        extra_data
                    )  # Merge extra_data into email_context

                actual_email_subject = email_subject or _(
                    "New Notification: {}"
                ).format(verb)
                actual_email_template = (
                    email_body_template_name or "emails/generic_notification_email"
                )

                dispatch_notification_email_task.delay(
                    notification_id=notification.id,
                    recipient_email=recipient.email,
                    subject=actual_email_subject,
                    body_template_name=actual_email_template,
                    context=email_context,
                )
                logger.info(
                    f"Dispatched email notification task for Notification ID {notification.id} to {recipient.email}"
                )
            except Exception as email_exc:
                logger.error(
                    f"Failed to dispatch email for notification {notification.id} for {recipient.username}. Error: {email_exc}",
                    exc_info=True,
                )

        return notification
    except ContentType.DoesNotExist as e:
        logger.error(
            f"Failed to create notification for {recipient.username}. "
            f"ContentType not found for target or action_object: {e}"
        )
        return None
    except Exception as e:
        logger.exception(
            f"Unexpected error creating notification for {recipient.username}: {e}"
        )
        return None


def bulk_mark_as_read(user: User, notification_ids: list[int]) -> int:
    """Marks a list of notification IDs as read for a specific user."""
    if not notification_ids:
        return 0

    with transaction.atomic():
        updated_count = Notification.objects.filter(
            recipient=user, id__in=notification_ids, is_read=False
        ).update(is_read=True, read_at=timezone.now())
    logger.info(
        f"User {user.id} bulk marked {updated_count} notifications as read from list: {notification_ids}."
    )
    return updated_count


def mark_all_as_read_for_user(user: User) -> int:
    """Marks all unread notifications as read for a specific user."""
    with transaction.atomic():
        updated_count = Notification.objects.filter(
            recipient=user, is_read=False
        ).update(is_read=True, read_at=timezone.now())
    logger.info(
        f"User {user.id} marked all ({updated_count}) their unread notifications as read."
    )
    return updated_count
