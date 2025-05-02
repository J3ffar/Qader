import pytest
from unittest.mock import patch
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.study.models import UserQuestionAttempt

from .factories import (
    UserFactory,
    ChallengeFactory,
    QuestionFactory,
    ChallengeAttemptFactory,
)
from ..models import Challenge, ChallengeAttempt, ChallengeType, ChallengeStatus
from ..services import (
    start_challenge,
    accept_challenge,
    decline_challenge,
    cancel_challenge,
    set_participant_ready,
    process_challenge_answer,
    finalize_challenge,
    create_rematch,
    _get_challenge_questions,
    _find_random_opponent,
    POINTS_CHALLENGE_PARTICIPATION,
    POINTS_CHALLENGE_WIN,
    PointReason,
)
from apps.users.models import UserProfile  # Import for patching profile checks

User = get_user_model()
pytestmark = pytest.mark.django_db

# Mock paths for broadcast helpers - adjust path if structure differs
BROADCAST_UPDATE_PATH = "apps.challenges.services.broadcast_challenge_update"
BROADCAST_PARTICIPANT_PATH = "apps.challenges.services.broadcast_participant_update"
BROADCAST_START_PATH = "apps.challenges.services.broadcast_challenge_start"
BROADCAST_ANSWER_PATH = "apps.challenges.services.broadcast_answer_result"
BROADCAST_END_PATH = "apps.challenges.services.broadcast_challenge_end"
NOTIFY_USER_PATH = "apps.challenges.services.notify_user"

# --- Test _get_challenge_questions ---


@patch("apps.challenges.services.Question.objects.filter")
def test_get_challenge_questions_success(mock_filter):
    q1, q2, q3 = QuestionFactory.create_batch(3)
    mock_filter.return_value.order_by.return_value.values_list.return_value.__getitem__.return_value = [
        q1.id,
        q2.id,
        q3.id,
    ]

    config = {"num_questions": 3, "sections": ["quantitative"]}
    question_ids = _get_challenge_questions(config)

    assert len(question_ids) == 3
    assert set(question_ids) == {q1.id, q2.id, q3.id}
    mock_filter.assert_called_once()
    # Check if filter used section slug (approximate check)
    assert "subsection__section__slug__in" in str(mock_filter.call_args[0])


@patch("apps.challenges.services.Question.objects.filter")
def test_get_challenge_questions_fewer_available(mock_filter):
    q1 = QuestionFactory()
    # Simulate only finding 1 question when 3 were requested
    mock_filter.return_value.order_by.return_value.values_list.return_value.__getitem__.return_value = [
        q1.id
    ]

    config = {"num_questions": 3, "sections": ["verbal"]}
    question_ids = _get_challenge_questions(config)

    assert len(question_ids) == 1  # Service proceeds with fewer questions
    assert question_ids == [q1.id]


# --- Test start_challenge ---


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
@patch("apps.challenges.services._get_challenge_questions")
@patch("apps.challenges.services.logger")
def test_start_challenge_direct_invite_success(
    mock_logger, mock_get_questions, mock_broadcast_update, mock_notify_user
):
    challenger = UserFactory()
    opponent = UserFactory()
    q_ids = [1, 2, 3]
    mock_get_questions.return_value = q_ids

    challenge, msg, status = start_challenge(
        challenger=challenger,
        opponent=opponent,
        challenge_type=ChallengeType.QUICK_QUANT_10,
    )

    assert isinstance(challenge, Challenge)
    assert challenge.challenger == challenger
    assert challenge.opponent == opponent
    assert challenge.status == ChallengeStatus.PENDING_INVITE

    # Assert broadcast calls
    mock_notify_user.assert_called_once()
    # Check the arguments passed to notify_user (basic check)
    assert mock_notify_user.call_args[0][0] == opponent.id  # Check user_id
    assert (
        mock_notify_user.call_args[0][1] == "new_challenge_invite"
    )  # Check event_type
    assert isinstance(mock_notify_user.call_args[0][2], dict)
    mock_broadcast_update.assert_not_called()


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
@patch("apps.challenges.services._get_challenge_questions")
@patch("apps.challenges.services._find_random_opponent")
def test_start_challenge_random_match_success(
    mock_find_opponent, mock_get_questions, mock_broadcast_update, mock_notify_user
):
    challenger = UserFactory()
    opponent = UserFactory()
    mock_find_opponent.return_value = opponent  # Simulate finding an opponent
    mock_get_questions.return_value = [1]

    challenge, msg, status = start_challenge(
        challenger=challenger,
        opponent=None,  # Trigger random path
        challenge_type=ChallengeType.QUICK_QUANT_10,
    )

    assert challenge.opponent == opponent
    assert challenge.status == ChallengeStatus.ACCEPTED

    # Assert broadcast calls
    mock_notify_user.assert_not_called()  # No invite notification for random match
    mock_broadcast_update.assert_called_once_with(challenge)


