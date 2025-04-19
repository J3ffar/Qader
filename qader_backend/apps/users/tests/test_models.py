import pytest
from django.test import TestCase  # Or use pytest directly with fixtures
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import (
    ValidationError,
)  # If clean method enforced validation

from ..models import SerialCode, UserProfile, SubscriptionTypeChoices
from .factories import UserFactory, SerialCodeFactory

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# Using pytest style tests with fixtures
def test_serial_code_creation_defaults():
    """Test creating a serial code uses default values correctly."""
    code = SerialCodeFactory()
    assert code.code is not None
    assert code.duration_days == 30  # Default from factory/model
    assert code.is_active is True
    assert code.is_used is False
    assert code.used_by is None
    assert code.used_at is None
    assert code.created_by is None
    assert code.subscription_type is None  # Default from factory


def test_serial_code_creation_with_type():
    """Test creating a serial code with specific types."""
    code_1m = SerialCodeFactory(
        subscription_type=SubscriptionTypeChoices.MONTH_1,
        duration_days=30,  # Explicitly set for clarity
    )
    code_6m = SerialCodeFactory(
        subscription_type=SubscriptionTypeChoices.MONTH_6, duration_days=183
    )
    code_12m = SerialCodeFactory(
        subscription_type=SubscriptionTypeChoices.MONTH_12, duration_days=365
    )
    code_custom = SerialCodeFactory(
        subscription_type=SubscriptionTypeChoices.CUSTOM,
        duration_days=45,  # Custom duration
    )
    code_no_type = SerialCodeFactory(subscription_type=None)  # Explicitly None

    assert code_1m.subscription_type == SubscriptionTypeChoices.MONTH_1
    assert code_1m.duration_days == 30
    assert code_6m.subscription_type == SubscriptionTypeChoices.MONTH_6
    assert code_6m.duration_days == 183
    assert code_12m.subscription_type == SubscriptionTypeChoices.MONTH_12
    assert code_12m.duration_days == 365
    assert code_custom.subscription_type == SubscriptionTypeChoices.CUSTOM
    assert code_custom.duration_days == 45
    assert code_no_type.subscription_type is None
    assert code_no_type.duration_days == 30  # Falls back to default


def test_serial_code_creation_with_traits():
    """Test creating codes using factory traits."""
    code_1m = SerialCodeFactory(type_1_month=True)
    code_6m = SerialCodeFactory(type_6_months=True)
    code_12m = SerialCodeFactory(type_12_months=True)
    code_custom = SerialCodeFactory(type_custom=True, duration_days=99)

    assert code_1m.subscription_type == SubscriptionTypeChoices.MONTH_1
    assert code_1m.duration_days == 30
    assert code_6m.subscription_type == SubscriptionTypeChoices.MONTH_6
    assert code_6m.duration_days == 183
    assert code_12m.subscription_type == SubscriptionTypeChoices.MONTH_12
    assert code_12m.duration_days == 365
    assert code_custom.subscription_type == SubscriptionTypeChoices.CUSTOM
    assert code_custom.duration_days == 99  # Overrides default


def test_serial_code_str_representation():
    """Test the __str__ method of SerialCode."""
    code_value = "TESTCODE123"
    code = SerialCodeFactory(code=code_value)
    assert str(code) == code_value


def test_serial_code_mark_used():
    """Test the mark_used method updates the code correctly."""
    user = UserFactory()
    code = SerialCodeFactory(is_active=True, is_used=False)

    assert code.is_used is False
    assert code.used_by is None
    assert code.used_at is None

    result = code.mark_used(user)
    code.refresh_from_db()  # Reload data from DB

    assert result is True
    assert code.is_used is True
    assert code.used_by == user
    assert code.used_at is not None
    assert timezone.now() - code.used_at < timezone.timedelta(
        seconds=5
    )  # Check time is recent


def test_serial_code_mark_used_when_inactive():
    """Test mark_used fails for an inactive code."""
    user = UserFactory()
    code = SerialCodeFactory(is_active=False, is_used=False)
    result = code.mark_used(user)
    code.refresh_from_db()

    assert result is False
    assert code.is_used is False
    assert code.used_by is None


def test_serial_code_mark_used_when_already_used():
    """Test mark_used fails for an already used code."""
    user1 = UserFactory()
    user2 = UserFactory()
    code = SerialCodeFactory(
        is_active=True, is_used=True, used_by=user1, used_at=timezone.now()
    )
    result = code.mark_used(user2)  # Attempt to use again by another user
    code.refresh_from_db()

    assert result is False
    assert code.is_used is True
    assert code.used_by == user1  # Remains used by the original user


def test_serial_code_clean_method_allows_mismatch():
    """
    Test that the current clean method allows saving even if duration
    doesn't perfectly match the non-custom type (as it doesn't raise Error).
    """
    code_value = "MISMATCH-TEST"
    mismatched_days = 35
    code = SerialCode(
        code=code_value,
        duration_days=mismatched_days,  # Mismatch for 1 month type
        is_active=True,
    )
    try:
        # full_clean() calls clean()
        code.full_clean()  # Should not raise ValidationError based on current clean impl.
        code.save()  # Saving should also work
    except ValidationError as e:
        pytest.fail(f"ValidationError was raised unexpectedly by clean(): {e}")

    assert SerialCode.objects.filter(code=code_value).exists()
    db_code = SerialCode.objects.get(code=code_value)
    # FIX: Assert that the saved value is the mismatched value provided
    assert db_code.duration_days == mismatched_days  # Should be 35, not 30


# You can add more tests for UserProfile properties if needed,
# but they seem covered in test_api.py already.
