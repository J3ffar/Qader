from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.users.models import UserProfile
from apps.notifications.services import create_notification
from apps.notifications.models import NotificationTypeChoices, Notification
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@shared_task(name="send_subscription_expiry_reminders")
def send_subscription_expiry_reminders():
    now = timezone.now()
    # Define reminder periods, e.g., 7 days, 3 days, 1 day before expiry
    reminder_periods_days = [7, 3, 1]

    for days_before_expiry in reminder_periods_days:
        target_expiry_date_start = now + timedelta(days=days_before_expiry)
        target_expiry_date_end = target_expiry_date_start + timedelta(
            days=1
        )  # Full day range

        expiring_profiles = UserProfile.objects.filter(
            subscription_expires_at__gte=target_expiry_date_start,
            subscription_expires_at__lt=target_expiry_date_end,
            account_type="SUBSCRIBED",  # Only for active subscribed users
        ).select_related("user")

        for profile in expiring_profiles:
            # Avoid sending duplicate reminders for the same threshold
            # Check if a similar notification was sent recently for this specific threshold
            reminder_already_sent = Notification.objects.filter(
                recipient=profile.user,
                notification_type=NotificationTypeChoices.SUBSCRIPTION,
                verb__icontains="expiring",  # More robust check might use extra_data
                # Check if 'data' field contains days_before_expiry
                data__has_key="days_before_expiry",
                data__days_before_expiry=days_before_expiry,
                created_at__gte=now
                - timedelta(days=days_before_expiry + 1),  # Check within the period
            ).exists()

            if not reminder_already_sent:
                create_notification(
                    recipient=profile.user,
                    verb=_("your subscription is expiring soon"),
                    description=_(
                        "Heads up! Your Qader subscription will expire in {days} day(s) on {expiry_date}. "
                        "Renew now to maintain access."
                    ).format(
                        days=days_before_expiry,
                        expiry_date=profile.subscription_expires_at.strftime(
                            "%Y-%m-%d"
                        ),
                    ),
                    notification_type=NotificationTypeChoices.SUBSCRIPTION,
                    url="/profile/subscription/renew",  # Example URL
                    extra_data={
                        "days_before_expiry": days_before_expiry,
                        "expiry_timestamp": profile.subscription_expires_at.isoformat(),
                    },
                )
                logger.info(
                    f"Sent {days_before_expiry}-day subscription expiry reminder to {profile.user.username}"
                )
    return f"Subscription expiry reminders check complete. Processed for {len(reminder_periods_days)} periods."


@shared_task(name="dispatch_notification_email_task")
def dispatch_notification_email_task(
    notification_id: int,
    recipient_email: str,
    subject: str,
    body_template_name: str,
    context: dict,
):
    """
    Sends a notification email to a user.
    """
    logger.info(
        f"Attempting to send notification email for Notification ID {notification_id} to {recipient_email}"
    )
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings

        # Add site base URL to context for constructing full URLs in email
        # Ensure SITE_BASE_URL is configured in settings.py
        context["site_base_url"] = getattr(settings, "SITE_BASE_URL", "")
        if not context["site_base_url"]:
            logger.warning(
                "SITE_BASE_URL is not configured in Django settings. Email links may be broken."
            )

        html_message = render_to_string(f"{body_template_name}.html", context)
        plain_message = render_to_string(f"{body_template_name}.txt", context)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(
            f"Successfully sent notification email for Notification ID {notification_id} to {recipient_email}"
        )
    except Exception as e:
        logger.error(
            f"Error sending notification email for Notification ID {notification_id} to {recipient_email}: {e}",
            exc_info=True,
        )
