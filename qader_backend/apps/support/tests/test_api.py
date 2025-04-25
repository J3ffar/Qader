import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.users.tests.factories import UserFactory

from ..models import SupportTicket, SupportTicketReply
from .factories import SupportTicketFactory, SupportTicketReplyFactory

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

# --- Test UserSupportTicketViewSet ---


class TestUserSupportTicketViewSet:

    def test_list_tickets_unauthenticated(self, api_client):
        url = reverse("api:v1:support:user-ticket-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_list_tickets_authenticated(self, authenticated_client):
        user = authenticated_client.user
        # Create tickets for the logged-in user and another user
        my_ticket = SupportTicketFactory(user=user)
        other_ticket = SupportTicketFactory()  # Belongs to a different user

        url = reverse("api:v1:support:user-ticket-list")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["id"] == my_ticket.id
        assert response.json()["results"][0]["subject"] == my_ticket.subject

    def test_create_ticket_unauthenticated(self, api_client):
        url = reverse("api:v1:support:user-ticket-list")
        data = {
            "issue_type": SupportTicket.IssueType.TECHNICAL,
            "subject": "Test Subject",
            "description": "Test description",
        }
        response = api_client.post(url, data=data)
        assert response.status_code == 401

    def test_create_ticket_valid_data(self, authenticated_client):
        url = reverse("api:v1:support:user-ticket-list")
        data = {
            "issue_type": SupportTicket.IssueType.TECHNICAL,
            "subject": "Login Issue",
            "description": "I cannot log in to my account.",
        }
        response = authenticated_client.post(url, data=data)

        assert response.status_code == 201
        assert SupportTicket.objects.count() == 1
        ticket = SupportTicket.objects.first()
        assert ticket.user == authenticated_client.user
        assert ticket.subject == "Login Issue"
        assert ticket.status == SupportTicket.Status.OPEN
        assert response.json()["subject"] == "Login Issue"
        assert response.json()["issue_type"] == SupportTicket.IssueType.TECHNICAL

    def test_create_ticket_invalid_data(self, authenticated_client):
        url = reverse("api:v1:support:user-ticket-list")
        data = {"subject": "Missing fields"}  # Missing issue_type and description
        response = authenticated_client.post(url, data=data)

        assert response.status_code == 400
        assert "issue_type" in response.json()
        assert "description" in response.json()
        assert SupportTicket.objects.count() == 0

    # Optional: Test with attachment (requires storage setup or mocking)
    # def test_create_ticket_with_attachment(self, authenticated_client):
    #     url = reverse("api:v1:support:user-ticket-list")
    #     attachment = SimpleUploadedFile("test.txt", b"file_content", content_type="text/plain")
    #     data = {
    #         "issue_type": SupportTicket.IssueType.OTHER,
    #         "subject": "File Upload Test",
    #         "description": "See attached file.",
    #         "attachment": attachment,
    #     }
    #     response = authenticated_client.post(url, data=data, format='multipart')
    #     assert response.status_code == 201
    #     ticket = SupportTicket.objects.first()
    #     assert ticket.attachment is not None
    #     assert 'test.txt' in ticket.attachment.name

    def test_retrieve_own_ticket(self, authenticated_client):
        ticket = SupportTicketFactory(user=authenticated_client.user)
        SupportTicketReplyFactory(
            ticket=ticket, user=authenticated_client.user
        )  # Add a reply
        SupportTicketReplyFactory(
            ticket=ticket, user=SupportTicketFactory().user, is_internal_note=True
        )  # Internal note

        url = reverse("api:v1:support:user-ticket-detail", kwargs={"pk": ticket.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.json()["id"] == ticket.id
        assert response.json()["subject"] == ticket.subject
        # User should only see non-internal replies
        assert len(response.json()["replies"]) == 1
        assert response.json()["replies"][0]["is_internal_note"] is False

    def test_retrieve_other_user_ticket(self, authenticated_client):
        other_ticket = SupportTicketFactory()  # Belongs to a different user
        url = reverse(
            "api:v1:support:user-ticket-detail", kwargs={"pk": other_ticket.pk}
        )
        response = authenticated_client.get(url)
        # Since get_queryset filters, this should be 404
        assert response.status_code == 404

    def test_retrieve_non_existent_ticket(self, authenticated_client):
        url = reverse("api:v1:support:user-ticket-detail", kwargs={"pk": 999})
        response = authenticated_client.get(url)
        assert response.status_code == 404

    # --- Reply Tests ---
    def test_list_replies_own_ticket(self, authenticated_client):
        ticket = SupportTicketFactory(user=authenticated_client.user)
        reply1 = SupportTicketReplyFactory(
            ticket=ticket, user=authenticated_client.user
        )
        reply2 = SupportTicketReplyFactory(
            ticket=ticket, user=SupportTicketFactory().user
        )  # Admin reply
        reply3 = SupportTicketReplyFactory(
            ticket=ticket, user=SupportTicketFactory().user, is_internal_note=True
        )  # Internal

        url = reverse("api:v1:support:user-ticket-replies", kwargs={"pk": ticket.pk})
        response = authenticated_client.get(url)

        assert response.status_code == 200
        # User sees only non-internal notes
        assert len(response.json()) == 2
        reply_ids = {r["id"] for r in response.json()}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids
        assert reply3.id not in reply_ids

    def test_list_replies_other_user_ticket(self, authenticated_client):
        other_ticket = SupportTicketFactory()
        SupportTicketReplyFactory(ticket=other_ticket)
        url = reverse(
            "api:v1:support:user-ticket-replies", kwargs={"pk": other_ticket.pk}
        )
        response = authenticated_client.get(url)
        # Custom action permission check fails before queryset check
        assert response.status_code == 404  # IsTicketOwner permission fails

    def test_create_reply_own_ticket(self, authenticated_client):
        ticket = SupportTicketFactory(
            user=authenticated_client.user, status=SupportTicket.Status.PENDING_USER
        )
        url = reverse("api:v1:support:user-ticket-replies", kwargs={"pk": ticket.pk})
        data = {"message": "Thanks for the update!"}

        response = authenticated_client.post(url, data=data)
        assert response.status_code == 201
        assert SupportTicketReply.objects.count() == 1
        reply = SupportTicketReply.objects.first()
        assert reply.user == authenticated_client.user
        assert reply.ticket == ticket
        assert reply.message == data["message"]
        assert reply.is_internal_note is False  # User cannot set this
        assert response.json()["message"] == data["message"]

        # Check if ticket status was updated
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.OPEN

    def test_create_reply_other_user_ticket(self, authenticated_client):
        other_ticket = SupportTicketFactory()
        url = reverse(
            "api:v1:support:user-ticket-replies", kwargs={"pk": other_ticket.pk}
        )
        data = {"message": "Trying to reply"}
        response = authenticated_client.post(url, data=data)
        # Custom action permission check fails
        assert response.status_code == 404  # IsTicketOwner permission fails

    def test_create_reply_cannot_set_internal(self, authenticated_client):
        ticket = SupportTicketFactory(user=authenticated_client.user)
        url = reverse("api:v1:support:user-ticket-replies", kwargs={"pk": ticket.pk})
        # Attempt to set is_internal_note as a regular user
        data = {"message": "Secret message", "is_internal_note": True}

        response = authenticated_client.post(url, data=data)
        assert response.status_code == 201
        reply = SupportTicketReply.objects.first()
        # Should ignore the is_internal_note field from user input
        assert reply.is_internal_note is False


# --- Test AdminSupportTicketViewSet ---


class TestAdminSupportTicketViewSet:

    def test_admin_list_tickets_unauthenticated(self, api_client):
        url = reverse("api:v1:admin_panel:admin-ticket-list")
        response = api_client.get(url)
        assert response.status_code == 401

    def test_admin_list_tickets_non_admin(self, authenticated_client):
        url = reverse("api:v1:admin_panel:admin-ticket-list")
        response = authenticated_client.get(url)
        assert response.status_code == 403

    def test_admin_list_all_tickets(self, admin_client):
        user1_ticket = SupportTicketFactory()
        user2_ticket = SupportTicketFactory()
        url = reverse("api:v1:admin_panel:admin-ticket-list")
        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json()["count"] == 2
        ticket_ids = {t["id"] for t in response.json()["results"]}
        assert user1_ticket.id in ticket_ids
        assert user2_ticket.id in ticket_ids

    def test_admin_list_filter_by_status(self, admin_client):
        open_ticket = SupportTicketFactory(status=SupportTicket.Status.OPEN)
        closed_ticket = SupportTicketFactory(status=SupportTicket.Status.CLOSED)
        url = reverse("api:v1:admin_panel:admin-ticket-list")
        response = admin_client.get(url, {"status": SupportTicket.Status.OPEN})

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["results"][0]["id"] == open_ticket.id

    def test_admin_retrieve_any_ticket(self, admin_client):
        ticket = SupportTicketFactory()
        # Add replies including internal note
        SupportTicketReplyFactory(ticket=ticket, user=ticket.user)
        SupportTicketReplyFactory(
            ticket=ticket, internal=True
        )  # Internal note by admin

        url = reverse(
            "api:v1:admin_panel:admin-ticket-detail", kwargs={"pk": ticket.pk}
        )
        response = admin_client.get(url)

        assert response.status_code == 200
        assert response.json()["id"] == ticket.id
        # Admin should see all replies
        assert len(response.json()["replies"]) == 2
        assert any(r["is_internal_note"] for r in response.json()["replies"])

    def test_admin_update_ticket(self, admin_client, admin_user):
        ticket = SupportTicketFactory(status=SupportTicket.Status.OPEN)
        assignee_admin = UserFactory(is_staff=True)  # Create another admin to assign to

        url = reverse(
            "api:v1:admin_panel:admin-ticket-detail", kwargs={"pk": ticket.pk}
        )
        data = {
            "status": SupportTicket.Status.PENDING_USER,
            "priority": SupportTicket.Priority.HIGH,
            "assigned_to_id": assignee_admin.id,
        }
        response = admin_client.patch(url, data=data)

        assert response.status_code == 200
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.PENDING_USER
        assert ticket.priority == SupportTicket.Priority.HIGH
        assert ticket.assigned_to == assignee_admin
        assert response.json()["status"] == SupportTicket.Status.PENDING_USER
        assert response.json()["priority"] == SupportTicket.Priority.HIGH
        assert response.json()["assigned_to"]["id"] == assignee_admin.id

    def test_admin_update_sets_closed_at(self, admin_client):
        ticket = SupportTicketFactory(status=SupportTicket.Status.OPEN, closed_at=None)
        url = reverse(
            "api:v1:admin_panel:admin-ticket-detail", kwargs={"pk": ticket.pk}
        )
        data = {"status": SupportTicket.Status.CLOSED}
        response = admin_client.patch(url, data=data)

        assert response.status_code == 200
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.CLOSED
        assert ticket.closed_at is not None
        assert ticket.closed_at <= timezone.now()

    def test_admin_update_clears_closed_at(self, admin_client):
        ticket = SupportTicketFactory(
            status=SupportTicket.Status.CLOSED, closed_at=timezone.now()
        )
        url = reverse(
            "api:v1:admin_panel:admin-ticket-detail", kwargs={"pk": ticket.pk}
        )
        data = {"status": SupportTicket.Status.OPEN}
        response = admin_client.patch(url, data=data)

        assert response.status_code == 200
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.OPEN
        assert ticket.closed_at is None  # Should be cleared

    def test_admin_delete_ticket(self, admin_client):
        ticket = SupportTicketFactory()
        url = reverse(
            "api:v1:admin_panel:admin-ticket-detail", kwargs={"pk": ticket.pk}
        )
        response = admin_client.delete(url)

        assert response.status_code == 204
        assert SupportTicket.objects.count() == 0

    # --- Admin Reply Tests ---
    def test_admin_list_replies_shows_internal(self, admin_client):
        ticket = SupportTicketFactory()
        reply1 = SupportTicketReplyFactory(ticket=ticket, user=ticket.user)
        reply2 = SupportTicketReplyFactory(
            ticket=ticket, internal=True
        )  # Internal note

        url = reverse(
            "api:v1:admin_panel:admin-ticket-replies", kwargs={"pk": ticket.pk}
        )
        response = admin_client.get(url)

        assert response.status_code == 200
        # Admin sees all notes
        assert len(response.json()) == 2
        reply_ids = {r["id"] for r in response.json()}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids

    def test_admin_create_reply_public(self, admin_client):
        ticket = SupportTicketFactory(status=SupportTicket.Status.OPEN)
        url = reverse(
            "api:v1:admin_panel:admin-ticket-replies", kwargs={"pk": ticket.pk}
        )
        data = {"message": "Admin response"}

        response = admin_client.post(url, data=data)
        assert response.status_code == 201
        assert SupportTicketReply.objects.count() == 1
        reply = SupportTicketReply.objects.first()
        assert reply.user == admin_client.user
        assert reply.ticket == ticket
        assert reply.message == data["message"]
        assert reply.is_internal_note is False
        assert response.json()["message"] == data["message"]

        # Check ticket status updated
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.PENDING_USER  # Or PENDING_ADMIN

    def test_admin_create_reply_internal(self, admin_client):
        ticket = SupportTicketFactory(status=SupportTicket.Status.OPEN)
        url = reverse(
            "api:v1:admin_panel:admin-ticket-replies", kwargs={"pk": ticket.pk}
        )
        data = {"message": "Internal discussion note", "is_internal_note": True}

        response = admin_client.post(url, data=data)
        assert response.status_code == 201
        assert SupportTicketReply.objects.count() == 1
        reply = SupportTicketReply.objects.first()
        assert reply.user == admin_client.user
        assert reply.ticket == ticket
        assert reply.is_internal_note is True

        # Check ticket status DID NOT change for internal note
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.OPEN
