import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta


# Use the specific factory path
from apps.users.tests.factories import UserFactory
from apps.users.models import (
    UserProfile,
    GenderChoices,
    RoleChoices,
)  # Direct import is fine here


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
def standard_user(db) -> User:  # Now represents a fully active, profile-complete user
    """Creates a standard, active, profile-complete user instance."""
    user = UserFactory(
        username="standarduser",
        email="standard@qader.test",
        is_active=True,
        profile_data={  # Add required profile fields
            "full_name": "Standard User",
            "gender": GenderChoices.MALE,
            "grade": "Grade 12",
            "has_taken_qiyas_before": False,
        },
    )
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.gender = GenderChoices.MALE  # Ensure fields are set
    profile.grade = "Grade 12"
    profile.has_taken_qiyas_before = False
    profile.save()
    user.refresh_from_db()
    assert user.profile.is_profile_complete  # Verify state
    return user


@pytest.fixture
def subscribed_user(db) -> User:
    """Creates a distinct, active, profile-complete user with an active subscription."""
    user = UserFactory(
        username="subscribed_user",
        email="subscribed@qader.test",
        is_active=True,
        profile_data={  # Add required profile fields
            "full_name": "Subscribed User",
            "gender": GenderChoices.FEMALE,
            "grade": "University",
            "has_taken_qiyas_before": True,
        },
    )
    profile, _ = UserProfile.objects.get_or_create(user=user)
    # Ensure profile is complete
    profile.gender = GenderChoices.FEMALE
    profile.grade = "University"
    profile.has_taken_qiyas_before = True
    # Set subscription
    profile.subscription_expires_at = timezone.now() + timedelta(days=30)
    profile.save()
    user.refresh_from_db()
    assert user.profile.is_profile_complete  # Verify state
    assert user.profile.is_subscribed  # Verify state
    return user


# Unsubscribed user is now effectively the same as standard_user unless explicitly given expired sub
@pytest.fixture
def unsubscribed_user(standard_user) -> User:
    """Alias for standard_user, representing an active, complete but unsubscribed user."""
    # Ensure subscription is not active (it shouldn't be by default for standard_user)
    profile = standard_user.profile
    if profile.is_subscribed:
        profile.subscription_expires_at = timezone.now() - timedelta(days=1)
        profile.save()
        standard_user.refresh_from_db()
    return standard_user


@pytest.fixture
def admin_user(db) -> User:
    """Creates an admin user instance."""
    user = UserFactory(make_admin=True, username="admin_user")
    # Profile role set via factory post-generation hook
    # Ensure admin profile is also considered complete for consistency
    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.is_profile_complete:
        profile.gender = GenderChoices.MALE  # Example completion data
        profile.grade = "N/A"
        profile.has_taken_qiyas_before = False
        profile.role = RoleChoices.ADMIN  # Ensure role is admin
        profile.save()
    user.refresh_from_db()
    return user


# --- API Client Fixtures ---


@pytest.fixture
def subscribed_client(api_client: APIClient, subscribed_user: User) -> APIClient:
    """Provides an API client authenticated as a subscribed user."""
    api_client.force_authenticate(user=subscribed_user)
    api_client.user = subscribed_user
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def authenticated_client(api_client: APIClient, unsubscribed_user: User) -> APIClient:
    """Provides an API client authenticated as a standard, unsubscribed user."""
    api_client.force_authenticate(user=unsubscribed_user)
    api_client.user = unsubscribed_user
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def admin_client(db, api_client: APIClient, admin_user: User) -> APIClient:
    """Provides an API client authenticated as an admin user via Django session."""
    default_password = "defaultpassword"
    login_successful = api_client.login(
        username=admin_user.username,
        password=default_password,  # Use the known default
    )
    assert (
        login_successful
    ), f"Admin client login failed for user '{admin_user.username}'"
    api_client.user = admin_user
    yield api_client
    api_client.logout()
