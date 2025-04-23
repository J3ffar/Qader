import pytest
from unittest.mock import patch
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

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

pytestmark = pytest.mark.django_db

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


@patch("apps.challenges.services._get_challenge_questions")
@patch("apps.challenges.services.logger")  # Mock logger to check messages
def test_start_challenge_direct_invite_success(mock_logger, mock_get_questions):
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
    assert challenge.question_ids == q_ids
    assert challenge.challenge_type == ChallengeType.QUICK_QUANT_10
    assert ChallengeAttempt.objects.filter(
        challenge=challenge, user=challenger
    ).exists()
    assert ChallengeAttempt.objects.filter(challenge=challenge, user=opponent).exists()
    assert opponent.username in msg
    mock_get_questions.assert_called_once()


@patch("apps.challenges.services._get_challenge_questions")
@patch("apps.challenges.services._find_random_opponent")
def test_start_challenge_random_match_success(mock_find_opponent, mock_get_questions):
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
    assert (
        challenge.status == ChallengeStatus.ACCEPTED
    )  # Assumes auto-accept for random
    assert opponent.username in msg


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


def test_accept_challenge_success():
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    opponent = challenge.opponent
    accepted_challenge = accept_challenge(challenge, opponent)
    assert accepted_challenge.status == ChallengeStatus.ACCEPTED
    assert accepted_challenge.accepted_at is not None


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


def test_decline_challenge_success():
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    opponent = challenge.opponent
    declined_challenge = decline_challenge(challenge, opponent)
    assert declined_challenge.status == ChallengeStatus.DECLINED


def test_cancel_challenge_success():
    challenge = ChallengeFactory(status=ChallengeStatus.PENDING_INVITE)
    challenger = challenge.challenger
    cancelled_challenge = cancel_challenge(challenge, challenger)
    assert cancelled_challenge.status == ChallengeStatus.CANCELLED


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


def test_set_participant_ready_first_user():
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    ChallengeAttemptFactory(challenge=challenge, user=challenger, is_ready=False)
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


def test_set_participant_ready_second_user_starts_challenge():
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    opponent = challenge.opponent
    ChallengeAttemptFactory(
        challenge=challenge, user=challenger, is_ready=True, start_time=timezone.now()
    )  # Challenger ready
    ChallengeAttemptFactory(challenge=challenge, user=opponent, is_ready=False)

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


def test_set_participant_ready_already_ready():
    challenge = ChallengeFactory(status=ChallengeStatus.ACCEPTED)
    challenger = challenge.challenger
    ChallengeAttemptFactory(
        challenge=challenge, user=challenger, is_ready=True, start_time=timezone.now()
    )  # Challenger already ready
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.opponent, is_ready=False
    )

    # Call ready again for the same user
    updated_challenge, started = set_participant_ready(challenge, challenger)

    assert started is False  # Does not start challenge
    assert updated_challenge.status == ChallengeStatus.ACCEPTED


# --- Test process_challenge_answer ---


@patch(
    "apps.challenges.services._check_and_finalize_challenge", return_value=False
)  # Mock finalization check initially
def test_process_challenge_answer_correct(mock_check_finalize):
    q1 = QuestionFactory(correct_answer="A")
    challenge = ChallengeFactory(
        ongoing=True, question_ids=[q1.id], challenge_config={"num_questions": 1}
    )
    challenger = challenge.challenger
    attempt_rec = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, ready_to_start=True, score=0
    )

    user_qa, challenge_ended = process_challenge_answer(
        challenge=challenge,
        user=challenger,
        question_id=q1.id,
        selected_answer="A",
        time_taken=30,
    )

    assert challenge_ended is False  # Mocked finalize returned False
    assert user_qa.is_correct is True
    assert user_qa.question == q1
    assert user_qa.selected_answer == "A"
    assert user_qa.mode == UserQuestionAttempt.Mode.CHALLENGE
    attempt_rec.refresh_from_db()
    assert attempt_rec.score == 1
    assert attempt_rec.question_attempts.count() == 1
    assert user_qa in attempt_rec.question_attempts.all()
    mock_check_finalize.assert_not_called()  # Finalize check happens AFTER user finishes their part


@patch(
    "apps.challenges.services._check_and_finalize_challenge", return_value=True
)  # Mock finalize check returns True
def test_process_challenge_answer_last_question_finalizes(mock_check_finalize):
    q1 = QuestionFactory(correct_answer="B")
    challenge = ChallengeFactory(
        ongoing=True, question_ids=[q1.id], challenge_config={"num_questions": 1}
    )
    challenger = challenge.challenger
    attempt_rec = ChallengeAttemptFactory(
        challenge=challenge, user=challenger, ready_to_start=True, score=0
    )

    user_qa, challenge_ended = process_challenge_answer(
        challenge=challenge,
        user=challenger,
        question_id=q1.id,
        selected_answer="C",
        time_taken=None,
    )

    # Assumes _check_and_finalize was called because user answered last question
    assert challenge_ended is True
    assert user_qa.is_correct is False
    attempt_rec.refresh_from_db()
    assert attempt_rec.score == 0
    assert attempt_rec.end_time is not None  # User finished their part
    mock_check_finalize.assert_called_once_with(challenge)


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


@patch("apps.challenges.services.award_points")
@patch("apps.challenges.services.check_and_award_badge")
def test_finalize_challenge_challenger_wins(mock_check_badge, mock_award_points):
    challenge = ChallengeFactory(ongoing=True)
    challenger = challenge.challenger
    opponent = challenge.opponent
    # Challenger scored higher
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


@patch("apps.challenges.services.award_points")
@patch("apps.challenges.services.check_and_award_badge")
def test_finalize_challenge_tie(mock_check_badge, mock_award_points):
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


# --- Test create_rematch ---


@patch("apps.challenges.services.start_challenge")
def test_create_rematch_success(mock_start_challenge):
    original_challenge = ChallengeFactory(completed_tie=True)
    challenger = original_challenge.challenger
    opponent = original_challenge.opponent
    # Simulate start_challenge returning a new challenge
    new_challenge_mock = ChallengeFactory(
        challenger=opponent, opponent=challenger
    )  # Initiator becomes challenger
    mock_start_challenge.return_value = (
        new_challenge_mock,
        "Rematch started",
        ChallengeStatus.PENDING_INVITE,
    )

    # Opponent initiates rematch
    new_challenge = create_rematch(original_challenge, opponent)

    assert new_challenge == new_challenge_mock
    mock_start_challenge.assert_called_once_with(
        challenger=opponent,  # Initiator is new challenger
        opponent=challenger,
        challenge_type=original_challenge.challenge_type,
    )


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
