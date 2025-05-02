import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.serializers import ValidationError

from .models import Challenge, ChallengeStatus, ChallengeAttempt
from .api.serializers import (
    ChallengeDetailSerializer,  # For sending full state
    ChallengeAttemptSerializer,  # For attempt updates
    ChallengeListSerializer,  # Could be useful for notifications
)
from .services import (
    set_participant_ready,
)  # Maybe call services directly? Or trigger via signals/tasks

logger = logging.getLogger(__name__)

# --- Consumer for specific Challenge Instance ---


class ChallengeConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for a specific ongoing challenge instance.
    Sends real-time updates about the challenge state to participants.
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)  # Custom code for unauthenticated
            return

        try:
            self.challenge_pk = self.scope["url_route"]["kwargs"]["challenge_pk"]
            self.challenge = await self.get_challenge(self.challenge_pk)
            self.is_participant = await self.check_participation(
                self.challenge, self.user
            )

            if not self.is_participant:
                logger.warning(
                    f"User {self.user.id} attempted to connect to challenge {self.challenge_pk} they are not part of."
                )
                await self.close(code=4003)  # Custom code for permission denied
                return

        except Challenge.DoesNotExist:
            logger.warning(
                f"User {self.user.id} attempted to connect to non-existent challenge {self.challenge_pk}."
            )
            await self.close(code=4004)  # Custom code for not found
            return
        except Exception as e:
            logger.error(
                f"Error during ChallengeConsumer connect for user {self.user.id}, challenge {self.challenge_pk}: {e}",
                exc_info=True,
            )
            await self.close(code=4000)  # Generic error
            return

        self.challenge_group_name = f"challenge_{self.challenge_pk}"

        # Join challenge group
        await self.channel_layer.group_add(self.challenge_group_name, self.channel_name)

        await self.accept()
        logger.info(
            f"User {self.user.id} connected to WebSocket for Challenge {self.challenge_pk}"
        )

        # Send initial state? Or rely on frontend fetching via REST?
        # await self.send_challenge_state()

    async def disconnect(self, close_code):
        if hasattr(self, "challenge_group_name"):
            logger.info(
                f"User {self.user.id} disconnected from WebSocket for Challenge {self.challenge_pk}. Code: {close_code}"
            )
            # Leave challenge group
            await self.channel_layer.group_discard(
                self.challenge_group_name, self.channel_name
            )
        else:
            logger.info(
                f"User (potentially unauthenticated/unvalidated) disconnected. Code: {close_code}"
            )

    # --- Incoming message handling (Optional - Primarily server-to-client) ---
    async def receive(self, text_data=None, bytes_data=None):
        """Handles messages sent FROM the client TO the server via WebSocket."""
        # Generally, complex actions like answering questions should still go via REST API
        # for validation, transaction safety, and standard processing.
        # This method could be used for simpler things like:
        # - Ping/Pong keepalives
        # - Client explicitly marking itself "ready" via WS (though REST action is safer)

        # Example: Handling a 'ready' message from client
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "mark_ready":
                # WARNING: Calling services directly from consumer bypasses DRF permissions/serializers.
                # It's often safer to trigger the existing REST endpoint from the frontend,
                # and let the service function handle broadcasting the update via group_send.
                # However, if you *must* handle it here:
                try:
                    logger.info(
                        f"Received 'mark_ready' from user {self.user.id} for challenge {self.challenge_pk}"
                    )
                    # Ensure challenge state allows this
                    if self.challenge.status != ChallengeStatus.ACCEPTED:
                        await self.send_error(
                            "Challenge not in ACCEPTED state to mark ready."
                        )
                        return
                    # Need to call the service function (make it async or use database_sync_to_async)
                    updated_challenge, started = await self.set_ready_service_call(
                        self.challenge, self.user
                    )
                    # No need to manually broadcast here if the service function already does group_send
                    # If it doesn't, you'd call group_send here.
                    await self.send_json_data(
                        {
                            "type": "ready_confirmation",
                            "status": "success",
                            "challenge_started": started,
                            "user_id": self.user.id,
                        }
                    )

                except (ValidationError, PermissionDenied) as e:
                    await self.send_error(str(e))
                except Exception as e:
                    logger.error(
                        f"Error processing 'mark_ready' for {self.user.id}, challenge {self.challenge_pk}: {e}",
                        exc_info=True,
                    )
                    await self.send_error(
                        "Internal server error processing ready status."
                    )

            # Handle other message types if needed

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format.")
        except Exception as e:
            logger.error(
                f"Error in receive for {self.user.id}, challenge {self.challenge_pk}: {e}",
                exc_info=True,
            )
            await self.send_error("Internal server error.")

    # --- Group message handlers (called by channel_layer.group_send) ---

    async def challenge_update(self, event):
        """Handles 'challenge.update' messages broadcast to the group."""
        logger.debug(
            f"Sending challenge_update event to client {self.channel_name}: {event}"
        )
        await self.send_json_data(
            {
                "type": "challenge.update",
                "payload": event["payload"],
            }
        )

    async def participant_update(self, event):
        """Handles 'participant.update' messages (e.g., ready status, score)."""
        logger.debug(
            f"Sending participant_update event to client {self.channel_name}: {event}"
        )
        await self.send_json_data(
            {
                "type": "participant.update",
                "payload": event["payload"],
            }
        )

    async def challenge_start(self, event):
        """Handles 'challenge.start' message."""
        logger.debug(
            f"Sending challenge_start event to client {self.channel_name}: {event}"
        )
        await self.send_json_data(
            {
                "type": "challenge.start",
                "payload": event["payload"],  # Might include questions, start time etc.
            }
        )

    async def answer_result(self, event):
        """Handles 'answer.result' messages (e.g., immediate feedback)."""
        logger.debug(
            f"Sending answer_result event to client {self.channel_name}: {event}"
        )
        # Only send result to the user who answered? Or both?
        # If specific user: Check event['payload']['user_id'] == self.user.id
        await self.send_json_data(
            {
                "type": "answer.result",
                "payload": event["payload"],
            }
        )

    async def challenge_end(self, event):
        """Handles 'challenge.end' message with final results."""
        logger.debug(
            f"Sending challenge_end event to client {self.channel_name}: {event}"
        )
        await self.send_json_data(
            {
                "type": "challenge.end",
                "payload": event["payload"],  # Final results from serializer
            }
        )

    async def error_message(self, event):
        """Handles broadcasting specific error messages."""
        logger.debug(
            f"Sending error_message event to client {self.channel_name}: {event}"
        )
        await self.send_json_data(
            {
                "type": "error",
                "payload": {"detail": event["message"]},
            }
        )

    # --- Helper methods ---

    @database_sync_to_async
    def get_challenge(self, pk):
        # Use select/prefetch related if needed for data sent on connect/update
        return Challenge.objects.select_related("challenger", "opponent").get(pk=pk)

    @database_sync_to_async
    def check_participation(self, challenge, user):
        return challenge.is_participant(user)

    async def send_json_data(self, data):
        """Helper to send JSON data down the WebSocket."""
        await self.send(text_data=json.dumps(data))

    async def send_error(self, message: str):
        """Helper to send a standardized error message."""
        await self.send_json_data({"type": "error", "payload": {"detail": message}})

    @database_sync_to_async
    def get_challenge_details_data(self, challenge):
        """Uses the serializer to get consistent data format."""
        # Pass context if serializer needs request (it likely doesn't for WS)
        serializer = ChallengeDetailSerializer(challenge)
        return serializer.data

    # Example of calling service (use with caution, REST endpoint is often better)
    @database_sync_to_async
    def set_ready_service_call(self, challenge, user):
        # Important: This call bypasses DRF permissions & validation layers!
        # Ensure `set_participant_ready` handles its own permission checks robustly.
        # Also, make sure `set_participant_ready` uses group_send internally.
        return set_participant_ready(challenge, user)


