# apps/admin_panel/tests/test_api_blog_management.py

import pytest
from django.urls import reverse
from rest_framework import status

# Factories
from apps.blog.tests.factories import BlogPostFactory, BlogAdviceRequestFactory
from apps.users.tests.factories import UserFactory
from apps.support.tests.factories import (
    SupportTicketFactory,
)  # Assuming this factory exists

# Models
from apps.blog.models import (
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
    AdviceRequestStatusChoices,
)
from apps.users.models import User

# Use database marker from pytest-django
pytestmark = pytest.mark.django_db

# --- Test AdminBlogPostViewSet ---


class TestAdminBlogPostAPI:
    """Tests for the Admin BlogPost API endpoints."""

    list_url = reverse("api:v1:admin_panel:admin-blogpost-list")  # Use router basename

    def detail_url(self, slug):
        """Helper to get detail URL for a blog post slug."""
        return reverse(
            "api:v1:admin_panel:admin-blogpost-detail", kwargs={"slug": slug}
        )

    # --- Authorization Tests ---
    def test_list_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_non_admin(self, authenticated_client):  # Standard user
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_non_admin(self, authenticated_client):
        payload = {"title": "Attempt", "content": "Denied"}
        response = authenticated_client.post(self.list_url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- List View Tests (Admin) ---
    def test_list_blog_posts_admin(self, admin_client):
        BlogPostFactory.create_batch(5)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        assert (
            len(response.data["results"]) == 5
        )  # Assuming default pagination covers 5

    def test_list_filter_by_status(self, admin_client):
        BlogPostFactory(status=PostStatusChoices.PUBLISHED)
        BlogPostFactory(status=PostStatusChoices.DRAFT)
        BlogPostFactory(status=PostStatusChoices.PUBLISHED)

        response = admin_client.get(
            self.list_url, {"status": PostStatusChoices.PUBLISHED}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        for post in response.data["results"]:
            assert post["status"] == PostStatusChoices.PUBLISHED

        response = admin_client.get(self.list_url, {"status": PostStatusChoices.DRAFT})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_search(self, admin_client):
        BlogPostFactory(title="Unique Search Term Alpha")
        BlogPostFactory(content="Contains Beta the search word")
        BlogPostFactory(title="Something Else")

        response = admin_client.get(self.list_url, {"search": "Alpha"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == "Unique Search Term Alpha"

        response = admin_client.get(self.list_url, {"search": "Beta"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert "Beta" in response.data["results"][0]["content"]

    # --- Create View Tests (Admin) ---
    def test_create_blog_post_admin(self, admin_client, admin_user: User):
        payload = {
            "title": "New Admin Post",
            "content": "Detailed content here.",
            "status": PostStatusChoices.DRAFT,
            "tags": ["new", "admin", "test"],
            "author": admin_user.pk,  # Assign author
        }
        response = admin_client.post(
            self.list_url, payload, format="json"
        )  # Use format='json' for list tags

        assert response.status_code == status.HTTP_201_CREATED
        assert BlogPost.objects.count() == 1
        post = BlogPost.objects.first()
        assert post.title == payload["title"]
        assert post.author == admin_user
        assert post.status == payload["status"]
        assert post.slug == "new-admin-post"  # Check auto-slug
        assert set(post.tags.names()) == set(payload["tags"])
        assert response.data["title"] == payload["title"]
        assert response.data["author"] == admin_user.pk
        assert set(response.data["tags"]) == set(payload["tags"])

    def test_create_post_published_sets_published_at(self, admin_client):
        payload = {
            "title": "Publish Now",
            "content": "Go live.",
            "status": PostStatusChoices.PUBLISHED,
        }
        response = admin_client.post(self.list_url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        post = BlogPost.objects.get(pk=response.data["id"])
        assert post.status == PostStatusChoices.PUBLISHED
        assert post.published_at is not None

    def test_create_post_invalid_data(self, admin_client):
        payload = {"content": "Missing title"}  # Missing required title
        response = admin_client.post(self.list_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "title" in response.data

    # --- Retrieve View Tests (Admin) ---
    def test_retrieve_blog_post_admin(self, admin_client):
        post = BlogPostFactory(title="Retrieve Me", status=PostStatusChoices.PUBLISHED)
        url = self.detail_url(post.slug)
        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == post.id
        assert response.data["title"] == post.title
        assert response.data["status"] == PostStatusChoices.PUBLISHED
        assert response.data["author_username"] == post.author.username

    def test_retrieve_non_existent_post(self, admin_client):
        url = self.detail_url("non-existent-slug")
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- Update View Tests (Admin) ---
    def test_update_blog_post_admin_patch(self, admin_client, admin_user):
        other_admin = UserFactory(make_admin=True, username="otheradmin")
        post = BlogPostFactory(status=PostStatusChoices.DRAFT, author=admin_user)
        url = self.detail_url(post.slug)
        payload = {
            "title": "Updated Title",
            "status": PostStatusChoices.PUBLISHED,
            "tags": ["updated", "published"],
            "author": other_admin.pk,
        }
        response = admin_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == payload["title"]
        assert post.status == payload["status"]
        assert post.author == other_admin
        assert set(post.tags.names()) == set(payload["tags"])
        assert (
            post.published_at is not None
        )  # Should be set on status change to published

    def test_update_blog_post_admin_put(self, admin_client, admin_user):
        post = BlogPostFactory(
            status=PostStatusChoices.DRAFT, author=admin_user, content="Original"
        )
        url = self.detail_url(post.slug)
        # PUT requires all fields (or at least those not read-only/nullable)
        payload = {
            "title": "Complete Update Title",
            "content": "Completely new content for PUT.",  # Need content
            "status": PostStatusChoices.ARCHIVED,
            "tags": ["put", "archived"],
            "author": admin_user.pk,  # Must specify author again
            # slug will be regenerated if title changes
        }
        response = admin_client.put(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == payload["title"]
        assert post.status == payload["status"]
        assert post.content == payload["content"]
        assert set(post.tags.names()) == set(payload["tags"])
        # published_at shouldn't change if moving from DRAFT -> ARCHIVED

    # --- Delete View Tests (Admin) ---
    def test_delete_blog_post_admin(self, admin_client):
        post = BlogPostFactory()
        url = self.detail_url(post.slug)
        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BlogPost.objects.filter(pk=post.pk).exists()


# --- Test AdminBlogAdviceRequestViewSet ---


class TestAdminBlogAdviceRequestAPI:
    """Tests for the Admin BlogAdviceRequest API endpoints."""

    list_url = reverse("api:v1:admin_panel:admin-advice-request-list")

    def detail_url(self, pk):
        """Helper to get detail URL for an advice request pk."""
        return reverse(
            "api:v1:admin_panel:admin-advice-request-detail", kwargs={"pk": pk}
        )

    # --- Authorization Tests ---
    def test_list_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_non_admin(self, authenticated_client):
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_non_admin(self, authenticated_client):
        advice_req = BlogAdviceRequestFactory()
        url = self.detail_url(advice_req.pk)
        payload = {"status": AdviceRequestStatusChoices.CLOSED}
        response = authenticated_client.patch(url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- List View Tests (Admin) ---
    def test_list_advice_requests_admin(self, admin_client):
        BlogAdviceRequestFactory.create_batch(3)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_list_filter_by_status(self, admin_client):
        BlogAdviceRequestFactory(status=AdviceRequestStatusChoices.SUBMITTED)
        BlogAdviceRequestFactory(status=AdviceRequestStatusChoices.ANSWERED_SUPPORT)
        BlogAdviceRequestFactory(status=AdviceRequestStatusChoices.SUBMITTED)

        response = admin_client.get(
            self.list_url, {"status": AdviceRequestStatusChoices.SUBMITTED}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        response = admin_client.get(
            self.list_url, {"status": AdviceRequestStatusChoices.ANSWERED_SUPPORT}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_list_search_by_user(self, admin_client):
        user1 = UserFactory(username="searchmeuser")
        user2 = UserFactory(username="anotheruser")
        BlogAdviceRequestFactory(user=user1)
        BlogAdviceRequestFactory(user=user2)

        response = admin_client.get(self.list_url, {"search": "searchmeuser"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["user_info"]["username"] == "searchmeuser"

    # --- Retrieve View Tests (Admin) ---
    def test_retrieve_advice_request_admin(self, admin_client):
        advice_req = BlogAdviceRequestFactory()
        url = self.detail_url(advice_req.pk)
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == advice_req.pk
        assert response.data["description"] == advice_req.description
        assert response.data["user_info"]["id"] == advice_req.user.id

    def test_retrieve_non_existent_advice_request(self, admin_client):
        url = self.detail_url(9999)
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    # --- Update View Tests (Admin - PATCH only needed as only few fields writable) ---
    def test_update_advice_request_status_admin(self, admin_client):
        advice_req = BlogAdviceRequestFactory(
            status=AdviceRequestStatusChoices.SUBMITTED
        )
        url = self.detail_url(advice_req.pk)
        payload = {"status": AdviceRequestStatusChoices.UNDER_REVIEW}
        response = admin_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        advice_req.refresh_from_db()
        assert advice_req.status == AdviceRequestStatusChoices.UNDER_REVIEW
        assert response.data["status"] == AdviceRequestStatusChoices.UNDER_REVIEW

    def test_update_advice_request_links_admin(self, admin_client):
        advice_req = BlogAdviceRequestFactory(
            status=AdviceRequestStatusChoices.SUBMITTED
        )
        ticket = SupportTicketFactory()  # Assumes this factory exists
        post = BlogPostFactory(status=PostStatusChoices.PUBLISHED)
        url = self.detail_url(advice_req.pk)
        payload = {
            "status": AdviceRequestStatusChoices.ANSWERED_SUPPORT,
            "response_via": "support",
            "related_support_ticket": ticket.pk,
            "related_blog_post": post.pk,  # Can link both if desired
        }
        response = admin_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        advice_req.refresh_from_db()
        assert advice_req.status == AdviceRequestStatusChoices.ANSWERED_SUPPORT
        assert advice_req.response_via == "support"
        assert advice_req.related_support_ticket == ticket
        assert advice_req.related_blog_post == post

    def test_update_advice_request_read_only_fields_ignored(self, admin_client):
        advice_req = BlogAdviceRequestFactory(description="Original Desc")
        original_user = advice_req.user
        url = self.detail_url(advice_req.pk)
        payload = {
            "description": "Attempt to change desc",  # Read-only field
            "user": 999,  # Read-only field
            "status": AdviceRequestStatusChoices.CLOSED,  # Writable field
        }
        response = admin_client.patch(url, payload, format="json")

        assert (
            response.status_code == status.HTTP_200_OK
        )  # Update still succeeds for writable fields
        advice_req.refresh_from_db()
        assert advice_req.description == "Original Desc"  # Description NOT changed
        assert advice_req.user == original_user  # User NOT changed
        assert (
            advice_req.status == AdviceRequestStatusChoices.CLOSED
        )  # Status IS changed

    def test_update_advice_request_invalid_status(self, admin_client):
        advice_req = BlogAdviceRequestFactory()
        url = self.detail_url(advice_req.pk)
        payload = {"status": "invalid_choice"}
        response = admin_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "status" in response.data
