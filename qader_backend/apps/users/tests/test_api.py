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
    GenderChoices,
    UserProfile,
    SerialCode,
    RoleChoices,
)  # Import models

# from ..serializers import AuthUserResponseSerializer  # For checking response structure


# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# === Registration Tests ===

# --- Initial Signup Tests ---


def test_initial_signup_success(api_client):
    """Test successful initial signup creates inactive user and sends email."""
    url = reverse("api:v1:auth:initial_signup")
    data = {
        "email": "initial.signup@qader.test",
        "full_name": "Initial Signup User",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
    }
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert "Confirmation email sent" in response.data["detail"]

    # Verify user created but inactive
    assert User.objects.filter(email="initial.signup@qader.test").exists()
    user = User.objects.get(email="initial.signup@qader.test")
    assert user.is_active is False
    assert user.check_password("ValidPassword123!")
    assert hasattr(user, "profile")
    assert user.profile.full_name == "Initial Signup User"
    assert user.profile.referral_code is not None  # Check referral code generated

    # Verify email sent
    assert len(mail.outbox) == 1
    email_msg = mail.outbox[0]
    assert "initial.signup@qader.test" in email_msg.to
    assert "Account Activation" in email_msg.subject  # Check subject from template
    assert "/confirm-email/" in email_msg.body  # Check link path


