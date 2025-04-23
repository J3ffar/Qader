import pytest
from ..utils import generate_unique_referral_code
from ..models import UserProfile
from .factories import UserFactory

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
