import pytest
from unittest.mock import patch, call, ANY
from django.conf import settings
from django.utils import timezone  # For setting end_time

from apps.study.tests.factories import (
    UserQuestionAttemptFactory,
    UserTestAttemptFactory,
)
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from apps.gamification.models import Badge
from ..services import PointReason
from apps.gamification.tests.factories import BadgeFactory

pytestmark = pytest.mark.django_db

POINTS_QUESTION_SOLVED_CORRECT = getattr(
    settings, "POINTS_QUESTION_SOLVED_CORRECT", 1
)  # Use the correct setting key

# Note: The signal gamify_on_test_completed now calls process_test_completion_gamification.
# So, tests for the signal should mock process_test_completion_gamification.


@patch("apps.gamification.signals.award_points")
def test_gamify_on_correct_question_solved(mock_award_points):
    # Test creation of new attempt
    attempt = UserQuestionAttemptFactory(
        is_correct=True, test_attempt=None
    )  # Ensure created=True logic
    if POINTS_QUESTION_SOLVED_CORRECT > 0:
        mock_award_points.assert_called_once_with(
            user=attempt.user,
            points_change=POINTS_QUESTION_SOLVED_CORRECT,
            reason_code=PointReason.QUESTION_SOLVED,
            description=ANY,
            related_object=attempt.question,
        )
    else:
        mock_award_points.assert_not_called()

    # Test update of existing attempt (should not re-award)
    mock_award_points.reset_mock()
    attempt.selected_answer = "B"  # Make a change to trigger save
    attempt.save()  # This is an update, not creation
    mock_award_points.assert_not_called()


@patch("apps.gamification.signals.award_points")
def test_gamify_on_incorrect_question_solved(mock_award_points):
    UserQuestionAttemptFactory(
        is_correct=False, test_attempt=None
    )  # Ensure created=True logic
    mock_award_points.assert_not_called()


# Test the gamify_on_test_completed signal which calls process_test_completion_gamification
@patch("apps.gamification.signals.process_test_completion_gamification")
def test_signal_gamify_on_test_completed_calls_service(mock_process_gamification):
    # Create a UserTestAttempt that is initially not completed
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.STARTED,
        completion_points_awarded=False,
        end_time=None,  # Ensure end_time is None initially
    )
    mock_process_gamification.assert_not_called()  # Not called on creation or if not completed

    # Now, update the attempt to be completed
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.end_time = (
        timezone.now()
    )  # Set end_time as the service/signal expects for valid completion
    attempt.save()  # This save should trigger the signal

    mock_process_gamification.assert_called_once_with(
        user=attempt.user, test_attempt=attempt
    )
    # The service process_test_completion_gamification itself will set completion_points_awarded.
    # We don't need to check it here as we're testing the signal's call to the service.


@patch("apps.gamification.signals.process_test_completion_gamification")
def test_signal_gamify_on_test_completed_already_awarded(mock_process_gamification):
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.COMPLETED,
        completion_points_awarded=True,  # Points already awarded
        end_time=timezone.now(),
    )
    # Update some other field to trigger save, but gamification should not run again via signal
    attempt.score_percentage = 90.0
    attempt.save()
    mock_process_gamification.assert_not_called()


@patch("apps.gamification.signals.process_test_completion_gamification")
def test_signal_gamify_on_test_status_not_completed(mock_process_gamification):
    # Test with ABANDONED status
    attempt_abandoned = UserTestAttemptFactory(
        status=UserTestAttempt.Status.ABANDONED, end_time=timezone.now()
    )
    attempt_abandoned.save()  # Should not trigger
    mock_process_gamification.assert_not_called()

    # Test with STARTED status (update)
    attempt_started = UserTestAttemptFactory(status=UserTestAttempt.Status.STARTED)
    attempt_started.score_percentage = 10  # Arbitrary change
    attempt_started.save()  # Should not trigger
    mock_process_gamification.assert_not_called()


@patch("apps.gamification.signals.process_test_completion_gamification")
def test_signal_gamify_on_test_completed_no_end_time_skipped(mock_process_gamification):
    """
    Test that the signal skips gamification if status is COMPLETED but end_time is None.
    This is a heuristic in the signal to avoid premature processing.
    """
    attempt = UserTestAttemptFactory(
        status=UserTestAttempt.Status.STARTED,
        completion_points_awarded=False,
        end_time=None,
    )
    # Manually set status to COMPLETED without setting end_time to simulate the edge case
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.save()

    # The signal handler should log a warning and return, not calling process_test_completion_gamification
    mock_process_gamification.assert_not_called()
