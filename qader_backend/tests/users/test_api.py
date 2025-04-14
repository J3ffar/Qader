from datetime import timezone
import pytest
from django.urls import reverse
from django.core import mail
from rest_framework import status
from django.contrib.auth.models import User
from .factories import UserFactory, SerialCodeFactory

pytestmark = pytest.mark.django_db  # Ensure DB access for all tests in this file


# === Registration Tests ===
def test_register_success(api_client):
    serial_code = SerialCodeFactory(is_active=True, is_used=False, duration_days=30)
    url = reverse("api:v1:auth:register")  # Use namespaced URL
    data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": serial_code.code,
        "full_name": "New User Test",
    }
    response = api_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()
    user = User.objects.get(username="newuser")
    assert user.profile.full_name == "New User Test"
    # Check subscription
    serial_code.refresh_from_db()
    assert serial_code.is_used is True
    assert serial_code.used_by == user
    assert user.profile.is_subscribed is True
    assert user.profile.subscription_expires_at is not None


def test_register_invalid_serial_code(api_client):
    url = reverse("api:v1:auth:register")
    data = {
        "username": "newuser2",
        "email": "new2@example.com",
        "password": "StrongPassword123!",
        "password_confirm": "StrongPassword123!",
        "serial_code": "INVALID-CODE",
        "full_name": "New User Test2",
    }
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "serial_code" in response.data


# ... other registration failure tests (duplicate user, password mismatch) ...


# === Login Tests ===
def test_login_success(api_client):
    user = UserFactory(password="loginpass")
    url = reverse("api:v1:auth:token_obtain_pair")
    data = {"username": user.username, "password": "loginpass"}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_fail(api_client):
    UserFactory(username="loginuser", password="loginpass")
    url = reverse("api:v1:auth:token_obtain_pair")
    data = {"username": "loginuser", "password": "wrongpassword"}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# === Profile Tests ===
def test_get_profile_me_success(authenticated_client):
    url = reverse("api:v1:users:user_profile")
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["username"] == authenticated_client.user.username


def test_get_profile_me_unauthenticated(api_client):
    url = reverse("api:v1:users:user_profile")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_patch_profile_me_success(authenticated_client):
    url = reverse("api:v1:users:user_profile")
    new_name = "Updated Name"
    data = {"preferred_name": new_name}
    response = authenticated_client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["preferred_name"] == new_name
    authenticated_client.user.profile.refresh_from_db()
    assert authenticated_client.user.profile.preferred_name == new_name


# === Password Reset Tests ===
def test_password_reset_request_success(api_client):
    user = UserFactory()
    url = reverse("api:v1:auth:password_reset_request")
    data = {"email": user.email}
    response = api_client.post(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert len(mail.outbox) == 1  # Check email was sent
    assert user.email in mail.outbox[0].to
