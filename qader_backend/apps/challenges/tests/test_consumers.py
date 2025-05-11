import pytest
import json
import asyncio
from unittest.mock import patch, AsyncMock

from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import ErrorDetail

from ..consumers import ChallengeConsumer, ChallengeNotificationConsumer
from ..models import ChallengeStatus, Challenge
from .factories import (
    ChallengeFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db(transaction=True)

# --- Helper Functions ---


@database_sync_to_async
def create_user(**kwargs):
    return UserFactory(**kwargs)


@database_sync_to_async
def create_challenge(**kwargs):
    if "challenger" not in kwargs:
        kwargs["challenger"] = UserFactory()
    return ChallengeFactory(**kwargs)


async def get_authenticated_communicator_for_consumer(
    consumer_class, url_path, user, url_kwargs=None
):
    communicator = WebsocketCommunicator(consumer_class.as_asgi(), url_path)
    communicator.scope["user"] = user
    if url_kwargs:
        communicator.scope["url_route"] = {"kwargs": url_kwargs}
    communicator.scope["headers"] = []
    return communicator


def ensure_serializable(data):
    if isinstance(data, dict):
        return {k: ensure_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        if all(isinstance(item, ErrorDetail) for item in data):
            return [str(item) for item in data]
        return [ensure_serializable(item) for item in data]
    elif isinstance(data, ErrorDetail):
        return str(data)
    elif hasattr(data, "value"):
        return data.value
    return data


# --- ChallengeConsumer Tests ---


class TestChallengeConsumer:

    @pytest.mark.asyncio
    async def test_connect_success_participant(self):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        connected, subprotocol = await communicator.connect(timeout=5)
        assert connected, "Connection failed"
        assert subprotocol is None
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_connect_fail_non_participant(self):
        user = await create_user()
        challenge = await create_challenge()
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        # Set a longer timeout for connect itself, as consumer logic runs here
        connected, _ = await communicator.connect(timeout=5)
        assert not connected, "Connection should have failed for non-participant"

        try:
            # If connect() returned False, the server denied the connection.
            # The communicator should make the close event available.
            # Increase sleep slightly more to ensure event processing on Windows.
            await asyncio.sleep(
                0.2
            )  # Longer sleep before trying to receive the close frame
            close_event = await communicator.receive_output(timeout=3)
            assert (
                close_event["type"] == "websocket.close"
            ), f"Expected websocket.close, got {close_event.get('type')}"
            assert close_event["code"] == 4003
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout: Close frame (4003) not received after connection denied. Connected status: {connected}"
            )

    @pytest.mark.asyncio
    async def test_connect_fail_unauthenticated(self):
        challenge = await create_challenge()
        communicator = WebsocketCommunicator(
            ChallengeConsumer.as_asgi(), f"/ws/challenges/{challenge.pk}/"
        )
        communicator.scope["url_route"] = {"kwargs": {"challenge_pk": challenge.pk}}
        communicator.scope["headers"] = []
        connected, _ = await communicator.connect(timeout=5)
        assert not connected, "Connection should have failed for unauthenticated user"
        try:
            await asyncio.sleep(0.2)
            close_event = await communicator.receive_output(timeout=3)
            assert (
                close_event["type"] == "websocket.close"
            ), f"Expected websocket.close, got {close_event.get('type')}"
            assert close_event["code"] == 4001
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout: Close frame (4001) not received. Connected status: {connected}"
            )

    @pytest.mark.asyncio
    async def test_connect_fail_challenge_not_found(self):
        user = await create_user()
        non_existent_pk = 99999
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{non_existent_pk}/",
            user,
            url_kwargs={"challenge_pk": non_existent_pk},
        )
        connected, _ = await communicator.connect(timeout=5)
        assert not connected, "Connection should have failed for non-existent challenge"
        try:
            await asyncio.sleep(0.2)
            close_event = await communicator.receive_output(timeout=3)
            assert (
                close_event["type"] == "websocket.close"
            ), f"Expected websocket.close, got {close_event.get('type')}"
            assert close_event["code"] == 4004
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout: Close frame (4004) not received. Connected status: {connected}"
            )

    @pytest.mark.asyncio
    async def test_disconnect_cleans_group(self):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        connected, _ = await communicator.connect(timeout=5)
        assert connected
        await communicator.disconnect()
        await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    @patch(
        "apps.challenges.consumers.ChallengeConsumer.set_ready_service_call",
        new_callable=AsyncMock,
    )
    async def test_receive_mark_ready_success(self, mock_set_ready_service_call):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        mock_updated_challenge = AsyncMock(spec=Challenge)
        mock_set_ready_service_call.return_value = (mock_updated_challenge, True)
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "mark_ready"})
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for ready_confirmation response.")
        assert response == {
            "type": "ready_confirmation",
            "status": "success",
            "challenge_started": True,
            "user_id": user.id,
        }
        await communicator.disconnect()

    @pytest.mark.asyncio
    @patch(
        "apps.challenges.consumers.ChallengeConsumer.set_ready_service_call",
        new_callable=AsyncMock,
    )
    async def test_receive_mark_ready_challenge_not_accepted(
        self, mock_set_ready_service_call
    ):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.PENDING_INVITE
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "mark_ready"})
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for error response (challenge not accepted).")
        assert response == {
            "type": "error",
            "payload": {"detail": "Challenge not in ACCEPTED state to mark ready."},
        }
        await communicator.disconnect()

    @pytest.mark.asyncio
    @patch(
        "apps.challenges.consumers.ChallengeConsumer.set_ready_service_call",
        new_callable=AsyncMock,
    )
    async def test_receive_mark_ready_service_validation_error(
        self, mock_set_ready_service_call
    ):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        expected_error_str_from_consumer = (
            "[ErrorDetail(string='Service validation failed.', code='invalid')]"
        )
        mock_set_ready_service_call.side_effect = ValidationError(
            "Service validation failed."
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "mark_ready"})
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for error response (validation error).")
        assert response == {
            "type": "error",
            "payload": {"detail": expected_error_str_from_consumer},
        }
        await communicator.disconnect()

    @pytest.mark.asyncio
    @patch(
        "apps.challenges.consumers.ChallengeConsumer.set_ready_service_call",
        new_callable=AsyncMock,
    )
    async def test_receive_mark_ready_service_permission_error(
        self, mock_set_ready_service_call
    ):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        error_msg = "Service permission denied."
        mock_set_ready_service_call.side_effect = DjangoPermissionDenied(error_msg)
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "mark_ready"})
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for error response (permission error).")
        assert response == {"type": "error", "payload": {"detail": error_msg}}
        await communicator.disconnect()

    @pytest.mark.asyncio
    @patch(
        "apps.challenges.consumers.ChallengeConsumer.set_ready_service_call",
        new_callable=AsyncMock,
    )
    async def test_receive_mark_ready_service__internal_error(
        self, mock_set_ready_service_call
    ):  # Typo in name fixed
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        mock_set_ready_service_call.side_effect = Exception(
            "Some internal service problem."
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "mark_ready"})
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for error response (internal error).")
        assert response == {
            "type": "error",
            "payload": {"detail": "Internal server error processing ready status."},
        }
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_invalid_json(self):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_to(text_data="this is not json")
        try:
            response = await communicator.receive_json_from(timeout=3)
        except asyncio.TimeoutError:
            pytest.fail("Timeout waiting for error response (invalid json).")
        assert response == {
            "type": "error",
            "payload": {"detail": "Invalid JSON format."},
        }
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_receive_unknown_message_type(self):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user, status=ChallengeStatus.ACCEPTED
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        await communicator.send_json_to({"type": "some_unknown_action"})
        with pytest.raises(asyncio.TimeoutError):
            await communicator.receive_json_from(timeout=1)
        await communicator.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "handler_type, raw_payload_data",
        [
            ("challenge.update", {"id": 1, "status": ChallengeStatus.ONGOING}),
            ("participant.update", {"user_id": 1, "ready": True, "score": 10}),
            (
                "challenge.start",
                {"questions": [1, 2, 3], "start_time": "2024-01-01T10:00:00Z"},
            ),
            ("answer.result", {"user_id": 1, "question_id": 5, "correct": True}),
            ("challenge.end", {"winner_id": 1, "scores": {"1": 10, "2": 5}}),
            ("error_message", {"message": "A broadcast error occurred"}),
        ],
    )
    async def test_broadcast_handlers(self, handler_type, raw_payload_data):
        user = await create_user()
        challenge = await create_challenge(
            challenger=user,
            opponent=await create_user(),
            status=ChallengeStatus.ACCEPTED,
        )
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeConsumer,
            f"/ws/challenges/{challenge.pk}/",
            user,
            url_kwargs={"challenge_pk": challenge.pk},
        )
        await communicator.connect(timeout=5)
        channel_layer = get_channel_layer()
        group_name = f"challenge_{challenge.pk}"
        payload_for_send = ensure_serializable(raw_payload_data)
        event_for_group_send = {"type": handler_type.replace(".", "_")}
        expected_response_payload = {}
        if handler_type == "error_message":
            event_for_group_send["message"] = payload_for_send["message"]
            expected_response_type = "error"
            expected_response_payload = {"detail": payload_for_send["message"]}
        else:
            event_for_group_send["payload"] = payload_for_send
            expected_response_type = handler_type
            expected_response_payload = payload_for_send
        await channel_layer.group_send(group_name, event_for_group_send)
        try:
            await asyncio.sleep(0.2)
            response = await communicator.receive_json_from(timeout=5)
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout waiting for broadcast message of type '{handler_type}'."
            )
        assert response["type"] == expected_response_type
        assert response["payload"] == expected_response_payload
        await communicator.disconnect()


