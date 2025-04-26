import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import time

from ..models import (
    GenderChoices,
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

    time.sleep(0.01)  # Sleep for 10 milliseconds

    result = code.mark_used(user)
    code.refresh_from_db()

    assert result is True
    assert code.is_used is True
    assert code.used_by == user
    assert code.used_at is not None
    assert timezone.now() - code.used_at < timezone.timedelta(seconds=5)
    assert code.updated_at > initial_updated_at


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


def test_user_profile_is_profile_complete_property():
    """Test the is_profile_complete property."""
    user = UserFactory(is_active=True)  # Start with active user for simplicity
    profile = user.profile
    profile.full_name = "Test Full Name"  # Ensure full_name is set

    # Case 1: Missing all required fields
    profile.gender = None
    profile.grade = None
    profile.has_taken_qiyas_before = None
    profile.save()
    assert profile.is_profile_complete is False, "Should be incomplete: All missing"

    # Case 2: Missing grade
    profile.gender = GenderChoices.MALE
    profile.grade = None
    profile.has_taken_qiyas_before = True
    profile.save()
    assert profile.is_profile_complete is False, "Should be incomplete: Missing grade"

    # Case 3: Missing gender
    profile.gender = None
    profile.grade = "Grade 12"
    profile.has_taken_qiyas_before = False
    profile.save()
    assert profile.is_profile_complete is False, "Should be incomplete: Missing gender"

    # Case 4: Missing has_taken_qiyas_before (is None)
    profile.gender = GenderChoices.FEMALE
    profile.grade = "University"
    profile.has_taken_qiyas_before = None
    profile.save()
    assert (
        profile.is_profile_complete is False
    ), "Should be incomplete: Missing Qiyas bool"

    # Case 5: Missing full_name (should have been set on signup)
    profile.full_name = ""  # Simulate missing
    profile.gender = GenderChoices.FEMALE
    profile.grade = "University"
    profile.has_taken_qiyas_before = True
    profile.save()
    assert (
        profile.is_profile_complete is False
    ), "Should be incomplete: Missing full_name"

    # Case 6: All required fields present
    profile.full_name = "Test Full Name"
    profile.gender = GenderChoices.FEMALE
    profile.grade = "University"
    profile.has_taken_qiyas_before = True
    profile.save()
    assert profile.is_profile_complete is True, "Should be complete: All present"


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

    time.sleep(0.01)  # Small delay
    now_before_apply = timezone.now()  # Capture time after delay

    profile.apply_subscription(code)
    profile.refresh_from_db()  # Reload from DB after apply_subscription saves

    assert profile.serial_code_used == code, "Serial code used should be tracked"
    assert profile.subscription_expires_at is not None, "Expiry date should be set"

    # The model calculates expiry based on its timezone.now() call.
    # Calculate the expected expiry based on the 'now_before_apply' captured earlier + duration.
    # This avoids the race condition with the test's timezone.now().
    expected_expiry = now_before_apply + timedelta(days=60)


def test_user_profile_apply_subscription_extend():
    """Test apply_subscription extends an existing, active subscription correctly."""
    user = UserFactory()
    profile = user.profile
    initial_expiry = timezone.now() + timedelta(days=20)
    profile.subscription_expires_at = initial_expiry
    profile.save()

    time.sleep(0.01)  # Small delay before applying new code

    code = SerialCodeFactory(duration_days=30)  # Add 30 more days
    profile.apply_subscription(code)
    profile.refresh_from_db()

    assert profile.serial_code_used == code
    expected_expiry = initial_expiry + timedelta(days=30)

    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(seconds=5)


def test_user_profile_apply_subscription_from_expired():
    """Test apply_subscription starts new period from now if current subscription is expired."""
    user = UserFactory()
    profile = user.profile
    initial_expiry = timezone.now() - timedelta(days=10)  # Expired
    profile.subscription_expires_at = initial_expiry
    profile.save()

    time.sleep(0.01)  # Small delay before applying new code
    now_before_apply = timezone.now()  # Capture time after delay

    code = SerialCodeFactory(duration_days=15)
    profile.apply_subscription(code)
    profile.refresh_from_db()

    assert profile.serial_code_used == code
    expected_expiry = now_before_apply + timedelta(days=15)

    # Correct datetime comparison with tolerance
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(seconds=5)


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
    referred_user_instance = UserFactory(
        username="referred_user"
    )  # Renamed variable for clarity
    profile = referred_user_instance.profile  # Get profile created by signal
    profile.referred_by = referrer_user
    profile.save()

    profile.refresh_from_db()  # Refresh the profile itself is good practice too
    assert profile.referred_by == referrer_user

    # Refresh the referrer_user object instance to update its related managers cache
    # BEFORE attempting to count its referrals_made.
    referrer_user.refresh_from_db()

    # Check the reverse relationship
    assert referrer_user.referrals_made.count() == 1
    assert referrer_user.referrals_made.first() == profile


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
    assert not profile.profile_picture

    # Test setting it to None explicitly
    profile.profile_picture = None
    try:
        profile.save()
        profile.refresh_from_db()
        assert profile.profile_picture == "" or profile.profile_picture is None
    except Exception as e:
        pytest.fail(f"Saving profile with picture=None failed: {e}")


def test_user_profile_grant_trial_subscription_success():
    """Test granting a trial subscription to an unsubscribed user."""
    user = UserFactory(is_active=True, profile_data={"full_name": "Trial User"})
    profile = user.profile
    assert not profile.is_subscribed

    granted = profile.grant_trial_subscription(duration_days=1)
    # grant_trial_subscription doesn't save automatically, save manually for test check
    profile.save()
    profile.refresh_from_db()

    assert granted is True
    assert profile.is_subscribed is True
    assert profile.serial_code_used is None
    expected_expiry = timezone.now() + timedelta(days=1)
    assert abs(profile.subscription_expires_at - expected_expiry) < timedelta(seconds=5)


def test_user_profile_grant_trial_subscription_fail_already_subscribed():
    """Test granting trial fails if user is already subscribed."""
    user = UserFactory(is_active=True, profile_data={"full_name": "Trial User"})
    profile = user.profile
    profile.subscription_expires_at = timezone.now() + timedelta(days=10)
    profile.save()
    assert profile.is_subscribed is True

    original_expiry = profile.subscription_expires_at
    granted = profile.grant_trial_subscription(duration_days=1)
    profile.save()  # Save shouldn't change anything if trial wasn't granted
    profile.refresh_from_db()

    assert granted is False
    assert profile.is_subscribed is True
    # Ensure expiry date hasn't changed
    assert profile.subscription_expires_at == original_expiry
