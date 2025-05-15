from django.conf import settings
import pytest
from unittest.mock import patch, MagicMock, ANY, call  # Added 'call'
from django.utils import timezone
import datetime
from datetime import timedelta
from freezegun import freeze_time
from django.core.exceptions import ObjectDoesNotExist

from apps.users.models import UserProfile
from apps.users.tests.factories import UserFactory
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
)  # Added UserQuestionAttemptFactory
from apps.challenges.models import Challenge, ChallengeStatus
from apps.challenges.tests.factories import ChallengeFactory


from ..services import (
    award_points,
    update_streak,
    check_and_award_badge,
    purchase_reward,
    PurchaseError,
    PointReason,
    process_test_completion_gamification,
)
from ..models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase
from .factories import BadgeFactory, RewardStoreItemFactory, UserBadgeFactory

pytestmark = pytest.mark.django_db


# --- Test award_points Service ---
def test_award_points_success_positive():
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    points_to_add = 10
    points_awarded = award_points(
        user, points_to_add, PointReason.TEST_COMPLETED, "Completed test"
    )
    assert points_awarded == points_to_add
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
    points_awarded = award_points(
        user, points_to_subtract, PointReason.REWARD_PURCHASE, "Bought item"
    )
    assert points_awarded == points_to_subtract
    profile.refresh_from_db()
    assert profile.points == initial_points + points_to_subtract
    assert PointLog.objects.filter(user=user, points_change=points_to_subtract).exists()


def test_award_points_zero_change():
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    points_awarded = award_points(
        user, 0, PointReason.TEST_COMPLETED, "Zero point change"
    )
    assert points_awarded == 0
    profile.refresh_from_db()
    assert profile.points == initial_points
    assert not PointLog.objects.filter(user=user).exists()


def test_award_points_invalid_user():
    points_awarded = award_points(None, 10, PointReason.TEST_COMPLETED, "Test")
    assert points_awarded == 0


def test_award_points_profile_missing():
    user = UserFactory()
    UserProfile.objects.filter(user=user).delete()
    points_awarded = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert points_awarded == 0


@patch("apps.gamification.services.PointLog.objects.create")
def test_award_points_transaction_rollback_on_log_create_fail(mock_create_log):
    user = UserFactory()
    profile = user.profile
    initial_points = profile.points
    mock_create_log.side_effect = Exception("DB error on log create")
    points_awarded = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert points_awarded == 0
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
    points_awarded = award_points(user, 10, PointReason.TEST_COMPLETED, "Test")
    assert points_awarded == 0
    profile_db = UserProfile.objects.get(user=user)
    assert profile_db.points == initial_points
    assert not PointLog.objects.filter(user=user).exists()
    mock_profile.save.assert_called_once()


# --- Test update_streak Service ---
@freeze_time("2024-07-25 10:00:00")
def test_update_streak_start_new():
    user = UserFactory()
    profile = user.profile
    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 1
    assert profile.longest_streak_days == 1
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is True
    assert results["current_streak_days"] == 1
    assert results["longest_streak_days"] == 1


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()

    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 4
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is True
    assert results["current_streak_days"] == 4


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_continue_and_update_longest():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 5
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()

    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 6
    assert profile.longest_streak_days == 6
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is True
    assert results["current_streak_days"] == 6
    assert results["longest_streak_days"] == 6


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_break_streak():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 3
    profile.longest_streak_days = 5
    profile.last_study_activity_at = timezone.now() - timedelta(days=2)
    profile.save()

    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 1
    assert profile.longest_streak_days == 5
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is True
    assert results["current_streak_days"] == 1


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_same_day_first_activity():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 2
    profile.longest_streak_days = 2
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()

    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()

    assert profile.current_streak_days == 3
    assert profile.longest_streak_days == 3
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is True
    assert results["current_streak_days"] == 3


@freeze_time("2024-07-25 10:00:00")
def test_update_streak_same_day_subsequent_activity():
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 2
    profile.longest_streak_days = 2
    earlier_today = timezone.now() - timedelta(hours=2)
    profile.last_study_activity_at = earlier_today
    profile.save()

    from apps.gamification.models import StudyDayLog

    StudyDayLog.objects.create(user=user, study_date=earlier_today.date())

    frozen_now = timezone.now()
    results = update_streak(user)
    profile.refresh_from_db()

    assert profile.current_streak_days == 2
    assert profile.longest_streak_days == 2
    assert profile.last_study_activity_at == frozen_now
    assert results["streak_was_updated"] is False
    assert results["current_streak_days"] == 2


