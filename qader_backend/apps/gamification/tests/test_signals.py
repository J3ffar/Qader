import pytest
from unittest.mock import patch

from apps.study.tests.factories import (
    UserQuestionAttemptFactory,
    UserTestAttemptFactory,
)
from apps.study.models import UserQuestionAttempt, UserTestAttempt

pytestmark = pytest.mark.django_db


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_award_point_on_correct_question_solved(mock_update_streak, mock_award_points):
    """Verify points/streak update ONLY on correct, NEW attempts."""
    # Create a correct attempt
    attempt = UserQuestionAttemptFactory(is_correct=True)

    mock_award_points.assert_called_once()
    # Check specific args if needed: e.g., args, kwargs = mock_award_points.call_args
    # assert args[0] == attempt.user
    # assert args[1] == 1 # Points
    mock_update_streak.assert_called_once_with(attempt.user)

    # Reset mocks and save again (should NOT trigger)
    mock_award_points.reset_mock()
    mock_update_streak.reset_mock()
    attempt.save()
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_award_point_on_incorrect_question_solved(
    mock_update_streak, mock_award_points
):
    """Verify NO points/streak update on incorrect attempts."""
    UserQuestionAttemptFactory(is_correct=False)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
# @patch('apps.gamification.signals.check_and_award_badge') # Add if testing badge logic
def test_award_point_on_test_completed(mock_update_streak, mock_award_points):
    """Verify points/streak update when test status becomes COMPLETED."""
    attempt = UserTestAttemptFactory(status=UserTestAttempt.Status.STARTED)

    # Initial save (STARTED) should not trigger
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()

    # Change status to COMPLETED and save
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.save()

    mock_award_points.assert_called_once()
    # Check args if needed
    mock_update_streak.assert_called_once_with(attempt.user)
    # mock_check_badge.assert_called_once_with(attempt.user, 'first-full-test') # If simulation

    # Reset mocks and save again (COMPLETED -> COMPLETED) should NOT trigger again
    mock_award_points.reset_mock()
    mock_update_streak.reset_mock()
    attempt.save()
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()


@patch("apps.gamification.signals.award_points")
@patch("apps.gamification.signals.update_streak")
def test_award_point_on_test_not_completed(mock_update_streak, mock_award_points):
    """Verify NO points/streak update if test is not completed."""
    # Create abandoned attempt
    UserTestAttemptFactory(status=UserTestAttempt.Status.ABANDONED)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()

    # Create started attempt
    UserTestAttemptFactory(status=UserTestAttempt.Status.STARTED)
    mock_award_points.assert_not_called()
    mock_update_streak.assert_not_called()