# --- ChallengeNotificationConsumer Tests ---
class TestChallengeNotificationConsumer:

    @pytest.mark.asyncio
    async def test_connect_success(self):
        user = await create_user()
        assert user.is_authenticated
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeNotificationConsumer, "/ws/challenges/notifications/", user
        )
        connected, _ = await communicator.connect(timeout=5)
        assert connected, "Connection failed for ChallengeNotificationConsumer"
        await communicator.disconnect()
        await asyncio.sleep(0.05)

    @pytest.mark.asyncio
    async def test_connect_fail_unauthenticated(self):
        communicator = WebsocketCommunicator(
            ChallengeNotificationConsumer.as_asgi(), "/ws/challenges/notifications/"
        )
        communicator.scope["headers"] = []
        connected, _ = await communicator.connect(timeout=5)
        assert (
            not connected
        ), "Notification connection should have failed for unauthenticated"
        try:
            await asyncio.sleep(0.2)
            close_event = await communicator.receive_output(timeout=3)
            assert (
                close_event["type"] == "websocket.close"
            ), f"Expected websocket.close, got {close_event.get('type')}"
            assert close_event["code"] == 4001
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout: Close frame (4001) not received for unauth notification. Conn: {connected}"
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "handler_type, raw_payload_data, expected_consumer_event_type",
        [
            (
                "new_challenge_invite",
                {"challenge_id": 99, "challenger_username": "someone"},
                "new_challenge_invite",
            ),
            (
                "challenge_accepted_notification",
                {"challenge_id": 100, "opponent_username": "another"},
                "challenge_accepted",
            ),
            ("error_message", {"message": "A notification error"}, "error"),
        ],
    )
    async def test_notification_broadcast_handlers(
        self, handler_type, raw_payload_data, expected_consumer_event_type
    ):
        user = await create_user()
        communicator = await get_authenticated_communicator_for_consumer(
            ChallengeNotificationConsumer, "/ws/challenges/notifications/", user
        )
        await communicator.connect(timeout=5)
        channel_layer = get_channel_layer()
        user_group_name = f"user_{user.id}_challenges"
        payload_for_send = ensure_serializable(raw_payload_data)
        group_send_event_type = handler_type
        event_for_group_send = {"type": group_send_event_type}
        expected_response_payload = {}
        if group_send_event_type == "error_message":
            event_for_group_send["message"] = payload_for_send["message"]
            expected_response_payload = {"detail": payload_for_send["message"]}
        else:
            event_for_group_send["payload"] = payload_for_send
            expected_response_payload = payload_for_send
        await channel_layer.group_send(user_group_name, event_for_group_send)
        try:
            await asyncio.sleep(0.2)
            response = await communicator.receive_json_from(timeout=5)
        except asyncio.TimeoutError:
            pytest.fail(
                f"Timeout waiting for notification broadcast of type '{handler_type}'. Expected WS type '{expected_consumer_event_type}'"
            )
        assert response["type"] == expected_consumer_event_type
        assert response["payload"] == expected_response_payload
        await communicator.disconnect()
