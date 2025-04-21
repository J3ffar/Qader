from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class SupportTicket(models.Model):
    """
    Manages support requests submitted by users via "Admin Support".
    """

    class IssueType(models.TextChoices):
        TECHNICAL = "technical", _("Technical")
        FINANCIAL = "financial", _("Financial")
        QUESTION_PROBLEM = "question_problem", _("Problem with a question")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")  # Newly submitted or user replied
        PENDING_ADMIN = "pending_admin", _(
            "Pending Admin Response"
        )  # Admin replied, waiting for user
        PENDING_USER = "pending_user", _(
            "Pending User Response"
        )  # Admin replied, waiting for user (Alternative naming if clearer)
        CLOSED = "closed", _("Closed")  # Resolved

    class Priority(models.IntegerChoices):
        HIGH = 1, _("High")
        MEDIUM = 2, _("Medium")
        LOW = 3, _("Low")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
        verbose_name=_("User"),
    )
    issue_type = models.CharField(
        max_length=20,
        choices=IssueType.choices,
        verbose_name=_("Issue Type"),
        db_index=True,
    )
    subject = models.CharField(max_length=255, verbose_name=_("Subject"))
    description = models.TextField(verbose_name=_("Description"))
    attachment = models.FileField(
        upload_to="support_attachments/%Y/%m/",
        blank=True,
        null=True,
        verbose_name=_("Attachment"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        verbose_name=_("Status"),
        db_index=True,
    )
    priority = models.IntegerField(
        choices=Priority.choices, default=Priority.MEDIUM, verbose_name=_("Priority")
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
        blank=True,
        null=True,
        verbose_name=_("Assigned To"),
        limit_choices_to={"is_staff": True},  # Only staff can be assigned
        db_index=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"), db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    closed_at = models.DateTimeField(blank=True, null=True, verbose_name=_("Closed At"))

    class Meta:
        verbose_name = _("Support Ticket")
        verbose_name_plural = _("Support Tickets")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"Ticket #{self.pk} by {self.user.username} - {self.subject}"

    @property
    def last_reply_by_role(self):
        last_reply = self.replies.order_by("-created_at").first()
        if last_reply:
            return "admin" if last_reply.user.is_staff else "user"
        return "user"  # Assume user created it initially


class SupportTicketReply(models.Model):
    """
    Stores replies exchanged within a support ticket thread.
    """

    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name=_("Ticket"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # If user deleted, their replies go too
        related_name="support_replies",
        verbose_name=_("User"),
    )
    message = models.TextField(verbose_name=_("Message"))
    is_internal_note = models.BooleanField(
        default=False, verbose_name=_("Internal Note (Admin Only)")
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"), db_index=True
    )
    updated_at = models.DateTimeField(  # Less useful here, maybe remove
        auto_now=True, verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Support Ticket Reply")
        verbose_name_plural = _("Support Ticket Replies")
        ordering = ["created_at"]

    def __str__(self):
        note = "(Internal)" if self.is_internal_note else ""
        return f"Reply by {self.user.username} on Ticket #{self.ticket.pk} {note}"
