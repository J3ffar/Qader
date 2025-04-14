import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

# Use the specific factory path
from apps.users.tests.factories import UserFactory, SerialCodeFactory


@pytest.fixture(scope="session")  # Make factory boy session-scoped if needed
def _django_db_setup():
    # Setup for django db access across tests
    # Potentially clear cache or perform other setup here
    pass


@pytest.fixture
def api_client():
    """Provides a standard DRF API client instance."""
    return APIClient()


@pytest.fixture
def user(db):
    """Creates a standard user instance using the factory."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Creates an admin user instance using the factory helper."""
    return UserFactory(make_admin=True)


@pytest.fixture
def authenticated_client(api_client, user):
    """Provides an API client authenticated as a standard user."""
    api_client.force_authenticate(user=user)
    # Attach user to client for convenience in tests, if desired
    api_client.user = user
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up authentication state


@pytest.fixture
def admin_client(api_client, admin_user):
    """Provides an API client authenticated as an admin user."""
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up


@pytest.fixture
def active_serial_code(db):
    """Provides an active, unused SerialCode instance."""
    return SerialCodeFactory(is_active=True, is_used=False)


@pytest.fixture
def used_serial_code(db, user):
    """Provides a used SerialCode instance linked to a user."""
    return SerialCodeFactory(
        is_active=True, is_used=True, used_by=user, used_at=timezone.now()
    )


@pytest.fixture
def subscribed_user(db, user):  # Reuse the basic user fixture
    """Creates a user and gives them an active subscription."""
    profile = user.profile  # Get or create profile
    profile.subscription_expires_at = timezone.now() + timedelta(days=30)
    profile.save()
    user.refresh_from_db()  # Refresh user object if needed
    return user


@pytest.fixture
def subscribed_client(api_client, subscribed_user):
    """Provides an API client authenticated as a subscribed user."""
    api_client.force_authenticate(user=subscribed_user)
    api_client.user = subscribed_user
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up
