import io
from django.conf import settings
import pytest
from django.urls import reverse
from django.core import mail
from django.utils import timezone
from datetime import timedelta, date, time
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.files.uploadedfile import SimpleUploadedFile  # For file uploads
import json  # For checking JSON response structure
from rest_framework.test import APIClient
from PIL import Image
from apps.users.tests.factories import SerialCodeFactory

from ..models import (
    DarkModePrefChoices,
    UserProfile,
    SerialCode,
    RoleChoices,
)  # Import models

# from ..serializers import AuthUserResponseSerializer  # For checking response structure


# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# === Registration Tests ===


def test_register_success(api_client, active_serial_code):
    """Test successful user registration with valid data and serial code."""
    url = reverse("api:v1:auth:register")  # Corrected namespace referencing
    data = {
        "username": "testregister",
        "email": "register@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "Register Test User",
        "preferred_name": "Reg",
        "gender": "female",
        "grade": "Grade 11",
        "has_taken_qiyas_before": True,
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="testregister").exists()
    user = User.objects.get(username="testregister")
    assert user.email == "register@qader.test"
    assert user.check_password("ValidPassword123!")
    assert hasattr(user, "profile")

    profile = user.profile
    assert profile.full_name == "Register Test User"
    assert profile.preferred_name == "Reg"
    assert profile.gender == "female"
    assert profile.grade == "Grade 11"
    assert profile.has_taken_qiyas_before is True
    assert profile.role == RoleChoices.STUDENT
    assert profile.referral_code is not None  # Check referral code generation

    active_serial_code.refresh_from_db()
    assert active_serial_code.is_used is True
    assert active_serial_code.used_by == user
    assert active_serial_code.used_at is not None

    assert profile.is_subscribed is True
    expected_expiry = timezone.now() + timedelta(days=active_serial_code.duration_days)
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(
        seconds=10
    )

    # Verify response structure matches AuthUserResponseSerializer
    assert "user" in response.data
    assert "access" in response.data
    assert "refresh" in response.data
    user_data = response.data["user"]
    assert user_data["username"] == "testregister"
    assert user_data["role"] == RoleChoices.STUDENT
    assert "subscription" in user_data
    assert user_data["subscription"]["is_active"] is True
    assert user_data["subscription"]["serial_code"] == active_serial_code.code


def test_register_success_with_referral(api_client, active_serial_code, referrer_user):
    """Test registration with a valid referral code applies referral."""
    url = reverse("api:v1:auth:register")
    referrer_profile = referrer_user.profile
    original_referrer_expiry = (
        referrer_profile.subscription_expires_at
    )  # Store initial state

    data = {
        "username": "referreduser",
        "email": "referred@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "Referred User",
        "referral_code_used": referrer_profile.referral_code,  # Use referrer's code
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="referreduser").exists()
    new_user = User.objects.get(username="referreduser")
    new_profile = new_user.profile

    assert new_profile.referred_by == referrer_user  # Check referral link

    # Check if referrer's subscription was extended (example: 3 days)
    referrer_profile.refresh_from_db()
    expected_bonus_days = 3  # Define bonus logic
    expected_new_expiry = (original_referrer_expiry or timezone.now()) + timedelta(
        days=expected_bonus_days
    )
    if referrer_profile.subscription_expires_at:  # Only check if expiry is set
        assert abs(
            referrer_profile.subscription_expires_at - expected_new_expiry
        ) < timedelta(seconds=10)


def test_register_fail_invalid_referral_code(api_client, active_serial_code):
    """Test registration fails with an invalid referral code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "badreferraluser",
        "email": "badref@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "Bad Referral",
        "referral_code_used": "NONEXISTENT-CODE",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "referral_code_used" in response.data
    assert "Invalid referral code provided." in response.data["referral_code_used"]
    assert not User.objects.filter(username="badreferraluser").exists()


def test_register_fail_invalid_serial_code(api_client):
    """Test registration fails with a non-existent serial code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "testregister_invalid_sc",
        "email": "inv_sc@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": "FAKE-SERIAL-CODE",
        "full_name": "Invalid SC User",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    assert (
        "Invalid or already used serial code." in response.data["serial_code"]
    )  # Check specific message
    assert not User.objects.filter(username="testregister_invalid_sc").exists()


