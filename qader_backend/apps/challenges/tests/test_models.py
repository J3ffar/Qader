import pytest
from django.core.exceptions import ValidationError as DjangoValidationError

from .factories import (
    ChallengeFactory,
    ChallengeAttemptFactory,
    UserFactory,
    QuestionFactory,
)
from ..models import Challenge, ChallengeStatus, ChallengeAttempt

pytestmark = pytest.mark.django_db


def test_challenge_str():
    challenger = UserFactory(username="challenger1")
    opponent = UserFactory(username="opponent1")
    challenge = ChallengeFactory(
        challenger=challenger, opponent=opponent, status=ChallengeStatus.ONGOING
    )
    expected_str = f"Challenge {challenge.id}: challenger1 vs opponent1 (Ongoing)"
    assert str(challenge) == expected_str


def test_challenge_str_no_opponent():
    challenge = ChallengeFactory(random_pending=True)  # Use trait
    expected_str = f"Challenge {challenge.id}: {challenge.challenger.username} vs Pending Random/Invite (Pending Matchmaking)"
    print(f"Expected: {expected_str}")  # Add print statements for debugging
    print(f"Actual:   {str(challenge)}")
    assert str(challenge) == expected_str


def test_challenge_attempt_str():
    challenge = ChallengeFactory()
    attempt = ChallengeAttemptFactory(
        challenge=challenge, user=challenge.challenger, score=3
    )
    expected_str = f"Attempt by {challenge.challenger.username} for Challenge {challenge.id} (Score: 3)"
    assert str(attempt) == expected_str


def test_challenge_is_participant():
    challenger = UserFactory()
    opponent = UserFactory()
    other_user = UserFactory()
    challenge = ChallengeFactory(challenger=challenger, opponent=opponent)

    assert challenge.is_participant(challenger) is True
    assert challenge.is_participant(opponent) is True
    assert challenge.is_participant(other_user) is False


def test_challenge_num_questions():
    q1, q2, q3 = QuestionFactory.create_batch(3)
    challenge = ChallengeFactory(question_ids=[q1.id, q2.id, q3.id])
    assert challenge.num_questions == 3

    challenge_no_q = ChallengeFactory(question_ids=[])
    assert challenge_no_q.num_questions == 0


def test_challenge_get_questions_queryset_order():
    q1, q2, q3 = QuestionFactory.create_batch(3)
    # Deliberately non-sequential order
    challenge = ChallengeFactory(question_ids=[q2.id, q3.id, q1.id])
    question_queryset = challenge.get_questions_queryset()

    assert list(question_queryset.values_list("id", flat=True)) == [q2.id, q3.id, q1.id]


def test_challenge_attempt_unique_together():
    """Test the unique constraint on ChallengeAttempt."""
    challenge = ChallengeFactory()
    user = challenge.challenger
    # Create one attempt
    ChallengeAttemptFactory(challenge=challenge, user=user)
    # Try creating another identical attempt - should fail
    with pytest.raises(DjangoValidationError) as excinfo:
        # Use full_clean to trigger model validation including unique constraints
        attempt2 = ChallengeAttempt(challenge=challenge, user=user, score=0)
        attempt2.full_clean()
    # Check if the error message contains the constraint name or relevant fields
    # Note: Exact message might vary slightly depending on DB backend
    assert (
        "unique constraint" in str(excinfo.value).lower()
        or "already exists" in str(excinfo.value).lower()
    )
