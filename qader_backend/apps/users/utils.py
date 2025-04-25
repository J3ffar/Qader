import random
import string
import uuid
import logging
from typing import TYPE_CHECKING

# Avoid circular import for type checking
if TYPE_CHECKING:
    from .models import UserProfile

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