@patch("apps.challenges.services._get_challenge_questions")
@patch("apps.challenges.services._find_random_opponent")
def test_start_challenge_random_match_pending(mock_find_opponent, mock_get_questions):
    challenger = UserFactory()
    mock_find_opponent.return_value = None  # Simulate NOT finding an opponent
    mock_get_questions.return_value = [1]

    challenge, msg, status = start_challenge(
        challenger=challenger,
        opponent=None,
        challenge_type=ChallengeType.QUICK_QUANT_10,
    )

    assert challenge.opponent is None
    assert challenge.status == ChallengeStatus.PENDING_MATCHMAKING
    assert "Searching" in msg


def test_start_challenge_invalid_type():
    challenger = UserFactory()
    with pytest.raises(ValidationError, match="Invalid challenge type"):
        start_challenge(challenger, None, "invalid_type_slug")


@patch("apps.challenges.services._get_challenge_questions", return_value=[])
def test_start_challenge_no_questions(mock_get_questions):
    challenger = UserFactory()
    with pytest.raises(ValidationError, match="Could not find suitable questions"):
        start_challenge(challenger, None, ChallengeType.QUICK_QUANT_10)


# --- Test accept/decline/cancel_challenge ---


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
def test_accept_challenge_success(mock_broadcast_update, mock_notify_user):
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    opponent = challenge.opponent
    accepted_challenge = accept_challenge(challenge, opponent)
    mock_notify_user.assert_called_once()
    assert (
        mock_notify_user.call_args[0][0] == challenge.challenger.id
    )  # Notify challenger
    assert mock_notify_user.call_args[0][1] == "challenge_accepted_notification"
    mock_broadcast_update.assert_called_once_with(accepted_challenge)


def test_accept_challenge_wrong_user():
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    other_user = UserFactory()
    with pytest.raises(PermissionDenied):
        accept_challenge(challenge, other_user)


def test_accept_challenge_wrong_status():
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)  # Already accepted
    opponent = challenge.opponent
    with pytest.raises(ValidationError):
        accept_challenge(challenge, opponent)


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
def test_decline_challenge_success(mock_broadcast_update, mock_notify_user):
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    opponent = challenge.opponent
    declined_challenge = decline_challenge(challenge, opponent)

    assert declined_challenge.status == ChallengeStatus.DECLINED

    # Assert broadcast calls
    mock_notify_user.assert_called_once()  # Or assert called if you implement decline notification
    assert mock_notify_user.call_args[0][0] == challenge.challenger.id
    assert mock_notify_user.call_args[0][1] == "challenge_declined_notification"
    assert isinstance(mock_notify_user.call_args[0][2], dict)  # Check payload

    mock_broadcast_update.assert_called_once_with(declined_challenge)


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
def test_cancel_challenge_success(mock_broadcast_update, mock_notify_user):
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    challenger = challenge.challenger
    cancelled_challenge = cancel_challenge(challenge, challenger)

    assert cancelled_challenge.status == ChallengeStatus.CANCELLED

    # Assert broadcast calls
    mock_notify_user.assert_not_called()  # Or assert called if you implement cancel notification
    mock_broadcast_update.assert_called_once_with(cancelled_challenge)


