# apps/chat/tests/test_consumers_chat.py
import pytest
import json
import asyncio  # For potential delay
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from apps.chat.consumers import ChatConsumer
from apps.chat.models import Conversation, Message
from apps.users.models import UserProfile, RoleChoices
from django.contrib.auth.models import AnonymousUser


pytestmark = pytest.mark.django_db(transaction=True)


# --- Async DB Helpers ---
@database_sync_to_async
def get_profile_async(user):
    if user.is_anonymous:  # Handle AnonymousUser case
        return None
    try:
        return user.profile
    except UserProfile.DoesNotExist:  # Or related_object_does_not_exist
        return None


@database_sync_to_async
def get_or_create_conversation_async(student_profile, teacher_profile):
    # Ensure profiles are not None before passing to sync method
    if not student_profile or not teacher_profile:
        raise ValueError("Student or Teacher profile is None")
    return Conversation.get_or_create_conversation(
        student_profile=student_profile, teacher_profile=teacher_profile
    )


@database_sync_to_async
def create_message_async_test_helper(
    conversation, sender, content
):  # Renamed to avoid clash
    return Message.objects.create(
        conversation=conversation, sender=sender, content=content
    )


@database_sync_to_async
def get_all_messages_for_conversation_async(conversation):
    return list(Message.objects.filter(conversation=conversation).order_by("timestamp"))


@database_sync_to_async
def get_message_by_pk_async(pk):
    try:
        return Message.objects.get(pk=pk)
    except Message.DoesNotExist:
        return None


@database_sync_to_async
def get_unread_message_count_for_user_async(conversation, user):
    if user.is_anonymous:
        return 0
    return (
        Message.objects.filter(conversation=conversation, is_read=False)
        .exclude(sender=user)
        .count()
    )


# --- Tests ---


@pytest.mark.asyncio
async def test_student_connect_to_my_conversation(student_with_mentor, teacher_user):
    student_profile = await get_profile_async(student_with_mentor)
    teacher_profile = await get_profile_async(teacher_user)
    convo, _ = await get_or_create_conversation_async(student_profile, teacher_profile)

    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), "/ws/chat/my-conversation/"
    )
    communicator.scope["user"] = student_with_mentor
    communicator.scope["url_route"] = {
        "kwargs": {}
    }  # No conversation_id in path for student 'my-conversation'
    connected, _ = await communicator.connect()

    assert connected

    # Check for the connection_established message
    response = await communicator.receive_json_from(timeout=1)
    assert response["type"] == "connection_established"
    assert response["conversation_id"] == str(convo.pk)
    # Optionally check room group name if you send it
    # assert response['room_group_name'] == f'chat_{convo.pk}'

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_teacher_connect_to_specific_conversation(
    teacher_user, student_with_mentor
):
    student_profile = await get_profile_async(student_with_mentor)
    teacher_profile = await get_profile_async(teacher_user)
    convo, _ = await get_or_create_conversation_async(student_profile, teacher_profile)

    path = f"/ws/chat/conversations/{convo.id}/"
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), path)
    communicator.scope["user"] = teacher_user
    # Ensure the 'conversation_id' kwarg is correctly passed from the URL route simulation
    communicator.scope["url_route"] = {"kwargs": {"conversation_id": str(convo.id)}}
    connected, _ = await communicator.connect()

    assert connected

    # Check for the connection_established message
    response = await communicator.receive_json_from(timeout=1)
    assert response["type"] == "connection_established"
    assert response["conversation_id"] == str(convo.pk)

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_unauthenticated_user_connect_fails():  # Removed student_user fixture
    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), "/ws/chat/my-conversation/"
    )
    communicator.scope["user"] = AnonymousUser()
    communicator.scope["url_route"] = {"kwargs": {}}
    connected, _ = await communicator.connect()
    assert not connected
    # No explicit disconnect needed if connect fails and consumer closes connection


@pytest.mark.asyncio
async def test_student_sends_message(student_with_mentor, teacher_user):
    student_profile = await get_profile_async(student_with_mentor)
    teacher_profile = await get_profile_async(teacher_user)
    convo, _ = await get_or_create_conversation_async(student_profile, teacher_profile)

    communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), "/ws/chat/my-conversation/"
    )
    communicator.scope["user"] = student_with_mentor
    communicator.scope["url_route"] = {"kwargs": {}}
    connected, _ = await communicator.connect()
    assert connected

    # Consume the "connection_established" message first
    connection_ack = await communicator.receive_json_from(timeout=1)
    assert connection_ack["type"] == "connection_established"
    assert connection_ack["conversation_id"] == str(
        convo.pk
    )  # Verify it's the correct one

    test_message_content = "Hello Mentor from WebSocket Test!"
    await communicator.send_json_to({"message": test_message_content})

    # Now, expect the "new_message" echo
    response = await communicator.receive_json_from(timeout=2)
    assert response["type"] == "new_message"
    assert response["message"]["content"] == test_message_content
    assert response["message"]["sender"] == student_with_mentor.pk
    assert response["message"]["is_own_message"] is True

    messages = await get_all_messages_for_conversation_async(convo)
    assert len(messages) == 1, f"Expected 1 message in DB, found {len(messages)}"
    assert messages[0].content == test_message_content
    assert messages[0].sender_id == student_with_mentor.pk

    await communicator.disconnect()


