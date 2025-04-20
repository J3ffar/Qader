# qader_backend/apps/gamification/tests/test_signals.py

import pytest
from unittest.mock import patch, call, ANY  # Import ANY
from django.conf import settings

from apps.study.tests.factories import (
    UserQuestionAttemptFactory,
    UserTestAttemptFactory,
    # Need UserFactory if creating users directly in tests
)
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from ..services import PointReason  # Import PointReason
from apps.gamification.tests.factories import BadgeFactory  # For badge test setup

pytestmark = pytest.mark.django_db

# Define expected point values for tests
POINTS_QUESTION_SOLVED = getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
POINTS_TEST_COMPLETED = getattr(settings, "POINTS_TEST_COMPLETED", 10)
POINTS_LEVEL_ASSESSMENT_COMPLETED = getattr(
    settings, "POINTS_LEVEL_ASSESSMENT_COMPLETED", 25
)


# Add mocker fixture
@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_gamify_on_correct_question_solved(
    mock_update_streak, mock_award_points, mocker
):  # Add mocker
    attempt = UserQuestionAttemptFactory(is_correct=True)
    if POINTS_QUESTION_SOLVED > 0:
        mock_award_points.assert_called_once_with(
            user=attempt.user,
            points_change=POINTS_QUESTION_SOLVED,
            reason_code=PointReason.QUESTION_SOLVED,
            description=ANY,  # Use ANY
            related_object=attempt.question,
        )
    else:
        mock_award_points.assert_not_called()
    mock_update_streak.assert_called_once_with(attempt.user)

    mock_award_points.reset_mock()
    mock_update_streak.reset_mock()
    attempt.save()
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_gamify_on_incorrect_question_solved(mock_update_streak, mock_award_points):
    UserQuestionAttemptFactory(is_correct=False)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()


# Add mocker fixture
@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
@patch("apps.gamification.signals.check_and_award_badge")
def test_gamify_on_test_completed_practice(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):  # Add mocker
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.STARTED,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        completion_points_awarded=False,
    )
    mock_award_points.assert_not_called()  # Before completion
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.save()  # Trigger completion logic

    if POINTS_TEST_COMPLETED > 0:
        mock_award_points.assert_called_once_with(
            user=attempt.user,
            points_change=POINTS_TEST_COMPLETED,
            reason_code=PointReason.TEST_COMPLETED,
            description=ANY,  # Use ANY
            related_object=attempt,
        )
    else:
        mock_award_points.assert_not_called()
    mock_update_streak.assert_called_once_with(attempt.user)
    mock_check_badge.assert_not_called()
    attempt.refresh_from_db()
    assert attempt.completion_points_awarded is True


# Add mocker fixture
@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
@patch("apps.gamification.signals.check_and_award_badge")
def test_gamify_on_test_completed_simulation(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):  # Add mocker
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.STARTED,
        attempt_type=UserTestAttempt.AttemptType.SIMULATION,
        completion_points_awarded=False,
    )
    BadgeFactory(slug="first-full-test")  # Ensure badge exists for check

    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.save()

    if POINTS_TEST_COMPLETED > 0:
        mock_award_points.assert_called_once_with(
            user=attempt.user,
            points_change=POINTS_TEST_COMPLETED,
            reason_code=PointReason.TEST_COMPLETED,
            description=ANY,  # Use ANY
            related_object=attempt,
        )
    else:
        mock_award_points.assert_not_called()
    mock_update_streak.assert_called_once_with(attempt.user)
    # Check badge call if the logic is expected to run
    mock_check_badge.assert_called_once_with(attempt.user, "first-full-test")
    attempt.refresh_from_db()
    assert attempt.completion_points_awarded is True


# Add mocker fixture
@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
@patch("apps.gamification.signals.check_and_award_badge")
def test_gamify_on_test_completed_level_assessment(
    mock_check_badge, mock_update_streak, mock_award_points, mocker
):  # Add mocker
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.STARTED,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        completion_points_awarded=False,
    )
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.save()

    if POINTS_LEVEL_ASSESSMENT_COMPLETED > 0:
        mock_award_points.assert_called_once_with(
            user=attempt.user,
            points_change=POINTS_LEVEL_ASSESSMENT_COMPLETED,
            reason_code=PointReason.LEVEL_ASSESSMENT_COMPLETED,
            description=ANY,  # Use ANY
            related_object=attempt,
        )
    else:
        mock_award_points.assert_not_called()
    mock_update_streak.assert_called_once_with(attempt.user)
    mock_check_badge.assert_not_called()
    attempt.refresh_from_db()
    assert attempt.completion_points_awarded is True


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_gamify_on_test_completed_idempotency(mock_update_streak, mock_award_points):
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.COMPLETED, completion_points_awarded=True
    )
    attempt.score_percentage = 95.5
    attempt.save()  # Save again
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()
    attempt.refresh_from_db()
    assert attempt.completion_points_awarded is True


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_gamify_on_test_status_not_completed(mock_update_streak, mock_award_points):
    UserTestAttemptFactory(status=UserTestAttempt.Status.ABANDONED)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()
    UserTestAttemptFactory(status=UserTestAttempt.Status.STARTED)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()