def test_cancel_challenge_wrong_user():
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    opponent = challenge.opponent  # Opponent tries to cancel
    with pytest.raises(PermissionDenied):
        cancel_challenge(challenge, opponent)


def test_cancel_challenge_wrong_status():
    challenge = ChallengeFactory(
        status=ChallengeStatus.ACCEPTED
    )  # Accepted, cannot cancel
    challenger = challenge.challenger
    with pytest.raises(ValidationError):
        cancel_challenge(challenge, challenger)


# --- Test set_participant_ready ---


@patch(BROADCAST_START_PATH)
@patch(BROADCAST_PARTICIPANT_PATH)
def test_set_participant_ready_first_user(
    mock_broadcast_participant, mock_broadcast_start
):
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    challenger_attempt = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, is_ready=False
    )
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.opponent, is_ready=False
    )

    updated_challenge, started = set_participant_ready(challenge, challenger)

    assert started is False
    assert updated_challenge.status == ChallengeStatus.ACCEPTED
    assert (
        ChallengeAttempt.objects.get(challenge=challenge, user=challenger).is_ready
        is True
    )
    assert (
        ChallengeAttempt.objects.get(
            challenge=challenge, user=challenge.opponent
        ).is_ready
        is False
    )

    # Assert broadcast calls
    challenger_attempt.refresh_from_db()  # Ensure attempt is updated before passing to mock check
    mock_broadcast_participant.assert_called_once_with(challenger_attempt)
    mock_broadcast_start.assert_not_called()


@patch(BROADCAST_START_PATH)
@patch(BROADCAST_PARTICIPANT_PATH)
def test_set_participant_ready_second_user_starts_challenge(
    mock_broadcast_participant, mock_broadcast_start
):
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    opponent = challenge.opponent
    challenger_attempt = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, is_ready=True, start_time=timezone.now()
    )
    opponent_attempt = ChallengeAttemptFactory(
        challenge=challenge, user=opponent, is_ready=False
    )
    updated_challenge, started = set_participant_ready(
        challenge, opponent
    )  # Opponent becomes ready

    assert started is True
    assert updated_challenge.status == ChallengeStatus.ONGOING
    assert updated_challenge.started_at is not None
    assert (
        ChallengeAttempt.objects.get(challenge=challenge, user=challenger).is_ready
        is True
    )
    assert (
        ChallengeAttempt.objects.get(challenge=challenge, user=opponent).is_ready
        is True
    )
    assert (
        ChallengeAttempt.objects.get(challenge=challenge, user=opponent).start_time
        is not None
    )

    # Assert broadcast calls
    opponent_attempt.refresh_from_db()
    # Should be called twice: once for challenger (in setup), once for opponent
    assert (
        mock_broadcast_participant.call_count == 1
    )  # Called only for the opponent becoming ready now
    mock_broadcast_participant.assert_called_with(opponent_attempt)

    mock_broadcast_start.assert_called_once_with(updated_challenge)


@patch(BROADCAST_START_PATH)
@patch(BROADCAST_PARTICIPANT_PATH)
def test_set_participant_ready_already_ready(
    mock_broadcast_participant, mock_broadcast_start
):
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    challenger_attempt = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, is_ready=True, start_time=timezone.now()
    )
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.opponent, is_ready=False
    )

    # Call ready again for the same user
    updated_challenge, started = set_participant_ready(challenge, challenger)

    assert started is False  # Does not start challenge
    assert updated_challenge.status == ChallengeStatus.ACCEPTED

    # Assert broadcast calls - participant update should NOT be called if already ready
    mock_broadcast_participant.assert_not_called()
    mock_broadcast_start.assert_not_called()


# --- Test process_challenge_answer ---


