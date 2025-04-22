# apps/community/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status

from apps.community.models import CommunityPost, CommunityReply, CommunityPost
from apps.community.tests.factories import CommunityPostFactory, CommunityReplyFactory
from apps.users.tests.factories import (
    UserFactory,
)  # Import UserFactory if needed directly

# Constants for URLs
POSTS_LIST_CREATE_URL = reverse("api:v1:community:communitypost-list")
TAGS_LIST_URL = reverse("api:v1:community:tag-list")


def post_detail_url(post_id):
    return reverse("api:v1:community:communitypost-detail", kwargs={"pk": post_id})


def replies_list_create_url(post_id):
    return reverse("api:v1:community:post-replies", kwargs={"post_pk": post_id})


# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

# --- CommunityPostViewSet Tests ---


class TestCommunityPostList:

    def test_list_posts_unauthenticated(self, api_client):
        """Verify unauthenticated users cannot list posts."""
        response = api_client.get(POSTS_LIST_CREATE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_posts_authenticated_not_subscribed(self, authenticated_client):
        """Verify authenticated but non-subscribed users cannot list posts."""
        response = authenticated_client.get(POSTS_LIST_CREATE_URL)
        # Assuming IsSubscribed returns 403
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_posts_success(self, subscribed_client):
        """Verify subscribed users can list posts with correct structure."""
        CommunityPostFactory.create_batch(5)
        response = subscribed_client.get(POSTS_LIST_CREATE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data
        assert "results" in response.data
        assert (
            len(response.data["results"]) <= subscribed_client.settings.PAGE_SIZE
        )  # Respect pagination
        # Check structure of one result
        if response.data["results"]:
            post_data = response.data["results"][0]
            assert "id" in post_data
            assert "author" in post_data
            assert "username" in post_data["author"]
            assert "post_type" in post_data
            assert "content_excerpt" in post_data
            assert "reply_count" in post_data
            assert "created_at" in post_data
            assert "tags" in post_data
            # Ensure sensitive fields are NOT present in list view
            assert "content" not in post_data  # Should be excerpt
            assert "replies" not in post_data

    def test_list_posts_filtering_by_type(self, subscribed_client):
        """Verify filtering posts by post_type works."""
        discussion_post = CommunityPostFactory(
            post_type=CommunityPost.PostType.DISCUSSION
        )
        achievement_post = CommunityPostFactory(
            post_type=CommunityPost.PostType.ACHIEVEMENT
        )

        url = f"{POSTS_LIST_CREATE_URL}?post_type={CommunityPost.PostType.DISCUSSION}"
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == discussion_post.id
        assert (
            response.data["results"][0]["post_type"]
            == CommunityPost.PostType.DISCUSSION
        )

    def test_list_posts_filtering_by_tags(self, subscribed_client):
        """Verify filtering posts by tags works."""
        post1 = CommunityPostFactory.create(tags=["python", "django"])
        post2 = CommunityPostFactory.create(tags=["python", "testing"])
        post3 = CommunityPostFactory.create(tags=["django"])

        # Filter by single tag
        url_python = f"{POSTS_LIST_CREATE_URL}?tags=python"
        response_python = subscribed_client.get(url_python)
        assert response_python.status_code == status.HTTP_200_OK
        assert response_python.data["count"] == 2
        post_ids_python = {p["id"] for p in response_python.data["results"]}
        assert post1.id in post_ids_python
        assert post2.id in post_ids_python

        # Filter by multiple tags (comma-separated)
        url_multi = f"{POSTS_LIST_CREATE_URL}?tags=python,testing"
        response_multi = subscribed_client.get(url_multi)
        assert response_multi.status_code == status.HTTP_200_OK
        assert response_multi.data["count"] == 1  # Only post2 matches both
        assert response_multi.data["results"][0]["id"] == post2.id

    def test_list_posts_search(self, subscribed_client):
        """Verify searching posts works."""
        post1 = CommunityPostFactory(
            title="About Quant Problems", content="Let's discuss algebra."
        )
        post2 = CommunityPostFactory(
            content="My experience with verbal section.", tags=["verbal"]
        )
        author = UserFactory(username="tester_search")
        post3 = CommunityPostFactory(
            author=author, content="Searching for study partner."
        )

        url = f"{POSTS_LIST_CREATE_URL}?search=algebra"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == post1.id

        url_tag = f"{POSTS_LIST_CREATE_URL}?search=verbal"
        response_tag = subscribed_client.get(url_tag)
        assert response_tag.status_code == status.HTTP_200_OK
        assert response_tag.data["count"] == 1
        assert response_tag.data["results"][0]["id"] == post2.id

        url_author = f"{POSTS_LIST_CREATE_URL}?search=tester_search"
        response_author = subscribed_client.get(url_author)
        assert response_author.status_code == status.HTTP_200_OK
        assert response_author.data["count"] == 1
        assert response_author.data["results"][0]["id"] == post3.id

    def test_list_posts_ordering(self, subscribed_client):
        """Verify ordering of posts (pinned first, then date)."""
        post_normal1 = CommunityPostFactory()
        post_pinned = CommunityPostFactory(is_pinned=True)
        post_normal2 = CommunityPostFactory()  # Created after post_normal1

        response = subscribed_client.get(POSTS_LIST_CREATE_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data["results"]
        assert len(results) == 3
        assert results[0]["id"] == post_pinned.id  # Pinned post first
        assert results[1]["id"] == post_normal2.id  # Newer normal post second
        assert results[2]["id"] == post_normal1.id  # Older normal post last

        # Test ordering by reply_count (needs annotation in view)
        post_many_replies = CommunityPostFactory()
        CommunityReplyFactory.create_batch(5, post=post_many_replies)
        post_few_replies = CommunityPostFactory()
        CommunityReplyFactory.create_batch(2, post=post_few_replies)

        url = f"{POSTS_LIST_CREATE_URL}?ordering=-reply_count"
        response_ordered = subscribed_client.get(url)
        results_ordered = response_ordered.data["results"]
        # Find the posts with replies within the full list
        ids_ordered = [p["id"] for p in results_ordered]
        assert ids_ordered.index(post_many_replies.id) < ids_ordered.index(
            post_few_replies.id
        )


class TestCommunityPostCreate:

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_create_post_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated or non-subscribed users cannot create posts."""
        client = request.getfixturevalue(client_fixture_name)
        payload = {
            "post_type": CommunityPost.PostType.DISCUSSION,
            "content": "This is a test post.",
        }
        response = client.post(POSTS_LIST_CREATE_URL, data=payload)
        expected_status = (
            status.HTTP_401_UNAUTHORIZED
            if client_fixture_name == "api_client"
            else status.HTTP_403_FORBIDDEN
        )
        assert response.status_code == expected_status

    def test_create_post_success(self, subscribed_client):
        """Verify subscribed users can create a valid post."""
        user = subscribed_client.user
        payload = {
            "post_type": CommunityPost.PostType.TIP,
            "title": "My Study Tip",
            "content": "Focus on understanding concepts!",
            "tags": ["tips", "study"],
        }
        response = subscribed_client.post(
            POSTS_LIST_CREATE_URL, data=payload, format="json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityPost.objects.count() == 1
        post = CommunityPost.objects.first()
        assert post.author == user
        assert post.post_type == CommunityPost.PostType.TIP
        assert post.title == "My Study Tip"
        assert post.content == "Focus on understanding concepts!"
        # Check response data structure
        assert response.data["id"] == post.id
        assert response.data["author"]["username"] == user.username
        assert response.data["post_type"] == CommunityPost.PostType.TIP
        # Check tags were saved (TaggitSerializerField handles this)
        assert isinstance(response.data["tags"], list)
        assert "tips" in response.data["tags"]
        assert "study" in response.data["tags"]

    def test_create_post_missing_content(self, subscribed_client):
        """Verify validation error for missing content."""
        payload = {"post_type": CommunityPost.PostType.DISCUSSION}
        response = subscribed_client.post(POSTS_LIST_CREATE_URL, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "content" in response.data

    def test_create_post_invalid_type(self, subscribed_client):
        """Verify validation error for invalid post_type."""
        payload = {"post_type": "invalid_type", "content": "Test"}
        response = subscribed_client.post(POSTS_LIST_CREATE_URL, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "post_type" in response.data


class TestCommunityPostRetrieve:

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_retrieve_post_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated or non-subscribed users cannot retrieve posts."""
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

    def test_retrieve_post_success(self, subscribed_client):
        """Verify subscribed users can retrieve a post with correct details."""
        post = CommunityPostFactory(
            author=subscribed_client.user, tags=["detail", "test"]
        )
        reply1 = CommunityReplyFactory(post=post)
        reply2 = CommunityReplyFactory(post=post)  # Another reply

        url = post_detail_url(post.id)
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Check main post fields (using base serializer)
        assert response.data["id"] == post.id
        assert response.data["author"]["username"] == post.author.username
        assert response.data["content"] == post.content
        assert "tags" in response.data
        assert "detail" in [tag["name"] for tag in response.data["tags"]]

        # Check nested replies structure added by the retrieve method
        assert "replies" in response.data
        assert "count" in response.data["replies"]
        assert "results" in response.data["replies"]
        assert response.data["replies"]["count"] == 2
        assert len(response.data["replies"]["results"]) == 2
        reply_ids = {r["id"] for r in response.data["replies"]["results"]}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids
        # Check reply structure
        reply_data = response.data["replies"]["results"][0]
        assert "id" in reply_data
        assert "author" in reply_data
        assert "content" in reply_data
        assert "parent_reply_id" in reply_data  # Important for frontend threading

    def test_retrieve_post_not_found(self, subscribed_client):
        """Verify 404 for non-existent post."""
        url = post_detail_url(9999)
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCommunityPostUpdate:

    def test_update_post_not_author(self, subscribed_client):
        """Verify non-authors cannot update a post."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = post_detail_url(post.id)
        payload = {"content": "Updated content by wrong user."}
        response = subscribed_client.put(url, data=payload)  # PUT requires all fields
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_partial_update_post_author_success(self, subscribed_client):
        """Verify authors can partially update their post."""
        post = CommunityPostFactory(author=subscribed_client.user, content="Original")
        url = post_detail_url(post.id)
        payload = {"content": "Updated content by author."}
        response = subscribed_client.patch(url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.content == "Updated content by author."
        assert response.data["content"] == "Updated content by author."

    def test_update_pin_close_by_author(self, subscribed_client):
        """Verify authors cannot pin or close their posts."""
        post = CommunityPostFactory(
            author=subscribed_client.user, is_pinned=False, is_closed=False
        )
        url = post_detail_url(post.id)
        payload = {"is_pinned": True, "is_closed": True}
        response = subscribed_client.patch(url, data=payload)

        assert response.status_code == status.HTTP_200_OK  # Update succeeds but...
        post.refresh_from_db()
        assert not post.is_pinned  # ...pinned status should not change
        assert not post.is_closed  # ...closed status should not change

    def test_update_pin_close_by_admin(self, admin_client):
        """Verify admins can pin or close posts."""
        post = CommunityPostFactory(is_pinned=False, is_closed=False)
        url = post_detail_url(post.id)
        payload = {"is_pinned": True, "is_closed": True}
        response = admin_client.patch(
            url, data=payload
        )  # Assuming admin_client uses JWT/token auth

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.is_pinned
        assert post.is_closed
        assert response.data["is_pinned"]
        assert response.data["is_closed"]


class TestCommunityPostDelete:

    def test_delete_post_not_author(self, subscribed_client):
        """Verify non-authors cannot delete a post."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = post_detail_url(post.id)
        response = subscribed_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_author_success(self, subscribed_client):
        """Verify authors can delete their post."""
        post = CommunityPostFactory(author=subscribed_client.user)
        url = post_detail_url(post.id)
        response = subscribed_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CommunityPost.objects.filter(id=post.id).exists()

    def test_delete_post_admin_success(self, admin_client):
        """Verify admins can delete any post."""
        post = CommunityPostFactory()  # Author doesn't matter
        url = post_detail_url(post.id)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CommunityPost.objects.filter(id=post.id).exists()


# --- CommunityReplyListCreateView Tests ---


class TestCommunityReplyList:

    def test_list_replies_unauthenticated(self, api_client):
        """Verify unauthenticated users cannot list replies."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_replies_authenticated_not_subscribed(self, authenticated_client):
        """Verify non-subscribed users cannot list replies."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_replies_success(self, subscribed_client):
        """Verify subscribed users can list replies for a post."""
        post = CommunityPostFactory()
        reply1 = CommunityReplyFactory(post=post)
        reply2 = CommunityReplyFactory(post=post)
        # Create reply for another post, should not be listed
        other_post = CommunityPostFactory()
        CommunityReplyFactory(post=other_post)

        url = replies_list_create_url(post.id)
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        reply_ids = {r["id"] for r in response.data["results"]}
        assert reply1.id in reply_ids
        assert reply2.id in reply_ids

    def test_list_replies_post_not_found(self, subscribed_client):
        """Verify 404 when listing replies for a non-existent post."""
        url = replies_list_create_url(9999)
        response = subscribed_client.get(url)
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # Based on view's check


class TestCommunityReplyCreate:

    @pytest.mark.parametrize(
        "client_fixture_name", ["api_client", "authenticated_client"]
    )
    def test_create_reply_unauthorized(self, request, client_fixture_name):
        """Verify unauthenticated/non-subscribed cannot create replies."""
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

    def test_create_reply_success(self, subscribed_client):
        """Verify subscribed users can create a top-level reply."""
        user = subscribed_client.user
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {"content": "This is a test reply"}
        response = subscribed_client.post(url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityReply.objects.count() == 1
        reply = CommunityReply.objects.first()
        assert reply.author == user
        assert reply.post == post
        assert reply.content == "This is a test reply"
        assert reply.parent_reply is None
        # Check response data
        assert response.data["id"] == reply.id
        assert response.data["author"]["username"] == user.username
        assert response.data["content"] == "This is a test reply"
        assert response.data["parent_reply_id"] is None

    def test_create_threaded_reply_success(self, subscribed_client):
        """Verify subscribed users can create a threaded reply."""
        user = subscribed_client.user
        post = CommunityPostFactory()
        parent_reply = CommunityReplyFactory(post=post)  # Reply to reply to
        url = replies_list_create_url(post.id)
        payload = {
            "content": "This is a threaded reply",
            "parent_reply_id": parent_reply.id,
        }
        response = subscribed_client.post(url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert CommunityReply.objects.count() == 2  # Parent + new reply
        new_reply = CommunityReply.objects.get(content="This is a threaded reply")
        assert new_reply.author == user
        assert new_reply.post == post
        assert new_reply.parent_reply == parent_reply
        # Check response data
        assert response.data["parent_reply_id"] == parent_reply.id

    def test_create_reply_missing_content(self, subscribed_client):
        """Verify validation error for missing content."""
        post = CommunityPostFactory()
        url = replies_list_create_url(post.id)
        payload = {}
        response = subscribed_client.post(url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "content" in response.data

    def test_create_reply_post_not_found(self, subscribed_client):
        """Verify error when creating reply for non-existent post."""
        url = replies_list_create_url(9999)
        payload = {"content": "Test"}
        response = subscribed_client.post(url, data=payload)
        # Based on view implementation, this might be caught in perform_create
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Post not found" in response.data.get("detail", "")

    def test_create_reply_post_closed(self, subscribed_client):
        """Verify user cannot reply to a closed post."""
        post = CommunityPostFactory(is_closed=True)
        url = replies_list_create_url(post.id)
        payload = {"content": "Trying to reply to closed post"}
        response = subscribed_client.post(url, data=payload)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # PermissionDenied raised
        assert "This post is closed" in response.data.get("detail", "")

    def test_create_reply_invalid_parent(self, subscribed_client):
        """Verify error if parent_reply belongs to a different post."""
        post1 = CommunityPostFactory()
        post2 = CommunityPostFactory()
        parent_reply_wrong_post = CommunityReplyFactory(post=post2)
        url = replies_list_create_url(post1.id)  # Replying to post1
        payload = {
            "content": "Invalid parent test",
            "parent_reply_id": parent_reply_wrong_post.id,
        }
        response = subscribed_client.post(url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "parent_reply_id" in response.data
        assert (
            "Parent reply does not belong to this post."
            in response.data["parent_reply_id"][0]
        )


# --- TagListView Tests ---


class TestTagList:

    def test_list_tags_unauthenticated(self, api_client):
        """Verify unauthenticated cannot list tags."""
        response = api_client.get(TAGS_LIST_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Assuming IsAuthenticated is sufficient for listing tags, not IsSubscribed
    def test_list_tags_success(self, authenticated_client):
        """Verify authenticated users can list tags."""
        post1 = CommunityPostFactory.create(tags=["common", "tag1"])
        post2 = CommunityPostFactory.create(tags=["common", "tag2"])
        post3 = CommunityPostFactory.create(tags=["common"])
        # Add a tag used outside community app, should not be counted if view filters correctly
        # SomeOtherModelFactory(tags=['other_tag'])

        response = authenticated_client.get(TAGS_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

        results = response.data["results"]
        tag_names = [t["name"] for t in results]

        assert "common" in tag_names
        assert "tag1" in tag_names
        assert "tag2" in tag_names
        # assert 'other_tag' not in tag_names # If view filters by content type

        # Check ordering by count
        common_tag_data = next(t for t in results if t["name"] == "common")
        tag1_data = next(t for t in results if t["name"] == "tag1")
        assert common_tag_data["count"] == 3  # Assuming view filters by CommunityPost
        assert tag1_data["count"] == 1
        # Ensure 'common' appears before 'tag1' or 'tag2' due to higher count
        assert tag_names.index("common") == 0  # Most common first