@freeze_time("2024-07-26 10:00:00")
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.check_and_award_badge")
def test_update_streak_triggers_rewards_on_hitting_milestone(
    mock_check_badge, mock_award_points
):
    user = UserFactory()
    profile = user.profile
    profile.current_streak_days = 1
    profile.longest_streak_days = 1
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()

    mock_award_points.side_effect = (
        lambda user, points_change, reason_code, description, related_object: points_change
    )
    badge_details_for_5_days = {
        "slug": settings.BADGE_SLUG_5_DAY_STREAK,
        "name": "5 Day Streak",
        "description": "...",
        "points_awarded": 0,
    }
    mock_check_badge.return_value = None

    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 2

    points_for_2_days = settings.POINTS_STREAK_BONUS_MAP.get(2, 0)
    if points_for_2_days > 0:
        mock_award_points.assert_any_call(
            user=user,
            points_change=points_for_2_days,
            reason_code=PointReason.STREAK_BONUS,
            description=ANY,
            related_object=profile,
        )
        assert results["points_awarded_for_streak_bonus"] == points_for_2_days
    else:
        called_for_streak_bonus = False
        for call_args in mock_award_points.call_args_list:
            if call_args[1].get("reason_code") == PointReason.STREAK_BONUS:
                called_for_streak_bonus = True
                break
        assert not called_for_streak_bonus
        assert results["points_awarded_for_streak_bonus"] == 0

    assert results["badges_awarded_during_streak_update"] == []

    mock_award_points.reset_mock()
    mock_check_badge.reset_mock()
    mock_check_badge.side_effect = lambda u, slug: (
        badge_details_for_5_days if slug == settings.BADGE_SLUG_5_DAY_STREAK else None
    )

    profile.current_streak_days = 4
    profile.longest_streak_days = 4
    with freeze_time("2024-07-30 10:00:00"):
        profile.last_study_activity_at = timezone.now() - timedelta(days=1)
        profile.save()
        BadgeFactory(
            slug=settings.BADGE_SLUG_5_DAY_STREAK,
            name="5 Day Streak",
            criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK,
            target_value=5,
        )

        results = update_streak(user)
        profile.refresh_from_db()
        assert profile.current_streak_days == 5

        points_for_5_days = settings.POINTS_STREAK_BONUS_MAP.get(5, 0)
        if points_for_5_days > 0:
            mock_award_points.assert_any_call(
                user=user,
                points_change=points_for_5_days,
                reason_code=PointReason.STREAK_BONUS,
                description=ANY,
                related_object=profile,
            )
            assert results["points_awarded_for_streak_bonus"] == points_for_5_days
        else:
            called_for_streak_bonus = False
            for call_args in mock_award_points.call_args_list:
                if call_args[1].get("reason_code") == PointReason.STREAK_BONUS:
                    called_for_streak_bonus = True
                    break
            assert not called_for_streak_bonus
            assert results["points_awarded_for_streak_bonus"] == 0

        mock_check_badge.assert_any_call(user, settings.BADGE_SLUG_5_DAY_STREAK)
        assert len(results["badges_awarded_during_streak_update"]) == 1
        assert (
            results["badges_awarded_during_streak_update"][0]["slug"]
            == settings.BADGE_SLUG_5_DAY_STREAK
        )


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
    profile.last_study_activity_at = timezone.now() - timedelta(days=1)
    profile.save()

    results = update_streak(user)
    profile.refresh_from_db()
    assert profile.current_streak_days == 7
    mock_award_points.assert_not_called()
    mock_check_badge.assert_not_called()
    assert results["points_awarded_for_streak_bonus"] == 0
    assert results["badges_awarded_during_streak_update"] == []