def test_register_fail_used_serial_code(api_client, used_serial_code):
    """Test registration fails with an already used serial code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "testregister_used_sc",
        "email": "used_sc@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": used_serial_code.code,  # Use the fixture for used code
        "full_name": "Used SC User",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    assert "Invalid or already used serial code." in response.data["serial_code"]
    assert not User.objects.filter(username="testregister_used_sc").exists()


def test_register_fail_inactive_serial_code(api_client, inactive_serial_code):
    """Test registration fails with an inactive serial code."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "testregister_inactive_sc",
        "email": "inactive_sc@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": inactive_serial_code.code,
        "full_name": "Inactive SC User",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    assert "Invalid or already used serial code." in response.data["serial_code"]
    assert not User.objects.filter(username="testregister_inactive_sc").exists()


def test_register_fail_duplicate_username(
    api_client, active_serial_code, standard_user
):
    """Test registration fails with an existing username."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": standard_user.username,  # Existing username
        "email": "dup_user@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "Duplicate User",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "username" in response.data
    assert "user with that username already exists" in response.data["username"][0]


def test_register_fail_duplicate_email(api_client, active_serial_code, standard_user):
    """Test registration fails with an existing email."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "unique_username_dup_email",
        "email": standard_user.email,  # Existing email
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
        "serial_code": active_serial_code.code,
        "full_name": "Duplicate Email",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    assert "user with that email already exists" in response.data["email"][0]