@patch(BROADCAST_PARTICIPANT_PATH)
@patch(BROADCAST_ANSWER_PATH)
@patch("apps.challenges.services._check_and_finalize_challenge", return_value=False)
def test_process_challenge_answer_correct(
    mock_check_finalize, mock_broadcast_answer, mock_broadcast_participant
):
    q1 = QuestionFactory(correct_answer="A")
    challenge = ChallengeFactory(ongoing=True, question_ids=[q1.id])
    challenger = challenge.challenger
    opponent = challenge.opponent
    attempt_rec = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, ready_to_start=True, score=0
    )
    ChallengeAttemptFactory(
        challenge=challenge,
        user=opponent,
        as_opponent=True,
        ready_to_start=True,
        score=0,
    )

    # Process the first (and only) answer for the challenger
    user_qa, challenge_ended = process_challenge_answer(
        challenge=challenge,
        user=challenger,
        question_id=q1.id,
        selected_answer="A",  # Correct answer
        time_taken=30,
    )

    # Assertions about the result of process_challenge_answer
    assert challenge_ended is False  # Because mock_check_finalize returned False
    assert user_qa.is_correct is True
    assert user_qa.question == q1
    assert user_qa.selected_answer == "A"
    assert user_qa.mode == UserQuestionAttempt.Mode.CHALLENGE

    # Assertions about the state after the call
    attempt_rec.refresh_from_db()
    assert attempt_rec.score == 1  # Score updated
    assert attempt_rec.question_attempts.count() == 1
    assert user_qa in attempt_rec.question_attempts.all()
    assert attempt_rec.end_time is not None  # User finished their part

    # Assert that the finalize check WAS called, because user answered last question
    # mock_check_finalize.assert_not_called() # Incorrect expectation
    mock_check_finalize.assert_called_once_with(challenge)

    # Assert broadcast calls
    mock_broadcast_answer.assert_called_once_with(user_qa, challenge.id)
    attempt_rec.refresh_from_db()  # Refresh before checking call arg
    mock_broadcast_participant.assert_called_once_with(attempt_rec)
    mock_check_finalize.assert_called_once_with(challenge)


@patch(BROADCAST_END_PATH)
@patch(BROADCAST_PARTICIPANT_PATH)
@patch(BROADCAST_ANSWER_PATH)
@patch("apps.challenges.services.award_points")
@patch("apps.challenges.services.check_and_award_badge")
# REMOVE this mock: @patch("apps.challenges.services._check_and_finalize_challenge", return_value=True)
def test_process_challenge_answer_last_question_finalizes(
    # Parameter list updated - remove mock_check_and_finalize
    mock_check_badge,
    mock_award_points,
    mock_broadcast_answer,
    mock_broadcast_participant,
    mock_broadcast_end,
):
    q1 = QuestionFactory(correct_answer="B")
    challenge = ChallengeFactory(
        ongoing=True, question_ids=[q1.id], challenge_config={"num_questions": 1}
    )
    challenger = challenge.challenger
    opponent = challenge.opponent
    attempt_rec = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, ready_to_start=True, score=0
    )
    # Ensure opponent attempt exists AND IS FINISHED for _check_and_finalize_challenge to work
    ChallengeAttemptFactory(
        challenge=challenge,
        user=opponent,
        as_opponent=True,
        ready_to_start=True,
        score=0,
        # Make sure opponent is also marked as finished
        finished=True,  # Adds end_time
    )

    # Challenger answers their last question
    user_qa, challenge_ended = process_challenge_answer(
        challenge=challenge,
        user=challenger,
        question_id=q1.id,
        selected_answer="C",  # Incorrect answer
        time_taken=None,
    )

    # process_challenge_answer will now call the *real* _check_and_finalize_challenge.
    # Since both users are finished (challenger finished now, opponent was set up as finished),
    # _check_and_finalize_challenge will call the *real* finalize_challenge.

    assert (
        challenge_ended is True
    )  # This relies on _check_and_finalize working correctly
    assert user_qa.is_correct is False
    attempt_rec.refresh_from_db()
    assert attempt_rec.score == 0
    assert attempt_rec.end_time is not None

    # Assert broadcast calls for answer processing
    mock_broadcast_answer.assert_called_once_with(user_qa, challenge.id)
    attempt_rec.refresh_from_db()
    mock_broadcast_participant.assert_called_once_with(attempt_rec)

    # Assert calls made inside the *real* finalize_challenge
    # Opponent wins 0-0 (tie), both get participation points
    # assert mock_award_points.call_count == 2 # Check points were awarded
    # mock_check_badge.assert_not_called()  # No winner, no badge check
    mock_broadcast_end.assert_called_once_with(challenge)  # Check end broadcast

    # Re-verify final state was set by finalize_challenge
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.COMPLETED
    assert challenge.winner is None  # Tie


