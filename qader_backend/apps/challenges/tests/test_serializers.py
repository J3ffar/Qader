import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock

from .factories import (
    ChallengeFactory,
    UserFactory,
    QuestionFactory,
    ChallengeAttemptFactory,
)
from apps.challenges.api.serializers import (
    ChallengeListSerializer,
    ChallengeDetailSerializer,
    ChallengeCreateSerializer,
    ChallengeAnswerSerializer,
    ChallengeResultSerializer,
)
from ..models import ChallengeStatus, ChallengeType

pytestmark = pytest.mark.django_db


# Fixture for creating a mock request context needed by some serializers
@pytest.fixture
def mock_request():
    factory = APIRequestFactory()
    request = factory.get("/")  # Dummy request
    # Simulate authentication if needed by serializer context methods
    request.user = UserFactory()
    # Wrap in DRF Request object
    return Request(request)


# --- Test ChallengeCreateSerializer ---


def test_create_serializer_valid_direct_invite(mock_request):
    challenger = mock_request.user
    opponent = UserFactory(username="opponent_test")
    data = {
        "opponent_username": "opponent_test",
        "challenge_type": ChallengeType.QUICK_QUANT_10,
    }
    serializer = ChallengeCreateSerializer(data=data, context={"request": mock_request})
    assert serializer.is_valid()
    assert serializer.validated_data["opponent"] == opponent
    assert (
        "opponent_username" not in serializer.validated_data
    )  # Username removed after validation


def test_create_serializer_valid_random(mock_request):
    data = {
        "opponent_username": None,  # Explicitly None for random
        "challenge_type": ChallengeType.MEDIUM_VERBAL_15,
    }
    serializer = ChallengeCreateSerializer(data=data, context={"request": mock_request})
    assert serializer.is_valid()
    assert serializer.validated_data["opponent"] is None


def test_create_serializer_invalid_opponent(mock_request):
    data = {
        "opponent_username": "non_existent_user",
        "challenge_type": ChallengeType.QUICK_QUANT_10,
    }
    serializer = ChallengeCreateSerializer(data=data, context={"request": mock_request})
    assert not serializer.is_valid()
    assert "opponent_username" in serializer.errors
    assert "not found" in str(serializer.errors["opponent_username"])


def test_create_serializer_challenge_self(mock_request):
    challenger = mock_request.user
    data = {
        "opponent_username": challenger.username,
        "challenge_type": ChallengeType.QUICK_QUANT_10,
    }
    serializer = ChallengeCreateSerializer(data=data, context={"request": mock_request})
    assert not serializer.is_valid()
    assert "opponent_username" in serializer.errors
    assert "challenge yourself" in str(serializer.errors["opponent_username"])


def test_create_serializer_invalid_type(mock_request):
    data = {"opponent_username": None, "challenge_type": "invalid_slug"}
    serializer = ChallengeCreateSerializer(data=data, context={"request": mock_request})
    assert not serializer.is_valid()
    assert "challenge_type" in serializer.errors


# --- Test List/Detail/Result Serializers (Representation) ---


def test_challenge_list_serializer(mock_request):
    challenge = ChallengeFactory(completed_challenger_win=True)  # Challenger wins
    # Add attempts with scores
    ChallengeAttemptFactory(challenge=challenge, user=challenge.challenger, score=5)
    ChallengeAttemptFactory(challenge=challenge, user=challenge.opponent, score=3)
    mock_request.user = challenge.challenger  # Set context user

    serializer = ChallengeListSerializer(challenge, context={"request": mock_request})
    data = serializer.data

    assert data["id"] == challenge.id
    assert data["challenger"]["username"] == challenge.challenger.username
    assert data["opponent"]["username"] == challenge.opponent.username
    assert data["winner"]["username"] == challenge.challenger.username
    assert data["status"] == ChallengeStatus.COMPLETED
    assert data["user_is_participant"] is True
    assert data["user_is_winner"] is True
    assert data["user_score"] == 5
    assert data["opponent_score"] == 3


