import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from ..models import (
    SerialCode,
    UserProfile,
    SubscriptionTypeChoices,
    RoleChoices,
    DarkModePrefChoices,
)
from .factories import UserFactory, SerialCodeFactory

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

# --- SerialCode Model Tests (Completed in previous response) ---


def test_serial_code_creation_defaults():
    """Test default values when creating a SerialCode via factory."""
    code = SerialCodeFactory()
    assert code.code is not None
    assert code.subscription_type is None
    assert code.duration_days == 30
    assert code.is_active is True
    assert code.is_used is False
    assert code.used_by is None
    assert code.used_at is None
    assert code.created_by is None  # Factory doesn't set this by default
    assert code.notes is not None  # Faker generates sentence


def test_serial_code_creation_with_params():
    """Test creating SerialCode with specific parameters."""
    user = UserFactory(make_staff=True)  # Creator needs to be staff
    code = SerialCodeFactory(
        code="CUSTOM-CODE-1",
        subscription_type=SubscriptionTypeChoices.MONTH_6,
        duration_days=183,
        is_active=False,
        created_by=user,
        notes="Specific test notes",
    )
    assert code.code == "CUSTOM-CODE-1"
    assert code.subscription_type == SubscriptionTypeChoices.MONTH_6
    assert code.duration_days == 183
    assert code.is_active is False
    assert code.created_by == user
    assert code.notes == "Specific test notes"


def test_serial_code_creation_with_traits():
    """Test using factory traits for predefined types."""
    code_1m = SerialCodeFactory(type_1_month=True)
    code_6m = SerialCodeFactory(type_6_months=True)
    code_12m = SerialCodeFactory(type_12_months=True)
    code_custom = SerialCodeFactory(type_custom=True, duration_days=50)

    assert (
        code_1m.subscription_type == SubscriptionTypeChoices.MONTH_1
        and code_1m.duration_days == 30
    )
    assert (
        code_6m.subscription_type == SubscriptionTypeChoices.MONTH_6
        and code_6m.duration_days == 183
    )
    assert (
        code_12m.subscription_type == SubscriptionTypeChoices.MONTH_12
        and code_12m.duration_days == 365
    )
    assert (
        code_custom.subscription_type == SubscriptionTypeChoices.CUSTOM
        and code_custom.duration_days == 50
    )


def test_serial_code_str_representation():
    """Test the __str__ method returns the code string."""
    code_value = "STR-TEST-CODE"
    code = SerialCodeFactory(code=code_value)
    assert str(code) == code_value


def test_serial_code_unique_constraint():
    """Test the unique constraint on the 'code' field."""
    code_value = "UNIQUE-TEST"
    SerialCodeFactory(code=code_value)
    with pytest.raises(IntegrityError):
        SerialCodeFactory(code=code_value)  # Attempt to create another with same code


def test_serial_code_mark_used_success():
    """Test successfully marking an active, unused code as used."""
    user = UserFactory()
    code = SerialCodeFactory(is_active=True, is_used=False)
    initial_updated_at = code.updated_at

    result = code.mark_used(user)
    code.refresh_from_db()

    assert result is True
    assert code.is_used is True
    assert code.used_by == user
    assert code.used_at is not None
    assert timezone.now() - code.used_at < timezone.timedelta(seconds=5)
    assert code.updated_at > initial_updated_at  # Check timestamp updated


def test_serial_code_mark_used_fail_inactive():
    """Test mark_used returns False for an inactive code."""
    user = UserFactory()
    code = SerialCodeFactory(is_active=False, is_used=False)
    result = code.mark_used(user)
    code.refresh_from_db()
    assert result is False
    assert code.is_used is False
    assert code.used_by is None


def test_serial_code_mark_used_fail_already_used():
    """Test mark_used returns False for an already used code."""
    user1 = UserFactory(username="user_original")
    user2 = UserFactory(username="user_attempting")
    code = SerialCodeFactory(
        is_active=True, is_used=True, used_by=user1, used_at=timezone.now()
    )
    result = code.mark_used(user2)
    code.refresh_from_db()
    assert result is False
    assert code.is_used is True
    assert code.used_by == user1  # Remains used by user1