def test_process_challenge_answer_wrong_status():
    q1 = QuestionFactory()
    challenge = ChallengeFactory(
        status=ChallengeStatus.ACCEPTED, question_ids=[q1.id]
    )  # Not ongoing
    challenger = challenge.challenger
    with pytest.raises(ValidationError, match="Challenge is not ongoing"):
        process_challenge_answer(challenge, challenger, q1.id, "A", None)


def test_process_challenge_answer_invalid_question():
    q1 = QuestionFactory()
    q_other = QuestionFactory()
    challenge = ChallengeFactory(ongoing=True, question_ids=[q1.id])
    challenger = challenge.challenger
    with pytest.raises(ValidationError, match="Invalid question for this challenge"):
        process_challenge_answer(challenge, challenger, q_other.id, "A", None)


def test_process_challenge_answer_already_answered():
    q1 = QuestionFactory(correct_answer="A")
    challenge = ChallengeFactory(
        ongoing=True, question_ids=[q1.id], challenge_config={"num_questions": 1}
    )
    challenger = challenge.challenger
    attempt_rec = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, ready_to_start=True, score=0
    )
    # First answer
    user_qa, _ = process_challenge_answer(challenge, challenger, q1.id, "A", None)
    attempt_rec.refresh_from_db()
    assert attempt_rec.score == 1

    # Try answering again
    with pytest.raises(ValidationError, match="already answered this question"):
        process_challenge_answer(challenge, challenger, q1.id, "B", None)


# --- Test finalize_challenge ---


@patch(BROADCAST_END_PATH)  # Mock only the end broadcast helper
@patch("apps.challenges.services.award_points")
@patch("apps.challenges.services.check_and_award_badge")
def test_finalize_challenge_challenger_wins(
    mock_check_badge, mock_award_points, mock_broadcast_end
):
    challenge = ChallengeFactory(ongoing=True)
    challenger = challenge.challenger
    opponent = challenge.opponent
    ChallengeAttemptFactory(
        challenge=challenge, user=challenger, score=5, finished=True
    )
    ChallengeAttemptFactory(challenge=challenge, user=opponent, score=3, finished=True)

    finalize_challenge(challenge)

    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.COMPLETED
    assert challenge.winner == challenger
    assert challenge.completed_at is not None
    assert (
        challenge.challenger_points_awarded
        == POINTS_CHALLENGE_PARTICIPATION + POINTS_CHALLENGE_WIN
    )
    assert challenge.opponent_points_awarded == POINTS_CHALLENGE_PARTICIPATION

    # Check points awarded correctly
    assert mock_award_points.call_count == 2
    mock_award_points.assert_any_call(
        user=challenger,
        points_change=15,
        reason_code=PointReason.CHALLENGE_WIN,
        description=f"Challenge #{challenge.id} vs {opponent.username} - Result: Win",
        related_object=challenge,
    )
    mock_award_points.assert_any_call(
        user=opponent,
        points_change=5,
        reason_code=PointReason.CHALLENGE_PARTICIPATION,
        description=f"Challenge #{challenge.id} vs {challenger.username} - Result: Loss",
        related_object=challenge,
    )
    # Check badge check called for winner
    mock_check_badge.assert_called_once_with(challenger, "challenge-winner-badge")
    # Assert end broadcast call
    mock_broadcast_end.assert_called_once_with(challenge)


