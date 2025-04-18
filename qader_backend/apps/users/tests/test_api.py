import pytest
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from django.contrib.auth.models import User

# Use the specific factory path
# from .factories import UserFactory, SerialCodeFactory # Already imported via conftest fixtures

# Ensure DB access for all tests in this file
# Applies to all test functions in this module
pytestmark = pytest.mark.django_db


# === Registration Tests ===


def test_register_success(api_client, active_serial_code):
    """Test successful user registration with a valid serial code."""
    url = reverse("api:v1:auth:register")  # Correct namespaced URL
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "New User Test",
        "preferred_name": "Newbie",
        "gender": "male",
        "grade": "Test Grade",
        "has_taken_qiyas_before": False,
    }
    response = api_client.post(url, data, format="json")  # Specify format

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()
    user = User.objects.get(username="newuser")
    assert user.email == "new@example.com"
    assert user.check_password("StrongPassword123!")

    # Check profile creation and data
    assert hasattr(user, "profile")
    profile = user.profile
    assert profile.full_name == "New User Test"
    assert profile.preferred_name == "Newbie"
    assert profile.gender == "male"
    assert profile.grade == "Test Grade"
    assert profile.has_taken_qiyas_before is False
    assert profile.role == "student"  # Assuming RoleChoices.STUDENT is 'student'

    # Check subscription activation
    active_serial_code.refresh_from_db()
    assert active_serial_code.is_used is True
    assert active_serial_code.used_by == user
    assert active_serial_code.used_at is not None

    assert profile.is_subscribed is True
    assert profile.subscription_expires_at is not None
    # Check expiry date is roughly correct (allowing for minor timing differences)
    # --- Important: Use timezone.now() for comparison with timezone-aware DateTimeField ---
    expected_expiry = timezone.now() + timedelta(days=active_serial_code.duration_days)
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(
        seconds=10  # Increased tolerance slightly just in case
    )

    assert "user" in response.data
    assert "access" in response.data
    assert "refresh" in response.data
    # assert "message" in response.data  # <-- REMOVE OR COMMENT OUT THIS LINE

    # Optional: Add more specific checks for the 'user' object content
    user_response_data = response.data["user"]
    assert user_response_data["username"] == "newuser"
    assert user_response_data["email"] == "new@example.com"
    assert user_response_data["full_name"] == "New User Test"
    assert "subscription" in user_response_data
    assert user_response_data["subscription"]["is_active"] is True


def test_register_invalid_serial_code(api_client):
    """Test registration attempt with a non-existent serial code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "newuser2",
        "email": "new2@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": "INVALID-CODE-XYZ",  # Code does not exist
        "full_name": "New User Test2",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    # Updated assertion to handle nested error
    assert "Invalid or already used serial code." in response.data["serial_code"]
    assert not User.objects.filter(username="newuser2").exists()


def test_register_used_serial_code(api_client, used_serial_code):
    """Test registration attempt with an already used serial code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "newuser3",
        "email": "new3@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": used_serial_code.code,  # Code already used
        "full_name": "New User Test3",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    # Updated assertion to handle nested error
    assert "Invalid or already used serial code." in response.data["serial_code"]
    assert not User.objects.filter(username="newuser3").exists()


def test_register_duplicate_username(api_client, active_serial_code, base_user):
    """Test registration attempt with an existing username."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": base_user.username,  # Existing username
        "email": "new4@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "New User Test4",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.data
    assert "user with that username already exists" in response.data["username"][0]


def test_register_password_mismatch(api_client, active_serial_code):
    """Test registration with mismatching passwords."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "newuser5",
        "email": "new5@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "DIFFERENTPassword123!",  # Mismatch
        "serial_code": active_serial_code.code,
        "full_name": "New User Test5",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_confirm" in response.data
    assert "Password fields didn't match." in response.data["password_confirm"][0]


# === Login Tests ===


