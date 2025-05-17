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
