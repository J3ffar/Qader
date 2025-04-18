import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

# Use the specific factory path
from apps.users.tests.factories import UserFactory, SerialCodeFactory
from apps.users.models import UserProfile


@pytest.fixture(scope="session")
def _django_db_setup():
    pass


@pytest.fixture
def api_client():
    return APIClient()


# --- User Fixtures ---


@pytest.fixture
def base_user(db):
    """Creates a basic user instance using the factory."""
    # Ensure profile is created via factory or signal
    user = UserFactory()
    UserProfile.objects.get_or_create(user=user)  # Ensure profile exists
    return user


@pytest.fixture
def subscribed_user(db):
    """Creates a distinct user and gives them an active subscription."""
    user = UserFactory(username="subscribed_user_fixture")  # Use distinct username
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.subscription_expires_at = timezone.now() + timedelta(days=30)
    profile.save()
    user.refresh_from_db()
    return user


@pytest.fixture
def unsubscribed_user(db):
    """Creates a distinct user with NO active subscription."""
    user = UserFactory(username="unsubscribed_user_fixture")  # Use distinct username
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.subscription_expires_at = None  # Ensure no subscription
    profile.save()
    user.refresh_from_db()
    return user


@pytest.fixture
def admin_user(db):
    """Creates an admin user instance with a known password."""
    # Use a predictable password for admin login during tests
    admin_password = "testadminpassword"
    user = UserFactory(
        make_admin=True, username="admin_user_fixture", password=admin_password
    )
    UserProfile.objects.get_or_create(user=user)  # Ensure profile exists
    # Store password with the user object for easy access in the client fixture
    user._test_admin_password = admin_password
    return user


# --- API Client Fixtures ---


@pytest.fixture
def subscribed_client(api_client, subscribed_user):
    """Provides an API client authenticated as a subscribed user."""
    api_client.force_authenticate(user=subscribed_user)
    api_client.user = subscribed_user  # Attach user for convenience
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up


@pytest.fixture
def authenticated_client(api_client, unsubscribed_user):
    """
    Provides an API client authenticated as a standard, UNSUBSCRIBED user.
    Renamed from original 'authenticated_client' which was potentially ambiguous.
    Use this client for tests checking behavior for non-subscribed users.
    """
    api_client.force_authenticate(user=unsubscribed_user)
    api_client.user = unsubscribed_user  # Attach user for convenience
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up


@pytest.fixture
def admin_client(db, api_client, admin_user):  # Add db dependency for login
    """
    Provides an API client LOGGED IN via Django sessions as an admin user.
    This is necessary for testing Django Admin views.
    """
    # Use client.login() for session-based authentication
    login_successful = api_client.login(
        username=admin_user.username,
        password=admin_user._test_admin_password,  # Use the password set in the admin_user fixture
    )
    # Add an assertion to make sure the login worked, crucial for debugging
    assert (
        login_successful
    ), f"Admin client login failed for user '{admin_user.username}'"

    api_client.user = admin_user  # Attach user object for convenience
    yield api_client
    api_client.logout()  # Use logout to clear the session


@pytest.fixture
def active_serial_code(db):
    """Provides an active, unused SerialCode instance."""
    return SerialCodeFactory(is_active=True, is_used=False)


@pytest.fixture
def used_serial_code(db, base_user):
    """Provides a used SerialCode instance linked to a user."""
    return SerialCodeFactory(
        is_active=True, is_used=True, used_by=base_user, used_at=timezone.now()
    )