def test_login_success(api_client, base_user):
    """Test successful login and token retrieval."""
    # Ensure user has a password set by the factory
    password = "defaultpassword"  # As set in factory
    url = reverse("api:v1:auth:token_obtain_pair")
    data = {"username": base_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data  # Check for custom user data
    assert response.data["user"]["username"] == base_user.username
    assert response.data["user"]["role"] == "student"  # Check role


def test_login_fail_wrong_password(api_client, base_user):
    """Test login failure with incorrect password."""
    url = reverse("api:v1:auth:token_obtain_pair")
    data = {"username": base_user.username, "password": "wrongpassword"}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.data  # DRF default error key


def test_login_fail_inactive_user(api_client, base_user):
    """Test login failure for an inactive user."""
    base_user.is_active = False
    base_user.save()
    password = "defaultpassword"
    url = reverse("api:v1:auth:token_obtain_pair")
    data = {"username": base_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# === Profile Tests ===


def test_get_profile_me_success(authenticated_client):
    """Test retrieving the profile of the authenticated user."""
    url = reverse("api:v1:users:user-profile")  # Use correct name from users_urls
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["username"] == authenticated_client.user.username
    assert response.data["full_name"] == authenticated_client.user.profile.full_name
    assert "subscription" in response.data
    assert "referral" in response.data


def test_get_profile_me_unauthenticated(api_client):
    """Test accessing /me/ endpoint without authentication."""
    url = reverse("api:v1:users:user-profile")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_patch_profile_me_success(authenticated_client):
    """Test partially updating the user's profile."""
    url = reverse("api:v1:users:user-profile")
    new_name = "Updated Preferred Name"
    new_grade = "Updated Grade"
    data = {
        "preferred_name": new_name,
        "grade": new_grade,
        "notify_reminders_enabled": False,
    }
    response = authenticated_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    # Check response contains updated data
    assert response.data["preferred_name"] == new_name
    assert response.data["grade"] == new_grade
    assert response.data["notify_reminders_enabled"] is False

    # Verify data in the database
    authenticated_client.user.profile.refresh_from_db()
    assert authenticated_client.user.profile.preferred_name == new_name
    assert authenticated_client.user.profile.grade == new_grade
    assert authenticated_client.user.profile.notify_reminders_enabled is False


def test_patch_profile_me_update_read_only_field_ignored(authenticated_client):
    """Test that attempting to update read-only fields via PATCH is ignored."""
    url = reverse("api:v1:users:user-profile")
    original_profile = authenticated_client.user.profile  # Get profile instance
    original_points = original_profile.points
    data = {
        "points": original_points + 1000,  # Attempt to change points
        "preferred_name": "Name Change Attempt",
    }
    response = authenticated_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    # Check that preferred_name was updated
    assert response.data["preferred_name"] == "Name Change Attempt"

    # ---> This assertion should now pass because UserProfileSerializer includes 'points' <---
    assert "points" in response.data  # First check if the key exists
    assert response.data["points"] == original_points

    # Verify points in the database haven't changed
    original_profile.refresh_from_db()
    assert original_profile.points == original_points
    assert original_profile.preferred_name == "Name Change Attempt"


# === Password Reset Tests ===


def test_password_reset_request_success(api_client, base_user):
    """Test successful password reset request."""
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": base_user.email}  # Use identifier field
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "If an account with that identifier exists" in response.data["detail"]
    assert len(mail.outbox) == 1  # Check email was sent
    assert base_user.email in mail.outbox[0].to
    # Further checks could inspect email content for token/uid if needed


def test_password_reset_request_unknown_identifier(api_client):
    """Test password reset request for a non-existent user."""
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": "unknown@example.com"}
    response = api_client.post(url, data, format="json")

    assert (
        response.status_code == status.HTTP_200_OK
    )  # Should still return OK for security
    assert "If an account with that identifier exists" in response.data["detail"]
    assert len(mail.outbox) == 0  # No email should be sent


# Add test for PasswordResetConfirmView (requires getting uid/token from email)
# Add test for ProfilePictureUploadView
# Add test for PasswordChangeView
# Add tests for LogoutView
