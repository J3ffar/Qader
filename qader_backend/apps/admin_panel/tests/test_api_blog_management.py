# qader_backend/apps/admin_panel/tests/test_api_blog_management.py
import json
import pytest
from django.urls import reverse
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import os
import shutil
import base64
import re  # For more flexible HTML assertions if needed

# Factories
from apps.blog.tests.factories import BlogPostFactory, BlogAdviceRequestFactory
from apps.users.tests.factories import UserFactory
from apps.support.tests.factories import SupportTicketFactory

# Models
from apps.blog.models import (
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
    AdviceRequestStatusChoices,
    AdviceResponseViaChoices,
)
from apps.users.models import User

pytestmark = pytest.mark.django_db


def get_dummy_image_file(name="test_image.gif", content_type="image/gif", size=None):
    base64_gif = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
    image_content = base64.b64decode(base64_gif)
    return SimpleUploadedFile(name, image_content, content_type=content_type)


class TestAdminBlogPostAPI:
    list_url = reverse("api:v1:admin_panel:admin-blogpost-list")

    def detail_url(self, slug):
        return reverse(
            "api:v1:admin_panel:admin-blogpost-detail", kwargs={"slug": slug}
        )

    @classmethod
    def teardown_class(cls):
        pass

    def test_list_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_non_admin(self, authenticated_client):
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_non_admin(self, authenticated_client):
        payload = {"title": "Attempt", "content": "Denied"}
        response = authenticated_client.post(self.list_url, payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_blog_posts_admin(self, admin_client):
        BlogPostFactory.create_batch(5, with_image=True)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 5
        assert "image" in response.data["results"][0]

    def test_create_blog_post_admin_with_markdown_and_image(
        self, admin_client, admin_user: User
    ):
        markdown_content = "# Title Header\n*   List item\n\nSome text with `code`."
        image_file = get_dummy_image_file(name="creation_test.gif")
        tags_list = ["new", "admin", "test"]
        payload = {
            "title": "New Admin Post Markdown Image",
            "content": markdown_content,
            "status": PostStatusChoices.PUBLISHED,
            "tags": tags_list,  # Send as a JSON string dump of the list
            "author": admin_user.pk,
            "image": image_file,
        }
        response = admin_client.post(self.list_url, payload, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        post = BlogPost.objects.first()
        assert post.title == payload["title"]
        # Check HTML content more flexibly
        assert re.search(r"<h1[^>]*>Title Header</h1>", post.content)
        assert "<li>List item</li>" in post.content
        assert "<code>code</code>" in post.content
        assert "<script>" not in post.content

        assert post.image is not None
        assert post.image.name.endswith(image_file.name)
        assert os.path.exists(post.image.path)
        assert response.data["image"].endswith(image_file.name)

    def test_create_blog_post_admin_no_image(self, admin_client, admin_user: User):
        markdown_content = "Simple text content."
        payload = {
            "title": "Admin Post No Image",
            "content": markdown_content,
            "status": PostStatusChoices.DRAFT,
            "tags": ["no-image", "draft"],
            "author": admin_user.pk,
        }
        response = admin_client.post(self.list_url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED, response.data
        post = BlogPost.objects.get(title=payload["title"])
        assert not post.image  # Check if image field is empty
        assert response.data["image"] is None
        assert "<p>Simple text content.</p>" in post.content
        assert set(post.tags.names()) == set(payload["tags"])

    def test_create_post_invalid_data(self, admin_client):
        payload = {"content": "Missing title"}
        response = admin_client.post(self.list_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_retrieve_blog_post_admin(self, admin_client):
        post = BlogPostFactory(
            title="Retrieve Me", status=PostStatusChoices.PUBLISHED, with_image=True
        )
        url = self.detail_url(post.slug)
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["image"] is not None

    def test_update_blog_post_admin_patch_content_and_image(
        self, admin_client, admin_user
    ):
        other_admin = UserFactory(
            is_staff=True, is_superuser=True, username="othereditor"
        )
        post = BlogPostFactory(
            status=PostStatusChoices.DRAFT, author=admin_user, with_image=True
        )
        original_image_name = post.image.name
        url = self.detail_url(post.slug)

        new_markdown = "## Updated Section\n* New point"
        new_image = get_dummy_image_file(name="updated_patch.gif")
        payload = {
            "title": "Updated Title PATCH",
            "content": new_markdown,
            "status": PostStatusChoices.PUBLISHED,
            "tags": "updated,patch",
            "author": other_admin.pk,
            "image": new_image,
        }
        response = admin_client.patch(url, payload, format="multipart")

        assert response.status_code == status.HTTP_200_OK, response.data
        post.refresh_from_db()
        assert post.title == payload["title"]
        # Check HTML content more flexibly
        assert re.search(r"<h2[^>]*>Updated Section</h2>", post.content)
        assert "<li>New point</li>" in post.content
        assert post.image is not None
        assert post.image.name.endswith(new_image.name)
        assert post.image.name != original_image_name

    def test_update_blog_post_admin_put_replace_all(self, admin_client, admin_user):
        post = BlogPostFactory(
            status=PostStatusChoices.DRAFT, author=admin_user, with_image=True
        )
        url = self.detail_url(post.slug)
        new_markdown_content_put = "# Full Rewrite\nThis is new."
        new_image_put = get_dummy_image_file("put_image.gif")

        payload_put = {
            "title": "Complete Update Title PUT",
            "content": new_markdown_content_put,
            "status": PostStatusChoices.ARCHIVED,
            "tags": "put,archived",
            "author": admin_user.pk,
            "image": new_image_put,
        }
        response = admin_client.put(url, payload_put, format="multipart")
        assert response.status_code == status.HTTP_200_OK, response.data
        post.refresh_from_db()
        assert post.title == payload_put["title"]
        # Check HTML content more flexibly
        assert re.search(r"<h1[^>]*>Full Rewrite</h1>", post.content)
        assert "<p>This is new.</p>" in post.content
        assert post.image.name.endswith(new_image_put.name)

    def test_admin_partial_update_remove_image(self, admin_client):
        post_with_image = BlogPostFactory(with_image=True)
        url = self.detail_url(post_with_image.slug)
        payload = {"image": ""}
        response = admin_client.patch(url, payload, format="multipart")
        assert response.status_code == status.HTTP_200_OK, response.data
        post_with_image.refresh_from_db()
        assert not post_with_image.image

    def test_delete_blog_post_admin(self, admin_client):
        post = BlogPostFactory()
        url = self.detail_url(post.slug)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not BlogPost.objects.filter(pk=post.pk).exists()


class TestAdminBlogAdviceRequestAPI:
    list_url = reverse("api:v1:admin_panel:admin-advice-request-list")

    def detail_url(self, pk):
        return reverse(
            "api:v1:admin_panel:admin-advice-request-detail", kwargs={"pk": pk}
        )

    def test_list_unauthenticated(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_advice_requests_admin(self, admin_client):
        BlogAdviceRequestFactory.create_batch(3)
        response = admin_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 3

    def test_update_advice_request_links_admin(self, admin_client):
        advice_req = BlogAdviceRequestFactory(
            status=AdviceRequestStatusChoices.SUBMITTED
        )
        ticket = SupportTicketFactory()
        post = BlogPostFactory(status=PostStatusChoices.PUBLISHED)
        url = self.detail_url(advice_req.pk)
        payload = {
            "status": AdviceRequestStatusChoices.ANSWERED_SUPPORT.value,
            "response_via": AdviceResponseViaChoices.SUPPORT.value,
            "related_support_ticket": ticket.pk,
            "related_blog_post": post.pk,
        }
        response = admin_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK, response.data
        advice_req.refresh_from_db()
        assert advice_req.status == AdviceRequestStatusChoices.ANSWERED_SUPPORT.value
        assert advice_req.response_via == AdviceResponseViaChoices.SUPPORT.value
        assert advice_req.related_support_ticket == ticket
        assert advice_req.related_blog_post == post

    def test_update_advice_request_read_only_fields_ignored(self, admin_client):
        advice_req = BlogAdviceRequestFactory(description="Original Desc")
        original_user = advice_req.user
        url = self.detail_url(advice_req.pk)
        new_user_for_test = UserFactory(username="attemptchangeuser")
        payload = {
            "description": "Attempt to change desc",
            "user": new_user_for_test.pk,
            "status": AdviceRequestStatusChoices.CLOSED.value,
        }
        response = admin_client.patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        advice_req.refresh_from_db()
        assert advice_req.description == "Original Desc"
        assert advice_req.user == original_user
        assert advice_req.status == AdviceRequestStatusChoices.CLOSED.value
