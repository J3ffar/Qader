import pytest
from unittest.mock import patch
from django.urls import reverse

from .factories import (
    ChallengeFactory,
    UserFactory,
    QuestionFactory,
    ChallengeAttemptFactory,
)
from ..models import Challenge, ChallengeStatus, ChallengeType

pytestmark = pytest.mark.django_db

# --- List Challenges ---


def test_list_challenges_unauthenticated(api_client):
    url = reverse("api:v1:challenges:challenge-list")
    response = api_client.get(url)
    assert (
        response.status_code == 401
    )  # Assuming default is IsAuthenticatedOrReadOnly or similar


def test_list_challenges_authenticated_not_subscribed(
    authenticated_client,
):  # Uses unsubscribed user fixture
    # Create challenges for other users
    ChallengeFactory.create_batch(3)
    # Create challenges involving this user
    ChallengeFactory(challenger=authenticated_client.user)
    ChallengeFactory(opponent=authenticated_client.user)
    url = reverse("api:v1:challenges:challenge-list")
    response = authenticated_client.get(url)
    # Check if IsSubscribed permission is correctly applied (adjust if needed)
    assert (
        response.status_code == 200
    )  # Or 403 if IsSubscribed enforced strictly on list
    # If 200, check count matches *only* user's challenges
    if response.status_code == 200:
        assert response.data["count"] == 2  # Only the two the user is part of


def test_list_challenges_subscribed_user(subscribed_client):
    user = subscribed_client.user
    ChallengeFactory.create_batch(2)  # Other challenges
    c1 = ChallengeFactory(challenger=user)
    c2 = ChallengeFactory(opponent=user)
    url = reverse("api:v1:challenges:challenge-list")
    response = subscribed_client.get(url)
    assert response.status_code == 200
    assert response.data["count"] == 2
    ids = [item["id"] for item in response.data["results"]]
    assert set(ids) == {c1.id, c2.id}


def test_list_challenges_filter_by_status(subscribed_client):
    user = subscribed_client.user
    ChallengeFactory(challenger=user, status=ChallengeStatus.PENDING_INVITE)
    ChallengeFactory(challenger=user, status=ChallengeStatus.COMPLETED)
    url = reverse("api:v1:challenges:challenge-list")
    response = subscribed_client.get(url, {"status": ChallengeStatus.COMPLETED})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["status"] == ChallengeStatus.COMPLETED


# --- Create Challenge ---


@patch(
    "apps.challenges.services._get_challenge_questions", return_value=[1, 2]
)  # Mock question selection
def test_create_challenge_direct_invite(mock_get_q, subscribed_client):
    opponent = UserFactory()
    url = reverse("api:v1:challenges:challenge-list")
    data = {
        "opponent_username": opponent.username,
        "challenge_type": ChallengeType.QUICK_QUANT_10,
    }
    response = subscribed_client.post(url, data)
    assert response.status_code == 201
    assert Challenge.objects.count() == 1
    challenge = Challenge.objects.first()
    assert challenge.challenger == subscribed_client.user
    assert challenge.opponent == opponent
    assert challenge.status == ChallengeStatus.PENDING_INVITE
    assert response.data["challenger"]["username"] == subscribed_client.user.username


@patch("apps.challenges.services._get_challenge_questions", return_value=[1, 2])
@patch("apps.challenges.services._find_random_opponent")  # Mock matchmaking
def test_create_challenge_random(mock_find_opp, mock_get_q, subscribed_client):
    opponent = UserFactory()
    mock_find_opp.return_value = opponent  # Simulate finding someone
    url = reverse("api:v1:challenges:challenge-list")
    data = {"opponent_username": None, "challenge_type": ChallengeType.MEDIUM_VERBAL_15}
    post_data = {k: v for k, v in data.items() if v is not None}
    response = subscribed_client.post(url, post_data)
    assert response.status_code == 201
    challenge = Challenge.objects.first()
    assert challenge.opponent == opponent
    assert challenge.status == ChallengeStatus.ACCEPTED  # Auto-accept


def test_create_challenge_not_subscribed(authenticated_client):  # Unsubscribed user
    url = reverse("api:v1:challenges:challenge-list")
    data = {
        "opponent_username": UserFactory().username,
        "challenge_type": ChallengeType.QUICK_QUANT_10,
    }
    response = authenticated_client.post(url, data)
    assert response.status_code == 403  # Forbidden due to IsSubscribed permission


# --- Retrieve Challenge ---


def test_retrieve_challenge_participant(subscribed_client):
    challenge = ChallengeFactory(challenger=subscribed_client.user)
    url = reverse("api:v1:challenges:challenge-detail", kwargs={"pk": challenge.pk})
    response = subscribed_client.get(url)
    assert response.status_code == 200
    assert response.data["id"] == challenge.id


def test_retrieve_challenge_non_participant(subscribed_client):
    challenge = ChallengeFactory()  # Belongs to other users
    url = reverse("api:v1:challenges:challenge-detail", kwargs={"pk": challenge.pk})
    response = subscribed_client.get(url)
    # View's get_queryset filters this out -> 404
    assert response.status_code == 404


# --- Accept/Decline/Cancel Actions ---


def test_accept_challenge_action_success(subscribed_client):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-accept", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.ACCEPTED


