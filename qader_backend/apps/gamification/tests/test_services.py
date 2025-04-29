# qader_backend/apps/gamification/tests/test_services.py

from django.conf import settings
import pytest
from unittest.mock import patch, MagicMock, ANY  # Import ANY from unittest.mock
from django.utils import timezone
import datetime  # <-- Import datetime
from datetime import timedelta
from freezegun import freeze_time
from django.core.exceptions import ObjectDoesNotExist

from apps.users.models import UserProfile
from apps.users.tests.factories import UserFactory
from ..services import (
    award_points,
    update_streak,
    check_and_award_badge,
    purchase_reward,
    PurchaseError,
    PointReason,
)
from ..models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase
from .factories import BadgeFactory, RewardStoreItemFactory, UserBadgeFactory

pytestmark = pytest.mark.django_db


# --- Test award_points Service ---
# (No changes needed in award_points tests themselves)
def test_award_points_success_positive():
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    points_to_add = 10
    success = award_points(
        user, points_to_add, PointReason.TEST_COMPLETED, "Completed test"
    )
    assert success is True
    profile.refresh_from_db()
    assert profile.points == initial_points + points_to_add
    assert PointLog.objects.filter(user=user, points_change=points_to_add).exists()


def test_award_points_success_negative():
    user = UserFactory()
    profile = user.profile
    profile.points = 100
    profile.save()
    initial_points = profile.points
    points_to_subtract = -50
    success = award_points(
        user, points_to_subtract, PointReason.REWARD_PURCHASE, "Bought item"
    )
    assert success is True
    profile.refresh_from_db()
    assert profile.points == initial_points + points_to_subtract
    assert PointLog.objects.filter(user=user, points_change=points_to_subtract).exists()


def test_award_points_zero_change():
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    success = award_points(user, 0, PointReason.TEST_COMPLETED, "Zero point change")
    assert success is True
    profile.refresh_from_db()
    assert profile.points == initial_points
    assert not PointLog.objects.filter(user=user).exists()


def test_award_points_invalid_user():
    success = award_points(None, 10, PointReason.TEST_COMPLETED, "Test")
    assert success is False


def test_award_points_profile_missing():
    user = UserFactory()
    UserProfile.objects.filter(user=user).delete()
    success = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert success is False


@patch("apps.gamification.services.PointLog.objects.create")
def test_award_points_transaction_rollback_on_log_create_fail(mock_create_log):
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    mock_create_log.side_effect = Exception("DB error on log create")
    success = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert success is False
    profile.refresh_from_db()
    assert profile.points == initial_points
    assert not PointLog.objects.filter(user=user).exists()
    mock_create_log.assert_called_once()


@patch("apps.gamification.services.UserProfile.objects.select_for_update")
def test_award_points_transaction_rollback_on_profile_save_fail(mock_select_for_update):
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    mock_profile = MagicMock(spec=UserProfile)
    mock_profile.points = initial_points
    mock_profile.save.side_effect = Exception("DB error on profile save")
    mock_select_for_update.return_value.get.return_value = mock_profile
    success = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert success is False
    profile_db = UserProfile.objects.get(user=user)
    assert profile_db.points == initial_points
    assert not PointLog.objects.filter(user=user).exists()
    mock_profile.save.assert_called_once()


