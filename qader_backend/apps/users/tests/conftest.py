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


# --- User Fixtures ---


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
def confirmation_link_data(inactive_user):
    """Generates uidb64 and token for email confirmation."""
    token = default_token_generator.make_token(inactive_user)
    uidb64 = urlsafe_base64_encode(force_bytes(inactive_user.pk))
    return {"uidb64": uidb64, "token": token, "user": inactive_user}