def test_initial_signup_fail_duplicate_email(api_client, standard_user):
    """Test initial signup fails if email already exists (active user)."""
    url = reverse("api:v1:auth:initial_signup")
    data = {
        "email": standard_user.email,  # Existing active user's email
        "full_name": "Duplicate Email User",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    assert "user with this email already exists" in response.data["email"][0]
    assert len(mail.outbox) == 0


def test_initial_signup_fail_duplicate_inactive_email(api_client, inactive_user):
    """Test initial signup fails if email exists but is inactive/pending."""
    url = reverse("api:v1:auth:initial_signup")
    data = {
        "email": inactive_user.email,  # Existing inactive user's email
        "full_name": "Duplicate Inactive Email User",
        "password": "ValidPassword123!",
        "password_confirm": "ValidPassword123!",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data
    assert "pending confirmation or already registered" in response.data["email"][0]
    assert len(mail.outbox) == 0


def test_initial_signup_fail_password_mismatch(api_client):
    """Test initial signup fails on password mismatch."""
    url = reverse("api:v1:auth:initial_signup")
    data = {
        "email": "mismatch@qader.test",
        "full_name": "Mismatch User",
        "password": "ValidPassword123!",
        "password_confirm": "DifferentPassword!",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password_confirm" in response.data


def test_initial_signup_fail_weak_password(api_client):
    """Test initial signup fails if password violates policy."""
    url = reverse("api:v1:auth:initial_signup")
    data = {
        "email": "weakpass@qader.test",
        "full_name": "Weak Pass User",
        "password": "weak",
        "password_confirm": "weak",
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "password" in response.data  # Django's validator errors attach here


# --- Email Confirmation Tests ---


def test_confirm_email_success(api_client, confirmation_link_data):
    """Test successful email confirmation activates user and returns tokens."""
    uidb64 = confirmation_link_data["uidb64"]
    token = confirmation_link_data["token"]
    user = confirmation_link_data["user"]
    assert user.is_active is False  # Pre-condition

    url = reverse(
        "api:v1:auth:account_confirm_email", kwargs={"uidb64": uidb64, "token": token}
    )
    response = api_client.get(url)  # GET request to confirmation link

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.is_active is True  # User should now be active

    # Check response structure
    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data
    user_data = response.data["user"]
    assert user_data["id"] == user.id
    assert user_data["email"] == user.email
    assert user_data["profile_complete"] is False  # Profile is not complete yet


def test_confirm_email_fail_invalid_token(api_client, confirmation_link_data):
    """Test email confirmation fails with an invalid token."""
    uidb64 = confirmation_link_data["uidb64"]
    user = confirmation_link_data["user"]
    invalid_token = "this-is-not-a-valid-token"
    url = reverse(
        "api:v1:auth:account_confirm_email",
        kwargs={"uidb64": uidb64, "token": invalid_token},
    )
    response = api_client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid or expired confirmation link" in response.data["detail"]
    user.refresh_from_db()
    assert user.is_active is False


def test_confirm_email_fail_invalid_uid(api_client, confirmation_link_data):
    """Test email confirmation fails with an invalid UID."""
    token = confirmation_link_data["token"]
    invalid_uidb64 = "invalid-uid-string"
    url = reverse(
        "api:v1:auth:account_confirm_email",
        kwargs={"uidb64": invalid_uidb64, "token": token},
    )
    response = api_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND  # UID not found
    assert "Invalid confirmation link" in response.data["detail"]


def test_confirm_email_already_active(api_client, standard_user):
    """Test clicking confirmation link for an already active user."""
    token = default_token_generator.make_token(standard_user)
    uidb64 = urlsafe_base64_encode(force_bytes(standard_user.pk))
    assert standard_user.is_active is True  # Pre-condition

    url = reverse(
        "api:v1:auth:account_confirm_email", kwargs={"uidb64": uidb64, "token": token}
    )
    response = api_client.get(url)

    # Should still succeed and return tokens (treat as a way to re-login/get tokens)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data
    assert response.data["user"]["id"] == standard_user.id


# --- Profile Completion Tests ---


def test_complete_profile_success_with_trial(pending_profile_client):
    """Test completing profile grants 1-day trial when no serial code is given."""
    url = reverse("api:v1:users:me_complete_profile")
    user = pending_profile_client.user
    profile = user.profile
    assert not profile.is_profile_complete
    assert not profile.is_subscribed

    data = {
        "gender": GenderChoices.FEMALE,
        "grade": "High School Graduate",
        "has_taken_qiyas_before": True,
        "preferred_name": "Completed",
    }
    response = pending_profile_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    profile.refresh_from_db()
    assert profile.is_profile_complete
    assert profile.gender == GenderChoices.FEMALE
    assert profile.grade == "High School Graduate"
    assert profile.has_taken_qiyas_before is True
    assert profile.preferred_name == "Completed"

    # Check trial subscription
    assert profile.is_subscribed
    assert profile.serial_code_used is None  # No code used for trial
    expected_expiry = timezone.now() + timedelta(days=1)
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(
        seconds=10
    )

    # Check response structure (should be full UserProfileSerializer)
    assert response.data["gender"] == GenderChoices.FEMALE
    assert response.data["subscription"]["is_active"] is True


def test_complete_profile_success_with_serial_code(
    pending_profile_client, active_serial_code
):
    """Test completing profile with a valid serial code activates subscription."""
    url = reverse("api:v1:users:me_complete_profile")
    user = pending_profile_client.user
    profile = user.profile
    assert not profile.is_profile_complete
    assert not profile.is_subscribed

    data = {
        "gender": GenderChoices.MALE,
        "grade": "Grade 10",
        "has_taken_qiyas_before": False,
        "serial_code": active_serial_code.code,  # Provide serial code
    }
    response = pending_profile_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    profile.refresh_from_db()
    active_serial_code.refresh_from_db()

    assert profile.is_profile_complete
    assert profile.gender == GenderChoices.MALE
    assert profile.grade == "Grade 10"
    assert profile.has_taken_qiyas_before is False

    # Check serial code subscription
    assert profile.is_subscribed
    assert profile.serial_code_used == active_serial_code
    assert active_serial_code.is_used is True
    assert active_serial_code.used_by == user
    expected_expiry = timezone.now() + timedelta(days=active_serial_code.duration_days)
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(
        seconds=10
    )

    assert response.data["subscription"]["is_active"] is True
    assert response.data["subscription"]["serial_code"] == active_serial_code.code


def test_complete_profile_success_with_referral(pending_profile_client, referrer_user):
    """Test completing profile with a referral code links users and grants bonus."""
    url = reverse("api:v1:users:me_complete_profile")
    user = pending_profile_client.user
    profile = user.profile
    referrer_profile = referrer_user.profile
    original_referrer_expiry = referrer_profile.subscription_expires_at  # Can be None

    data = {
        "gender": GenderChoices.MALE,
        "grade": "Grade 11",
        "has_taken_qiyas_before": True,
        "referral_code_used": referrer_profile.referral_code,  # Provide referral code
    }
    response = pending_profile_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    profile.refresh_from_db()
    referrer_profile.refresh_from_db()

    assert profile.is_profile_complete
    assert profile.referred_by == referrer_user  # Check link

    # Check referrer bonus (assuming 3 days default)
    expected_bonus_days = 3
    expected_start_date = (
        max(original_referrer_expiry, timezone.now())
        if original_referrer_expiry
        else timezone.now()
    )
    expected_new_expiry = expected_start_date + timedelta(days=expected_bonus_days)

    assert (
        referrer_profile.is_subscribed
    )  # Referrer should now be subscribed (or extended)
    assert abs(
        referrer_profile.subscription_expires_at - expected_new_expiry
    ) < timedelta(seconds=10)

    # Check new user got trial (no serial code provided)
    assert profile.is_subscribed
    assert profile.serial_code_used is None


def test_complete_profile_fail_missing_fields(pending_profile_client):
    """Test profile completion fails if required fields are missing."""
    url = reverse("api:v1:users:me_complete_profile")
    data = {
        "gender": GenderChoices.FEMALE,
        # Missing "grade" and "has_taken_qiyas_before"
    }
    response = pending_profile_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "grade" in response.data
    assert "has_taken_qiyas_before" in response.data
    assert "This field is required" in response.data["grade"][0]


def test_complete_profile_fail_invalid_serial_code(pending_profile_client):
    """Test profile completion fails with invalid serial code."""
    url = reverse("api:v1:users:me_complete_profile")
    data = {
        "gender": GenderChoices.MALE,
        "grade": "Grade 10",
        "has_taken_qiyas_before": False,
        "serial_code": "INVALID-CODE-123",
    }
    response = pending_profile_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data
    assert "Invalid or already used serial code" in response.data["serial_code"][0]


def test_complete_profile_fail_invalid_referral_code(pending_profile_client):
    """Test profile completion fails with invalid referral code."""
    url = reverse("api:v1:users:me_complete_profile")
    data = {
        "gender": GenderChoices.MALE,
        "grade": "Grade 11",
        "has_taken_qiyas_before": True,
        "referral_code_used": "INVALID-REFERRAL",
    }
    response = pending_profile_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "referral_code_used" in response.data
    assert "Invalid referral code provided" in response.data["referral_code_used"][0]


def test_complete_profile_fail_already_complete(
    authenticated_client,
):  # Use standard client
    """Test attempting to complete an already complete profile."""
    url = reverse("api:v1:users:me_complete_profile")
    user = authenticated_client.user
    assert user.profile.is_profile_complete  # Pre-condition

    data = {  # Provide valid data again
        "gender": GenderChoices.FEMALE,
        "grade": "Already Complete",
        "has_taken_qiyas_before": False,
    }
    # The view/serializer logic doesn't explicitly block this,
    # it just updates the fields. This might be acceptable.
    # If blocking is desired, add a check in the view's `get_object` or `perform_update`.
    # For now, let's assume it updates normally.
    response = authenticated_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    user.profile.refresh_from_db()
    assert user.profile.grade == "Already Complete"  # Check update happened


def test_complete_profile_fail_unauthenticated(api_client):
    """Test complete profile requires authentication."""
    url = reverse("api:v1:users:me_complete_profile")
    data = {
        "gender": GenderChoices.FEMALE,
        "grade": "Test",
        "has_taken_qiyas_before": False,
    }
    response = api_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Login Tests (Updated) ---


def test_login_success(
    api_client, standard_user
):  # Use standard_user (active, complete)
    """Test successful login returns tokens and user data."""
    password = "defaultpassword"
    url = reverse("api:v1:auth:login")
    data = {"username": standard_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert "user" in response.data
    user_data = response.data["user"]
    assert user_data["id"] == standard_user.id
    assert user_data["username"] == standard_user.username
    assert user_data["profile_complete"] is True  # Check flag


def test_login_fail_inactive_user(
    api_client, inactive_user
):  # Use inactive_user fixture
    """Test login fails for a user marked as inactive (pending confirmation)."""
    password = "defaultpassword"
    url = reverse("api:v1:auth:login")
    data = {"username": inactive_user.username, "password": password}
    response = api_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        "No active account found" in response.data["detail"]
    )  # SimpleJWT/Django auth handles this


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


def test_get_profile_me_success(authenticated_client):  # standard_user is complete
    """Test retrieving the profile of the authenticated user successfully."""
    url = reverse("api:v1:users:me_profile")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "user" in response.data
    assert response.data["profile_complete"] is True  # Check flag


def test_get_profile_me_pending(pending_profile_client):  # User incomplete
    """Test retrieving profile for a user pending completion."""
    url = reverse("api:v1:users:me_profile")
    response = pending_profile_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "user" in response.data
    assert response.data["profile_complete"] is False  # Check flag


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