# --- Test update_streak Service ---
# (No changes needed in update_streak tests, they don't use mocker)


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_start_new():
    user = UserFactory()
    profile = user.profile
    frozen_now = timezone.now()  # Capture frozen time
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 1
    assert profile.longest_streak_days == 1
    assert profile.last_study_activity_at == frozen_now  # Compare directly


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    # --- FIXED: Use timezone.now() for setup ---
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()
    # --- END FIXED ---

    frozen_now = timezone.now()  # Capture frozen time
    update_streak(user)
    profile.refresh_from_db()
    # --- FIXED: Correct expected value ---
    assert profile.current_streak_days == 4  # Should increment 3 -> 4
    # --- END FIXED ---
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == frozen_now


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue_and_update_longest():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 5
    profile.longest_streak_days = 5
    # --- FIXED: Use timezone.now() for setup ---
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()
    # --- END FIXED ---

    frozen_now = timezone.now()  # Capture frozen time
    update_streak(user)
    profile.refresh_from_db()
    # --- FIXED: Correct expected value ---
    assert profile.current_streak_days == 6  # Should increment 5 -> 6
    assert profile.longest_streak_days == 6  # Should update longest
    # --- END FIXED ---
    assert profile.last_study_activity_at == frozen_now


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_break_streak():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    # --- FIXED: Use timezone.now() for setup ---
    profile.last_study_activity_at = timezone.now() - timedelta(days=2)
    profile.save()
    # --- END FIXED ---

    frozen_now = timezone.now()  # Capture frozen time
    update_streak(user)
    profile.refresh_from_db()
    # --- FIXED: Correct expected value ---
    assert profile.current_streak_days == 1  # Should reset to 1
    # --- END FIXED ---
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == frozen_now


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_same_day():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 2
    profile.longest_streak_days = 2
    # --- FIXED: Use timezone.now() for setup ---
    earlier_today = timezone.now() - timedelta(hours=2)
    profile.last_study_activity_at = earlier_today
    # --- END FIXED ---
    profile.save()

    frozen_now = timezone.now()  # Capture frozen time
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 2
    assert profile.longest_streak_days == 2
    # --- FIXED: Assert against frozen now ---
    assert profile.last_study_activity_at > earlier_today  # Still true
    assert profile.last_study_activity_at == frozen_now  # Should be updated to now
    # --- END FIXED ---


@freeze_time("2024-07-26 10:00:00")  # Needs a different day to trigger increment
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.check_and_award_badge")
def test_update_streak_triggers_rewards_on_hitting_milestone(
    mock_check_badge, mock_award_points
):
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 1
    profile.longest_streak_days = 1
    # --- FIXED: Use timezone.now() for setup ---
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()
    # --- END FIXED ---

    update_streak(user)
    profile.refresh_from_db()
    # --- FIXED: Correct expected value ---
    assert profile.current_streak_days == 2  # Incremented 1 -> 2
    # --- END FIXED ---
    # Check if points awarded for hitting 2 days (assuming 2 is a milestone in settings)
    # Adjust points/reason based on settings.POINTS_STREAK_BONUS_MAP
    points_for_2_days = settings.POINTS_STREAK_BONUS_MAP.get(2)
    if points_for_2_days and points_for_2_days > 0:
        # --- FIXED: Use ANY for description and profile ---
        mock_award_points.assert_called_once_with(
            user=user,
            points_change=points_for_2_days,
            reason_code=PointReason.STREAK_BONUS,
            description=ANY,
            related_object=profile,
        )
        # --- END FIXED ---
    else:
        mock_award_points.assert_not_called()  # Or assert called 0 times
    mock_check_badge.assert_not_called()  # No badge for 2 days usually

    # --- Reset and test hitting 5 days ---
    mock_award_points.reset_mock()
    mock_check_badge.reset_mock()
    profile.current_streak_days = 4  # Start at 4 days
    profile.longest_streak_days = 4
    # Set last activity to yesterday relative to the *new* frozen time
    with freeze_time("2024-07-30 10:00:00"):  # Advance time further
        profile.last_study_activity_at = timezone.now() - timedelta(days=1)
        profile.save()
        BadgeFactory(slug=settings.BADGE_SLUG_5_DAY_STREAK)  # Ensure badge exists

        update_streak(user)
        profile.refresh_from_db()
        assert profile.current_streak_days == 5  # Incremented 4 -> 5

        # Check points for 5 days
        points_for_5_days = settings.POINTS_STREAK_BONUS_MAP.get(5)
        if points_for_5_days and points_for_5_days > 0:
            mock_award_points.assert_called_once_with(
                user=user,
                points_change=points_for_5_days,
                reason_code=PointReason.STREAK_BONUS,
                description=ANY,
                related_object=profile,
            )
        else:
            mock_award_points.assert_not_called()

        # Check badge call for 5 days
        mock_check_badge.assert_called_once_with(user, settings.BADGE_SLUG_5_DAY_STREAK)


