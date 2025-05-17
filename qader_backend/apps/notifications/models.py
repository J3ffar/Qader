from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class NotificationTypeChoices(models.TextChoices):
    # General Types
    INFO = "INFO", _("Information")
    SUCCESS = "SUCCESS", _("Success")
    WARNING = "WARNING", _("Warning")
    ERROR = "ERROR", _("Error")
    SYSTEM = "SYSTEM", _("System Update")

    # App-Specific (can be expanded)
    USER_PROFILE = "USER_PROFILE", _("User Profile Update")
    SUBSCRIPTION = "SUBSCRIPTION", _("Subscription Update")
    BADGE_EARNED = "BADGE_EARNED", _("Badge Earned")
    COMMUNITY_POST = "COMMUNITY_POST", _("Community Post Interaction")
    COMMUNITY_REPLY = "COMMUNITY_REPLY", _("Community Reply Interaction")
    CHALLENGE_INVITE = "CHALLENGE_INVITE", _("Challenge Invitation")
    CHALLENGE_UPDATE = "CHALLENGE_UPDATE", _("Challenge Update")
    MENTOR_ASSIGNMENT = "MENTOR_ASSIGNMENT", _("Mentor Assignment")
    SUPPORT_TICKET = "SUPPORT_TICKET", _("Support Ticket Update")
    # Add more types as your application grows


class Notification(models.Model):
    """
    Represents a notification for a user.
    Inspired by activity stream patterns.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Recipient"),
        db_index=True,
    )
    # The user who performed the action (optional, system notifications might not have an actor)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_notifications",
        verbose_name=_("Actor"),
    )
    verb = models.CharField(
        _("Verb"),
        max_length=255,
        help_text=_(
            "A short description of the action, e.g., 'liked your post', 'earned a new badge'."
        ),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_(
            "Optional: More detailed text for the notification. Can include simple HTML if rendered carefully."
        ),
    )

    # Target: The primary object the notification is about (e.g., the CommunityPost that was liked)
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_target",
    )
    target_object_id = models.CharField(
        _("Target Object ID"), max_length=255, null=True, blank=True, db_index=True
    )  # Use CharField for UUIDs too
    target = GenericForeignKey("target_content_type", "target_object_id")

    # Action Object: An optional secondary object related to the action (e.g., the Like object itself, or a Comment)
    action_object_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_action_object",
    )
    action_object_object_id = models.CharField(
        _("Action Object ID"), max_length=255, null=True, blank=True, db_index=True
    )
    action_object = GenericForeignKey(
        "action_object_content_type", "action_object_object_id"
    )

    notification_type = models.CharField(
        _("Notification Type"),
        max_length=20,
        choices=NotificationTypeChoices.choices,
        default=NotificationTypeChoices.INFO,
        db_index=True,
    )
    is_read = models.BooleanField(_("Is Read?"), default=False, db_index=True)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    created_at = models.DateTimeField(
        _("Created At"), default=timezone.now, db_index=True
    )  # Use default=timezone.now

    # A direct URL the user can navigate to when clicking the notification
    url = models.URLField(_("URL"), max_length=500, blank=True, null=True)
    # Additional data that might be useful for frontend rendering or logic
    data = models.JSONField(_("Additional Data"), null=True, blank=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["target_content_type", "target_object_id"]),
            models.Index(
                fields=["action_object_content_type", "action_object_object_id"]
            ),
        ]

    def __str__(self):
        parts = [str(self.recipient), self.verb]
        if self.actor:
            parts.insert(0, str(self.actor))
        if self.target:
            parts.append(f"on {self.target}")
        return " ".join(parts)

    def mark_as_read(self, save=True):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            if save:
                self.save(
                    update_fields=["is_read", "read_at", "data"]
                )  # Include data if it changes on read

    def mark_as_unread(self, save=True):
        if self.is_read:
            self.is_read = False
            self.read_at = None
            if save:
                self.save(update_fields=["is_read", "read_at", "data"])
