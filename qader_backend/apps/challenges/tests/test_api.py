import pytest
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone

from apps.study.models import UserQuestionAttempt
from apps.users.models import UserProfile

from .factories import (
    ChallengeFactory,
    UserFactory,
    QuestionFactory,
    ChallengeAttemptFactory,
)
from ..models import Challenge, ChallengeStatus, ChallengeType
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.django_db

# Mock paths for broadcast helpers used by services called from views
BROADCAST_UPDATE_PATH = "apps.challenges.services.broadcast_challenge_update"
BROADCAST_PARTICIPANT_PATH = "apps.challenges.services.broadcast_participant_update"
BROADCAST_START_PATH = "apps.challenges.services.broadcast_challenge_start"
BROADCAST_ANSWER_PATH = "apps.challenges.services.broadcast_answer_result"
BROADCAST_END_PATH = "apps.challenges.services.broadcast_challenge_end"
NOTIFY_USER_PATH = "apps.challenges.services.notify_user"

# --- List Challenges ---


@patch(BROADCAST_START_PATH)
@patch(BROADCAST_PARTICIPANT_PATH)
@patch("apps.challenges.api.views.set_participant_ready")
def test_ready_action_success(
    mock_set_ready_service,
    mock_broadcast_participant,
    mock_broadcast_start,
    subscribed_client,
):
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, status=ChallengeStatus.ACCEPTED
    )
    # Need the attempt object to verify broadcast call argument
    challenger_attempt = ChallengeAttemptFactory(
        challenge=challenge, user=challenge.challenger, is_ready=False
    )
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.opponent, as_opponent=True, is_ready=False
    )

    # Simulate service return value
    challenge.status = (
        ChallengeStatus.ACCEPTED
    )  # Ensure status is correct before passing
    mock_set_ready_service.return_value = (
        challenge,
        False,
    )  # Simulate challenge not starting yet

    url = reverse("api:v1:challenges:challenge-ready", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    assert response.data.get("user_status") == "ready"
    assert response.data.get("challenge_started") is False

    # Verify the service was called
    mock_set_ready_service.assert_called_once_with(challenge, subscribed_client.user)
    # Broadcasts happen *inside* the service, so we don't check them directly here if mocking the service
    # If we *don't* mock the service, then we check the broadcast mocks:
    # mock_broadcast_participant.assert_called_once_with(challenger_attempt)
    # mock_broadcast_start.assert_not_called()


@patch(BROADCAST_PARTICIPANT_PATH)
@patch(BROADCAST_ANSWER_PATH)
@patch("apps.challenges.api.views.process_challenge_answer")
def test_answer_action_success(
    mock_process_answer_service,
    mock_broadcast_answer,
    mock_broadcast_participant,
    subscribed_client,
):
    q1 = QuestionFactory(correct_answer="B")
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True, question_ids=[q1.id]
    )
    # Setup attempts if needed by serializer in view/permissions
    ChallengeAttemptFactory(
        challenge=challenge, user=challenge.challenger, ready_to_start=True
    )
    ChallengeAttemptFactory(
        challenge=challenge,
        user=challenge.opponent,
        as_opponent=True,
        ready_to_start=True,
    )

    # Simulate service return: (user_question_attempt_instance, challenge_ended_flag)
    mock_user_qa = MagicMock(
        spec=UserQuestionAttempt,
        is_correct=True,
        user_id=subscribed_client.user.id,
        question_id=q1.id,
    )
    mock_process_answer_service.return_value = (
        mock_user_qa,
        False,
    )  # Challenge not ended

    url = reverse("api:v1:challenges:challenge-answer", kwargs={"pk": challenge.pk})
    data = {"question_id": q1.id, "selected_answer": "B", "time_taken_seconds": 15}
    response = subscribed_client.post(url, data)

    assert response.status_code == 200
    assert response.data.get("is_correct") is True
    assert response.data.get("challenge_ended") is False

    # Verify the service call
    mock_process_answer_service.assert_called_once_with(
        challenge=challenge,
        user=subscribed_client.user,
        question_id=data["question_id"],
        selected_answer=data["selected_answer"],
        time_taken=data["time_taken_seconds"],
    )
    # Broadcasts happen *inside* the service
    # If not mocking the service:
    # mock_broadcast_answer.assert_called_once()
    # mock_broadcast_participant.assert_called_once()


@patch("apps.challenges.api.views.process_challenge_answer")
def test_answer_action_ends_challenge(mock_process_answer, subscribed_client):
    q1 = QuestionFactory(correct_answer="A")
    challenge = ChallengeFactory(
        challenger=subscribed_client.user,
        status=ChallengeStatus.ONGOING,  # Set status directly
        question_ids=[q1.id],
    )
    # Ensure attempts exist and ready
    opponent = challenge.opponent
    ChallengeAttemptFactory(
        challenge=challenge,
        user=challenge.challenger,
        is_ready=True,
        start_time=timezone.now(),
    )
    ChallengeAttemptFactory(
        challenge=challenge, user=opponent, is_ready=True, start_time=timezone.now()
    )

    # Simulate service returns: (attempt_instance, challenge_ended_flag)
    mock_user_qa = MagicMock(spec=UserQuestionAttempt, is_correct=False)
    mock_process_answer.return_value = (mock_user_qa, True)  # Simulate challenge ending

    url = reverse("api:v1:challenges:challenge-answer", kwargs={"pk": challenge.pk})
    data = {"question_id": q1.id, "selected_answer": "C", "time_taken_seconds": 20}
    response = subscribed_client.post(url, data)

    assert (
        response.status_code == 200
    ), f"Expected 200, got {response.status_code}. Response: {response.data}"
    assert response.data.get("is_correct") is False
    # The assertion below should now pass because the mock call will work correctly
    assert response.data.get("challenge_ended") is True

    # Verify mock was called correctly
    mock_process_answer.assert_called_once_with(
        challenge=challenge,
        user=subscribed_client.user,
        question_id=data["question_id"],
        selected_answer=data["selected_answer"],
        time_taken=data["time_taken_seconds"],
    )


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