@freeze_time("2024-07-26 10:00:00")  # Needs a different day to trigger increment
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.check_and_award_badge")
def test_update_streak_does_not_trigger_rewards_if_already_past_milestone(
    mock_check_badge, mock_award_points
):
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 6  # Already past 5-day milestone
    profile.longest_streak_days = 6
    # --- FIXED: Use timezone.now() for setup ---
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()
    # --- END FIXED ---

    update_streak(user)
    profile.refresh_from_db()
    # --- FIXED: Correct expected value ---
    assert profile.current_streak_days == 7  # Incremented 6 -> 7
    # --- END FIXED ---
    mock_award_points.assert_not_called()  # No points for day 7 usually
    mock_check_badge.assert_not_called()  # No badge check for day 7 usually


# --- Test check_and_award_badge Service ---
# Fix badge test to use a testable scenario
def test_check_award_badge_success_criteria_met(mocker):  # Add mocker fixture argument
    # Patch objects using mocker inside the test
    mock_logger = mocker.patch("apps.gamification.services.logger")
    mock_award_points = mocker.patch("apps.gamification.services.award_points")

    user = UserFactory()
    # Use a badge slug that exists in settings and BADGE_CHECKERS
    badge_slug = getattr(settings, "BADGE_SLUG_10_DAY_STREAK", "10-day-streak")
    badge = BadgeFactory(slug=badge_slug, is_active=True)
    profile = user.profile
    profile.current_streak_days = 10  # Set profile state to meet criteria
    profile.save()

    awarded = check_and_award_badge(user, badge_slug)

    assert awarded is True
    assert UserBadge.objects.filter(user=user, badge=badge).exists()

    # Check points awarded (use safe getattr for point value)
    points_badge_earned = getattr(settings, "POINTS_BADGE_EARNED", 0)
    if points_badge_earned > 0:
        mock_award_points.assert_called_once_with(
            user=user,
            points_change=points_badge_earned,
            reason_code=PointReason.BADGE_EARNED,
            description=ANY,
            related_object=ANY,  # Check it's called with a UserBadge instance
        )
        # Optional: Verify the related object type more specifically
        call_args, call_kwargs = mock_award_points.call_args
        assert isinstance(call_kwargs.get("related_object"), UserBadge)
        assert call_kwargs.get("related_object").badge == badge
    else:
        mock_award_points.assert_not_called()


def test_check_award_badge_already_earned():
    user = UserFactory()
    badge_slug = getattr(settings, "BADGE_SLUG_5_DAY_STREAK", "5-day-streak")
    badge = BadgeFactory(slug=badge_slug)
    UserBadgeFactory(user=user, badge=badge)  # User already has it

    # Ensure profile state meets criteria just to be sure it's not that
    profile = user.profile
    profile.current_streak_days = 5
    profile.save()

    awarded = check_and_award_badge(user, badge_slug)
    # --- FIXED: Assert is False ---
    assert awarded is False
    # --- END FIXED ---
    assert UserBadge.objects.filter(user=user, badge=badge).count() == 1


@patch("apps.gamification.services.logger")
@patch(
    "apps.gamification.services.award_points"
)  # Mock award_points even if not called
def test_check_award_badge_criteria_not_met(mock_award_points, mock_logger):
    user = UserFactory()
    badge_slug = getattr(settings, "BADGE_SLUG_10_DAY_STREAK", "10-day-streak")
    badge = BadgeFactory(slug=badge_slug)
    profile = user.profile
    profile.current_streak_days = 9  # Criteria NOT met
    profile.save()

    awarded = check_and_award_badge(user, badge_slug)
    # --- FIXED: Assert is False ---
    assert awarded is False
    # --- END FIXED ---
    assert not UserBadge.objects.filter(user=user, badge=badge).exists()
    mock_award_points.assert_not_called()