# --- Consumer for General User Notifications (Optional) ---


class ChallengeNotificationConsumer(AsyncWebsocketConsumer):
    """
    Handles WebSocket connections for general challenge notifications for a user
    (e.g., new invites, rematch requests).
    """

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_group_name = f"user_{self.user.id}_challenges"

        # Join user-specific group
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()
        logger.info(
            f"User {self.user.id} connected to Challenge Notifications WebSocket"
        )

    async def disconnect(self, close_code):
        if hasattr(self, "user_group_name"):
            logger.info(
                f"User {self.user.id} disconnected from Challenge Notifications WebSocket. Code: {close_code}"
            )
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    # --- Group message handlers ---
    async def new_challenge_invite(self, event):
        """Handles 'new.challenge.invite' message broadcast to the user."""
        logger.debug(
            f"Sending new_challenge_invite event to client {self.channel_name}: {event}"
        )
        await self.send(
            text_data=json.dumps(
                {
                    "type": "new_challenge_invite",
                    "payload": event["payload"],  # Likely ChallengeListSerializer data
                }
            )
        )

    async def challenge_accepted_notification(self, event):
        """Handles 'challenge.accepted.notification' message broadcast to the challenger."""
        logger.debug(
            f"Sending challenge_accepted_notification event to client {self.channel_name}: {event}"
        )
        await self.send(
            text_data=json.dumps(
                {"type": "challenge_accepted", "payload": event["payload"]}
            )
        )

    # Add handlers for declined, cancelled notifications etc.

    async def error_message(self, event):
        """Handles broadcasting specific error messages."""
        logger.debug(
            f"Sending error_message event to client {self.channel_name}: {event}"
        )
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "payload": {"detail": event["message"]},
                }
            )
        )
