import random
import string
import uuid
import logging
from typing import TYPE_CHECKING, Optional
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import (
    urlsafe_base64_encode,
    urlsafe_base64_decode,
)  # Added decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _, override
from decouple import config
from django.core.exceptions import ValidationError as DjangoValidationError

# Avoid circular import for type checking
if TYPE_CHECKING:
    from .models import UserProfile, SerialCode

logger = logging.getLogger(__name__)


def generate_unique_referral_code(username: str) -> str:
    """
    Generates a unique referral code based on the username.
    Format: PREFIX-HEX (e.g., ALI-A1B2C3)
    Ensures uniqueness against existing UserProfile referral codes.
    """
    from .models import (
        UserProfile,
    )  # Import locally to avoid circular dependency at runtime

    prefix = (
        username[:6].upper().replace("_", "").replace("-", "")
    )  # Take first 6 chars, uppercase, remove common separators
    if not prefix:  # Handle edge case of very short/empty username
        prefix = "USER"

    max_attempts = 10  # Prevent infinite loop in extremely unlikely collision scenario
    for attempt in range(max_attempts):
        unique_part = (
            uuid.uuid4().hex[:6].upper()
        )  # 6 hex chars = 16^6 = ~16.7 million possibilities
        code = f"{prefix}-{unique_part}"

        if not UserProfile.objects.filter(referral_code=code).exists():
            logger.debug(
                f"Generated unique referral code '{code}' for username prefix '{prefix}'"
            )
            return code

    # Fallback if collision persists after multiple attempts (highly improbable)
    logger.error(
        f"Could not generate a unique referral code for username prefix '{prefix}' after {max_attempts} attempts. Using full UUID."
    )
    return str(uuid.uuid4())  # Return a full UUID as a last resort


def generate_unique_serial_code(
    prefix="QADER", length=12, separator="-", segment_length=4
) -> str:
    """
    Generates a likely unique serial code in a segmented format (e.g., QADER-ABCD-EFGH-IJKL).

    Args:
        prefix: Optional prefix for the code.
        length: Total length of the random part (excluding prefix and separators).
        separator: Character to use between segments.
        segment_length: Length of each random segment.

    Returns:
        A unique serial code string.
    """
    from .models import SerialCode  # Local import

    if not prefix:
        prefix_part = ""
    else:
        prefix_part = prefix.upper() + separator

    num_segments = (length + segment_length - 1) // segment_length  # Ceiling division
    chars = string.ascii_uppercase + string.digits  # Characters to use

    while True:
        segments = []
        current_length = 0
        for _ in range(num_segments):
            segment_chars_needed = min(segment_length, length - current_length)
            if segment_chars_needed <= 0:
                break
            segment = "".join(random.choices(chars, k=segment_chars_needed))
            segments.append(segment)
            current_length += segment_chars_needed

        random_part = separator.join(segments)
        code = prefix_part + random_part

        # Ensure code is unique (case-insensitive check)
        if not SerialCode.objects.filter(code__iexact=code).exists():
            return code
        # If collision (rare), loop continues to generate a new one


def send_password_reset_email(user: User, context: dict = None):
    """
    Sends the standard password reset email to a user.
    Can be used by both public and admin reset views.
    """
    if not user or not user.email:
        logger.error(
            "Attempted to send password reset email to invalid user or user without email."
        )
        return False

    # Determine the language to use
    language_code = settings.LANGUAGE_CODE

    try:
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_base_url = getattr(
            settings, "FRONTEND_BASE_URL", "http://localhost:3000"
        )
        password_reset_path = getattr(
            settings, "FRONTEND_PASSWORD_RESET_PATH", "/reset-password-confirm"
        )
        reset_link = (
            f"{frontend_base_url.rstrip('/')}{password_reset_path}/{uidb64}/{token}/"
        )

        email_context = {
            "email": user.email,
            "username": user.username,
            "reset_link": reset_link,
            "site_name": settings.SITE_NAME,  # SITE_NAME is already lazy translated
            "user": user,
            **(context or {}),
        }

        # Activate the user's language for template rendering
        with override(language_code):
            subject = render_to_string(
                "emails/password_reset_subject.txt", email_context
            ).strip()
            html_body = render_to_string(
                "emails/password_reset_body.html", email_context
            )
            text_body = render_to_string(
                "emails/password_reset_body.txt", email_context
            )

        msg = EmailMultiAlternatives(
            subject,  # Subject is now translated
            text_body,  # Body is now translated
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        msg.attach_alternative(html_body, "text/html")  # HTML body also translated
        msg.send()
        logger.info(
            f"Password reset email sent successfully to {user.email} in language '{language_code}'."
        )
        return True
    except Exception as e:
        logger.exception(f"Error sending password reset email to {user.email}: {e}")
        return False


def send_confirmation_email(user: User, request=None, context: dict = None):
    """
    Sends an email with an account confirmation link to a newly registered user.
    """
    if not user or not user.email:
        logger.error(
            "Attempted to send confirmation email to invalid user or user without email."
        )
        return False

    language_code = settings.LANGUAGE_CODE

    try:
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        frontend_base_url = getattr(
            settings, "FRONTEND_BASE_URL", "http://localhost:3000"
        )
        confirmation_path = getattr(
            settings, "FRONTEND_EMAIL_CONFIRMATION_PATH", "/confirm-email"
        )
        confirmation_link = (
            f"{frontend_base_url.rstrip('/')}{confirmation_path}/{uidb64}/{token}/"
        )

        # Get full_name safely, defaulting if profile doesn't exist yet (common during signup)
        full_name = "User"  # Default
        try:
            if hasattr(user, "profile") and user.profile.full_name:
                full_name = user.profile.full_name
        except Exception:  # Catch DoesNotExist or other issues
            pass  # Keep default full_name

        email_context = {
            "email": user.email,
            "username": getattr(user, "username", user.email),
            "full_name": full_name,
            "confirmation_link": confirmation_link,
            "site_name": settings.SITE_NAME,  # Already lazy translated
            "user": user,
            **(context or {}),
        }

        # Activate the language for template rendering
        with override(language_code):
            subject = render_to_string(
                "emails/confirmation_subject.txt", email_context
            ).strip()
            html_body = render_to_string("emails/confirmation_body.html", email_context)
            text_body = render_to_string("emails/confirmation_body.txt", email_context)

        msg = EmailMultiAlternatives(
            subject,  # Subject is now translated
            text_body,  # Body is now translated
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        msg.attach_alternative(html_body, "text/html")  # HTML body also translated
        msg.send()
        logger.info(
            f"Account confirmation email sent successfully to {user.email} in language '{language_code}'."
        )
        return True
    except Exception as e:
        logger.exception(f"Error sending confirmation email to {user.email}: {e}")
        return False


def get_user_from_uidb64(uidb64: str) -> Optional[User]:
    """Helper to safely decode uidb64 and retrieve the User object (can be active or inactive)."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)  # Don't filter by is_active here
        return user
    except (
        TypeError,
        ValueError,
        OverflowError,
        User.DoesNotExist,
        DjangoValidationError,
    ) as e:
        logger.debug(f"Failed to get user from UIDB64 '{uidb64}': {e}")
        return None