@patch(NOTIFY_USER_PATH)
@patch("apps.challenges.api.views.create_rematch")
def test_rematch_action_success(
    mock_create_rematch_service, mock_notify_user, subscribed_client
):
    opponent_user = UserFactory()
    original_challenge = ChallengeFactory(
        challenger=subscribed_client.user, opponent=opponent_user, completed_tie=True
    )  # completed_tie sets status=COMPLETED
    # Ensure attempts exist if needed
    ChallengeAttemptFactory(
        challenge=original_challenge, user=original_challenge.challenger
    )
    ChallengeAttemptFactory(
        challenge=original_challenge, user=original_challenge.opponent
    )

    # Simulate service returning the new challenge
    mock_new_challenge_instance = Challenge(
        id=999,
        challenger=subscribed_client.user,
        opponent=opponent_user,
        challenge_type=original_challenge.challenge_type,
        status=ChallengeStatus.PENDING_INVITE,
        challenge_config=original_challenge.challenge_config,
        question_ids=[1, 2, 3],
    )
    # Add necessary related fields if serializer needs them
    mock_new_challenge_instance.challenger.profile = UserProfile.objects.get(
        user=subscribed_client.user
    )
    mock_new_challenge_instance.opponent.profile = UserProfile.objects.get(
        user=opponent_user
    )

    mock_create_rematch_service.return_value = mock_new_challenge_instance

    url = reverse(
        "api:v1:challenges:challenge-rematch", kwargs={"pk": original_challenge.pk}
    )
    response = subscribed_client.post(url)

    assert response.status_code == 201
    assert response.data["id"] == mock_new_challenge_instance.id

    # Verify the service call
    mock_create_rematch_service.assert_called_once_with(
        original_challenge, subscribed_client.user
    )
    # Notification happens inside start_challenge called by create_rematch
    # If not mocking create_rematch service:
    # mock_notify_user.assert_called_once()


def test_rematch_action_original_not_completed(subscribed_client):
    original_challenge = ChallengeFactory(
        challenger=subscribed_client.user, ongoing=True
    )
    url = reverse(
        "api:v1:challenges:challenge-rematch", kwargs={"pk": original_challenge.pk}
    )
    response = subscribed_client.post(url)
    assert response.status_code == 400  # Bad request from service validation
    assert "detail" in response.data
    # Check the specific error message string
    assert "Can only rematch completed challenges" in str(response.data["detail"])


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
    assert response.status_code == 403


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


@patch(NOTIFY_USER_PATH)
@patch(BROADCAST_UPDATE_PATH)
def test_accept_challenge_action_success(
    mock_broadcast_update, mock_notify_user, subscribed_client
):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-accept", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.ACCEPTED

    # Verify broadcasts were triggered by the service called by the view
    mock_notify_user.assert_called_once()
    mock_broadcast_update.assert_called_once_with(challenge)


def test_accept_challenge_action_not_opponent(subscribed_client):
    challenge = ChallengeFactory(
        status=ChallengeStatus.PENDING_INVITE
    )  # User is not opponent
    url = reverse("api:v1:challenges:challenge-accept", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)
    assert response.status_code == 404  # Permission denied by IsInvitedOpponent


@patch(NOTIFY_USER_PATH)  # Mock even if not expecting call, to isolate
@patch(BROADCAST_UPDATE_PATH)
def test_decline_challenge_action_success(
    mock_broadcast_update, mock_notify_user, subscribed_client
):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-decline", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.DECLINED

    # Verify broadcasts were triggered
    mock_notify_user.assert_called_once()  # Assuming no notification on decline
    assert mock_notify_user.call_args[0][0] == challenge.challenger.id
    assert mock_notify_user.call_args[0][1] == "challenge_declined_notification"
    mock_broadcast_update.assert_called_once_with(challenge)


@patch(NOTIFY_USER_PATH)  # Mock even if not expecting call
@patch(BROADCAST_UPDATE_PATH)
def test_cancel_challenge_action_success(
    mock_broadcast_update, mock_notify_user, subscribed_client
):
    challenge = ChallengeFactory(
        challenger=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-cancel", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)

    assert response.status_code == 200
    challenge.refresh_from_db()
    assert challenge.status == ChallengeStatus.CANCELLED

    # Verify broadcasts were triggered
    mock_notify_user.assert_not_called()  # Assuming no notification on cancel
    mock_broadcast_update.assert_called_once_with(challenge)


def test_cancel_challenge_action_not_challenger(subscribed_client):
    challenge = ChallengeFactory(
        opponent=subscribed_client.user, status=ChallengeStatus.PENDING_INVITE
    )
    url = reverse("api:v1:challenges:challenge-cancel", kwargs={"pk": challenge.pk})
    response = subscribed_client.post(url)  # Opponent tries to cancel
    assert response.status_code == 403  # Permission denied by IsChallengeOwner


# --- Ready Action ---