@pytest.mark.asyncio
async def test_message_broadcast_to_group(student_with_mentor, teacher_user):
    student_profile = await get_profile_async(student_with_mentor)
    teacher_profile = await get_profile_async(teacher_user)
    convo, _ = await get_or_create_conversation_async(student_profile, teacher_profile)

    # Student Communicator
    student_communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), "/ws/chat/my-conversation/"
    )
    student_communicator.scope["user"] = student_with_mentor
    student_communicator.scope["url_route"] = {"kwargs": {}}
    await student_communicator.connect()
    # Consume student's connection_established ack
    student_conn_ack = await student_communicator.receive_json_from(timeout=1)
    assert student_conn_ack["type"] == "connection_established"
    assert student_conn_ack["conversation_id"] == str(convo.pk)

    # Teacher Communicator
    teacher_path = f"/ws/chat/conversations/{convo.id}/"
    teacher_communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), teacher_path)
    teacher_communicator.scope["user"] = teacher_user
    teacher_communicator.scope["url_route"] = {
        "kwargs": {"conversation_id": str(convo.id)}
    }
    await teacher_communicator.connect()
    # Consume teacher's connection_established ack
    teacher_conn_ack = await teacher_communicator.receive_json_from(timeout=1)
    assert teacher_conn_ack["type"] == "connection_established"
    assert teacher_conn_ack["conversation_id"] == str(convo.pk)

    # Student sends a message
    message_content_from_student = "Test Broadcast Message!"
    await student_communicator.send_json_to({"message": message_content_from_student})

    # Student should receive their own message back (this is the "new_message")
    student_response = await student_communicator.receive_json_from(timeout=2)
    assert student_response["type"] == "new_message"
    assert student_response["message"]["content"] == message_content_from_student
    assert student_response["message"]["is_own_message"] is True

    # Teacher should receive the student's message (this is the "new_message")
    teacher_response = await teacher_communicator.receive_json_from(timeout=2)
    assert teacher_response["type"] == "new_message"
    assert teacher_response["message"]["content"] == message_content_from_student
    assert teacher_response["message"]["sender"] == student_with_mentor.pk
    assert teacher_response["message"]["is_own_message"] is False

    await student_communicator.disconnect()
    await teacher_communicator.disconnect()


@pytest.mark.asyncio
async def test_messages_marked_as_read_on_connect(student_with_mentor, teacher_user):
    student_profile = await get_profile_async(student_with_mentor)
    teacher_profile = await get_profile_async(teacher_user)
    convo, _ = await get_or_create_conversation_async(student_profile, teacher_profile)

    # Use the test helper for creating messages
    msg1 = await create_message_async_test_helper(
        convo, teacher_user, "Unread message 1 from teacher"
    )
    msg2 = await create_message_async_test_helper(
        convo, teacher_user, "Unread message 2 from teacher"
    )
    assert (
        await get_unread_message_count_for_user_async(convo, student_with_mentor) == 2
    )

    student_communicator = WebsocketCommunicator(
        ChatConsumer.as_asgi(), "/ws/chat/my-conversation/"
    )
    student_communicator.scope["user"] = student_with_mentor
    student_communicator.scope["url_route"] = {"kwargs": {}}
    connected, _ = (
        await student_communicator.connect()
    )  # This call should trigger mark_messages_as_read_on_connect
    assert connected

    # Add a small delay to allow the database update from mark_messages_as_read_on_connect to complete
    await asyncio.sleep(0.05)

    assert (
        await get_unread_message_count_for_user_async(convo, student_with_mentor) == 0
    )

    msg1_db = await get_message_by_pk_async(msg1.pk)
    assert msg1_db is not None, "Message 1 not found in DB after connect"
    assert msg1_db.is_read is True

    msg2_db = await get_message_by_pk_async(msg2.pk)
    assert msg2_db is not None, "Message 2 not found in DB after connect"
    assert msg2_db.is_read is True

    await student_communicator.disconnect()