def test_accept_challenge_action_not_opponent(subscribed_client):
    challenge = ChallengeFactory(
        status=ChallengeStatus.PENDING_INVITE
    )  # User is not opponent
    url = reverse("api:v1:challenges:challenge-accept", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 403  # Permission denied by IsInvitedOpponent


def test_decline_challenge_action_success(subscribed_client):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-decline", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.DECLINED


def test_cancel_challenge_action_success(subscribed_client):
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-cancel", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.CANCELLED


def test_cancel_challenge_action_not_challenger(subscribed_client):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-cancel", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)  # Opponent tries to cancel
    assert response.status_code == 403  # Permission denied by IsChallengeOwner


# --- Ready Action ---


@patch("apps.challenges.services.set_participant_ready")
def test_ready_action_success(mock_set_ready, subscribed_client):
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, status=ChallengeStatus.ACCEPTED
    )
    # Simulate service returning updated challenge and challenge not started yet
    mock_set_ready.return_value = (challenge, False)
    url = reverse("api:v1:challenges:challenge-ready", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 200
    assert response.data["user_status"] == "ready"
    assert response.data["challenge_started"] is False
    mock_set_ready.assert_called_once_with(challenge, subscribed_client.user)


# --- Answer Action ---


@patch("apps.challenges.services.process_challenge_answer")
def test_answer_action_success(mock_process_answer, subscribed_client):
    q1 = QuestionFactory(correct_answer="B")
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True, question_ids=[q1.id]
    )
    # Simulate service returning the attempt and challenge not ended
    mock_user_qa = MagicMock(is_correct=True)
    mock_process_answer.return_value = (mock_user_qa, False)

    url = reverse("api:v1:challenges:challenge-answer", kwargs={"pk": challenge.pk})
    data = {"question_id": q1.id, "selected_answer": "B"}
    response = subscribed_client.post(url, data)

    assert response.status_code == 200
    assert response.data["status"] == "answer_received"
    assert response.data["is_correct"] is True
    assert response.data["challenge_ended"] is False
    mock_process_answer.assert_called_once()


@patch("apps.challenges.services.process_challenge_answer")
def test_answer_action_ends_challenge(mock_process_answer, subscribed_client):
    q1 = QuestionFactory(correct_answer="A")
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True, question_ids=[q1.id]
    )
    challenge.status = (
        ChallengeStatus.COMPLETED
    )  # Simulate finalization happened in service
    # Simulate service returning attempt and challenge ended
    mock_user_qa = MagicMock(is_correct=False)
    mock_process_answer.return_value = (mock_user_qa, True)  # challenge_ended = True

    url = reverse("api:v1:challenges:challenge-answer", kwargs={"pk": challenge.pk})
    data = {"question_id": q1.id, "selected_answer": "C"}
    response = subscribed_client.post(url, data)

    assert response.status_code == 200
    assert response.data["is_correct"] is False
    assert response.data["challenge_ended"] is True
    # Check if final results are included
    assert "final_results" in response.data
    assert response.data["final_results"]["id"] == challenge.id
    assert response.data["final_results"]["status"] == ChallengeStatus.COMPLETED


def test_answer_action_invalid_data(subscribed_client):
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True, question_ids=[1]
    )
    url = reverse("api:v1:challenges:challenge-answer", kwargs={"pk": challenge.pk})
    data = {"question_id": 1}  # Missing selected_answer
    response = subscribed_client.post(url, data)
    assert response.status_code == 400
    assert "selected_answer" in response.data


# --- Results Action ---


def test_results_action_success(subscribed_client):
    challenge = ChallengeFactory(challenger=subscribed_client.user, completed_tie=True)
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.challenger, score=5, finished=True
    )
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.opponent, score=5, finished=True
    )

    url = reverse("api:v1:challenges:challenge-results", kwargs={"pk": challenge.pk})
    response = subscribed_client.get(url)
    assert response.status_code == 200
    assert response.data["id"] == challenge.id
    assert response.data["status"] == ChallengeStatus.COMPLETED
    assert response.data["winner"] is None


def test_results_action_not_completed(subscribed_client):
    challenge = ChallengeFactory(challenger=subscribed_client.user, ongoing=True)
    url = reverse("api:v1:challenges:challenge-results", kwargs={"pk": challenge.pk})
    response = subscribed_client.get(url)
    assert response.status_code == 400  # Bad request
    assert "not completed" in response.data["detail"]


# --- Rematch Action ---


@patch("apps.challenges.services.create_rematch")
def test_rematch_action_success(mock_create_rematch, subscribed_client):
    original_challenge = ChallengeFactory(
        challenger=subscribed_client.user, completed_tie=True
    )
    # Simulate service returning the new challenge
    new_challenge = ChallengeFactory(
        challenger=original_challenge.opponent, opponent=subscribed_client.user
    )
    mock_create_rematch.return_value = new_challenge

    url = reverse(
        "api:v1:challenges:challenge-rematch", kwargs={"pk": original_challenge.pk}
    )
    response = subscribed_client.post(url)

    assert response.status_code == 201  # Created
    assert response.data["id"] == new_challenge.id
    assert (
        response.data["challenger"]["username"] == original_challenge.opponent.username
    )  # New challenger
    mock_create_rematch.assert_called_once_with(
        original_challenge, subscribed_client.user
    )


def test_rematch_action_original_not_completed(subscribed_client):
    original_challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True
    )
    url = reverse(
        "api:v1:challenges:challenge-rematch", kwargs={"pk": original_challenge.pk}
    )
    response = subscribed_client.post(url)
    assert response.status_code == 400  # Bad request from service validation
    assert "Can only rematch completed challenges" in response.data["detail"][0]