def test_serial_code_clean_method_standardizes_code():
    """Test the clean method converts code to uppercase."""
    code = SerialCode(code="lowercase-code")
    code.clean()  # Call clean manually
    assert code.code == "LOWERCASE-CODE"


# --- UserProfile Model Tests ---


def test_user_profile_creation_via_signal():
    """Test UserProfile is created automatically when a User is created."""
    user = UserFactory()  # Signal should trigger profile creation
    assert hasattr(user, "profile")
    assert UserProfile.objects.filter(user=user).exists()
    profile = UserProfile.objects.get(user=user)
    assert profile.role == RoleChoices.STUDENT  # Check default role
    # Check a field known to be set by the factory/signal interaction
    assert (
        profile.full_name is not None or profile.full_name == ""
    )  # Default might be blank
    assert profile.referral_code is not None  # Check referral code generated


def test_user_profile_str_representation(standard_user):
    """Test the __str__ method of UserProfile returns expected string."""
    profile = standard_user.profile
    assert str(profile) == f"Profile for {standard_user.username}"


def test_user_profile_is_subscribed_property():
    """Test the is_subscribed property accurately reflects expiry date."""
    user = UserFactory()
    profile = user.profile

    # Case 1: No expiry date
    profile.subscription_expires_at = None
    profile.save()
    assert (
        profile.is_subscribed is False
    ), "Should not be subscribed with no expiry date"

    # Case 2: Expiry date in the future
    profile.subscription_expires_at = timezone.now() + timedelta(days=10)
    profile.save()
    assert profile.is_subscribed is True, "Should be subscribed with future expiry date"

    # Case 3: Expiry date in the past
    profile.subscription_expires_at = timezone.now() - timedelta(days=1)
    profile.save()
    assert (
        profile.is_subscribed is False
    ), "Should not be subscribed with past expiry date"

    # Case 4: Expiry date is exactly now (should be false)
    profile.subscription_expires_at = timezone.now()
    profile.save()
    # Give a tiny buffer for execution time
    profile.refresh_from_db()
    assert (
        profile.is_subscribed is False
    ), "Should not be subscribed if expiry is exactly now"


def test_user_profile_level_determined_property():
    """Test the level_determined property reflects assessment status."""
    user = UserFactory()
    profile = user.profile

    # Case 1: Neither level set
    profile.current_level_verbal = None
    profile.current_level_quantitative = None
    profile.save()
    assert (
        profile.level_determined is False
    ), "Level should not be determined with no scores"

    # Case 2: Only verbal level set
    profile.current_level_verbal = 80.5
    profile.save()
    assert (
        profile.level_determined is False
    ), "Level should not be determined with only verbal score"

    # Case 3: Only quantitative level set
    profile.current_level_verbal = None
    profile.current_level_quantitative = 75.0
    profile.save()
    assert (
        profile.level_determined is False
    ), "Level should not be determined with only quantitative score"

    # Case 4: Both levels set
    profile.current_level_verbal = 85.0
    profile.save()
    assert (
        profile.level_determined is True
    ), "Level should be determined when both scores are present"

    # Case 5: Check zero values count
    profile.current_level_verbal = 0.0
    profile.current_level_quantitative = 0.0
    profile.save()
    assert (
        profile.level_determined is True
    ), "Level should be determined even if scores are zero"


def test_user_profile_apply_subscription_new():
    """Test apply_subscription sets expiry correctly for a new subscription."""
    user = UserFactory()
    profile = user.profile
    code = SerialCodeFactory(duration_days=60)

    assert profile.subscription_expires_at is None
    assert profile.serial_code_used is None

    profile.apply_subscription(code)
    profile.refresh_from_db()  # Reload from DB after apply_subscription saves

    assert profile.serial_code_used == code, "Serial code used should be tracked"
    assert profile.subscription_expires_at is not None, "Expiry date should be set"
    expected_expiry = timezone.now() + timedelta(days=60)
    # Use assertAlmostEqual for datetime comparison with tolerance
    assert profile.subscription_expires_at == pytest.approx(
        expected_expiry, abs=timedelta(seconds=5)
    )


