import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta, date, time
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


# Use the specific factory path
from apps.users.tests.factories import UserFactory, SerialCodeFactory
from apps.users.models import (
    SerialCode,
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
def inactive_user(db) -> User:
    """Creates an inactive user instance (e.g., after initial signup)."""
    user = UserFactory(
        username="inactive_user",
        email="inactive@qader.test",
        is_active=False,  # Explicitly inactive
        profile_data={
            "full_name": "Inactive User Test"
        },  # Simulate initial signup data
    )
    # Signal should have created profile, this ensures it
    UserProfile.objects.get_or_create(user=user)
    user.refresh_from_db()  # Ensure relations are loaded
    return user


@pytest.fixture
def pending_profile_user(db) -> User:
    """Creates an active user who has confirmed email but not completed profile."""
    user = UserFactory(
        username="pending_profile_user",
        email="pending@qader.test",
        is_active=True,  # Activated via confirmation
        profile_data={
            "full_name": "Pending Profile User",
            # Ensure essential fields are missing
            "gender": None,
            "grade": None,
            "has_taken_qiyas_before": None,
        },
    )
    profile, _ = UserProfile.objects.get_or_create(user=user)
    # Clear fields that might be set by factory defaults if necessary
    profile.gender = None
    profile.grade = None
    profile.has_taken_qiyas_before = None
    profile.save()
    user.refresh_from_db()
    assert not user.profile.is_profile_complete  # Verify state
    return user


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


@pytest.fixture
def referrer_user(standard_user) -> User:
    """Alias for standard_user, ensuring they have a referral code."""
    # standard_user fixture already ensures profile + referral code exist
    return standard_user


# --- API Client Fixtures ---


@pytest.fixture
def pending_profile_client(
    api_client: APIClient, pending_profile_user: User
) -> APIClient:
    """Provides an API client authenticated as a user needing profile completion."""
    api_client.force_authenticate(user=pending_profile_user)
    api_client.user = pending_profile_user
    yield api_client
    api_client.force_authenticate(user=None)


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


@pytest.fixture
def confirmation_link_data(inactive_user):
    """Generates uidb64 and token for email confirmation."""
    token = default_token_generator.make_token(inactive_user)
    uidb64 = urlsafe_base64_encode(force_bytes(inactive_user.pk))
    return {"uidb64": uidb64, "token": token, "user": inactive_user}