def test_challenge_list_serializer_opponent_view(mock_request):
    challenge = ChallengeFactory(completed_challenger_win=True)  # Challenger wins
    ChallengeAttemptFactory(challenge=challenge, user=challenge.challenger, score=5)
    ChallengeAttemptFactory(challenge=challenge, user=challenge.opponent, score=3)
    mock_request.user = challenge.opponent  # Set context user as opponent

    serializer = ChallengeListSerializer(challenge, context={"request": mock_request})
    data = serializer.data

    assert data["winner"]["username"] == challenge.challenger.username
    assert data["user_is_participant"] is True
    assert data["user_is_winner"] is False  # User (opponent) did not win
    assert data["user_score"] == 3  # Opponent's score
    assert (
        data["opponent_score"] == 5
    )  # Challenger's score (opponent from user's perspective)


def test_challenge_detail_serializer_ongoing_shows_questions(mock_request):
    q1, q2 = QuestionFactory.create_batch(2)
    challenge = ChallengeFactory(ongoing=True, question_ids=[q1.id, q2.id])
    challenger = challenge.challenger
    opponent = challenge.opponent
    ChallengeAttemptFactory(challenge=challenge, user=challenger, ready_to_start=True)
    ChallengeAttemptFactory(challenge=challenge, user=opponent, ready_to_start=True)
    mock_request.user = challenger  # Set context user

    serializer = ChallengeDetailSerializer(challenge, context={"request": mock_request})
    data = serializer.data

    assert data["status"] == ChallengeStatus.ONGOING
    assert "questions" in data
    assert len(data["questions"]) == 2
    assert data["questions"][0]["id"] == q1.id
    assert data["attempts"][0]["user"]["username"] == challenger.username


def test_challenge_detail_serializer_completed_hides_questions(mock_request):
    challenge = ChallengeFactory(completed_tie=True)
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.challenger, finished=True
    )
    ChallengeAttemptFactory(challenge=challenge, user=challenge.opponent, finished=True)
    mock_request.user = challenge.challenger

    serializer = ChallengeDetailSerializer(challenge, context={"request": mock_request})
    data = serializer.data

    assert data["status"] == ChallengeStatus.COMPLETED
    assert data["questions"] is None  # Questions hidden after completion in detail view


# --- Test ChallengeAnswerSerializer ---


def test_answer_serializer_valid(mock_request):
    q1 = QuestionFactory()
    challenge = ChallengeFactory(ongoing=True, question_ids=[q1.id])
    # Mock the view context needed for validation
    mock_view = MagicMock()
    mock_view.get_object.return_value = challenge
    context = {"request": mock_request, "view": mock_view}

    data = {"question_id": q1.id, "selected_answer": "A", "time_taken_seconds": 10}
    serializer = ChallengeAnswerSerializer(data=data, context=context)
    assert serializer.is_valid()


def test_answer_serializer_invalid_question_id(mock_request):
    q_other = QuestionFactory()
    challenge = ChallengeFactory(
        ongoing=True, question_ids=[QuestionFactory().id]
    )  # Different Q ID
    mock_view = MagicMock()
    mock_view.get_object.return_value = challenge
    context = {"request": mock_request, "view": mock_view}

    data = {"question_id": q_other.id, "selected_answer": "B"}
    serializer = ChallengeAnswerSerializer(data=data, context=context)
    assert not serializer.is_valid()
    assert "question_id" in serializer.errors
    assert "Invalid question ID" in str(serializer.errors["question_id"])


def test_answer_serializer_missing_answer(mock_request):
    challenge = ChallengeFactory(ongoing=True, question_ids=[QuestionFactory().id])
    mock_view = MagicMock()
    mock_view.get_object.return_value = challenge
    context = {"request": mock_request, "view": mock_view}
    data = {"question_id": challenge.question_ids[0]}  # Missing selected_answer
    serializer = ChallengeAnswerSerializer(data=data, context=context)
    assert not serializer.is_valid()
    assert "selected_answer" in serializer.errors
