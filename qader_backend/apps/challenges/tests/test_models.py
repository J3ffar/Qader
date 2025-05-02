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
    expected_str = f"Challenge {challenge.id}: {challenge.challenger.username} vs Random/Pending (Pending Matchmaking)"
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
    # Create one attempt successfully
    ChallengeAttemptFactory(challenge=challenge, user=user)

    # Try creating another identical attempt - should fail validation
    with pytest.raises(DjangoValidationError) as excinfo:
        attempt2 = ChallengeAttempt(challenge=challenge, user=user, score=0)
        # Use full_clean() to trigger model validation including unique constraints
        attempt2.full_clean()

    # Check the structured error dictionary for the unique_together constraint violation
    assert excinfo.value.error_dict is not None
    assert (
        "__all__" in excinfo.value.error_dict
    )  # unique_together errors are typically non-field

    unique_error_found = False
    for error in excinfo.value.error_dict["__all__"]:
        # Check for the specific error code associated with unique_together
        if error.code == "unique_together":
            unique_error_found = True
            break
        # Fallback: check if message contains 'unique' if code isn't set as expected
        elif "unique" in error.message.lower():
            unique_error_found = True
            break

    assert (
        unique_error_found
    ), "Validation error for unique_together constraint not found in __all__ errors."

    # Optionally, check the parameters passed to the ValidationError message if available
    # e.g., error.params might contain the fields involved, but this can vary.
