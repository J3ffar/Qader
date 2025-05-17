from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import Optional, Any, Dict
import logging

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
    url: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    # send_realtime: bool = True, # For future WebSocket integration
) -> Optional[Notification]:
    """
    Creates and saves a notification.

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
