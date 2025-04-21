import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import SupportTicket, SupportTicketReply
from .factories import (
    SupportTicketFactory,
    SupportTicketReplyFactory,
    UserFactory,
)  # Need UserFactory too

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

User = get_user_model()


class TestSupportTicketModel:

    def test_support_ticket_creation_defaults(self):
        """Test creating a ticket sets default values correctly."""
        ticket = SupportTicketFactory()

        assert ticket.pk is not None
        assert ticket.status == SupportTicket.Status.OPEN
        assert ticket.priority == SupportTicket.Priority.MEDIUM
        assert ticket.assigned_to is None
        assert ticket.closed_at is None
        assert ticket.created_at is not None
        assert ticket.updated_at is not None
        # Check timestamps are recent
        assert (timezone.now() - ticket.created_at).total_seconds() < 5
        assert (timezone.now() - ticket.updated_at).total_seconds() < 5

    def test_support_ticket_str_representation(self):
        """Test the __str__ method of the SupportTicket model."""
        ticket = SupportTicketFactory(subject="Test Subject String")
        expected_str = (
            f"Ticket #{ticket.pk} by {ticket.user.username} - Test Subject String"
        )
        assert str(ticket) == expected_str

    def test_last_reply_by_role_no_replies(self):
        """Test last_reply_by_role returns 'user' when there are no replies."""
        ticket = SupportTicketFactory()
        assert ticket.last_reply_by_role == "user"  # Initial creator is a user

    def test_last_reply_by_role_last_is_user(self):
        """Test last_reply_by_role returns 'user' when the last reply is by the ticket owner."""
        ticket_owner = UserFactory(is_staff=False)  # Ensure ticket owner is NOT staff
        ticket = SupportTicketFactory(user=ticket_owner)
        admin_user = UserFactory(is_staff=True)  # Ensure admin IS staff

        # Add explicit checks
        assert not ticket_owner.is_staff
        assert admin_user.is_staff

        # First reply by admin (older)
        SupportTicketReplyFactory(
            ticket=ticket,
            user=admin_user,
            created_at=timezone.now() - timezone.timedelta(minutes=10),
        )
        # Second (last) reply by user (newer)
        last_reply = SupportTicketReplyFactory(
            ticket=ticket,
            user=ticket_owner,  # Use the explicitly non-staff user
            created_at=timezone.now(),
        )

        # Add check on the user object of the last reply itself
        assert not last_reply.user.is_staff

        ticket.refresh_from_db()
        assert ticket.last_reply_by_role == "user"

    def test_last_reply_by_role_last_is_admin(self):
        """Test last_reply_by_role returns 'admin' when the last reply is by an admin."""
        ticket_owner = UserFactory(is_staff=False)  # Ensure ticket owner is NOT staff
        ticket = SupportTicketFactory(user=ticket_owner)
        admin_user = UserFactory(is_staff=True)  # Ensure admin IS staff

        # Add explicit checks
        assert not ticket_owner.is_staff
        assert admin_user.is_staff

        # First reply by user (older)
        SupportTicketReplyFactory(
            ticket=ticket,
            user=ticket_owner,
            created_at=timezone.now() - timezone.timedelta(minutes=10),
        )
        # Second (last) reply by admin (newer)
        last_reply = SupportTicketReplyFactory(
            ticket=ticket,
            user=admin_user,  # Use the explicitly staff user
            created_at=timezone.now(),
        )

        # Add check on the user object of the last reply itself
        assert last_reply.user.is_staff

        ticket.refresh_from_db()
        assert ticket.last_reply_by_role == "admin"

    def test_ticket_relationship_user(self):
        """Test the relationship between Ticket and User."""
        user = UserFactory()
        ticket = SupportTicketFactory(user=user)
        assert ticket.user == user
        assert ticket in user.support_tickets.all()

    def test_ticket_relationship_assigned_to(self):
        """Test the relationship between Ticket and Assigned Admin."""
        admin_user = UserFactory(is_staff=True)
        ticket = SupportTicketFactory(assigned_to=admin_user)
        assert ticket.assigned_to == admin_user
        assert ticket in admin_user.assigned_tickets.all()


class TestSupportTicketReplyModel:

    def test_reply_creation_defaults(self):
        """Test creating a reply sets default values correctly."""
        reply = SupportTicketReplyFactory()

        assert reply.pk is not None
        assert reply.is_internal_note is False
        assert reply.created_at is not None
        # Check timestamp is recent
        assert (timezone.now() - reply.created_at).total_seconds() < 5

    def test_reply_str_representation_public(self):
        """Test the __str__ method for a public reply."""
        reply = SupportTicketReplyFactory(is_internal_note=False)
        expected_str = f"Reply by {reply.user.username} on Ticket #{reply.ticket.pk} "  # Note trailing space from f-string
        assert (
            str(reply) == expected_str.strip()
        )  # Use strip to handle potential whitespace

    def test_reply_str_representation_internal(self):
        """Test the __str__ method for an internal note."""
        # Use trait to ensure user is staff and flag is set
        reply = SupportTicketReplyFactory(internal=True)
        expected_str = (
            f"Reply by {reply.user.username} on Ticket #{reply.ticket.pk} (Internal)"
        )
        assert str(reply) == expected_str

    def test_reply_relationship_ticket(self):
        """Test the relationship between Reply and Ticket."""
        ticket = SupportTicketFactory()
        reply = SupportTicketReplyFactory(ticket=ticket)
        assert reply.ticket == ticket
        assert reply in ticket.replies.all()

    def test_reply_relationship_user(self):
        """Test the relationship between Reply and User."""
        user = UserFactory()
        reply = SupportTicketReplyFactory(user=user)
        assert reply.user == user
        assert reply in user.support_replies.all()