# --- Test check_and_award_badge Service ---
def test_check_award_badge_success_criteria_met_streak(mocker):
    mock_award_points = mocker.patch("apps.gamification.services.award_points")
    points_badge_earned = getattr(settings, "POINTS_BADGE_EARNED", 0)
    mock_award_points.return_value = points_badge_earned

    user = UserFactory()
    badge_slug = getattr(settings, "BADGE_SLUG_10_DAY_STREAK", "10-day-streak")
    badge = BadgeFactory(
        slug=badge_slug,
        name="10 Day Streak Master",
        description="Achieved 10 day streak",
        is_active=True,
        criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK,
        target_value=10,
    )
    profile = user.profile
    profile.current_streak_days = 10
    profile.save()

    awarded_badge_info = check_and_award_badge(user, badge_slug)

    assert awarded_badge_info is not None
    assert awarded_badge_info["slug"] == badge.slug
    assert awarded_badge_info["name"] == badge.name
    assert UserBadge.objects.filter(user=user, badge=badge).exists()

    if points_badge_earned > 0:
        mock_award_points.assert_called_once_with(
            user=user,
            points_change=points_badge_earned,
            reason_code=PointReason.BADGE_EARNED,
            description=ANY,
            related_object=ANY,
        )
        assert awarded_badge_info["points_awarded"] == points_badge_earned
        call_args_actual, call_kwargs_actual = (
            mock_award_points.call_args
        )  # Renamed to avoid conflict
        assert isinstance(call_kwargs_actual.get("related_object"), UserBadge)
        assert call_kwargs_actual.get("related_object").badge == badge
    else:
        mock_award_points.assert_not_called()
        assert awarded_badge_info["points_awarded"] == 0


def test_check_award_badge_already_earned():
    user = UserFactory()
    badge_slug = getattr(settings, "BADGE_SLUG_5_DAY_STREAK", "5-day-streak")
    badge = BadgeFactory(slug=badge_slug)
    UserBadgeFactory(user=user, badge=badge)

    profile = user.profile
    profile.current_streak_days = 5
    profile.save()

    awarded_badge_info = check_and_award_badge(user, badge_slug)
    assert awarded_badge_info is None


@patch("apps.gamification.services.award_points")
def test_check_award_badge_criteria_not_met(mock_award_points):
    user = UserFactory()
    badge_slug = getattr(settings, "BADGE_SLUG_10_DAY_STREAK", "10-day-streak")
    badge = BadgeFactory(
        slug=badge_slug,
        criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK,
        target_value=10,
    )
    profile = user.profile
    profile.current_streak_days = 9
    profile.save()

    awarded_badge_info = check_and_award_badge(user, badge_slug)
    assert awarded_badge_info is None
    assert not UserBadge.objects.filter(user=user, badge=badge).exists()
    mock_award_points.assert_not_called()


@patch("apps.gamification.services.award_points")
def test_check_award_badge_inactive_badge(mock_award_points):
    user = UserFactory()
    badge_slug = "test-badge-inactive"
    BadgeFactory(slug=badge_slug, is_active=False)

    awarded_badge_info = check_and_award_badge(user, badge_slug)
    assert awarded_badge_info is None
    mock_award_points.assert_not_called()


@patch("apps.gamification.services.award_points")
def test_check_award_badge_non_existent_badge(mock_award_points):
    user = UserFactory()
    badge_slug = "non-existent-badge"

    awarded_badge_info = check_and_award_badge(user, badge_slug)
    assert awarded_badge_info is None
    mock_award_points.assert_not_called()


def test_check_award_badge_questions_solved_correctly(mocker):
    mock_award_points = mocker.patch("apps.gamification.services.award_points")
    points_badge_earned = getattr(settings, "POINTS_BADGE_EARNED", 15)
    mock_award_points.return_value = points_badge_earned

    user = UserFactory()
    badge = BadgeFactory(
        criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY, target_value=5
    )
    for _ in range(5):
        UserQuestionAttemptFactory(
            user=user, is_correct=True
        )  # Corrected: UserQuestionAttemptFactory was missing

    awarded_info = check_and_award_badge(user, badge.slug)
    assert awarded_info is not None
    assert awarded_info["slug"] == badge.slug
    assert UserBadge.objects.filter(user=user, badge=badge).exists()
    if points_badge_earned > 0:
        mock_award_points.assert_called_once()
        assert awarded_info["points_awarded"] == points_badge_earned