def test_user_profile_apply_subscription_extend():
    """Test apply_subscription extends an existing, active subscription correctly."""
    user = UserFactory()
    profile = user.profile
    initial_expiry = timezone.now() + timedelta(days=20)
    profile.subscription_expires_at = initial_expiry
    profile.save()

    code = SerialCodeFactory(duration_days=30)  # Add 30 more days
    profile.apply_subscription(code)
    profile.refresh_from_db()

    assert profile.serial_code_used == code
    expected_expiry = initial_expiry + timedelta(days=30)
    assert profile.subscription_expires_at == pytest.approx(
        expected_expiry, abs=timedelta(seconds=5)
    )


def test_user_profile_apply_subscription_from_expired():
    """Test apply_subscription starts new period from now if current subscription is expired."""
    user = UserFactory()
    profile = user.profile
    initial_expiry = timezone.now() - timedelta(days=10)  # Expired
    profile.subscription_expires_at = initial_expiry
    profile.save()

    code = SerialCodeFactory(duration_days=15)
    profile.apply_subscription(code)
    profile.refresh_from_db()

    assert profile.serial_code_used == code
    # Should start from NOW, not the expired date
    expected_expiry = timezone.now() + timedelta(days=15)
    assert profile.subscription_expires_at == pytest.approx(
        expected_expiry, abs=timedelta(seconds=5)
    )


def test_user_profile_referral_code_generation_on_save():
    """Test a unique referral code is generated when a new profile is saved."""
    user = UserFactory()
    # Signal creates profile, fetch it
    profile = UserProfile.objects.get(user=user)
    assert profile.referral_code is not None
    assert len(profile.referral_code) > 5  # Basic check for non-empty

    # Check uniqueness (implicitly tested if signal+util work, but explicit is better)
    user2 = UserFactory(
        username=user.username + "_alt"
    )  # Ensure different username prefix
    profile2 = UserProfile.objects.get(user=user2)
    assert profile2.referral_code is not None
    assert (
        profile.referral_code != profile2.referral_code
    ), "Referral codes should be unique"


def test_user_profile_referral_code_stable_on_update():
    """Test referral code doesn't change on subsequent profile saves."""
    user = UserFactory()
    profile = UserProfile.objects.get(user=user)
    code_before = profile.referral_code
    assert code_before is not None

    # Modify another field and save
    profile.full_name = "Updated Full Name For Stability Test"
    profile.save()
    profile.refresh_from_db()

    assert (
        profile.referral_code == code_before
    ), "Referral code should not change on unrelated updates"


def test_user_profile_referral_link(referrer_user):
    """Test setting the referred_by field links correctly."""
    referred_user = UserFactory(username="referred_user")
    profile = referred_user.profile  # Get profile created by signal
    profile.referred_by = referrer_user
    profile.save()
    profile.refresh_from_db()

    assert profile.referred_by == referrer_user
    # Check the reverse relationship
    assert referred_user.referrals_made.count() == 1
    assert referred_user.referrals_made.first() == profile


def test_user_profile_defaults():
    """Test default values for profile settings."""
    user = UserFactory()
    profile = user.profile

    assert profile.points == 0
    assert profile.current_streak_days == 0
    assert profile.longest_streak_days == 0
    assert profile.last_study_activity_at is None
    assert profile.current_level_verbal is None
    assert profile.current_level_quantitative is None
    assert profile.last_visited_study_option is None
    assert profile.dark_mode_preference == DarkModePrefChoices.LIGHT
    assert profile.dark_mode_auto_enabled is False
    assert profile.notify_reminders_enabled is True
    assert profile.upcoming_test_date is None
    assert profile.study_reminder_time is None
    assert profile.referred_by is None


def test_user_profile_picture_field():
    """Test the profile_picture ImageField allows null/blank."""
    user = UserFactory()
    profile = user.profile
    # Ensure it can be saved as null (default)
    assert profile.profile_picture == "" or profile.profile_picture is None

    # Test setting it to None explicitly
    profile.profile_picture = None
    try:
        profile.save()
        profile.refresh_from_db()
        assert profile.profile_picture == "" or profile.profile_picture is None
    except Exception as e:
        pytest.fail(f"Saving profile with picture=None failed: {e}")
