from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import logging

from apps.notifications.services import create_notification
from apps.notifications.models import (
    NotificationTypeChoices,
)  # Ensure this exists in your notifications app
from .models import SupportTicket, SupportTicketReply

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=SupportTicketReply)
def send_support_ticket_reply_notification(
    sender, instance: SupportTicketReply, created: bool, **kwargs
):
    """
    Sends a notification when a new reply is added to a support ticket.
    - If a user replies, notifies the assigned admin (if any).
    - If an admin replies (and it's not an internal note), notifies the user who created the ticket.
    """
    if not created:
        return

    reply: SupportTicketReply = instance
    ticket: SupportTicket = reply.ticket
    replier: User = reply.user  # The user who made the reply

    recipient: User = None
    notification_verb_for_recipient = ""
    email_subject = ""
    # Define base URLs for your frontend. Adjust these to your actual frontend routes.
    # These URLs will be combined with SITE_BASE_URL in the email task.
    ticket_url_for_user = f"/profile/support/tickets/{ticket.id}/"
    ticket_url_for_admin = (
        f"/admin-panel/support-tickets/{ticket.id}/"  # Example for admin panel
    )
    final_ticket_url = ""

    # Case 1: A non-staff user (ticket owner) replied.
    # Notify the assigned admin (if any).
    if not replier.is_staff:
        # Basic check: ensure the replier is the owner of the ticket.
        if replier != ticket.user:
            logger.warning(
                f"Support ticket reply {reply.id} by non-staff user {replier.username} (ID: {replier.id}) "
                f"who is not the ticket owner {ticket.user.username} (ID: {ticket.user.id}). "
                f"Skipping notification logic for this reply."
            )
            return

        if ticket.assigned_to:
            recipient = ticket.assigned_to
            # Avoid admin notifying themselves if they were also the ticket creator and are assigned.
            if recipient == replier:
                logger.debug(
                    f"Admin {replier.username} (ID: {replier.id}) replied to a ticket they own and are assigned to. Skipping self-notification."
                )
                return

            # Verb is from the perspective of the recipient (the admin)
            notification_verb_for_recipient = _(
                "replied to support ticket #{ticket_id} which is assigned to you"
            ).format(ticket_id=ticket.id)

            email_subject = _(
                "New Reply on Support Ticket #{ticket_id}: {subject}"
            ).format(
                ticket_id=ticket.id,
                subject=ticket.subject[:75],  # Truncate subject for brevity
            )
            final_ticket_url = ticket_url_for_admin
        else:
            # No admin assigned. Product decision: notify a default group or log and do nothing.
            logger.info(
                f"User {replier.username} replied to unassigned ticket {ticket.id}. No admin assigned to notify."
            )
            return  # Explicitly stop if no admin is assigned

    # Case 2: A staff user (admin/support) replied.
    # Notify the ticket owner (user), unless it's an internal note.
    elif replier.is_staff:
        if reply.is_internal_note:
            # Internal notes are not for the end-user.
            # Future enhancement: could notify other relevant staff members.
            logger.info(
                f"Admin {replier.username} (ID: {replier.id}) added internal note to ticket {ticket.id}. No user notification will be sent."
            )
            return

        recipient = ticket.user
        # Avoid user notifying themselves if they are staff and also opened the ticket.
        if recipient == replier:
            logger.debug(
                f"User {replier.username} (ID: {replier.id}) (who is staff) replied to a ticket they also own. Skipping self-notification."
            )
            return

        # Verb is from the perspective of the recipient (the user)
        notification_verb_for_recipient = _(
            "replied to your support ticket #{ticket_id}"
        ).format(ticket_id=ticket.id)

        email_subject = _(
            "Update on your Support Ticket #{ticket_id}: {subject}"
        ).format(ticket_id=ticket.id, subject=ticket.subject[:75])
        final_ticket_url = ticket_url_for_user

    if recipient:
        # Ensure NotificationTypeChoices.SUPPORT_TICKET is defined in your notifications/models.py
        # e.g., SUPPORT_TICKET = "SUPPORT_TICKET", _("Support Ticket Update")
        create_notification(
            recipient=recipient,
            actor=replier,  # The user who performed the action (made the reply)
            verb=notification_verb_for_recipient,
            description=reply.message[:200],  # Snippet of the reply message
            target=ticket,  # The SupportTicket instance
            action_object=reply,  # The SupportTicketReply instance
            notification_type=NotificationTypeChoices.SUPPORT_TICKET,
            url=final_ticket_url,  # Relative URL for the frontend
            send_email=True,
            email_subject=email_subject,
            # Consider creating specific email templates for better formatting
            email_body_template_name="emails/generic_notification_email",
            extra_data={
                "ticket_id": str(ticket.id),
                "reply_id": str(reply.id),
                "replier_id": str(replier.id),
                "replier_username": replier.username,
                "ticket_subject": ticket.subject,
                "is_admin_reply": replier.is_staff,  # Useful for frontend to differentiate
            },
        )
        logger.info(
            f"Successfully queued support reply notification for ticket {ticket.id} (reply {reply.id}) "
            f"to {recipient.username} (ID: {recipient.id}) from {replier.username} (ID: {replier.id})"
        )
    else:
        logger.debug(
            f"No recipient determined for support reply {reply.id} on ticket {ticket.id} by {replier.username}. "
            "This might be intentional (e.g., internal note, unassigned ticket, or self-reply)."
        )