def test_check_award_badge_tests_completed(mocker):
    mock_award_points = mocker.patch("apps.gamification.services.award_points")
    points_badge_earned = getattr(settings, "POINTS_BADGE_EARNED", 15)
    mock_award_points.return_value = points_badge_earned

    user = UserFactory()
    badge = BadgeFactory(
        criteria_type=Badge.BadgeCriteriaType.TESTS_COMPLETED, target_value=2
    )
    UserTestAttemptFactory.create_batch(
        2, user=user, status=UserTestAttempt.Status.COMPLETED
    )

    awarded_info = check_and_award_badge(user, badge.slug)
    assert awarded_info is not None
    assert awarded_info["slug"] == badge.slug
    assert UserBadge.objects.filter(user=user, badge=badge).exists()
    if points_badge_earned > 0:
        mock_award_points.assert_called_once()
        assert awarded_info["points_awarded"] == points_badge_earned


def test_check_award_badge_challenges_won(mocker):
    mock_award_points = mocker.patch("apps.gamification.services.award_points")
    points_badge_earned = getattr(settings, "POINTS_BADGE_EARNED", 15)
    mock_award_points.return_value = points_badge_earned

    user = UserFactory()
    badge = BadgeFactory(
        criteria_type=Badge.BadgeCriteriaType.CHALLENGES_WON, target_value=1
    )
    ChallengeFactory(winner=user, status=ChallengeStatus.COMPLETED)

    awarded_info = check_and_award_badge(user, badge.slug)
    assert awarded_info is not None
    assert awarded_info["slug"] == badge.slug
    assert UserBadge.objects.filter(user=user, badge=badge).exists()
    if points_badge_earned > 0:
        mock_award_points.assert_called_once()
        assert awarded_info["points_awarded"] == points_badge_earned


# --- Test purchase_reward Service ---
def test_purchase_reward_success():
    user = UserFactory()
    profile = user.profile
    initial_profile_points = 1000
    profile.points = initial_profile_points
    profile.save()

    item_cost = 500
    item = RewardStoreItemFactory(cost_points=item_cost, is_active=True)

    # No mock for award_points here, let the real service run
    result = purchase_reward(user, item.id)

    profile.refresh_from_db()  # Ensure we have the latest from DB

    assert UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert PointLog.objects.filter(
        user=user, reason_code=PointReason.REWARD_PURCHASE, points_change=-item_cost
    ).exists()

    assert result["item_name"] == item.name
    assert result["points_spent"] == item_cost
    assert result["remaining_points"] == initial_profile_points - item_cost
    assert profile.points == initial_profile_points - item_cost

    assert UserRewardPurchase.objects.filter(user=user, item=item).exists()
    assert result["item_name"] == item.name
    assert result["points_spent"] == item.cost_points
    assert result["remaining_points"] == profile.points


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


@patch("apps.gamification.services.award_points")
def test_purchase_reward_point_deduction_fails(mock_award_points):
    mock_award_points.return_value = 0
    user = UserFactory()
    profile = user.profile
    profile.points = 1000
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)

    with pytest.raises(PurchaseError, match="Failed to update points balance"):
        purchase_reward(user, item.id)

    profile.refresh_from_db()
    assert profile.points == 1000
    assert not UserRewardPurchase.objects.filter(user=user, item=item).exists()
    mock_award_points.assert_called_once_with(
        user=user,
        points_change=-500,
        reason_code=PointReason.REWARD_PURCHASE,
        description=ANY,
        related_object=item,
    )


@patch("apps.gamification.services.UserRewardPurchase.objects.create")
def test_purchase_reward_purchase_record_fails(mock_create_purchase):
    mock_create_purchase.side_effect = Exception("DB error creating purchase")
    user = UserFactory()
    profile = user.profile
    initial_points = 1000
    profile.points = initial_points
    profile.save()
    item = RewardStoreItemFactory(cost_points=500, is_active=True)

    # Mock award_points so the transaction for point deduction is part of what's tested
    # We expect this to be rolled back if UserRewardPurchase.objects.create fails
    with patch(
        "apps.gamification.services.award_points", wraps=award_points
    ) as mock_award_points_spy:
        with pytest.raises(PurchaseError, match="An unexpected error occurred"):
            purchase_reward(user, item.id)

        # Check that award_points was attempted
        mock_award_points_spy.assert_called_once_with(
            user=user,
            points_change=-item.cost_points,
            reason_code=PointReason.REWARD_PURCHASE,
            description=ANY,
            related_object=item,
        )

    profile.refresh_from_db()
    # Points should be rolled back to initial state due to transaction failure
    assert profile.points == initial_points
    assert not UserRewardPurchase.objects.filter(user=user, item=item).exists()
    # PointLog should also not exist if the transaction was rolled back before its creation could commit
    assert not PointLog.objects.filter(
        user=user, reason_code=PointReason.REWARD_PURCHASE
    ).exists()


