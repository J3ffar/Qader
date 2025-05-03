from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.study.models import ConversationSession, ConversationMessage, Question
from apps.study.api.serializers.conversation import (
    AIQuestionResponseSerializer,
    ConversationSessionListSerializer,
    ConversationSessionDetailSerializer,
    ConversationSessionCreateSerializer,
    ConversationMessageSerializer,
    ConversationUserMessageInputSerializer,
    ConfirmUnderstandingSerializer,
    ConversationTestQuestionSerializer,
    ConversationTestSubmitSerializer,
    ConversationTestResultSerializer,
)
from apps.study import conversation_service
from apps.api.permissions import IsSubscribed  # Import the permission class
from apps.learning.models import Question  # Ensure Question model is available
from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter

import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=["Study - Conversational Learning"])
class ConversationViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing Learning via Conversation sessions.

    Provides endpoints to:
    - Start a new conversation session.
    - List existing sessions for the user.
    - Retrieve details and message history of a specific session.
    - Send messages to the AI within a session.
    - Indicate understanding of a concept ('Got It').
    - Submit answers to test questions presented during the conversation.
    """

    serializer_class = ConversationSessionDetailSerializer  # Default for retrieve
    permission_classes = [
        IsAuthenticated,
        IsSubscribed,
    ]  # Must be logged in and subscribed

    def get_queryset(self):
        """Only return sessions belonging to the current user."""
        return ConversationSession.objects.filter(
            user=self.request.user
        ).prefetch_related("messages", "messages__related_question")

    def get_serializer_class(self):
        """Return appropriate serializer class based on action."""
        action_map = {
            "list": ConversationSessionListSerializer,
            "create": ConversationSessionCreateSerializer,
            "send_message": ConversationUserMessageInputSerializer,  # Input
            "confirm_understanding": ConversationTestQuestionSerializer,  # Output
            "submit_test_answer": ConversationTestSubmitSerializer,  # Input
            "ask_question": None,  # No input serializer needed
            # Add other actions if needed
        }
        if self.action in action_map:
            return action_map[self.action]
        # Default (retrieve) uses self.serializer_class
        return super().get_serializer_class()

    @extend_schema(
        summary="Start a New Conversation Session",
        request=ConversationSessionCreateSerializer,
        responses={201: ConversationSessionDetailSerializer},
    )
    def create(self, request, *args, **kwargs):
        """Starts a new conversation session for the logged-in user."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save(user=request.user)
        logger.info(
            f"User {request.user.username} started conversation session {session.id} with tone {session.ai_tone}"
        )
        # Return the detailed view of the newly created session
        output_serializer = ConversationSessionDetailSerializer(
            session, context=self.get_serializer_context()
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="List User's Conversation Sessions")
    def list(self, request, *args, **kwargs):
        """Retrieves a list of conversation sessions for the current user."""
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Retrieve Conversation Session Details")
    def retrieve(self, request, *args, **kwargs):
        """Retrieves details and message history for a specific conversation session."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Send Message to AI",
        request=ConversationUserMessageInputSerializer,
        responses={
            201: ConversationMessageSerializer,  # Returns the AI's response message
            400: {"description": "Session completed or invalid input."},
            403: {"description": "Usage limit exceeded or permission denied."},
            500: {"description": "Internal server error / AI unavailable."},
            503: {"description": "AI service unavailable."},
        },
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="Conversation Session ID",
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="messages")
    def send_message(self, request, pk=None):
        """Sends a user message within a session and gets the AI's response."""
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_serializer = self.get_serializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        user_message_text = input_serializer.validated_data["message_text"]
        # Ensure related_question object is fetched if ID is provided
        related_question_instance = input_serializer.validated_data.get(
            "related_question_id"
        )

        user = request.user

        # *** Usage Limit Check ***
        try:
            limiter = UsageLimiter(user)
            limiter.check_can_send_conversation_message()
        except UsageLimitExceeded as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:  # Handle potential limiter init errors
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            return Response(
                {"detail": "Could not verify account limits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            with transaction.atomic():
                # 1. Save user message
                user_msg = ConversationMessage.objects.create(
                    session=session,
                    sender_type=ConversationMessage.SenderType.USER,
                    message_text=user_message_text,
                    related_question=related_question_instance,  # Save FK instance
                )
                logger.info(
                    f"User message saved (ID: {user_msg.id}) for session {session.id}"
                )

                # Update session context if user explicitly linked a question
                if (
                    related_question_instance
                    and session.current_topic_question != related_question_instance
                ):
                    session.current_topic_question = related_question_instance
                    session.save(update_fields=["current_topic_question", "updated_at"])
                    logger.info(
                        f"Session {session.id} context updated to question {related_question_instance.id}"
                    )

                # 2. Get AI response (call service layer)
                ai_response_text = conversation_service.get_ai_response(
                    session, user_message_text
                )

                # Handle potential service unavailability messages from the service layer
                if (
                    "unavailable" in ai_response_text.lower()
                    or "issue communicating" in ai_response_text.lower()
                ):
                    # Don't save this as a message, return error to user
                    status_code = (
                        status.HTTP_503_SERVICE_UNAVAILABLE
                        if "unavailable" in ai_response_text.lower()
                        else status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    return Response({"detail": ai_response_text}, status=status_code)

                # 3. Save AI response
                ai_msg = ConversationMessage.objects.create(
                    session=session,
                    sender_type=ConversationMessage.SenderType.AI,
                    message_text=ai_response_text,
                    # related_question is typically null here unless AI explicitly asks one
                )
                logger.info(
                    f"AI response message saved (ID: {ai_msg.id}) for session {session.id}"
                )

            # 4. Return the AI message using the correct serializer
            output_serializer = ConversationMessageSerializer(
                ai_msg, context=self.get_serializer_context()
            )
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:  # Catch broader exceptions during the process
            logger.exception(f"Error processing message for session {session.id}: {e}")
            return Response(
                {"detail": _("An error occurred while processing your message.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # --- NEW ACTION ---
    @extend_schema(
        summary="Ask AI to Provide a Question",
        request=None,  # No request body needed
        responses={
            200: AIQuestionResponseSerializer,
            400: {"description": "Session completed or cannot find question."},
            403: {"description": "Usage limit exceeded or permission denied."},
            404: {"description": "Could not find a suitable question."},
            500: {"description": "Internal server error."},
            503: {"description": "AI service unavailable."},
        },
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="Conversation Session ID",
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="ask-question")
    def ask_question(self, request, pk=None):
        """Requests the AI to select and ask a relevant question with a cheer message."""
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        # *** Usage Limit Check ***
        try:
            limiter = UsageLimiter(user)
            limiter.check_can_ask_ai_question()  # Use the new check method
        except UsageLimitExceeded as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            return Response(
                {"detail": "Could not verify account limits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            # Call the service function to generate the question and message
            response_data = conversation_service.generate_ai_question_and_message(
                session, user
            )

            # Use the specific response serializer
            serializer = AIQuestionResponseSerializer(
                response_data, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            logger.warning(f"ask_question failed for session {session.id}: {e}")
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except (
            ValueError
        ) as e:  # Catch explicit ValueErrors from service (e.g., AI unavailable)
            logger.error(f"ask_question value error for session {session.id}: {e}")
            return Response(
                {"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.exception(f"Error during ask_question for session {session.id}: {e}")
            return Response(
                {"detail": _("An error occurred while asking for a question.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Confirm Understanding ('Got It')",
        request=None,  # No request body needed, uses session context
        responses={
            200: ConversationTestQuestionSerializer,  # Returns the test question
            204: None,  # No Content if no test question is generated
            400: {"detail": "Error message"},
        },
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="Conversation Session ID",
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="confirm-understanding")
    def confirm_understanding(self, request, pk=None):
        """
        User confirms understanding of the current topic. Triggers a test question.
        Relies on `current_topic_question` being set in the session context.
        """
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_question = session.current_topic_question
        if not original_question:
            logger.warning(
                f"'Got It' clicked for session {session.id} but no current_topic_question set."
            )
            return Response(
                {
                    "detail": _(
                        "No specific topic context found to test. Please discuss a question first."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Select a test question based on the original concept/skill
        test_question = conversation_service.select_test_question_for_concept(
            original_question, request.user
        )

        if not test_question:
            logger.info(
                f"No suitable test question found after 'Got It' for session {session.id}, original Q {original_question.id}."
            )
            # Optionally send an AI message saying "Great! Let's move on." or similar
            # For now, return No Content to indicate success but no test follows
            return Response(status=status.HTTP_204_NO_CONTENT)

        # Return the selected test question for the frontend to display
        serializer = ConversationTestQuestionSerializer(
            test_question, context=self.get_serializer_context()
        )
        logger.info(
            f"Presenting test question {test_question.id} to user {request.user.username} for session {session.id}"
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Submit Answer to Conversation Test",
        request=ConversationTestSubmitSerializer,
        responses={200: ConversationTestResultSerializer},
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="Conversation Session ID",
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="submit-test-answer")
    def submit_test_answer(self, request, pk=None):
        """Submits the user's answer to the test question presented after 'Got It'."""
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        test_question = serializer.validated_data["question_id"]
        selected_answer = serializer.validated_data["selected_answer"]

        # try:
        #     test_question = Question.objects.get(pk=question_id)
        # except Question.DoesNotExist:
        #     return Response(
        #         {"detail": _("Test question not found.")},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )

        try:
            # Record the attempt and update stats via service layer
            attempt = conversation_service.record_conversation_test_attempt(
                user=request.user,
                session=session,
                test_question=test_question,
                selected_answer=selected_answer,
            )

            # Return the detailed result
            result_serializer = ConversationTestResultSerializer(
                attempt, context=self.get_serializer_context()
            )
            return Response(result_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error submitting conversation test answer for session {session.id}, question {question_id}: {e}",
                exc_info=True,
            )
            return Response(
                {"detail": _("An error occurred while submitting your answer.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    # Optional: Add an action to explicitly end a session
    @extend_schema(
        summary="End Conversation Session",
        request=None,
        responses={200: {"detail": "Session ended successfully."}},
        parameters=[
            OpenApiParameter(
                name="id",
                location=OpenApiParameter.PATH,
                description="Conversation Session ID",
                required=True,
                type=OpenApiTypes.INT,
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="end-session")
    def end_session_action(self, request, pk=None):
        """Explicitly marks a conversation session as completed."""
        session = self.get_object()
        session.end_session()
        logger.info(
            f"User {request.user.username} explicitly ended conversation session {session.id}"
        )
        return Response(
            {"detail": _("Session ended successfully.")}, status=status.HTTP_200_OK
        )
