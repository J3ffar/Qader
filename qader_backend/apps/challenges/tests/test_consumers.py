# qader_backend/apps/challenges/tests/test_consumers.py

import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async  # Import the wrapper
from django.contrib.auth.models import AnonymousUser

from ..consumers import ChallengeConsumer, ChallengeNotificationConsumer
from ..models import ChallengeStatus, Challenge
from .factories import ChallengeFactory, UserFactory, ChallengeAttemptFactory

# Use the ASGI application instance configured for tests
from qader_project.asgi import application  # Adjust import path if needed

pytestmark = pytest.mark.django_db(
    transaction=True
)  # Ensure transactions for async tests

# --- ChallengeConsumer Tests ---


@pytest.mark.asyncio
async def test_challenge_consumer_connect_success_participant():
    # Wrap factory calls with await database_sync_to_async
    user = await database_sync_to_async(UserFactory)()
    challenge = await database_sync_to_async(ChallengeFactory)(
        challenger=user, status=ChallengeStatus.ACCEPTED
    )

    communicator = WebsocketCommunicator(application, f"/ws/challenges/{challenge.pk}/")
    communicator.scope["user"] = user  # Authenticate the scope

    connected, subprotocol = await communicator.connect()
    assert connected
    assert subprotocol is None

    # Check if added to the correct group
    channel_layer = get_channel_layer()
    # Ensure group name is correct
    group_name = f"challenge_{challenge.pk}"
    # Check if the group exists and the channel is in it
    # Note: Direct inspection of InMemoryChannelLayer groups might vary slightly
    # A more robust check might involve sending a message and seeing if it's received
    channel_names_in_group = await channel_layer.group_channels(group_name)
    assert communicator.channel_name in channel_names_in_group

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_challenge_consumer_connect_fail_non_participant():
    user = await database_sync_to_async(UserFactory)()
    challenge = await database_sync_to_async(
        ChallengeFactory
    )()  # Belongs to other users
    communicator = WebsocketCommunicator(application, f"/ws/challenges/{challenge.pk}/")
    communicator.scope["user"] = user

    connected, subprotocol = await communicator.connect()
    assert not connected  # Connection should be rejected


@pytest.mark.asyncio
async def test_challenge_consumer_connect_fail_unauthenticated():
    challenge = await database_sync_to_async(ChallengeFactory)()
    communicator = WebsocketCommunicator(application, f"/ws/challenges/{challenge.pk}/")
    # communicator.scope['user'] = AnonymousUser() # Default is Anonymous

    connected, subprotocol = await communicator.connect()
    assert not connected


@pytest.mark.asyncio
async def test_challenge_consumer_connect_fail_not_found():
    user = await database_sync_to_async(UserFactory)()
    communicator = WebsocketCommunicator(application, "/ws/challenges/9999/")
    communicator.scope["user"] = user

    connected, subprotocol = await communicator.connect()
    assert not connected


@pytest.mark.asyncio
async def test_challenge_consumer_receive_broadcast():
    user = await database_sync_to_async(UserFactory)()
    challenge = await database_sync_to_async(ChallengeFactory)(
        challenger=user, status=ChallengeStatus.ACCEPTED
    )
    communicator = WebsocketCommunicator(application, f"/ws/challenges/{challenge.pk}/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    group_name = f"challenge_{challenge.pk}"
    test_payload = {"id": challenge.pk, "status": ChallengeStatus.ONGOING}

    await channel_layer.group_send(
        group_name,
        {
            "type": "challenge.update",
            "payload": test_payload,
        },
    )

    response = (
        await communicator.receive_json_from()
    )  # Use receive_json_from for convenience
    assert response["type"] == "challenge.update"
    assert response["payload"]["id"] == challenge.pk
    assert response["payload"]["status"] == ChallengeStatus.ONGOING

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_challenge_consumer_disconnect_cleans_group():
    user = await database_sync_to_async(UserFactory)()
    challenge = await database_sync_to_async(ChallengeFactory)(challenger=user)
    communicator = WebsocketCommunicator(application, f"/ws/challenges/{challenge.pk}/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    group_name = f"challenge_{challenge.pk}"

    # Check group membership before disconnect
    channels_before = await channel_layer.group_channels(group_name)
    assert communicator.channel_name in channels_before

    await communicator.disconnect()

    # Check group membership after disconnect
    channels_after = await channel_layer.group_channels(group_name)
    assert communicator.channel_name not in channels_after


# --- ChallengeNotificationConsumer Tests ---


@pytest.mark.asyncio
async def test_notification_consumer_connect_success():
    user = await database_sync_to_async(UserFactory)()
    communicator = WebsocketCommunicator(application, "/ws/challenges/notifications/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    # Optional: Check group membership
    channel_layer = get_channel_layer()
    user_group_name = f"user_{user.id}_challenges"
    channels_in_group = await channel_layer.group_channels(user_group_name)
    assert communicator.channel_name in channels_in_group

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_notification_consumer_connect_fail_unauthenticated():
    communicator = WebsocketCommunicator(application, "/ws/challenges/notifications/")
    connected, _ = await communicator.connect()
    assert not connected


@pytest.mark.asyncio
async def test_notification_consumer_receive_broadcast():
    user = await database_sync_to_async(UserFactory)()
    communicator = WebsocketCommunicator(application, "/ws/challenges/notifications/")
    communicator.scope["user"] = user
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    user_group_name = f"user_{user.id}_challenges"
    test_payload = {"challenge_id": 99, "challenger_username": "someone"}

    await channel_layer.group_send(
        user_group_name,
        {
            "type": "new_challenge_invite",  # Use snake_case to match consumer handler
            "payload": test_payload,
        },
    )

    response = await communicator.receive_json_from()
    assert response["type"] == "new_challenge_invite"
    assert response["payload"]["challenge_id"] == 99

    await communicator.disconnect()
