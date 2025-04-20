# qader_backend/apps/gamification/tests/test_services.py

import pytest
from unittest.mock import patch, MagicMock, ANY  # Import ANY from unittest.mock
from django.utils import timezone
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
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 1
    assert profile.longest_streak_days == 1
    assert profile.last_study_activity_at == timezone.localtime(timezone.now())


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=1)
    )
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 4
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == timezone.localtime(timezone.now())


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue_and_update_longest():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 5
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=1)
    )
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 6
    assert profile.longest_streak_days == 6
    assert profile.last_study_activity_at == timezone.localtime(timezone.now())


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_break_streak():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=2)
    )
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 1
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == timezone.localtime(timezone.now())


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_same_day():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 2
    profile.longest_streak_days = 2
    earlier_today = timezone.localtime(timezone.now() - timedelta(hours=2))
    profile.last_study_activity_at = earlier_today
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 2
    assert profile.longest_streak_days == 2
    assert profile.last_study_activity_at > earlier_today
    assert profile.last_study_activity_at == timezone.localtime(timezone.now())


# Fix mocker usage here
@freeze_time("2024-07-26 10:00:00")
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.check_and_award_badge")
def test_update_streak_triggers_rewards_on_hitting_milestone(
    mock_check_badge, mock_award_points, mocker
):  # Add mocker fixture
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 1
    profile.longest_streak_days = 1
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=1)
    )
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 2
    mock_award_points.assert_called_once_with(
        user, 5, PointReason.STREAK_BONUS, ANY, profile
    )  # Use ANY
    mock_check_badge.assert_not_called()

    mock_award_points.reset_mock()
    mock_check_badge.reset_mock()
    profile.current_streak_days = 4
    profile.longest_streak_days = 4
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=1)
    )
    profile.save()
    BadgeFactory(slug="5-day-streak")
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 5
    mock_award_points.assert_not_called()
    mock_check_badge.assert_called_once_with(user, "5-day-streak")


@freeze_time("2024-07-26 10:00:00")
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.check_and_award_badge")
def test_update_streak_does_not_trigger_rewards_if_already_past_milestone(
    mock_check_badge, mock_award_points
):
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 6
    profile.longest_streak_days = 6
    profile.last_study_activity_at = timezone.localtime(
        timezone.now() - timedelta(days=1)
    )
    profile.save()
    update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 7
    mock_award_points.assert_not_called()
    mock_check_badge.assert_not_called()


# --- Test check_and_award_badge Service ---
# Fix badge test to use a testable scenario
@patch("apps.gamification.services.logger")
@patch("apps.gamification.services.award_points")  # Also mock points awarding
def test_check_award_badge_success_criteria_met(mock_award_points, mock_logger):
    user = UserFactory()
    badge = BadgeFactory(slug="10-days-studying")  # Use a badge with logic in service
    profile = user.profile
    profile.current_streak_days = 10  # Set profile state to meet criteria
    profile.save()

    awarded = check_and_award_badge(user, "10-days-studying")

    assert awarded is True  # Now criteria should be met
    assert UserBadge.objects.filter(user=user, badge=badge).exists()
    # Check that points for earning badge were awarded
    mock_award_points.assert_called_once_with(
        user, 15, PointReason.BADGE_EARNED, ANY, badge
    )


def test_check_award_badge_already_earned():
    user = UserFactory()
    badge = BadgeFactory(slug="test-badge")
    UserBadgeFactory(user=user, badge=badge)
    awarded = check_and_award_badge(user, "test-badge")
    assert awarded is False
    assert UserBadge.objects.filter(user=user, badge=badge).count() == 1


@patch("apps.gamification.services.logger")
def test_check_award_badge_criteria_not_met(mock_logger):
    user = UserFactory()
    badge = BadgeFactory(slug="10-days-studying")  # Use badge with logic
    profile = user.profile
    profile.current_streak_days = 9  # Criteria NOT met
    profile.save()
    awarded = check_and_award_badge(user, "10-days-studying")
    assert awarded is False
    assert not UserBadge.objects.filter(user=user, badge=badge).exists()


@patch("apps.gamification.services.logger")
def test_check_award_badge_inactive_badge(mock_logger):
    user = UserFactory()
    BadgeFactory(slug="test-badge-inactive", is_active=False)
    awarded = check_and_award_badge(user, "test-badge-inactive")
    assert awarded is False


@patch("apps.gamification.services.logger")
def test_check_award_badge_non_existent_badge(mock_logger):
    user = UserFactory()
    awarded = check_and_award_badge(user, "non-existent-badge")
    assert awarded is False


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
    mock_award_points, mocker
):  # Add mocker fixture
    mock_award_points.return_value = False
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)
    with pytest.raises(PurchaseError, match="Failed to update points balance"):
        purchase_reward(user, item.id)
    assert not UserRewardPurchase.objects.filter(user=user, item=item).exists()
    mock_award_points.assert_called_once_with(
        user=user,
        points_change=-500,
        reason_code=PointReason.REWARD_PURCHASE,
        description=ANY,
        related_object=item,  # Use ANY
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
