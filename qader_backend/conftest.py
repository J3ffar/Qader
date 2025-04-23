import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

# Use the specific factory path
from apps.users.tests.factories import UserFactory, SerialCodeFactory
from apps.users.models import SerialCode, UserProfile  # Direct import is fine here


@pytest.fixture(scope="session")
def _django_db_setup():
    """Standard pytest-django fixture to ensure DB setup happens once per session."""
    pass


@pytest.fixture
def api_client() -> APIClient:
    """Provides a basic, unauthenticated DRF APIClient instance."""
    return APIClient()


# --- User Fixtures ---


@pytest.fixture
def standard_user(db) -> User:  # Renamed from base_user for clarity
    """Creates a standard, active user instance with a profile."""
    user = UserFactory(username="standarduser")
    # Ensure profile exists - factory or signal should handle, this is defensive
    UserProfile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def subscribed_user(db) -> User:
    """Creates a distinct user with an active subscription."""
    user = UserFactory(username="subscribed_user")
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.subscription_expires_at = timezone.now() + timedelta(days=30)
    profile.save(update_fields=["subscription_expires_at"])
    user.profile = profile  # Attach profile for easier access if needed
    return user


@pytest.fixture
def unsubscribed_user(db) -> User:
    """Creates a distinct user with NO active subscription (or expired)."""
    user = UserFactory(username="unsubscribed_user")
    profile, _ = UserProfile.objects.get_or_create(user=user)
    # Ensure subscription is not active
    if (
        profile.subscription_expires_at
        and profile.subscription_expires_at > timezone.now()
    ):
        profile.subscription_expires_at = timezone.now() - timedelta(days=1)
    elif profile.subscription_expires_at is None:
        pass  # Already unsubscribed
    else:  # In the past
        pass
    profile.save()
    user.profile = profile
    return user


@pytest.fixture
def admin_user(db) -> User:
    """Creates an admin user instance with is_staff=True, is_superuser=True, and a known password."""
    admin_password = "testadminpassword123"  # Make slightly more complex
    user = UserFactory(make_admin=True, username="admin_user", password=admin_password)
    # Profile role set via factory post-generation hook
    user._test_admin_password = (
        admin_password  # Attach password for admin_client fixture
    )
    return user


@pytest.fixture
def referrer_user(db) -> User:
    """Creates a standard user who can act as a referrer (has a profile and referral code)."""
    user = UserFactory(username="referrer_user")
    UserProfile.objects.get_or_create(
        user=user
    )  # Ensure profile and referral code exist
    # Ensure referral code is generated
    user.profile.save()
    user.refresh_from_db()  # Reload profile with code
    assert user.profile.referral_code is not None
    return user


# --- API Client Fixtures ---


@pytest.fixture
def subscribed_client(api_client: APIClient, subscribed_user: User) -> APIClient:
    """Provides an API client authenticated as a subscribed user via token."""
    api_client.force_authenticate(user=subscribed_user)
    api_client.user = subscribed_user  # Attach user for convenience in tests
    yield api_client
    api_client.force_authenticate(user=None)  # Clean up authentication


@pytest.fixture
def authenticated_client(api_client: APIClient, unsubscribed_user: User) -> APIClient:
    """Provides an API client authenticated as a standard, UNSUBSCRIBED user via token."""
    api_client.force_authenticate(user=unsubscribed_user)
    api_client.user = unsubscribed_user
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def admin_client(db, api_client: APIClient, admin_user: User) -> APIClient:
    """Provides an API client authenticated as an admin user via Django session (for Admin site tests)."""
    login_successful = api_client.login(
        username=admin_user.username,
        password=admin_user._test_admin_password,
    )
    assert (
        login_successful
    ), f"Admin client login failed for user '{admin_user.username}'"
    api_client.user = admin_user
    yield api_client
    api_client.logout()


# --- Serial Code Fixtures ---


@pytest.fixture
def active_serial_code(db) -> SerialCode:
    """Provides an active, unused SerialCode instance."""
    return SerialCodeFactory(is_active=True, is_used=False, duration_days=30)


@pytest.fixture
def used_serial_code(db, standard_user: User) -> SerialCode:
    """Provides a used SerialCode instance linked to a user."""
    return SerialCodeFactory(
        is_active=True,  # Can be active but still used
        is_used=True,
        used_by=standard_user,
        used_at=timezone.now() - timedelta(days=10),  # Used some time ago
    )


@pytest.fixture
def inactive_serial_code(db) -> SerialCode:
    """Provides an inactive, unused SerialCode instance."""
    return SerialCodeFactory(is_active=False, is_used=False)
