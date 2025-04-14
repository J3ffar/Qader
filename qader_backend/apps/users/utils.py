import uuid
from .models import UserProfile


def generate_unique_referral_code(username):
    """Generates a unique referral code for a UserProfile."""
    prefix = username[:8].upper().replace("_", "")
    while True:
        unique_part = uuid.uuid4().hex[:6].upper()
        code = f"{prefix}-{unique_part}"
        if not UserProfile.objects.filter(referral_code=code).exists():
            return code
