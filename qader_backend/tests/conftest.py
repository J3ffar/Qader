import pytest
from rest_framework.test import APIClient
from tests.users.factories import UserFactory


@pytest.fixture
def api_client():
    """Fixture for DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, db):
    """Fixture for an authenticated API client (regular user)."""
    user = UserFactory()
    api_client.force_authenticate(user=user)
    # Attach user to client for convenience in tests
    api_client.user = user
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up


@pytest.fixture
def admin_client(api_client, db):
    """Fixture for an authenticated admin client."""
    admin_user = UserFactory(make_admin=True)  # Use factory helper
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up
