import random
import secrets
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
from django.utils.text import slugify

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
            "full_name": user.profile.full_name,
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


def generate_otp(length: Optional[int] = None) -> str:
    """Generates a secure random OTP of a specified length."""
    otp_actual_length = length if length is not None else settings.OTP_LENGTH
    return "".join(secrets.choice(string.digits) for _ in range(otp_actual_length))


def send_password_reset_otp_email(
    user: User, otp_code: str, context: Optional[dict] = None
) -> bool:
    """
    Sends an email with the OTP for password reset.
    """
    if not user or not user.email:
        logger.error(
            "Attempted to send password reset OTP to invalid user or user without email."
        )
        return False

    language_code = (
        user.profile.language
        if hasattr(user, "profile") and user.profile.language
        else settings.LANGUAGE_CODE
    )

    try:
        email_context = {
            "email": user.email,
            "full_name": user.profile.full_name,
            "otp_code": otp_code,
            "otp_expiry_minutes": settings.OTP_EXPIRY_MINUTES,
            "site_name": settings.SITE_NAME,
            "user": user,
            **(context or {}),
        }

        with override(language_code):
            subject = render_to_string(
                "emails/password_reset_otp/password_reset_otp_subject.txt",
                email_context,
            ).strip()
            html_body = render_to_string(
                "emails/password_reset_otp/password_reset_otp_body.html", email_context
            )
            text_body = render_to_string(
                "emails/password_reset_otp/password_reset_otp_body.txt", email_context
            )

        msg = EmailMultiAlternatives(
            subject,
            text_body,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(
            f"Password reset OTP email sent successfully to {user.email} in language '{language_code}'."
        )
        return True
    except Exception as e:
        logger.exception(f"Error sending password reset OTP email to {user.email}: {e}")
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


def generate_unique_username_from_fullname(full_name: str, email: str) -> str:
    """
    Generates a unique, sanitized username from a full name.
    Falls back to an email-derived username if full_name is problematic or empty.
    Ensures the username conforms to typical Django User model constraints.
    """
    if not full_name or not full_name.strip():
        # Fallback if full_name is empty or only whitespace
        candidate_name = email.split("@")[0]  # Use local part of email
    else:
        candidate_name = full_name

    # 1. Slugify: handles spaces, non-ASCII, converts to lowercase, and uses hyphens.
    # Example: "John Doe!" -> "john-doe"
    base_username = slugify(candidate_name)

    # 2. Replace hyphens with underscores (common preference for usernames)
    # Example: "john-doe" -> "john_doe"
    base_username = base_username.replace("-", "_")

    # 3. Ensure base_username is not empty after slugification (e.g., if full_name was "!!!")
    if not base_username:
        # Fallback to a more robust email part if initial candidate_name yielded empty slug
        email_prefix = email.split("@")[0]
        base_username = slugify(email_prefix).replace("-", "_")
        if not base_username:  # Ultimate fallback if email_prefix is also problematic
            base_username = "user"

    # 4. Truncate to avoid exceeding max_length, leaving space for a suffix.
    # User.username.max_length is typically 150.
    username_field = User._meta.get_field("username")
    username_max_length = username_field.max_length

    # Leave space for a suffix like "_1234"
    # Adjust suffix_space if you expect very high number of collisions for the same base.
    suffix_space = 7

    if len(base_username) > username_max_length - suffix_space:
        base_username = base_username[: username_max_length - suffix_space]

    # Ensure base_username is not empty after truncation
    if not base_username:  # Should be extremely rare if previous fallbacks worked
        base_username = "user"

    # 5. Check for uniqueness and append counter if necessary
    original_base_for_suffixing = base_username  # Store the potentially truncated base
    username_to_check = base_username
    counter = 1

    while User.objects.filter(username=username_to_check).exists():
        suffix = f"_{counter}"
        # Ensure the base + suffix doesn't exceed max_length
        if len(original_base_for_suffixing) + len(suffix) > username_max_length:
            # If too long, we need to shorten the original_base_for_suffixing part
            allowed_base_len = username_max_length - len(suffix)
            if (
                allowed_base_len <= 0
            ):  # This means suffix itself is too long (e.g. _100000 for short max_length)
                # Fallback to a highly unique alternative
                import uuid

                username_to_check = (
                    f"u_{uuid.uuid4().hex[:username_max_length-2]}"  # "u_" prefix
                )
                if User.objects.filter(
                    username=username_to_check
                ).exists():  # Extremely unlikely
                    logger.error(
                        f"CRITICAL: Could not generate unique username for {full_name}/{email} even with UUID."
                    )
                    raise ValueError(
                        "Could not generate a unique username after extensive attempts."
                    )
                break  # Exit while loop with this UUID-based username

            current_base_for_loop = original_base_for_suffixing[:allowed_base_len]
            username_to_check = f"{current_base_for_loop}{suffix}"
        else:
            username_to_check = f"{original_base_for_suffixing}{suffix}"

        counter += 1
        if (
            counter > 10000
        ):  # Safety break for extreme edge cases or very short max_length
            logger.error(
                f"Exceeded 10000 attempts to generate unique username for {full_name}/{email}."
            )
            import uuid  # Fallback to a more random username

            username_to_check = f"user_{uuid.uuid4().hex[:username_max_length-5]}"
            if User.objects.filter(
                username=username_to_check
            ).exists():  # Extremely unlikely
                raise ValueError(
                    "Could not generate a unique username after extensive attempts (post-safety-break)."
                )
            break  # Exit while loop

    return username_to_check