def test_register_fail_password_mismatch(api_client, active_serial_code):
    """Test registration fails if password and confirmation don't match."""
    url = reverse("api:v1:auth:register")
    data = {
        "username": "testregister_pw_mismatch",
        "email": "pw_mismatch@qader.test",
        "password": "ValidPassword123!",
        "password_confirm": "DifferentPassword!",  # Mismatch
        "serial_code": active_serial_code.code,
        "full_name": "Mismatch User",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_confirm" in response.data
    assert "Password fields didn't match." in response.data["password_confirm"]


# === Login Tests ===


def test_login_success(api_client, standard_user):
    """Test successful login returns tokens and user data."""
    password = "defaultpassword"  # From UserFactory default
    url = reverse("api:v1:auth:login")  # Correct name
    data = {"username": standard_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data
    user_data = response.data["user"]
    assert user_data["id"] == standard_user.id
    assert user_data["username"] == standard_user.username
    assert user_data["role"] == standard_user.profile.role
    assert "subscription" in user_data


def test_login_fail_wrong_password(api_client, standard_user):
    """Test login fails with an incorrect password."""
    url = reverse("api:v1:auth:login")
    data = {"username": standard_user.username, "password": "IncorrectPassword!"}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.data  # Default DRF SimpleJWT error key
    assert "No active account found" in response.data["detail"]


def test_login_fail_inactive_user(api_client, standard_user):
    """Test login fails for a user marked as inactive."""
    standard_user.is_active = False
    standard_user.save()
    password = "defaultpassword"
    url = reverse("api:v1:auth:login")
    data = {"username": standard_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "No active account found" in response.data["detail"]


def test_login_fail_nonexistent_user(api_client):
    """Test login fails for a username that doesn't exist."""
    url = reverse("api:v1:auth:login")
    data = {"username": "nonexistentuser", "password": "anypassword"}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "No active account found" in response.data["detail"]


# === Logout Test ===


def test_logout_success(authenticated_client):
    """Test successful logout invalidates the refresh token."""
    # 1. Obtain tokens first (simulate login)
    user = authenticated_client.user
    password = "defaultpassword"
    login_url = reverse("api:v1:auth:login")
    login_data = {"username": user.username, "password": password}
    login_response = authenticated_client.post(login_url, login_data, format="json")
    assert login_response.status_code == status.HTTP_200_OK
    refresh_token = login_response.data.get("refresh")
    access_token = login_response.data.get("access")
    assert refresh_token
    assert access_token

    # 2. Use the refresh token to logout
    logout_url = reverse("api:v1:auth:logout")
    logout_data = {"refresh": refresh_token}
    # Ensure the client is still authenticated for the logout request itself
    authenticated_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = authenticated_client.post(logout_url, logout_data, format="json")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # 3. Verify the refresh token is blacklisted (attempt to refresh)
    refresh_url = reverse("api:v1:auth:token_refresh")
    refresh_data = {"refresh": refresh_token}
    # Use a basic client for the refresh attempt
    basic_client = APIClient()
    refresh_response = basic_client.post(refresh_url, refresh_data, format="json")
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token is blacklisted" in refresh_response.data.get("detail", "")


def test_logout_fail_no_token(authenticated_client):
    """Test logout fails if refresh token is not provided."""
    logout_url = reverse("api:v1:auth:logout")
    response = authenticated_client.post(logout_url, {}, format="json")  # Empty data
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Refresh token is required" in response.data.get("detail", "")


def test_logout_fail_invalid_token(authenticated_client):
    """Test logout fails if an invalid refresh token is provided."""
    logout_url = reverse("api:v1:auth:logout")
    response = authenticated_client.post(
        logout_url, {"refresh": "invalid.token.string"}, format="json"
    )
    assert (
        response.status_code == status.HTTP_400_BAD_REQUEST
    )  # simplejwt returns 400 for bad format
    assert "Invalid refresh token" in response.data.get(
        "detail", ""
    )  # Or similar error


def test_logout_fail_unauthenticated(api_client):
    """Test logout endpoint requires authentication."""
    logout_url = reverse("api:v1:auth:logout")
    response = api_client.post(logout_url, {"refresh": "some_token"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# === Profile Tests ===


def test_get_profile_me_success(subscribed_client):  # Use subscribed client for variety
    """Test retrieving the profile of the authenticated user successfully."""
    url = reverse("api:v1:users:me_profile")  # Correct namespaced name
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    # Check structure based on UserProfileSerializer
    assert "user" in response.data
    assert response.data["user"]["username"] == subscribed_client.user.username
    assert response.data["full_name"] == subscribed_client.user.profile.full_name
    assert "subscription" in response.data
    assert response.data["subscription"]["is_active"] is True
    assert "referral" in response.data
    assert "points" in response.data


def test_get_profile_me_unauthenticated(api_client):
    """Test accessing /me/ endpoint fails without authentication."""
    url = reverse("api:v1:users:me_profile")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_patch_profile_me_success(authenticated_client):
    """Test partially updating the user's profile data via PATCH."""
    url = reverse("api:v1:users:me_profile")
    profile = authenticated_client.user.profile
    original_full_name = profile.full_name

    new_preferred_name = "Patch Test Name"
    new_grade = "Grade Patch"
    new_dark_mode = DarkModePrefChoices.DARK
    new_reminder_time = time(19, 30)

    data = {
        "preferred_name": new_preferred_name,
        "grade": new_grade,
        "dark_mode_preference": new_dark_mode,
        "study_reminder_time": new_reminder_time.strftime("%H:%M:%S"),  # Format time
    }
    response = authenticated_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    # Check response contains updated data
    assert response.data["preferred_name"] == new_preferred_name
    assert response.data["grade"] == new_grade
    assert response.data["dark_mode_preference"] == new_dark_mode
    assert response.data["study_reminder_time"] == new_reminder_time.strftime(
        "%H:%M:%S"
    )
    assert response.data["full_name"] == original_full_name  # Check unchanged field

    # Verify data in the database
    profile.refresh_from_db()
    assert profile.preferred_name == new_preferred_name
    assert profile.grade == new_grade
    assert profile.dark_mode_preference == new_dark_mode
    assert profile.study_reminder_time == new_reminder_time
    assert profile.full_name == original_full_name


def test_patch_profile_me_profile_picture_upload(authenticated_client):
    """Test updating the profile picture via PATCH."""
    url = reverse("api:v1:users:me_profile")
    profile = authenticated_client.user.profile
    # Ensure initial state is no picture
    profile.profile_picture.delete()  # Clean up any potential factory remnants
    profile.refresh_from_db()
    assert not profile.profile_picture  # Use `not` for standard check

    # Create a small, valid image file using Pillow
    # This is more robust than arbitrary bytes
    image_file = io.BytesIO()
    image = Image.new("RGB", (1, 1), color="red")
    image.save(image_file, "PNG")
    image_file.seek(0)  # Important: Rewind the file pointer

    dummy_image = SimpleUploadedFile(
        "test_avatar.png", image_file.read(), content_type="image/png"
    )
    data = {"profile_picture": dummy_image}

    # Use multipart format for file upload
    response = authenticated_client.patch(url, data, format="multipart")

    assert response.status_code == status.HTTP_200_OK
    assert "profile_picture_url" in response.data
    assert response.data["profile_picture_url"] is not None
    # Check if filename part is in URL (or verify it's not None)
    assert "test_avatar" in response.data[
        "profile_picture_url"
    ] or "test_avatar" in str(
        profile.profile_picture.name
    )  # Add check for .name too

    # Verify in DB
    profile.refresh_from_db()
    assert profile.profile_picture is not None
    assert "test_avatar" in profile.profile_picture.name

    # Test deleting the picture - Use JSON format for nullifying the field
    data_delete = {"profile_picture": None}
    response_delete = authenticated_client.patch(
        url, data_delete, format="json"  # *** CHANGE format to "json" ***
    )
    assert response_delete.status_code == status.HTTP_200_OK
    assert response_delete.data["profile_picture_url"] is None

    profile.refresh_from_db()
    assert not profile.profile_picture


def test_patch_profile_me_fail_invalid_choice(authenticated_client):
    """Test PATCH fails if an invalid choice is provided for a choice field."""
    url = reverse("api:v1:users:me_profile")
    data = {"gender": "invalid_gender_choice"}
    response = authenticated_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "gender" in response.data
    assert '"invalid_gender_choice" is not a valid choice' in response.data["gender"][0]


# === Password Change Tests ===


def test_password_change_success(authenticated_client):
    """Test successfully changing the password for the authenticated user."""
    url = reverse("api:v1:users:me_change_password")
    user = authenticated_client.user
    old_password = "defaultpassword"
    new_password = "NewSecurePassword123!"
    data = {
        "current_password": old_password,
        "new_password": new_password,
        "new_password_confirm": new_password,
    }
    response = authenticated_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "Password updated successfully" in response.data["detail"]

    # Verify the new password works for login
    user.refresh_from_db()
    assert user.check_password(new_password) is True
    assert user.check_password(old_password) is False


def test_password_change_fail_wrong_current_password(authenticated_client):
    """Test password change fails with incorrect current password."""
    url = reverse("api:v1:users:me_change_password")
    new_password = "NewSecurePassword123!"
    data = {
        "current_password": "WrongCurrentPassword",
        "new_password": new_password,
        "new_password_confirm": new_password,
    }
    response = authenticated_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "current_password" in response.data
    assert "Incorrect current password" in response.data["current_password"][0]


def test_password_change_fail_mismatch_new_password(authenticated_client):
    """Test password change fails when new passwords don't match."""
    url = reverse("api:v1:users:me_change_password")
    data = {
        "current_password": "defaultpassword",
        "new_password": "NewSecurePassword123!",
        "new_password_confirm": "DifferentPasswordConfirm!",
    }
    response = authenticated_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password_confirm" in response.data
    assert (
        "New password fields didn't match" in response.data["new_password_confirm"][0]
    )


def test_password_change_fail_new_same_as_old(authenticated_client):
    """Test password change fails if the new password is the same as the old one."""
    url = reverse("api:v1:users:me_change_password")
    old_password = "defaultpassword"
    data = {
        "current_password": old_password,
        "new_password": old_password,  # Same as current
        "new_password_confirm": old_password,
    }
    response = authenticated_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password" in response.data
    assert (
        "New password cannot be the same as the current password"
        in response.data["new_password"][0]
    )


# === Password Reset Tests ===


def test_password_reset_request_success_email(api_client, standard_user):
    """Test successful password reset request using email identifier."""
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": standard_user.email}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert (
        "If an active account with that identifier exists" in response.data["detail"]
    )  # Check for the correct message
    assert len(mail.outbox) == 1
    email_msg = mail.outbox[0]
    assert standard_user.email in email_msg.to
    assert "Password Reset for Qader Platform" in email_msg.subject


def test_password_reset_request_success_username(api_client, standard_user):
    """Test successful password reset request using username identifier."""
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": standard_user.username}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "If an active account with that identifier exists" in response.data["detail"]
    assert len(mail.outbox) == 1


def test_password_reset_request_unknown_identifier(api_client):
    """Test password reset request for an identifier that doesn't exist."""
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": "nobody@nowhere.test"}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK  # Still OK for security
    assert "If an active account" in response.data["detail"]
    assert len(mail.outbox) == 0  # No email sent


def test_password_reset_request_inactive_user(api_client, standard_user):
    """Test password reset request for an inactive user identifier."""
    standard_user.is_active = False
    standard_user.save()
    url = reverse("api:v1:auth:password_reset_request")
    data = {"identifier": standard_user.email}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK  # Still OK
    assert "If an active account" in response.data["detail"]
    assert len(mail.outbox) == 0  # No email sent for inactive user


def test_password_reset_confirm_success(api_client, standard_user):
    """Test successfully confirming password reset with valid uid/token."""
    # 1. Generate token and uid like the request view does
    token = default_token_generator.make_token(standard_user)
    uidb64 = urlsafe_base64_encode(force_bytes(standard_user.pk))
    new_password = "ResetPasswordSuccessfully123!"

    # 2. Call the confirm endpoint
    url = reverse("api:v1:auth:password_reset_confirm")
    data = {
        "uidb64": uidb64,
        "token": token,
        "new_password": new_password,
        "new_password_confirm": new_password,
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "Password has been reset successfully" in response.data["detail"]

    # 3. Verify the password was actually changed
    standard_user.refresh_from_db()
    assert standard_user.check_password(new_password) is True


def test_password_reset_confirm_fail_invalid_token(api_client, standard_user):
    """Test password reset confirmation fails with an invalid token."""
    uidb64 = urlsafe_base64_encode(force_bytes(standard_user.pk))
    invalid_token = "invalid-token-string"
    new_password = "ResetPasswordFail123!"

    url = reverse("api:v1:auth:password_reset_confirm")
    data = {
        "uidb64": uidb64,
        "token": invalid_token,
        "new_password": new_password,
        "new_password_confirm": new_password,
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired password reset link" in response.data["detail"]


def test_password_reset_confirm_fail_invalid_uid(api_client, standard_user):
    """Test password reset confirmation fails with an invalid uidb64."""
    token = default_token_generator.make_token(standard_user)
    invalid_uidb64 = "invalidbase64string"
    new_password = "ResetPasswordFail123!"

    url = reverse("api:v1:auth:password_reset_confirm")
    data = {
        "uidb64": invalid_uidb64,
        "token": token,
        "new_password": new_password,
        "new_password_confirm": new_password,
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired password reset link" in response.data["detail"]


def test_password_reset_confirm_fail_password_mismatch(api_client, standard_user):
    """Test password reset confirmation fails if new passwords don't match."""
    token = default_token_generator.make_token(standard_user)
    uidb64 = urlsafe_base64_encode(force_bytes(standard_user.pk))

    url = reverse("api:v1:auth:password_reset_confirm")
    data = {
        "uidb64": uidb64,
        "token": token,
        "new_password": "ResetPasswordMismatch1!",
        "new_password_confirm": "ResetPasswordMismatch2!",  # Different
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "new_password_confirm" in response.data
    assert (
        "New password fields didn't match" in response.data["new_password_confirm"][0]
    )


# === Apply Serial Code Tests ===


def test_apply_serial_code_success(subscribed_client, active_serial_code):
    """Test applying a new valid code successfully updates expiry."""
    profile = subscribed_client.user.profile
    original_expiry = profile.subscription_expires_at
    new_code = SerialCodeFactory(
        is_active=True, is_used=False, duration_days=15
    )  # Different code
    url = reverse("api:v1:users:me_apply_serial_code")
    data = {"serial_code": new_code.code}

    response = subscribed_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "subscription" in response.data
    assert response.data["subscription"]["is_active"] is True
    assert response.data["subscription"]["serial_code"] == new_code.code

    profile.refresh_from_db()
    new_code.refresh_from_db()
    assert new_code.is_used is True
    assert new_code.used_by == subscribed_client.user
    assert profile.serial_code_used == new_code
    expected_expiry = (original_expiry or timezone.now()) + timedelta(
        days=15
    )  # Check extension logic
    assert profile.subscription_expires_at == pytest.approx(
        expected_expiry, abs=timedelta(seconds=5)
    )


def test_apply_serial_code_fail_invalid(
    authenticated_client,
):  # Use any authenticated client
    """Test applying a non-existent code fails."""
    url = reverse("api:v1:users:me_apply_serial_code")
    data = {"serial_code": "INVALID-NONEXISTENT-CODE"}
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    assert "Invalid or already used serial code." in response.data["serial_code"]


# ... add tests for used, inactive, unauthenticated cases ...


# === Subscription Plan List Tests ===


def test_list_subscription_plans_success(
    api_client,
):  # Use unauthenticated client as it's AllowAny
    """Test retrieving the list of subscription plans."""
    url = reverse("api:v1:users:subscription_plans_list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data, list)
    assert len(response.data) > 0  # Check it's not empty
    # Check structure of the first plan
    assert "id" in response.data[0]
    assert "name" in response.data[0]
    assert "duration_days" in response.data[0]


# === Cancel Subscription Tests ===


def test_cancel_subscription_success(subscribed_client):
    """Test successfully cancelling an active subscription."""
    profile = subscribed_client.user.profile
    assert profile.is_subscribed is True  # Pre-condition

    url = reverse("api:v1:users:me_cancel_subscription")
    response = subscribed_client.post(url, {}, format="json")  # No body needed

    assert response.status_code == status.HTTP_200_OK
    assert "Subscription cancelled successfully" in response.data["detail"]
    assert "subscription" in response.data
    assert response.data["subscription"]["is_active"] is False
    assert response.data["subscription"]["expires_at"] is None

    profile.refresh_from_db()
    assert profile.is_subscribed is False
    assert profile.subscription_expires_at is None
    assert profile.serial_code_used is None


def test_cancel_subscription_fail_not_subscribed(
    authenticated_client,
):  # Use unsubscribed client
    """Test cancelling fails if the user has no active subscription."""
    profile = authenticated_client.user.profile
    assert profile.is_subscribed is False  # Pre-condition

    url = reverse("api:v1:users:me_cancel_subscription")
    response = authenticated_client.post(url, {}, format="json")

    # Should be denied by permission
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "active subscription" in response.data["detail"]


def test_cancel_subscription_fail_unauthenticated(api_client):
    """Test cancelling requires authentication."""
    url = reverse("api:v1:users:me_cancel_subscription")
    response = api_client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
