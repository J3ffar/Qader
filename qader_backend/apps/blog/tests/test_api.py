import pytest
from django.urls import reverse
from rest_framework import status
from taggit.models import Tag

# --- Import SimpleUploadedFile ---
from django.core.files.uploadedfile import SimpleUploadedFile
import os  # For MEDIA_ROOT cleanup if necessary
from django.conf import settings  # For MEDIA_ROOT
import shutil  # For cleaning up MEDIA_ROOT

from .factories import BlogPostFactory, BlogAdviceRequestFactory
from ..models import (
    AdviceRequestStatusChoices,
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
)

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- BlogPostViewSet Tests (Public API) ---
class TestBlogPostAPI:

    @pytest.fixture(autouse=True)
    def setup_posts(self):
        tag_tech, _ = Tag.objects.get_or_create(name="tech")
        tag_guide, _ = Tag.objects.get_or_create(name="guide")
        tag_python, _ = Tag.objects.get_or_create(name="python")

        self.published_post1 = BlogPostFactory(
            published=True,
            title="Published One",
            tags=[tag_tech.name, tag_guide.name],
            with_image=True,
        )
        self.published_post2 = BlogPostFactory(
            published=True,
            title="Published Two",
            content="About tech and python",  # This content is already HTML-like from Faker
            tags=[tag_tech.name, tag_python.name],
            # No image for this one
        )
        self.draft_post = BlogPostFactory(
            status=PostStatusChoices.DRAFT, title="Draft Post"
        )
        self.archived_post = BlogPostFactory(
            status=PostStatusChoices.ARCHIVED, title="Archived Post"
        )

    @classmethod
    def teardown_class(cls):
        """Clean up media files created during tests."""
        # Warning: This is a simple cleanup. For more complex scenarios,
        # you might want a more robust media cleanup strategy.
        # This also assumes MEDIA_ROOT is dedicated to tests or disposable.
        media_root = settings.MEDIA_ROOT
        blog_image_path = os.path.join(media_root, "blog", "images")
        if os.path.exists(blog_image_path):
            # Be CAREFUL with shutil.rmtree if MEDIA_ROOT is not specific to tests
            # print(f"Cleaning up test media directory: {blog_image_path}")
            # shutil.rmtree(blog_image_path)
            pass  # For now, let's not auto-delete to avoid accidental data loss if MEDIA_ROOT is shared.
            # Proper test media storage is recommended.

    def test_list_posts_unauthenticated(self, api_client):
        url = reverse("api:v1:blog:blogpost-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        results = response.data["results"]
        assert (
            results[0]["title"] == self.published_post2.title
        )  # Post 2 has no image initially, comes second due to created_at
        assert results[1]["title"] == self.published_post1.title

        assert "image" in results[0]  # Image field should be present
        assert results[0]["image"] is None  # published_post2 has no image
        assert "image" in results[1]
        assert results[1]["image"] is not None  # published_post1 has an image
        assert results[1]["image"].endswith(".png")  # Or .jpg, depending on factory
        assert "excerpt" in results[0]
        assert "content" not in results[0]

    def test_retrieve_post_unauthenticated(self, api_client):
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.published_post1.slug}
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == self.published_post1.title
        assert "content" in response.data
        assert "image" in response.data
        assert response.data["image"] is not None
        assert response.data["image"].endswith(".png")

        # Test post with no image
        url_no_image = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.published_post2.slug}
        )
        response_no_image = api_client.get(url_no_image)
        assert response_no_image.status_code == status.HTTP_200_OK
        assert response_no_image.data["image"] is None

    # ... (other TestBlogPostAPI tests remain largely the same, checking for 404s etc.) ...
    def test_list_posts_authenticated(self, authenticated_client):
        """Verify authenticated (but unsubscribed) users can list published posts."""
        url = reverse("api:v1:blog:blogpost-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_list_posts_subscribed(self, subscribed_client):
        """Verify subscribed users can list published posts."""
        url = reverse("api:v1:blog:blogpost-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_retrieve_draft_post_fails(self, api_client):
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.draft_post.slug}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_archived_post_fails(self, api_client):
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.archived_post.slug}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_post_fails(self, api_client):
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": "non-existent-slug"}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_posts_filter_by_tag(self, api_client):
        url = reverse("api:v1:blog:blogpost-list")
        response = api_client.get(url, {"tag": "python"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post2.title

    def test_list_posts_search(self, api_client):
        url = reverse("api:v1:blog:blogpost-list")
        response = api_client.get(url, {"search": "One"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post1.title


# --- BlogAdviceRequestViewSet Tests (Public API for create/list-mine) ---
# These tests should largely remain the same as they don't involve images or markdown
class TestBlogAdviceRequestAPI:

    def test_create_advice_request_unauthenticated(self, api_client):
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "Need help!"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_advice_request_authenticated_unsubscribed(
        self, authenticated_client
    ):
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "Need help!"}
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_advice_request_subscribed(self, subscribed_client):
        url = reverse("api:v1:blog:advice-request-create")
        data = {
            "problem_type": "Time Management",
            "description": "I need specific tips for the Quant section.",
        }
        response = subscribed_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert BlogAdviceRequest.objects.count() == 1
        advice_request = BlogAdviceRequest.objects.first()
        assert advice_request.user == subscribed_client.user
        assert advice_request.description == data["description"]
        assert advice_request.status == AdviceRequestStatusChoices.SUBMITTED

    # ... other BlogAdviceRequest tests
    def test_create_advice_request_missing_description(self, subscribed_client):
        url = reverse("api:v1:blog:advice-request-create")
        data = {"problem_type": "Some Topic"}
        response = subscribed_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_advice_request_can_omit_problem_type(self, subscribed_client):
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "General question here."}
        response = subscribed_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
