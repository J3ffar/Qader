import pytest
from unittest.mock import patch, MagicMock
from django.core import mail
from ..models import UserProfile
from .factories import UserFactory
from django.conf import settings

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from ..utils import (
    generate_unique_referral_code,
    send_confirmation_email,
    get_user_from_uidb64,
    send_password_reset_email,  # Keep if testing this too
)

pytestmark = pytest.mark.django_db


def test_generate_unique_referral_code_format():
    """Test the generated code format."""
    username = "TestUser_123"
    code = generate_unique_referral_code(username)
    assert isinstance(code, str)
    assert len(code) > 5  # Basic check
    # Check format: PREFIX-HEXPART
    parts = code.split("-")
    assert len(parts) == 2
    assert parts[0] == username[:6].upper().replace("_", "")  # Check prefix calculation
    assert len(parts[1]) == 6  # Hex part length
    assert all(c in "0123456789ABCDEF" for c in parts[1])  # Check hex characters


def test_generate_unique_referral_code_uniqueness():
    """Test that generated codes are unique, even with similar usernames."""
    user1 = UserFactory(username="similar_user_a")
    profile1 = user1.profile
    profile1.referral_code = generate_unique_referral_code(
        user1.username
    )  # Generate manually for test
    profile1.save()

    # Try generating for another user, ensuring it's different
    username2 = "similar_user_b"
    code2 = generate_unique_referral_code(username2)

    assert code2 != profile1.referral_code
    # Ensure it doesn't exist yet (though generate func checks internally)
    assert not UserProfile.objects.filter(referral_code=code2).exists()


def test_generate_unique_referral_code_handles_collisions():
    """Test that the function generates a new code if a collision occurs."""
    username = "collision_test"
    # Manually create a profile with a code that might collide
    colliding_code = f"{username[:6].upper()}-ABCDEF"  # Predictable potential collision
    existing_user = UserFactory()
    existing_profile = existing_user.profile
    existing_profile.referral_code = colliding_code
    existing_profile.save()

    # Generate code for the new username - should avoid the collision
    new_code = generate_unique_referral_code(username)

    assert new_code is not None
    assert new_code != colliding_code
    assert not UserProfile.objects.filter(referral_code=new_code).exists()


# --- Email Confirmation Util Tests ---


@patch("apps.users.utils.EmailMultiAlternatives")  # Mock the email sending class
def test_send_confirmation_email_success(mock_email, inactive_user):
    """Test that send_confirmation_email constructs and sends the email."""
    result = send_confirmation_email(inactive_user)

    assert result is True
    # Check that EmailMultiAlternatives was called
    mock_email.assert_called_once()
    call_args, call_kwargs = mock_email.call_args

    # Check subject, recipient, from_email
    assert "Account Activation" in call_args[0]  # Subject is first arg
    assert call_args[2] == settings.DEFAULT_FROM_EMAIL  # From email
    assert call_args[3] == [inactive_user.email]  # Recipient

    # Check that attach_alternative was called (for HTML part)
    instance = mock_email.return_value
    instance.attach_alternative.assert_called_once()
    html_content = instance.attach_alternative.call_args[0][0]
    text_content = call_args[1]  # Body is second arg

    # Check content contains link and user info (basic checks)
    assert "/confirm-email/" in html_content
    assert inactive_user.profile.full_name in html_content
    assert "/confirm-email/" in text_content
    assert inactive_user.profile.full_name in text_content

    # Check email sending was called
    instance.send.assert_called_once()


@patch(
    "apps.users.utils.EmailMultiAlternatives.send", side_effect=Exception("SMTP Error")
)
@patch("apps.users.utils.logger")  # Mock logger
def test_send_confirmation_email_failure(mock_logger, mock_send, inactive_user):
    """Test handling of exceptions during email sending."""
    result = send_confirmation_email(inactive_user)

    assert result is False
    mock_send.assert_called_once()  # Send was attempted
    # Check that the error was logged
    mock_logger.exception.assert_called_once()
    assert (
        f"Error sending confirmation email to {inactive_user.email}"
        in mock_logger.exception.call_args[0][0]
    )


# --- Get User from UID Util Tests ---


def test_get_user_from_uidb64_success_active(standard_user):
    """Test retrieving an active user from uidb64."""
    uidb64 = urlsafe_base64_encode(force_bytes(standard_user.pk))
    user = get_user_from_uidb64(uidb64)
    assert user == standard_user
    assert user.is_active is True


def test_get_user_from_uidb64_success_inactive(inactive_user):
    """Test retrieving an inactive user from uidb64."""
    uidb64 = urlsafe_base64_encode(force_bytes(inactive_user.pk))
    user = get_user_from_uidb64(uidb64)
    assert user == inactive_user
    assert user.is_active is False  # Util doesn't filter by active status


def test_get_user_from_uidb64_fail_invalid_encoding():
    """Test returning None for invalid base64."""
    user = get_user_from_uidb64("this-is-not-base64")
    assert user is None


def test_get_user_from_uidb64_fail_nonexistent_pk():
    """Test returning None if decoded PK doesn't exist."""
    # Encode a PK that's unlikely to exist (e.g., 999999)
    non_existent_pk = 999999
    uidb64 = urlsafe_base64_encode(force_bytes(non_existent_pk))
    user = get_user_from_uidb64(uidb64)
    assert user is None