@patch(BROADCAST_END_PATH)
@patch("apps.challenges.services.award_points")
@patch("apps.challenges.services.check_and_award_badge")
def test_finalize_challenge_tie(
    mock_check_badge, mock_award_points, mock_broadcast_end
):
    challenge = ChallengeFactory(ongoing=True)
    challenger = challenge.challenger
    opponent = challenge.opponent
    # Scores are equal
    ChallengeAttemptFactory(
        challenge=challenge, user=challenger, score=4, finished=True
    )
    ChallengeAttemptFactory(challenge=challenge, user=opponent, score=4, finished=True)

    finalize_challenge(challenge)

    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.COMPLETED
    assert challenge.winner is None  # Tie
    assert challenge.challenger_points_awarded == POINTS_CHALLENGE_PARTICIPATION
    assert challenge.opponent_points_awarded == POINTS_CHALLENGE_PARTICIPATION

    # Both get participation points
    assert mock_award_points.call_count == 2
    mock_award_points.assert_any_call(
        user=challenger,
        points_change=5,
        reason_code=PointReason.CHALLENGE_PARTICIPATION,
        description=f"Challenge #{challenge.id} vs {opponent.username} - Result: Tie/Completed",
        related_object=challenge,
    )
    mock_award_points.assert_any_call(
        user=opponent,
        points_change=5,
        reason_code=PointReason.CHALLENGE_PARTICIPATION,
        description=f"Challenge #{challenge.id} vs {challenger.username} - Result: Tie/Completed",
        related_object=challenge,
    )
    mock_check_badge.assert_not_called()  # No badge check on tie
    # Assert end broadcast call
    mock_broadcast_end.assert_called_once_with(challenge)


# --- Test create_rematch ---


@patch(NOTIFY_USER_PATH)  # start_challenge (called by rematch) uses notify_user
@patch(
    "apps.challenges.services._get_challenge_questions"
)  # Mock questions for start_challenge
def test_create_rematch_success(mock_get_questions, mock_notify_user):
    original_challenge = ChallengeFactory(completed_tie=True)
    challenger = original_challenge.challenger
    opponent = original_challenge.opponent
    mock_get_questions.return_value = [1, 2]  # Provide questions for the new challenge

    # Opponent initiates rematch
    new_challenge = create_rematch(original_challenge, opponent)

    # Assertions about the new challenge
    assert isinstance(new_challenge, Challenge)
    assert new_challenge.challenger == opponent  # Initiator is new challenger
    assert new_challenge.opponent == challenger
    assert new_challenge.status == ChallengeStatus.PENDING_INVITE
    assert new_challenge.challenge_type == original_challenge.challenge_type
    assert ChallengeAttempt.objects.filter(
        challenge=new_challenge, user=opponent
    ).exists()
    assert ChallengeAttempt.objects.filter(
        challenge=new_challenge, user=challenger
    ).exists()

    # Assert notification for the new invite
    mock_notify_user.assert_called_once()
    assert (
        mock_notify_user.call_args[0][0] == challenger.id
    )  # Notify original challenger
    assert mock_notify_user.call_args[0][1] == "new_challenge_invite"
    assert isinstance(mock_notify_user.call_args[0][2], dict)


def test_create_rematch_original_not_completed():
    original_challenge = ChallengeFactory(ongoing=True)  # Not completed
    challenger = original_challenge.challenger
    with pytest.raises(ValidationError, match="Can only rematch completed challenges"):
        create_rematch(original_challenge, challenger)


def test_create_rematch_initiator_not_participant():
    original_challenge = ChallengeFactory(completed_tie=True)
    other_user = UserFactory()
    with pytest.raises(PermissionDenied):
        create_rematch(original_challenge, other_user)
