import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
import tempfile
import shutil
from django.conf import settings


# Use the specific factory path
from apps.users.tests.factories import SerialCodeFactory, UserFactory
from apps.users.models import (
    SerialCode,
    UserProfile,
    GenderChoices,
    RoleChoices,
)
from apps.chat.models import Conversation  # Direct import is fine here


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
def student_user(db, standard_user):  # Using standard_user as a base
    """Creates a user with the STUDENT role and a complete profile."""
    profile = standard_user.profile
    profile.role = RoleChoices.STUDENT
    # Ensure profile is complete if standard_user doesn't guarantee it for all fields
    if not profile.full_name:
        profile.full_name = "Student User"
    if not profile.gender:
        profile.gender = GenderChoices.MALE
    if not profile.grade:
        profile.grade = "Grade 10"
    if profile.has_taken_qiyas_before is None:
        profile.has_taken_qiyas_before = False
    profile.save()
    standard_user.refresh_from_db()
    return standard_user


@pytest.fixture
def teacher_user(db):
    """Creates a user with the TEACHER role and a complete profile."""
    user = UserFactory(
        username="teacher_chat",
        email="teacher_chat@qader.test",
        is_active=True,
        profile_data={
            "full_name": "Teacher Chat User",
            "gender": GenderChoices.MALE,
            "grade": "N/A",
            "has_taken_qiyas_before": False,
            "role": RoleChoices.TEACHER,  # Set role here
        },
    )
    user.refresh_from_db()
    return user


@pytest.fixture
def student_with_mentor(db, student_user, teacher_user):
    """A student user whose assigned_mentor is the teacher_user."""
    profile = student_user.profile
    profile.assigned_mentor = teacher_user.profile
    profile.save()
    student_user.refresh_from_db()
    return student_user


@pytest.fixture
def conversation_between_student_and_mentor(db, student_with_mentor, teacher_user):
    """Creates a conversation between the student_with_mentor and their teacher_user."""
    # The model's get_or_create_conversation should handle this correctly
    convo, _ = Conversation.get_or_create_conversation(
        student_profile=student_with_mentor.profile,
        teacher_profile=teacher_user.profile,
    )
    return convo


# API Client fixtures authenticated as specific roles for chat
@pytest.fixture
def student_client(api_client, student_user):
    api_client.force_authenticate(user=student_user)
    api_client.user = student_user  # Store user on client for easier access in tests
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def student_mentor_client(api_client, student_with_mentor):
    api_client.force_authenticate(user=student_with_mentor)
    api_client.user = student_with_mentor
    yield api_client
    api_client.force_authenticate(user=None)


@pytest.fixture
def teacher_client(api_client, teacher_user):
    api_client.force_authenticate(user=teacher_user)
    api_client.user = teacher_user
    yield api_client
    api_client.force_authenticate(user=None)
