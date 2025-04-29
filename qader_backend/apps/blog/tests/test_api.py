import pytest
from django.urls import reverse
from rest_framework import status
from taggit.models import Tag

from .factories import BlogPostFactory, BlogAdviceRequestFactory
from ..models import (
    AdviceRequestStatusChoices,
    BlogPost,
    BlogAdviceRequest,
    PostStatusChoices,
)

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- BlogPostViewSet Tests ---


class TestBlogPostAPI:

    @pytest.fixture(autouse=True)
    def setup_posts(self):
        """Auto-fixture to create posts for testing listing/filtering."""
        tag_tech, _ = Tag.objects.get_or_create(name="tech")
        tag_guide, _ = Tag.objects.get_or_create(name="guide")
        tag_python, _ = Tag.objects.get_or_create(name="python")

        # Now create posts, passing tag names. The factory's add() should find existing tags.
        self.published_post1 = BlogPostFactory(
            published=True, title="Published One", tags=[tag_tech.name, tag_guide.name]
        )
        self.published_post2 = BlogPostFactory(
            published=True,
            title="Published Two",
            content="About tech and python",
            tags=[tag_tech.name, tag_python.name],
        )
        self.draft_post = BlogPostFactory(
            status=PostStatusChoices.DRAFT, title="Draft Post"
        )
        self.archived_post = BlogPostFactory(
            status=PostStatusChoices.ARCHIVED, title="Archived Post"
        )

    def test_list_posts_unauthenticated(self, api_client):
        """Verify unauthenticated users can list published posts."""
        url = reverse("api:v1:blog:blogpost-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # Only published posts
        assert (
            response.data["results"][0]["title"] == self.published_post2.title
        )  # Default order is -published_at
        assert response.data["results"][1]["title"] == self.published_post1.title
        assert "excerpt" in response.data["results"][0]
        assert "content" not in response.data["results"][0]  # List uses list serializer
        assert "Draft Post" not in str(response.content)
        assert "Archived Post" not in str(response.content)

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

    def test_retrieve_post_unauthenticated(self, api_client):
        """Verify unauthenticated users can retrieve a published post by slug."""
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.published_post1.slug}
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == self.published_post1.title
        assert "content" in response.data  # Detail serializer includes content
        assert "excerpt" not in response.data
        assert response.data["tags"] == ["tech", "guide"]

    def test_retrieve_draft_post_fails(self, api_client):
        """Verify retrieving a draft post results in 404."""
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.draft_post.slug}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_archived_post_fails(self, api_client):
        """Verify retrieving an archived post results in 404."""
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": self.archived_post.slug}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_post_fails(self, api_client):
        """Verify retrieving a non-existent slug results in 404."""
        url = reverse(
            "api:v1:blog:blogpost-detail", kwargs={"slug": "non-existent-slug"}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_posts_filter_by_tag(self, api_client):
        """Verify filtering posts by tag slug."""
        # Ensure tags exist
        Tag.objects.create(name="tech")
        Tag.objects.create(name="python")

        url = reverse("api:v1:blog:blogpost-list")
        # Filter by 'python' tag
        response = api_client.get(url, {"tag": "python"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post2.title

        # Filter by 'tech' tag
        response = api_client.get(url, {"tag": "tech"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        # Filter by non-existent tag
        response = api_client.get(url, {"tag": "nonexistent"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_list_posts_search(self, api_client):
        """Verify searching posts by title, content, or tag name."""
        url = reverse("api:v1:blog:blogpost-list")

        # Search title
        response = api_client.get(url, {"search": "One"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post1.title

        # Search content
        response = api_client.get(url, {"search": "python"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post2.title

        # Search tag name
        response = api_client.get(url, {"search": "guide"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["title"] == self.published_post1.title

        # Search term matching multiple posts
        response = api_client.get(url, {"search": "Published"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

        # Search term matching nothing
        response = api_client.get(url, {"search": "xyzzy"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0


# --- BlogAdviceRequestViewSet Tests ---


class TestBlogAdviceRequestAPI:

    def test_create_advice_request_unauthenticated(self, api_client):
        """Verify unauthenticated users cannot create advice requests."""
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "Need help!"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_advice_request_authenticated_unsubscribed(
        self, authenticated_client
    ):
        """Verify authenticated but unsubscribed users cannot create advice requests."""
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "Need help!"}
        response = authenticated_client.post(url, data)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # IsSubscribed permission

    def test_create_advice_request_subscribed(self, subscribed_client):
        """Verify subscribed users can create advice requests."""
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
        assert advice_request.problem_type == data["problem_type"]
        assert advice_request.status == AdviceRequestStatusChoices.SUBMITTED
        assert response.data["description"] == data["description"]
        assert response.data["status"] == AdviceRequestStatusChoices.SUBMITTED

    def test_create_advice_request_missing_description(self, subscribed_client):
        """Verify request fails if description is missing."""
        url = reverse("api:v1:blog:advice-request-create")
        data = {"problem_type": "Some Topic"}  # Missing description
        response = subscribed_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "description" in response.data
        assert BlogAdviceRequest.objects.count() == 0

    def test_create_advice_request_can_omit_problem_type(self, subscribed_client):
        """Verify problem_type is optional."""
        url = reverse("api:v1:blog:advice-request-create")
        data = {"description": "General question here."}  # Missing problem_type
        response = subscribed_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert BlogAdviceRequest.objects.count() == 1
        advice_request = BlogAdviceRequest.objects.first()
        assert advice_request.user == subscribed_client.user
        assert advice_request.description == data["description"]
        assert advice_request.problem_type is None  # Should be null in DB
