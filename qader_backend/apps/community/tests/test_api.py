import pytest
from django.urls import reverse
from rest_framework import status
from taggit.models import Tag

from apps.community.models import CommunityPost, CommunityReply
from apps.community.tests.factories import (
    CommunityPostFactory,
    CommunityReplyFactory,
    LearningSectionFactory,
)

# Assuming UserFactory and client fixtures (api_client, authenticated_client,
# subscribed_client, admin_client) are defined in conftest.py or users app tests.
from apps.users.tests.factories import UserFactory

# Constants for URLs using f-strings for potential future version changes
API_VERSION = "v1"
POSTS_LIST_CREATE_URL = reverse(f"api:{API_VERSION}:community:communitypost-list")
TAGS_LIST_URL = reverse(f"api:{API_VERSION}:community:tag-list")


def post_detail_url(post_id):
    """Helper function to get the detail URL for a post."""
    return reverse(
        f"api:{API_VERSION}:community:communitypost-detail", kwargs={"pk": post_id}
    )


def replies_list_create_url(post_id):
    """Helper function to get the replies URL for a post."""
    return reverse(
        f"api:{API_VERSION}:community:post-replies-list-create",
        kwargs={"post_pk": post_id},
    )


# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- Fixtures (Optional: Can be in conftest.py) ---
@pytest.fixture
def discussion_post(db):
    """Fixture for a discussion post."""
    return CommunityPostFactory(
        post_type=CommunityPost.PostType.DISCUSSION, title="Discussion Title"
    )


@pytest.fixture
def achievement_post(db):
    """Fixture for an achievement post."""
    return CommunityPostFactory(post_type=CommunityPost.PostType.ACHIEVEMENT)


@pytest.fixture
def post_with_replies(db):
    """Fixture for a post with multiple replies."""
    post = CommunityPostFactory()
    replies = CommunityReplyFactory.create_batch(3, post=post)
    return post, replies


# --- CommunityPostViewSet Tests ---