# --- Test process_test_completion_gamification Service ---
@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.update_streak")
@patch("apps.gamification.services.check_and_award_badge")
def test_process_test_completion_gamification_practice_test(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):
    user = UserFactory()
    test_attempt = UserTestAttemptFactory(
        user=user,
        status=UserTestAttempt.Status.COMPLETED,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        completion_points_awarded=False,
    )
    profile = user.profile

    points_test_completed = settings.POINTS_TEST_COMPLETED
    points_streak_bonus = 5
    badge_award_points = settings.POINTS_BADGE_EARNED

    mock_award_points.side_effect = (
        lambda user, points_change, reason_code, description, related_object: points_change
    )
    mock_update_streak.return_value = {
        "streak_was_updated": True,
        "current_streak_days": 3,
        "longest_streak_days": 3,
        "points_awarded_for_streak_bonus": points_streak_bonus,
        "badges_awarded_during_streak_update": [],
    }

    test_badge_slug = "test-master"
    question_badge_slug = "question-whiz"
    BadgeFactory(
        slug=test_badge_slug,
        name="Test Master",
        criteria_type=Badge.BadgeCriteriaType.TESTS_COMPLETED,
        target_value=1,
        is_active=True,
    )
    # Create a Question badge that requires 10 correct answers
    # Note: process_test_completion_gamification relies on the *current state* of UserQuestionAttempt.
    # This test unit focuses on the service logic assuming check_and_award_badge gives correct results based on current db state.
    # The badge for questions solved will be checked. For this test, we'll assume the user *has* solved enough.
    # Actual count for questions badge would be UserQuestionAttempt.objects.filter(user=user, is_correct=True).count()
    # To make the test simpler, we control the outcome of check_and_award_badge via its mock.
    BadgeFactory(
        slug=question_badge_slug,
        name="Question Whiz",
        criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY,
        target_value=10,  # This is the target
        is_active=True,
    )
    # Simulate user having met the criteria for the question badge
    # UserQuestionAttemptFactory.create_batch(10, user=user, is_correct=True) # This would be needed if not mocking check_and_award_badge fully

    test_badge_details = {
        "slug": test_badge_slug,
        "name": "Test Master",
        "description": "...",
        "points_awarded": badge_award_points,
    }
    question_badge_details = {
        "slug": question_badge_slug,
        "name": "Question Whiz",
        "description": "...",
        "points_awarded": badge_award_points,
    }

    def check_badge_side_effect(usr, slug):
        if slug == test_badge_slug:  # User completes their first test
            return test_badge_details
        if slug == question_badge_slug:  # User has 10 correct answers overall
            return question_badge_details
        return None

    mock_check_badge.side_effect = check_badge_side_effect

    results = process_test_completion_gamification(user, test_attempt)
    test_attempt.refresh_from_db()

    assert test_attempt.completion_points_awarded is True
    expected_total_points = (
        points_test_completed + points_streak_bonus + (badge_award_points * 2)
    )
    assert results["total_points_earned"] == expected_total_points

    # Check the direct call for test completion points
    direct_test_completion_call_found = False
    for (
        acall
    ) in (
        mock_award_points.call_args_list
    ):  # Use the correct 'call' object from unittest.mock
        if (
            acall.kwargs["reason_code"] == PointReason.TEST_COMPLETED
            and acall.kwargs["related_object"] == test_attempt
        ):
            assert acall.kwargs["points_change"] == points_test_completed
            direct_test_completion_call_found = True
            break
    if points_test_completed > 0:
        assert direct_test_completion_call_found

    # Points for streak bonus are handled by update_streak's mock
    # Points for badges are handled by check_and_award_badge's mock

    mock_update_streak.assert_called_once_with(user)
    assert results["streak_info"]["was_updated"] is True
    assert results["streak_info"]["current_days"] == 3

    # Assert that check_and_award_badge was called for the relevant badge types
    # The service queries for active badges of type TESTS_COMPLETED and QUESTIONS_SOLVED_CORRECTLY
    # So, we expect calls for any badge slugs matching these criteria.
    # In our setup, this is test_badge_slug and question_badge_slug.
    mock_check_badge.assert_any_call(user, test_badge_slug)
    mock_check_badge.assert_any_call(user, question_badge_slug)
    # It might be called for other badges of these types if they exist in the db (e.g., from other tests or initial data)
    # So, let's check the count of badges that *would* be checked by the service.
    active_test_badges = Badge.objects.filter(
        is_active=True, criteria_type=Badge.BadgeCriteriaType.TESTS_COMPLETED
    ).count()
    active_question_badges = Badge.objects.filter(
        is_active=True, criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY
    ).count()
    # Streak badges are handled within update_streak, so we don't count them here for mock_check_badge direct calls from this service.

    # The number of calls to check_and_award_badge from *within* process_test_completion_gamification
    # (excluding those from update_streak which is mocked)
    # would be the sum of active badges for TESTS_COMPLETED and QUESTIONS_SOLVED_CORRECTLY.
    # This can be tricky if other tests create such badges.
    # For simplicity, we'll assume only our created badges are relevant for now.
    # If more robust checking is needed, you might clear Badge table or be more specific.

    assert len(results["badges_won_details"]) == 2
    returned_badge_slugs = {b["slug"] for b in results["badges_won_details"]}
    assert test_badge_slug in returned_badge_slugs
    assert question_badge_slug in returned_badge_slugs


