import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

# Import models and factories from the community app
from apps.community.models import CommunityPost, CommunityReply
from apps.community.tests.factories import CommunityPostFactory, CommunityReplyFactory
from apps.users.tests.factories import UserFactory  # For creating different users

# Constants for URLs
ADMIN_POSTS_LIST_URL = reverse("api:v1:admin_panel:admin-communitypost-list")
ADMIN_REPLIES_LIST_URL = reverse("api:v1:admin_panel:admin-communityreply-list")


def _get_post_detail_url(post_id):
    return reverse(
        "api:v1:admin_panel:admin-communitypost-detail", kwargs={"pk": post_id}
    )


def _get_reply_detail_url(reply_id):
    return reverse(
        "api:v1:admin_panel:admin-communityreply-detail", kwargs={"pk": reply_id}
    )


@pytest.mark.django_db
class TestAdminCommunityPostViewSetPermissions:
    """Tests permission handling for the Admin Community Post endpoints."""

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),  # Anonymous
            ("authenticated_client", status.HTTP_403_FORBIDDEN),  # Standard non-admin
            ("subscribed_client", status.HTTP_403_FORBIDDEN),  # Subscribed non-admin
            ("admin_client", status.HTTP_200_OK),  # Admin
        ],
    )
    def test_list_permissions(self, request, client_fixture, expected_status):
        """Test LIST permissions for different user types."""
        client: APIClient = request.getfixturevalue(client_fixture)
        response = client.get(ADMIN_POSTS_LIST_URL)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            (
                "admin_client",
                status.HTTP_201_CREATED,
            ),  # Expecting create success for admin
        ],
    )
    def test_create_permissions(self, request, client_fixture, expected_status):
        """Test CREATE permissions for different user types."""
        client: APIClient = request.getfixturevalue(client_fixture)
        post_data = {
            "post_type": CommunityPost.PostType.DISCUSSION,
            "title": "Admin Announcement",
            "content": "This is an important announcement.",
        }
        # Need admin client user for author setting in perform_create
        if client_fixture == "admin_client":
            post_data["author"] = client.user.id  # Simulate passing author ID

        response = client.post(ADMIN_POSTS_LIST_URL, data=post_data)

        # Adjust check for create success vs. permission denied
        if expected_status == status.HTTP_201_CREATED:
            assert response.status_code == expected_status
        else:
            assert response.status_code == expected_status

    # Similarly test retrieve, update, partial_update, destroy permissions...
    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_200_OK),  # Retrieve OK for admin
        ],
    )
    def test_retrieve_permissions(self, request, client_fixture, expected_status):
        """Test RETRIEVE permissions."""
        client: APIClient = request.getfixturevalue(client_fixture)
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = _get_post_detail_url(post.id)
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_200_OK),  # Update OK for admin
        ],
    )
    def test_update_permissions(self, request, client_fixture, expected_status):
        """Test UPDATE (PATCH) permissions."""
        client: APIClient = request.getfixturevalue(client_fixture)
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = _get_post_detail_url(post.id)
        update_data = {"content": "Updated by admin."}
        response = client.patch(url, data=update_data)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_204_NO_CONTENT),  # Delete OK for admin
        ],
    )
    def test_destroy_permissions(self, request, client_fixture, expected_status):
        """Test DESTROY permissions."""
        client: APIClient = request.getfixturevalue(client_fixture)
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = _get_post_detail_url(post.id)
        response = client.delete(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
class TestAdminCommunityPostViewSetActions:
    """Tests actions performed by an admin user."""

    def test_admin_can_list_all_posts(self, admin_client):
        """Admin should see posts from all users."""
        user1 = UserFactory()
        user2 = UserFactory()
        CommunityPostFactory.create_batch(3, author=user1)
        CommunityPostFactory.create_batch(2, author=user2)
        CommunityPostFactory.create_batch(1, author=admin_client.user)  # Post by admin

        response = admin_client.get(ADMIN_POSTS_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 6
        assert len(response.data["results"]) <= 20  # Check pagination limit

    def test_admin_can_retrieve_any_post(self, admin_client):
        """Admin can retrieve details of a post created by another user."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user, title="User Post Title")
        url = _get_post_detail_url(post.id)

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == post.id
        assert response.data["title"] == "User Post Title"
        assert response.data["author"]["id"] == other_user.id

    def test_admin_can_update_any_post(self, admin_client):
        """Admin can update content of a post created by another user."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user, content="Original content")
        url = _get_post_detail_url(post.id)
        update_data = {"content": "Updated by admin"}

        response = admin_client.patch(url, data=update_data)
        post.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Updated by admin"
        assert post.content == "Updated by admin"

    def test_admin_can_pin_unpin_post(self, admin_client):
        """Admin can set and unset the is_pinned flag."""
        post = CommunityPostFactory(is_pinned=False)
        url = _get_post_detail_url(post.id)

        # Pin the post
        response_pin = admin_client.patch(url, data={"is_pinned": True})
        post.refresh_from_db()
        assert response_pin.status_code == status.HTTP_200_OK
        assert response_pin.data["is_pinned"] is True
        assert post.is_pinned is True

        # Unpin the post
        response_unpin = admin_client.patch(url, data={"is_pinned": False})
        post.refresh_from_db()
        assert response_unpin.status_code == status.HTTP_200_OK
        assert response_unpin.data["is_pinned"] is False
        assert post.is_pinned is False

    def test_admin_can_close_open_post(self, admin_client):
        """Admin can set and unset the is_closed flag."""
        post = CommunityPostFactory(is_closed=False)
        url = _get_post_detail_url(post.id)

        # Close the post
        response_close = admin_client.patch(url, data={"is_closed": True})
        post.refresh_from_db()
        assert response_close.status_code == status.HTTP_200_OK
        assert response_close.data["is_closed"] is True
        assert post.is_closed is True

        # Open the post
        response_open = admin_client.patch(url, data={"is_closed": False})
        post.refresh_from_db()
        assert response_open.status_code == status.HTTP_200_OK
        assert response_open.data["is_closed"] is False
        assert post.is_closed is False

    def test_admin_can_delete_any_post(self, admin_client):
        """Admin can delete a post created by another user."""
        other_user = UserFactory()
        post = CommunityPostFactory(author=other_user)
        url = _get_post_detail_url(post.id)
        initial_count = CommunityPost.objects.count()

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CommunityPost.objects.count() == initial_count - 1
        with pytest.raises(CommunityPost.DoesNotExist):
            CommunityPost.objects.get(id=post.id)


@pytest.mark.django_db
class TestAdminCommunityReplyViewSetPermissions:
    """Tests permission handling for the Admin Community Reply endpoints."""

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_200_OK),
        ],
    )
    def test_list_permissions(self, request, client_fixture, expected_status):
        """Test LIST permissions for replies."""
        client: APIClient = request.getfixturevalue(client_fixture)
        response = client.get(ADMIN_REPLIES_LIST_URL)
        assert response.status_code == expected_status

    # Test retrieve, update, destroy permissions similarly...
    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_200_OK),  # Retrieve OK
        ],
    )
    def test_retrieve_permissions(self, request, client_fixture, expected_status):
        """Test RETRIEVE permissions for replies."""
        client: APIClient = request.getfixturevalue(client_fixture)
        reply = CommunityReplyFactory()
        url = _get_reply_detail_url(reply.id)
        response = client.get(url)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_200_OK),  # Update OK
        ],
    )
    def test_update_permissions(self, request, client_fixture, expected_status):
        """Test UPDATE (PATCH) permissions for replies."""
        client: APIClient = request.getfixturevalue(client_fixture)
        reply = CommunityReplyFactory()
        url = _get_reply_detail_url(reply.id)
        update_data = {"content": "Admin updated reply."}
        response = client.patch(url, data=update_data)
        assert response.status_code == expected_status

    @pytest.mark.parametrize(
        "client_fixture, expected_status",
        [
            ("api_client", status.HTTP_401_UNAUTHORIZED),
            ("authenticated_client", status.HTTP_403_FORBIDDEN),
            ("subscribed_client", status.HTTP_403_FORBIDDEN),
            ("admin_client", status.HTTP_204_NO_CONTENT),  # Delete OK
        ],
    )
    def test_destroy_permissions(self, request, client_fixture, expected_status):
        """Test DESTROY permissions for replies."""
        client: APIClient = request.getfixturevalue(client_fixture)
        reply = CommunityReplyFactory()
        url = _get_reply_detail_url(reply.id)
        response = client.delete(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
class TestAdminCommunityReplyViewSetActions:
    """Tests actions performed by an admin user on replies."""

    def test_admin_can_list_all_replies(self, admin_client):
        """Admin should see replies from all users on all posts."""
        user1 = UserFactory()
        user2 = UserFactory()
        post1 = CommunityPostFactory()
        post2 = CommunityPostFactory()
        CommunityReplyFactory.create_batch(2, post=post1, author=user1)
        CommunityReplyFactory.create_batch(3, post=post2, author=user2)
        CommunityReplyFactory(post=post1, author=admin_client.user)  # Reply by admin

        response = admin_client.get(ADMIN_REPLIES_LIST_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 6
        assert len(response.data["results"]) <= 20

    def test_admin_can_retrieve_any_reply(self, admin_client):
        """Admin can retrieve details of a reply created by another user."""
        other_user = UserFactory()
        reply = CommunityReplyFactory(author=other_user, content="User reply content")
        url = _get_reply_detail_url(reply.id)

        response = admin_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == reply.id
        assert response.data["content"] == "User reply content"
        assert response.data["author"]["id"] == other_user.id

    def test_admin_can_update_any_reply(self, admin_client):
        """Admin can update the content of a reply created by another user."""
        other_user = UserFactory()
        reply = CommunityReplyFactory(author=other_user, content="Original reply")
        url = _get_reply_detail_url(reply.id)
        update_data = {"content": "Updated reply by admin"}

        response = admin_client.patch(url, data=update_data)
        reply.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert response.data["content"] == "Updated reply by admin"
        assert reply.content == "Updated reply by admin"

    def test_admin_can_delete_any_reply(self, admin_client):
        """Admin can delete a reply created by another user."""
        other_user = UserFactory()
        reply = CommunityReplyFactory(author=other_user)
        url = _get_reply_detail_url(reply.id)
        initial_count = CommunityReply.objects.count()

        response = admin_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert CommunityReply.objects.count() == initial_count - 1
        with pytest.raises(CommunityReply.DoesNotExist):
            CommunityReply.objects.get(id=reply.id)

    # Optional: Test creating a reply as admin if that's a supported workflow
    # def test_admin_can_create_reply(self, admin_client):
    #     post = CommunityPostFactory()
    #     reply_data = {
    #         "post": post.id,
    #         "content": "Admin reply content."
    #     }
    #     response = admin_client.post(ADMIN_REPLIES_LIST_URL, data=reply_data)
    #     assert response.status_code == status.HTTP_201_CREATED
    #     assert response.data["content"] == "Admin reply content."
    #     assert response.data["author"]["id"] == admin_client.user.id
