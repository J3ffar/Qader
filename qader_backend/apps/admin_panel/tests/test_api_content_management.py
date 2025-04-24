import pytest
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone

from rest_framework import status

from apps.content import models as content_models

# Assuming factories are in apps.content.tests.factories
from apps.content.tests.factories import (
    PageFactory,
    FAQCategoryFactory,
    FAQItemFactory,
    PartnerCategoryFactory,
    HomepageFeatureCardFactory,
    HomepageStatisticFactory,
    ContactMessageFactory,
)

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- Test Helper Function ---
def check_permission_denied(client, url):
    """Checks for 401 Unauthorized or 403 Forbidden."""
    response = client.get(url)
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ]
    response = client.post(url, {})  # Check POST as well
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ]


# === Test PageAdminViewSet ===


class TestPageAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-pages-list")

    @staticmethod
    def detail_url(page_slug):
        return reverse(
            "api:v1:admin_panel:admin-pages-detail", kwargs={"slug": page_slug}
        )

    def test_permissions(self, api_client, authenticated_client, subscribed_client):
        page = PageFactory()
        check_permission_denied(api_client, self.LIST_URL)
        check_permission_denied(authenticated_client, self.LIST_URL)
        check_permission_denied(subscribed_client, self.LIST_URL)
        check_permission_denied(api_client, self.detail_url(page.slug))
        check_permission_denied(authenticated_client, self.detail_url(page.slug))
        check_permission_denied(subscribed_client, self.detail_url(page.slug))

    def test_list_pages_admin(self, admin_client):
        PageFactory.create_batch(3)
        response = admin_client.get(self.LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert len(response.data["results"]) == 3
        assert "title" in response.data["results"][0]
        assert "slug" in response.data["results"][0]
        assert "is_published" in response.data["results"][0]  # Admin sees this

    def test_retrieve_page_admin(self, admin_client):
        page = PageFactory(title="My Test Page", content="<p>Content</p>")
        response = admin_client.get(self.detail_url(page.slug))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == page.title
        assert response.data["content"] == page.content
        assert response.data["slug"] == page.slug

    def test_create_page_admin(self, admin_client):
        payload = {
            "title": "New Created Page",
            "slug": "new-created-page",
            "content": "Some content here.",
            "is_published": True,
            "icon_class": "icon-new",
        }
        response = admin_client.post(self.LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == payload["title"]
        assert response.data["slug"] == payload["slug"]
        assert content_models.Page.objects.filter(slug=payload["slug"]).exists()

    def test_create_page_invalid_admin(self, admin_client):
        payload = {"content": "Only content"}  # Missing required fields
        response = admin_client.post(self.LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data
        assert "slug" in response.data

    def test_update_page_admin(self, admin_client):
        page = PageFactory(is_published=True)
        payload = {
            "title": "Updated Page Title",
            "slug": page.slug,  # Slug typically doesn't change in PUT but required
            "content": "Updated content.",
            "is_published": False,
            "icon_class": "icon-updated",
        }
        response = admin_client.put(self.detail_url(page.slug), payload)
        assert response.status_code == status.HTTP_200_OK
        page.refresh_from_db()
        assert page.title == payload["title"]
        assert page.content == payload["content"]
        assert page.is_published == payload["is_published"]
        assert page.icon_class == payload["icon_class"]

    def test_partial_update_page_admin(self, admin_client):
        page = PageFactory(title="Original Title", is_published=True)
        payload = {"is_published": False}
        response = admin_client.patch(self.detail_url(page.slug), payload)
        assert response.status_code == status.HTTP_200_OK
        page.refresh_from_db()
        assert page.title == "Original Title"  # Not changed
        assert page.is_published is False  # Changed

    def test_delete_page_admin(self, admin_client):
        page = PageFactory()
        response = admin_client.delete(self.detail_url(page.slug))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not content_models.Page.objects.filter(slug=page.slug).exists()

    def test_search_page_admin(self, admin_client):
        PageFactory(
            title="Specific Search Term", content="Content for the target page."
        )
        PageFactory(
            title="Another Page", content="Unique text for the non-matching item."
        )
        response = admin_client.get(self.LIST_URL + "?search=Specific")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Specific Search Term"


# === Test FAQCategoryAdminViewSet ===


class TestFAQCategoryAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-faq-categories-list")

    @staticmethod
    def detail_url(cat_id):
        return reverse(
            "api:v1:admin_panel:admin-faq-categories-detail", kwargs={"pk": cat_id}
        )

    def test_permissions(self, api_client, authenticated_client, subscribed_client):
        cat = FAQCategoryFactory()
        check_permission_denied(api_client, self.LIST_URL)
        check_permission_denied(authenticated_client, self.LIST_URL)
        check_permission_denied(subscribed_client, self.LIST_URL)
        check_permission_denied(api_client, self.detail_url(cat.id))
        check_permission_denied(authenticated_client, self.detail_url(cat.id))
        check_permission_denied(subscribed_client, self.detail_url(cat.id))

    def test_list_faq_categories_admin(self, admin_client):
        FAQCategoryFactory.create_batch(2)
        response = admin_client.get(self.LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert "name" in response.data["results"][0]
        assert "order" in response.data["results"][0]

    def test_create_faq_category_admin(self, admin_client):
        payload = {"name": "New Category", "order": 5}
        response = admin_client.post(self.LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert content_models.FAQCategory.objects.filter(name=payload["name"]).exists()

    def test_update_faq_category_admin(self, admin_client):
        cat = FAQCategoryFactory(order=1)
        payload = {"name": "Updated Category Name", "order": 10}
        response = admin_client.put(self.detail_url(cat.id), payload)
        assert response.status_code == status.HTTP_200_OK
        cat.refresh_from_db()
        assert cat.name == payload["name"]
        assert cat.order == payload["order"]

    def test_delete_faq_category_admin(self, admin_client):
        cat = FAQCategoryFactory()
        # Create an item in it to test cascade delete if applicable (depends on FK settings)
        FAQItemFactory(category=cat)
        response = admin_client.delete(self.detail_url(cat.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not content_models.FAQCategory.objects.filter(id=cat.id).exists()
        # assert not content_models.FAQItem.objects.filter(category_id=cat.id).exists() # Check cascade


# === Test FAQItemAdminViewSet ===


class TestFAQItemAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-faq-items-list")

    @staticmethod
    def detail_url(item_id):
        return reverse(
            "api:v1:admin_panel:admin-faq-items-detail", kwargs={"pk": item_id}
        )

    def test_permissions(self, api_client, authenticated_client, subscribed_client):
        item = FAQItemFactory()
        check_permission_denied(api_client, self.LIST_URL)
        check_permission_denied(authenticated_client, self.LIST_URL)
        check_permission_denied(subscribed_client, self.LIST_URL)
        check_permission_denied(api_client, self.detail_url(item.id))
        check_permission_denied(authenticated_client, self.detail_url(item.id))
        check_permission_denied(subscribed_client, self.detail_url(item.id))

    def test_list_faq_items_admin(self, admin_client):
        cat = FAQCategoryFactory()
        FAQItemFactory.create_batch(3, category=cat)
        response = admin_client.get(self.LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert "question" in response.data["results"][0]
        assert "answer" in response.data["results"][0]
        assert "category" in response.data["results"][0]

    def test_create_faq_item_admin(self, admin_client):
        cat = FAQCategoryFactory()
        payload = {
            "category": cat.id,
            "question": "What is the capital of Testing?",
            "answer": "Pytestville",
            "is_active": True,
            "order": 1,
        }
        response = admin_client.post(self.LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert content_models.FAQItem.objects.filter(
            question=payload["question"]
        ).exists()

    def test_update_faq_item_admin(self, admin_client):
        item = FAQItemFactory(is_active=True)
        new_cat = FAQCategoryFactory()
        payload = {
            "category": new_cat.id,
            "question": item.question,
            "answer": "Updated Answer",
            "is_active": False,
            "order": item.order,
        }
        response = admin_client.put(self.detail_url(item.id), payload)
        assert response.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.answer == payload["answer"]
        assert item.is_active is False
        assert item.category == new_cat

    def test_delete_faq_item_admin(self, admin_client):
        item = FAQItemFactory()
        response = admin_client.delete(self.detail_url(item.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not content_models.FAQItem.objects.filter(id=item.id).exists()

    def test_filter_faq_items_admin(self, admin_client):
        cat1 = FAQCategoryFactory(name="Cat One")
        cat2 = FAQCategoryFactory(name="Cat Two")
        FAQItemFactory(category=cat1, is_active=True)
        FAQItemFactory(category=cat2, is_active=True)
        FAQItemFactory(category=cat1, is_active=False)

        # Filter by category
        response = admin_client.get(self.LIST_URL + f"?category={cat1.id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # Both active and inactive in this cat

        # Filter by active status
        response = admin_client.get(self.LIST_URL + "?is_active=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        # Filter by both
        response = admin_client.get(
            self.LIST_URL + f"?category={cat1.id}&is_active=true"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1


# === Test PartnerCategoryAdminViewSet ===
# (Structure similar to FAQCategoryAdminViewSet - Adapt fields)
class TestPartnerCategoryAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-partner-categories-list")

    @staticmethod
    def detail_url(pk):
        return reverse(
            "api:v1:admin_panel:admin-partner-categories-detail", kwargs={"pk": pk}
        )

    # Add tests for permissions, list, create, update, delete similar to above


# === Test HomepageFeatureCardAdminViewSet ===
# (Structure similar to FAQCategoryAdminViewSet - Adapt fields)
class TestHomepageFeatureCardAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-homepage-features-list")

    @staticmethod
    def detail_url(pk):
        return reverse(
            "api:v1:admin_panel:admin-homepage-features-detail", kwargs={"pk": pk}
        )

    # Add tests for permissions, list, create, update, delete similar to above


# === Test HomepageStatisticAdminViewSet ===
# (Structure similar to FAQCategoryAdminViewSet - Adapt fields)
class TestHomepageStatisticAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-homepage-stats-list")

    @staticmethod
    def detail_url(pk):
        return reverse(
            "api:v1:admin_panel:admin-homepage-stats-detail", kwargs={"pk": pk}
        )

    # Add tests for permissions, list, create, update, delete similar to above


# === Test ContactMessageAdminViewSet ===


class TestContactMessageAdminViewSet:
    LIST_URL = reverse("api:v1:admin_panel:admin-contact-messages-list")

    @staticmethod
    def detail_url(msg_id):
        return reverse(
            "api:v1:admin_panel:admin-contact-messages-detail", kwargs={"pk": msg_id}
        )

    def test_permissions(self, api_client, authenticated_client, subscribed_client):
        msg = ContactMessageFactory()
        check_permission_denied(api_client, self.LIST_URL)
        check_permission_denied(authenticated_client, self.LIST_URL)
        check_permission_denied(subscribed_client, self.LIST_URL)
        check_permission_denied(api_client, self.detail_url(msg.id))
        check_permission_denied(authenticated_client, self.detail_url(msg.id))
        check_permission_denied(subscribed_client, self.detail_url(msg.id))

    def test_list_contact_messages_admin(self, admin_client):
        ContactMessageFactory.create_batch(3)
        response = admin_client.get(self.LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3
        assert "full_name" in response.data["results"][0]
        assert "subject" in response.data["results"][0]
        assert "status" in response.data["results"][0]

    def test_retrieve_contact_message_admin(self, admin_client):
        msg = ContactMessageFactory()
        response = admin_client.get(self.detail_url(msg.id))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == msg.id
        assert response.data["email"] == msg.email

    def test_create_contact_message_not_allowed(self, admin_client):
        # Admins should not create contact messages via API
        payload = {
            "full_name": "Admin",
            "email": "admin@test.com",
            "subject": "Test",
            "message": "Test",
        }
        response = admin_client.post(self.LIST_URL, payload)
        # Method Not Allowed because we removed CreateModelMixin
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_update_contact_message_status_admin(self, admin_client, admin_user):
        msg = ContactMessageFactory(status=content_models.ContactMessage.STATUS_NEW)
        payload = {"status": content_models.ContactMessage.STATUS_READ}
        response = admin_client.patch(self.detail_url(msg.id), payload)
        assert response.status_code == status.HTTP_200_OK
        msg.refresh_from_db()
        assert msg.status == content_models.ContactMessage.STATUS_READ
        assert msg.responder is None
        assert msg.responded_at is None

    def test_update_contact_message_response_admin(self, admin_client, admin_user):
        msg = ContactMessageFactory(status=content_models.ContactMessage.STATUS_READ)
        payload = {
            "status": content_models.ContactMessage.STATUS_REPLIED,
            "response": "Here is the admin response.",
        }
        response = admin_client.patch(self.detail_url(msg.id), payload)
        assert response.status_code == status.HTTP_200_OK
        msg.refresh_from_db()
        assert msg.status == content_models.ContactMessage.STATUS_REPLIED
        assert msg.response == payload["response"]
        assert msg.responder == admin_user
        assert msg.responded_at is not None
        # Check that responded_at is recent
        assert timezone.now() - msg.responded_at < timezone.timedelta(seconds=10)

    def test_update_contact_message_invalid_status_admin(self, admin_client):
        msg = ContactMessageFactory()
        payload = {"status": "invalid-status"}
        response = admin_client.patch(self.detail_url(msg.id), payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data

    def test_delete_contact_message_admin(self, admin_client):
        msg = ContactMessageFactory()
        response = admin_client.delete(self.detail_url(msg.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not content_models.ContactMessage.objects.filter(id=msg.id).exists()

    def test_filter_contact_message_admin(self, admin_client):
        ContactMessageFactory(status=content_models.ContactMessage.STATUS_NEW)
        ContactMessageFactory(status=content_models.ContactMessage.STATUS_REPLIED)
        ContactMessageFactory(status=content_models.ContactMessage.STATUS_NEW)

        response = admin_client.get(
            self.LIST_URL + f"?status={content_models.ContactMessage.STATUS_NEW}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        response = admin_client.get(
            self.LIST_URL + f"?status={content_models.ContactMessage.STATUS_REPLIED}"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