@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.update_streak")
@patch("apps.gamification.services.check_and_award_badge")
def test_process_test_completion_gamification_already_processed(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):
    user = UserFactory()
    test_attempt = UserTestAttemptFactory(
        user=user,
        status=UserTestAttempt.Status.COMPLETED,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        completion_points_awarded=True,
    )
    profile = user.profile
    profile.current_streak_days = 5
    profile.save()

    results = process_test_completion_gamification(user, test_attempt)

    assert results["total_points_earned"] == 0
    assert results["badges_won_details"] == []
    assert results["streak_info"]["was_updated"] is False
    assert results["streak_info"]["current_days"] == 5

    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()
    mock_check_badge.assert_not_called()


@patch("apps.gamification.services.award_points")
@patch("apps.gamification.services.update_streak")
@patch("apps.gamification.services.check_and_award_badge")
def test_process_test_completion_level_assessment(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):
    user = UserFactory()
    test_attempt = UserTestAttemptFactory(
        user=user,
        status=UserTestAttempt.Status.COMPLETED,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        completion_points_awarded=False,
    )
    points_level_assessment = settings.POINTS_LEVEL_ASSESSMENT_COMPLETED
    mock_award_points.side_effect = (
        lambda user, points_change, reason_code, description, related_object: points_change
    )
    mock_update_streak.return_value = {
        "points_awarded_for_streak_bonus": 0,
        "badges_awarded_during_streak_update": [],
        "streak_was_updated": False,
        "current_streak_days": 1,
    }
    mock_check_badge.return_value = None

    results = process_test_completion_gamification(user, test_attempt)
    test_attempt.refresh_from_db()

    assert test_attempt.completion_points_awarded is True
    assert results["total_points_earned"] == points_level_assessment

    if points_level_assessment > 0:
        direct_level_assessment_call_found = False
        # mock_award_points.call_args_list gives a list of (args, kwargs) tuples for each call
        for acall_args, acall_kwargs in mock_award_points.call_args_list:
            if (
                acall_kwargs.get("reason_code")
                == PointReason.LEVEL_ASSESSMENT_COMPLETED
                and acall_kwargs.get("related_object") == test_attempt
            ):
                direct_level_assessment_call_found = True
                break
        assert direct_level_assessment_call_found

    mock_update_streak.assert_called_once_with(user)