class TestCommunityPostList:
    """Tests for listing Community Posts (GET /posts/)."""

    def test_list_posts_unauthenticated(self, api_client):
        """Verify unauthenticated users receive 401."""
        response = api_client.get(POSTS_LIST_CREATE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_posts_authenticated_not_subscribed(self, authenticated_client):
        """Verify authenticated but non-subscribed users receive 403 (based on IsSubscribed)."""
        response = authenticated_client.get(POSTS_LIST_CREATE_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_posts_success_structure_and_pagination(self, subscribed_client):
        """Verify subscribed users can list posts with correct structure and pagination."""
        # Create more posts than default page size to test pagination
        CommunityPostFactory.create_batch(25)
        response = subscribed_client.get(POSTS_LIST_CREATE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 25
        assert "next" in response.data  # Check pagination fields exist
        assert "previous" in response.data
        assert "results" in response.data
        # Assuming default PAGE_SIZE is 20 from settings
        assert len(response.data["results"]) == 20, "Default page size should be 20"
        assert response.data["next"] is not None, "Should be a next page link"
        assert (
            response.data["previous"] is None
        ), "Should be no previous page link on page 1"

        # Check structure of one result (using CommunityPostListSerializer)
        post_data = response.data["results"][0]
        assert "id" in post_data
        assert "author" in post_data and "username" in post_data["author"]
        assert "post_type" in post_data
        assert "title" in post_data  # Title might be empty, but key should exist
        assert "section_filter" in post_data  # Should be basic section data or null
        assert "content_excerpt" in post_data
        assert "reply_count" in post_data
        assert "created_at" in post_data
        assert "tags" in post_data and isinstance(post_data["tags"], list)
        assert "is_pinned" in post_data
        assert "is_closed" in post_data

        # Ensure sensitive/bulky fields are NOT present in list view
        assert "content" not in post_data, "Full content should not be in list view"
        assert "replies" not in post_data, "Replies should not be nested in list view"

        # Test fetching the second page
        response_page2 = subscribed_client.get(response.data["next"])
        assert response_page2.status_code == status.HTTP_200_OK
        assert (
            len(response_page2.data["results"]) == 5
        ), "Should have remaining 5 posts on page 2"
        assert response_page2.data["next"] is None
        assert response_page2.data["previous"] is not None

    def test_list_posts_filtering_by_type(
        self, subscribed_client, discussion_post, achievement_post
    ):
        """Verify filtering posts by post_type works correctly."""
        url = f"{POSTS_LIST_CREATE_URL}?post_type={CommunityPost.PostType.DISCUSSION}"
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1, "Should only find the discussion post"
        assert response.data["results"][0]["id"] == discussion_post.id
        assert (
            response.data["results"][0]["post_type"]
            == CommunityPost.PostType.DISCUSSION
        )

    def test_list_posts_filtering_by_tags(self, subscribed_client):
        """Verify filtering posts by tags (OR logic)."""
        post_py_dj = CommunityPostFactory.create(tags=["python", "django"])
        post_py_test = CommunityPostFactory.create(tags=["python", "testing"])
        post_dj = CommunityPostFactory.create(tags=["django"])
        post_other = CommunityPostFactory.create(tags=["other"])

        # Filter by single tag 'python'
        url_python = f"{POSTS_LIST_CREATE_URL}?tags=python"
        response_python = subscribed_client.get(url_python)
        assert response_python.status_code == status.HTTP_200_OK
        assert (
            response_python.data["count"] == 2
        ), "Should find posts tagged with 'python'"
        post_ids_python = {p["id"] for p in response_python.data["results"]}
        assert post_py_dj.id in post_ids_python
        assert post_py_test.id in post_ids_python

        # Filter by multiple tags 'python,testing' (OR logic)
        url_multi_or = f"{POSTS_LIST_CREATE_URL}?tags=python,testing"
        response_multi_or = subscribed_client.get(url_multi_or)
        assert response_multi_or.status_code == status.HTTP_200_OK
        # Should include posts tagged 'python' OR 'testing'
        assert (
            response_multi_or.data["count"] == 2
        ), "Should find posts tagged 'python' OR 'testing'"
        post_ids_multi_or = {p["id"] for p in response_multi_or.data["results"]}
        assert post_py_dj.id in post_ids_multi_or  # Has 'python'
        assert post_py_test.id in post_ids_multi_or  # Has 'python' and 'testing'

        # Filter by tags not present
        url_none = f"{POSTS_LIST_CREATE_URL}?tags=nonexistent"
        response_none = subscribed_client.get(url_none)
        assert response_none.status_code == status.HTTP_200_OK
        assert response_none.data["count"] == 0

    def test_list_posts_filtering_by_section(self, subscribed_client):
        """Verify filtering by learning section slug."""
        section1 = LearningSectionFactory(slug="quant-algebra")
        section2 = LearningSectionFactory(slug="verbal-reading")
        post_sec1 = CommunityPostFactory(section_filter=section1)
        post_sec2 = CommunityPostFactory(section_filter=section2)
        post_no_sec = CommunityPostFactory(section_filter=None)

        url = f"{POSTS_LIST_CREATE_URL}?section_filter=quant-algebra"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == post_sec1.id
        assert response.data["results"][0]["section_filter"]["slug"] == "quant-algebra"

    def test_list_posts_filtering_by_pinned(self, subscribed_client):
        """Verify filtering by pinned status."""
        pinned_post = CommunityPostFactory(is_pinned=True)
        unpinned_post = CommunityPostFactory(is_pinned=False)

        url = f"{POSTS_LIST_CREATE_URL}?pinned=true"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == pinned_post.id

    def test_list_posts_search(self, subscribed_client):
        """Verify searching posts by title, content, author username, and tags."""
        post_title = CommunityPostFactory(title="Specific Search Title")
        post_content = CommunityPostFactory(
            content="This content contains the word searchable."
        )
        author = UserFactory(username="searchable_author")
        post_author = CommunityPostFactory(author=author)
        post_tag = CommunityPostFactory(tags=["searchable_tag"])

        # Search Title
        response_title = subscribed_client.get(
            f"{POSTS_LIST_CREATE_URL}?search=Specific Search Title"
        )
        assert response_title.status_code == status.HTTP_200_OK
        assert response_title.data["count"] == 1
        assert response_title.data["results"][0]["id"] == post_title.id

        # Search Content
        response_content = subscribed_client.get(
            f"{POSTS_LIST_CREATE_URL}?search=searchable"
        )
        assert response_content.status_code == status.HTTP_200_OK
        # Could match content, author, or tag
        assert response_content.data["count"] >= 1
        assert post_content.id in {p["id"] for p in response_content.data["results"]}

        # Search Author Username
        response_author = subscribed_client.get(
            f"{POSTS_LIST_CREATE_URL}?search=searchable_author"
        )
        assert response_author.status_code == status.HTTP_200_OK
        assert response_author.data["count"] == 1
        assert response_author.data["results"][0]["id"] == post_author.id

        # Search Tag Name
        response_tag = subscribed_client.get(
            f"{POSTS_LIST_CREATE_URL}?search=searchable_tag"
        )
        assert response_tag.status_code == status.HTTP_200_OK
        assert response_tag.data["count"] == 1
        assert response_tag.data["results"][0]["id"] == post_tag.id

        # Search No Results
        response_none = subscribed_client.get(
            f"{POSTS_LIST_CREATE_URL}?search=__nonexistent__"
        )
        assert response_none.status_code == status.HTTP_200_OK
        assert response_none.data["count"] == 0

    def test_list_posts_ordering(self, subscribed_client, post_with_replies):
        """Verify default ordering (pinned, date) and ordering by reply_count."""
        post_replies, _ = post_with_replies  # Has 3 replies
        post_normal1 = CommunityPostFactory()  # 0 replies initially
        post_pinned = CommunityPostFactory(is_pinned=True)  # 0 replies
        post_normal2 = CommunityPostFactory()  # Created after post_normal1, 0 replies

        # Test default ordering
        response_default = subscribed_client.get(POSTS_LIST_CREATE_URL)
        assert response_default.status_code == status.HTTP_200_OK
        results_default = response_default.data["results"]
        assert len(results_default) == 4
        assert results_default[0]["id"] == post_pinned.id, "Pinned post should be first"
        assert results_default[1]["id"] == post_normal2.id, "Newer normal post next"
        assert results_default[2]["id"] == post_normal1.id
        assert results_default[3]["id"] == post_replies.id  # Oldest non-pinned

        # Test ordering by reply_count descending
        # Manually add a reply to ensure counts differ significantly
        CommunityReplyFactory(post=post_normal1)  # Now has 1 reply

        url_order_reply = f"{POSTS_LIST_CREATE_URL}?ordering=-reply_count_annotated"  # Use annotated field name
        response_ordered = subscribed_client.get(url_order_reply)
        assert response_ordered.status_code == status.HTTP_200_OK
        results_ordered = response_ordered.data["results"]
        assert results_ordered[0]["id"] == post_replies.id, "Post with 3 replies first"
        assert results_ordered[1]["id"] == post_normal1.id, "Post with 1 reply second"
        # Posts with 0 replies (pinned and normal2) follow, order depends on secondary sort (-created_at)
        zero_reply_ids = {results_ordered[2]["id"], results_ordered[3]["id"]}
        assert post_pinned.id in zero_reply_ids
        assert post_normal2.id in zero_reply_ids


class TestCommunityPostCreate:
    """Tests for creating Community Posts (POST /posts/)."""

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_create_post_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated or non-subscribed users cannot create posts (401/403)."""
        client = request.getfixturevalue(client_fixture_name)
        payload = {"post_type": CommunityPost.PostType.DISCUSSION, "content": "Test"}
        response = client.post(POSTS_LIST_CREATE_URL, data=payload)
        expected_status = (
            status.HTTP_401_UNAUTHORIZED
            if client_fixture_name == "api_client"
            else status.HTTP_403_FORBIDDEN
        )
        assert response.status_code == expected_status

    def test_create_post_success(self, subscribed_client):
        """Verify subscribed users can create a valid post with title and tags."""
        user = subscribed_client.user
        section = LearningSectionFactory()
        payload = {
            "post_type": CommunityPost.PostType.TIP,
            "title": "Effective Study Tip",
            "content": "Regular review is key to retention.",
            "section_filter": section.slug,  # Test associating with section
            "tags": ["study-hacks", "retention"],
        }
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )

        assert (
            response.status_code == status.HTTP_201_CREATED
        ), f"Error: {response.data}"
        assert CommunityPost.objects.count() == 1
        post = CommunityPost.objects.first()

        assert post.author == user
        assert post.post_type == payload["post_type"]
        assert post.title == payload["title"]
        assert post.content == payload["content"]
        assert post.section_filter == section
        assert set(post.tags.names()) == set(payload["tags"])

        # Check response structure (using CommunityPostCreateUpdateSerializer)
        assert response.data["id"] == post.id
        assert response.data["author"]["username"] == user.username
        assert response.data["post_type"] == payload["post_type"]
        assert response.data["title"] == payload["title"]
        assert response.data["content"] == payload["content"]
        assert response.data["section_filter"] == section.slug
        assert set(response.data["tags"]) == set(payload["tags"])
        assert response.data["is_pinned"] is False  # Check defaults
        assert response.data["is_closed"] is False

    def test_create_post_minimal_payload(self, subscribed_client):
        """Verify creating a post with only required fields."""
        payload = {
            "post_type": CommunityPost.PostType.ACHIEVEMENT,  # Type that might not need title
            "content": "Passed my assessment!",
        }
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        post = CommunityPost.objects.first()
        assert post.post_type == payload["post_type"]
        assert post.content == payload["content"]
        assert post.title is None  # Assuming factory sets empty string if no title
        assert post.section_filter is None
        assert (
            not post.tags.exists()
        ), "Post created with minimal payload should have no tags"

    @pytest.mark.parametrize("missing_field", ["post_type", "content"])
    def test_create_post_missing_required_field(self, subscribed_client, missing_field):
        """Verify validation error for missing required fields."""
        payload = {"post_type": CommunityPost.PostType.DISCUSSION, "content": "Test"}
        del payload[missing_field]  # Remove the field being tested
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            missing_field in response.data
        ), f"Error message expected for missing field '{missing_field}'"

    def test_create_post_invalid_type(self, subscribed_client):
        """Verify validation error for invalid post_type choice."""
        payload = {"post_type": "invalid_choice", "content": "Test"}
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "post_type" in response.data

    def test_create_post_invalid_section_slug(self, subscribed_client):
        """Verify validation error for non-existent section_filter slug."""
        payload = {
            "post_type": CommunityPost.PostType.DISCUSSION,
            "content": "Test",
            "section_filter": "non-existent-slug",
        }
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "section_filter" in response.data


class TestCommunityPostRetrieve:
    """Tests for retrieving a single Community Post (GET /posts/{pk}/)."""

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_retrieve_post_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated or non-subscribed users cannot retrieve posts (401/403)."""
        client = request.getfixturevalue(client_fixture_name)
        post = CommunityPostFactory()
        url = post_detail_url(post.id)
        response = client.get(url)
        expected_status = (
            status.HTTP_401_UNAUTHORIZED
            if client_fixture_name == "api_client"
            else status.HTTP_403_FORBIDDEN
        )
        assert response.status_code == expected_status

    def test_retrieve_post_success(self, subscribed_client, post_with_replies):
        """Verify subscribed users can retrieve a post with full content and paginated replies."""
        post, replies = post_with_replies
        reply1, reply2, reply3 = replies

        url = post_detail_url(post.id)
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check main post fields (using CommunityPostDetailSerializer)
        assert response.data["id"] == post.id
        assert response.data["author"]["username"] == post.author.username
        assert response.data["content"] == post.content  # Full content
        assert response.data["title"] == post.title
        assert "tags" in response.data and isinstance(response.data["tags"], list)
        assert response.data["reply_count"] == 3  # Check annotated count

        # Check nested replies structure (paginated)
        assert "replies" in response.data
        assert response.data["replies"]["count"] == 3
        assert "next" in response.data["replies"]  # Pagination structure
        assert "previous" in response.data["replies"]
        assert "results" in response.data["replies"]
        assert len(response.data["replies"]["results"]) == 3  # Assuming page size >= 3

        reply_ids = {r["id"] for r in response.data["replies"]["results"]}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids
        assert reply3.id in reply_ids

        # Check structure of one reply
        reply_data = response.data["replies"]["results"][0]
        assert "id" in reply_data
        assert "author" in reply_data and "username" in reply_data["author"]
        assert "content" in reply_data
        assert "created_at" in reply_data
        assert "parent_reply_read_id" in reply_data  # Read-only parent ID field

    def test_retrieve_post_not_found(self, subscribed_client):
        """Verify 404 for retrieving a non-existent post ID."""
        url = post_detail_url(99999)  # Use an ID unlikely to exist
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCommunityPostUpdate:
    """Tests for updating Community Posts (PUT / PATCH /posts/{pk}/)."""

    def test_update_put_not_author(self, subscribed_client):
        """Verify non-authors cannot PUT update a post (403)."""
        other_user = UserFactory()
        post = CommunityPostFactory(
            author=other_user,
            post_type=CommunityPost.PostType.DISCUSSION,
            content="Original",
        )
        url = post_detail_url(post.id)
        # PUT requires all fields for the serializer (CommunityPostCreateUpdateSerializer)
        payload = {
            "post_type": CommunityPost.PostType.DISCUSSION,
            "content": "Updated content by wrong user.",
            "title": post.title,  # Need to provide existing or new values for non-read-only fields
            "tags": list(post.tags.names()),  # Provide existing tags
            # section_filter might be needed if required by serializer logic
        }
        response = subscribed_client.put(url, data=payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_patch_not_author(self, subscribed_client):
        """Verify non-authors cannot PATCH update a post (403)."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = post_detail_url(post.id)
        payload = {"content": "Updated content by wrong user."}
        response = subscribed_client.patch(url, data=payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_post_author_success(self, subscribed_client):
        """Verify authors can partially update (PATCH) their own post."""
        post = CommunityPostFactory(
            author=subscribed_client.user,
            content="Original Content",
            title="Original Title",
        )
        url = post_detail_url(post.id)
        payload = {"content": "Updated Content by Author"}  # Only update content
        response = subscribed_client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.content == "Updated Content by Author"
        assert post.title == "Original Title"  # Title should remain unchanged
        assert response.data["content"] == "Updated Content by Author"
        assert response.data["title"] == "Original Title"

    def test_full_update_post_author_success(self, subscribed_client):
        """Verify authors can fully update (PUT) their own post."""
        post = CommunityPostFactory(
            author=subscribed_client.user,
            post_type=CommunityPost.PostType.TIP,
            content="Old",
        )
        url = post_detail_url(post.id)
        new_tags = ["updated", "put-test"]
        payload = {
            "post_type": CommunityPost.PostType.DISCUSSION,  # Change type
            "content": "New content via PUT",
            "title": "New PUT Title",
            "tags": new_tags,
            # section_filter can be added if needed
        }
        response = subscribed_client.put(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK, f"Error: {response.data}"
        post.refresh_from_db()
        assert post.post_type == CommunityPost.PostType.DISCUSSION
        assert post.content == "New content via PUT"
        assert post.title == "New PUT Title"
        assert set(post.tags.names()) == set(new_tags)
        # Check response mirrors the changes
        assert response.data["post_type"] == CommunityPost.PostType.DISCUSSION
        assert response.data["content"] == "New content via PUT"
        assert set(response.data["tags"]) == set(new_tags)

    def test_update_admin_fields_by_author(self, subscribed_client):
        """Verify authors cannot change is_pinned or is_closed via PATCH."""
        post = CommunityPostFactory(
            author=subscribed_client.user, is_pinned=False, is_closed=False
        )
        url = post_detail_url(post.id)
        payload = {
            "is_pinned": True,
            "is_closed": True,
            "content": "Author trying to pin",
        }
        response = subscribed_client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK  # Update of content succeeds
        post.refresh_from_db()
        assert post.is_pinned is False, "is_pinned should not be changed by author"
        assert post.is_closed is False, "is_closed should not be changed by author"
        assert (
            response.data["is_pinned"] is False
        )  # Response should reflect actual state
        assert response.data["is_closed"] is False
        assert post.content == "Author trying to pin"  # Content update should work

    def test_update_admin_fields_by_admin(self, admin_client):
        """Verify admins can change is_pinned and is_closed via PATCH."""
        post = CommunityPostFactory(is_pinned=False, is_closed=False)
        url = post_detail_url(post.id)
        payload = {"is_pinned": True, "is_closed": True}
        response = admin_client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.is_pinned is True
        assert post.is_closed is True
        assert response.data["is_pinned"] is True  # Response reflects admin changes
        assert response.data["is_closed"] is True

    def test_update_admin_fields_by_admin_mixed_payload(self, admin_client):
        """Verify admins can change admin fields and regular fields simultaneously."""
        post = CommunityPostFactory(is_pinned=False, content="Original for Admin")
        url = post_detail_url(post.id)
        payload = {"is_pinned": True, "content": "Admin updated content and pinned"}
        response = admin_client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.is_pinned is True
        assert post.content == "Admin updated content and pinned"
        assert response.data["is_pinned"] is True
        assert response.data["content"] == "Admin updated content and pinned"


class TestCommunityPostDelete:
    """Tests for deleting Community Posts (DELETE /posts/{pk}/)."""

    def test_delete_post_unauthorized(self, api_client):
        """Verify unauthenticated users cannot delete posts (401)."""
        post = CommunityPostFactory()
        url = post_detail_url(post.id)
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_not_subscribed(self, authenticated_client):
        """Verify non-subscribed users cannot delete posts (403)."""
        post = CommunityPostFactory(author=authenticated_client.user)  # Own post
        url = post_detail_url(post.id)
        response = authenticated_client.delete(url)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # IsSubscribed check first
        assert CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_not_author(self, subscribed_client):
        """Verify subscribed users cannot delete posts they don't own (403)."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = post_detail_url(post.id)
        response = subscribed_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN  # IsOwnerOrAdmin check
        assert CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_author_success(self, subscribed_client):
        """Verify authors can delete their own posts (204)."""
        post = CommunityPostFactory(author=subscribed_client.user)
        url = post_detail_url(post.id)
        response = subscribed_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_admin_success(self, admin_client):
        """Verify admins can delete any post (204)."""
        post = CommunityPostFactory()  # Author doesn't matter for admin
        url = post_detail_url(post.id)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CommunityPost.objects.filter(id=post.id).exists()


# --- CommunityReplyListCreateView Tests ---


class TestCommunityReplyList:
    """Tests for listing Replies for a post (GET /posts/{post_pk}/replies/)."""

    def test_list_replies_unauthenticated(self, api_client):
        """Verify unauthenticated users cannot list replies (401)."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_replies_authenticated_not_subscribed(self, authenticated_client):
        """Verify non-subscribed users cannot list replies (403)."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_replies_success(self, subscribed_client, post_with_replies):
        """Verify subscribed users can list replies for a specific post."""
        post, replies = post_with_replies
        reply1, reply2, reply3 = replies
        # Create reply for another post, should not be listed
        other_post = CommunityPostFactory()
        CommunityReplyFactory(post=other_post)

        url = replies_list_create_url(post.id)
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 3
        # Check pagination structure
        assert len(response.data["results"]) == 3  # Assuming page size allows all
        reply_ids = {r["id"] for r in response.data["results"]}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids
        assert reply3.id in reply_ids

        # Check structure of one reply
        reply_data = response.data["results"][0]
        assert "id" in reply_data
        assert "author" in reply_data and "username" in reply_data["author"]
        assert "content" in reply_data
        assert "created_at" in reply_data
        assert "parent_reply_read_id" in reply_data

    def test_list_replies_post_not_found(self, subscribed_client):
        """Verify 404 when listing replies for a non-existent post ID."""
        url = replies_list_create_url(99999)
        response = subscribed_client.get(url)
        # View's get_post_object raises NotFound
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCommunityReplyCreate:
    """Tests for creating Replies for a post (POST /posts/{post_pk}/replies/)."""

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_create_reply_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated/non-subscribed cannot create replies (401/403)."""
        client = request.getfixturevalue(client_fixture_name)
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {"content": "Test reply"}
        response = client.post(url, data=payload)
        expected_status = (
            status.HTTP_401_UNAUTHORIZED
            if client_fixture_name == "api_client"
            else status.HTTP_403_FORBIDDEN
        )
        assert response.status_code == expected_status

    def test_create_reply_success_top_level(self, subscribed_client):
        """Verify subscribed users can create a top-level reply."""
        user = subscribed_client.user
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {"content": "A new top-level reply"}
        response = subscribed_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityReply.objects.count() == 1
        reply = CommunityReply.objects.first()
        assert reply.author == user
        assert reply.post == post
        assert reply.content == payload["content"]
        assert reply.parent_reply is None
        # Check response data using CommunityReplySerializer
        assert response.data["id"] == reply.id
        assert response.data["author"]["username"] == user.username
        assert response.data["content"] == payload["content"]
        assert response.data["parent_reply_read_id"] is None  # Check read field

    def test_create_reply_success_threaded(self, subscribed_client):
        """Verify subscribed users can create a threaded reply linking parent_reply_id."""
        user = subscribed_client.user
        post = CommunityPostFactory()
        parent_reply = CommunityReplyFactory(post=post)  # Reply to reply to
        url = replies_list_create_url(post.id)
        payload = {
            "content": "Replying to the first comment",
            "parent_reply_id": parent_reply.id,  # Use the write-only field
        }
        response = subscribed_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityReply.objects.count() == 2  # Parent + new reply
        new_reply = CommunityReply.objects.get(parent_reply=parent_reply)
        assert new_reply.author == user
        assert new_reply.post == post
        assert new_reply.parent_reply == parent_reply
        # Check response data
        assert response.data["parent_reply_read_id"] == parent_reply.id

    def test_create_reply_missing_content(self, subscribed_client):
        """Verify validation error for missing content field (400)."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {}  # Missing content
        response = subscribed_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "content" in response.data

    def test_create_reply_post_not_found(self, subscribed_client):
        """Verify 404 when creating reply for a non-existent post ID."""
        url = replies_list_create_url(99999)
        payload = {"content": "Test"}
        response = subscribed_client.post(url, data=payload, format="json")
        # View's get_post_object raises NotFound
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_reply_post_closed_by_user(self, subscribed_client):
        """Verify non-admin users cannot reply to a closed post (403)."""
        post = CommunityPostFactory(is_closed=True)
        url = replies_list_create_url(post.id)
        payload = {"content": "Trying to reply to closed post"}
        response = subscribed_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "This post is closed" in response.data.get("detail", "")

    def test_create_reply_post_closed_by_admin(self, admin_client):
        """Verify admins *can* reply to a closed post."""
        post = CommunityPostFactory(is_closed=True)
        url = replies_list_create_url(post.id)
        payload = {"content": "Admin replying to closed post"}
        response = admin_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityReply.objects.filter(post=post).count() == 1

    def test_create_reply_invalid_parent_id(self, subscribed_client):
        """Verify error if parent_reply_id does not exist (400)."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {"content": "Invalid parent test", "parent_reply_id": 99999}
        response = subscribed_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "parent_reply_id" in response.data  # Serializer validation

    def test_create_reply_parent_from_different_post(self, subscribed_client):
        """Verify error if parent_reply belongs to a different post (400)."""
        post1 = CommunityPostFactory()
        post2 = CommunityPostFactory()
        parent_reply_wrong_post = CommunityReplyFactory(post=post2)  # Belongs to post2
        url = replies_list_create_url(post1.id)  # Replying to post1
        payload = {
            "content": "Parent from wrong post test",
            "parent_reply_id": parent_reply_wrong_post.id,
        }
        response = subscribed_client.post(url, data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "parent_reply_id" in response.data
        assert (
            "Parent reply does not belong to this post"
            in response.data["parent_reply_id"]
        )


# --- TagListView Tests ---


class TestTagList:
    """Tests for listing Tags (GET /tags/)."""

    def test_list_tags_unauthenticated(self, api_client):
        """Verify unauthenticated users cannot list tags (401)."""
        response = api_client.get(TAGS_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Assuming IsAuthenticated is the permission, not IsSubscribed
    def test_list_tags_success(self, authenticated_client):
        """Verify authenticated users can list tags with counts, ordered by count."""
        # Create posts with varying tag usage
        CommunityPostFactory.create(tags=["common", "unique1"])
        CommunityPostFactory.create(tags=["common", "unique2"])
        CommunityPostFactory.create(tags=["common"])
        CommunityPostFactory.create(tags=["unique2"])  # unique2 used twice now
        Tag.objects.create(name="unused_tag")  # Tag not associated with any post

        response = authenticated_client.get(TAGS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data  # Check pagination structure

        results = response.data["results"]
        # Should only list tags used in Community Posts (view filters count > 0)
        tag_names = [t["name"] for t in results]
        assert "common" in tag_names
        assert "unique1" in tag_names
        assert "unique2" in tag_names
        assert "unused_tag" not in tag_names

        assert len(results) == 3  # Only 3 tags are used

        # Check counts and ordering (most frequent first)
        tag_data = {t["name"]: t for t in results}
        assert tag_data["common"]["count"] == 3
        assert tag_data["unique2"]["count"] == 2
        assert tag_data["unique1"]["count"] == 1

        # Verify order: common (3), unique2 (2), unique1 (1)
        assert tag_names[0] == "common"
        assert tag_names[1] == "unique2"
        assert tag_names[2] == "unique1"

    def test_list_tags_empty(self, authenticated_client):
        """Verify empty list is returned when no posts/tags exist."""
        response = authenticated_client.get(TAGS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0