@patch("apps.gamification.services.logger")
@patch("apps.gamification.services.award_points")  # Mock award_points
def test_check_award_badge_inactive_badge(mock_award_points, mock_logger):
    user = UserFactory()
    badge_slug = "test-badge-inactive"
    BadgeFactory(slug=badge_slug, is_active=False)  # Inactive badge

    awarded = check_and_award_badge(user, badge_slug)
    # --- FIXED: Assert is False ---
    assert awarded is False
    # --- END FIXED ---
    mock_award_points.assert_not_called()


@patch("apps.gamification.services.logger")
@patch("apps.gamification.services.award_points")  # Mock award_points
def test_check_award_badge_non_existent_badge(mock_award_points, mock_logger):
    user = UserFactory()
    badge_slug = "non-existent-badge"
    # Don't create the badge

    awarded = check_and_award_badge(user, badge_slug)
    # --- FIXED: Assert is False ---
    assert awarded is False
    # --- END FIXED ---
    mock_award_points.assert_not_called()


# --- Test purchase_reward Service ---
# (No changes needed in purchase_reward tests, they don't use mocker directly here)
def test_purchase_reward_success():
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)
    result = purchase_reward(user, item.id)
    profile.refresh_from_db()
    assert profile.points == 500
    assert UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert PointLog.objects.filter(
        user=user, reason_code=PointReason.REWARD_PURCHASE, points_change=-500
    ).exists()
    assert result["item_name"] == item.name
    assert result["points_spent"] == 500
    assert result["remaining_points"] == 500


def test_purchase_reward_insufficient_points():
    user = UserFactory()
    profile = user.profile
    profile.points = 100
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)
    with pytest.raises(PurchaseError, match="Insufficient points"):
        purchase_reward(user, item.id)
    profile.refresh_from_db()
    assert profile.points == 100
    assert not UserRewardPurchase.objects.filter(user=user).exists()


def test_purchase_reward_inactive_item():
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=False)
    with pytest.raises(RewardStoreItem.DoesNotExist):
        purchase_reward(user, item.id)
    profile.refresh_from_db()
    assert profile.points == 1000


def test_purchase_reward_non_existent_item():
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    with pytest.raises(RewardStoreItem.DoesNotExist):
        purchase_reward(user, 999)
    profile.refresh_from_db()
    assert profile.points == 1000


# Fix mocker usage here
@patch("apps.gamification.services.award_points")
def test_purchase_reward_point_deduction_fails(
    mock_award_points,
):  # Remove mocker if unused
    mock_award_points.return_value = False  # Simulate award_points failure
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)

    with pytest.raises(PurchaseError, match="Failed to update points balance"):
        purchase_reward(user, item.id)

    profile.refresh_from_db()
    assert profile.points == 1000  # Points should not have changed
    assert not UserRewardPurchase.objects.filter(user=user, item=item).exists()
    # --- FIXED: Check award_points call arguments with ANY ---
    mock_award_points.assert_called_once_with(
        user=user,
        points_change=-500,
        reason_code=PointReason.REWARD_PURCHASE,
        description=ANY,  # Description can vary slightly
        related_object=item,
    )


@patch("apps.gamification.services.UserRewardPurchase.objects.create")
def test_purchase_reward_purchase_record_fails(mock_create_purchase):
    mock_create_purchase.side_effect = Exception("DB error creating purchase")
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)
    with pytest.raises(PurchaseError, match="An unexpected error occurred"):
        purchase_reward(user, item.id)
    profile.refresh_from_db()
    assert profile.points == 1000
    assert not UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert not PointLog.objects.filter(user=user).exists()
