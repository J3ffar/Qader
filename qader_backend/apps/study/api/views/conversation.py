from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.core.exceptions import ObjectDoesNotExist

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    Question,
    UserQuestionAttempt,
)
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
from apps.study.services import conversation
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
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_serializer = ConversationUserMessageInputSerializer(
            data=request.data
        )  # Use specific input serializer
        input_serializer.is_valid(raise_exception=True)
        user_message_text = input_serializer.validated_data["message_text"]
        related_question_instance = input_serializer.validated_data.get(
            "related_question_id"
        )
        user = request.user

        # *** Usage Limit Check (keep existing) ***
        try:
            limiter = UsageLimiter(user)
            limiter.check_can_send_conversation_message()
        except UsageLimitExceeded as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            return Response(
                {"detail": "Could not verify account limits."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # --- Core Logic ---
        try:
            current_question = session.current_topic_question  # Get context Q
            ai_response_data = {}  # To store structured response from service

            # Use a single transaction block for user message, AI call (read-only part),
            # potential attempt saving, and AI message saving.
            with transaction.atomic():
                # 1. Save user message
                user_msg = ConversationMessage.objects.create(
                    session=session,
                    sender_type=ConversationMessage.SenderType.USER,
                    message_text=user_message_text,
                    related_question=related_question_instance,
                )
                logger.info(
                    f"User message saved (ID: {user_msg.id}) for session {session.id}"
                )

                # Update session context if user explicitly linked a different question
                if (
                    related_question_instance
                    and current_question != related_question_instance
                ):
                    session.current_topic_question = related_question_instance
                    session.save(update_fields=["current_topic_question", "updated_at"])
                    current_question = (
                        related_question_instance  # Update local variable
                    )
                    logger.info(
                        f"Session {session.id} context updated by user message to question {current_question.id}"
                    )

                # 2. Call AI Service to process message and get structured response
                ai_response_data = conversation.process_user_message_with_ai(
                    session=session,
                    user_message_text=user_message_text,
                    current_topic_question=current_question,  # Pass context
                )

                # Check for critical AI errors indicated by the response structure/text
                if (
                    "unavailable" in ai_response_data["feedback_text"].lower()
                    or "couldn't connect" in ai_response_data["feedback_text"].lower()
                ):
                    # Don't save AI message, return error directly
                    # Use raise Exception to rollback transaction if needed, or handle differently
                    # For now, return response, transaction will commit user message.
                    logger.warning(
                        f"AI Service unavailable/error during processing for session {session.id}. AI Response: {ai_response_data}"
                    )
                    return Response(
                        {"detail": ai_response_data["feedback_text"]},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )

                # 3. Conditionally Save UserQuestionAttempt based on AI interpretation
                if (
                    ai_response_data.get("processed_as_answer")
                    and ai_response_data.get("user_choice")
                    and current_question
                ):
                    submitted_choice = ai_response_data["user_choice"]
                    logger.info(
                        f"AI processed message as answer '{submitted_choice}' for Q {current_question.id}. Saving attempt."
                    )
                    try:
                        # Use update_or_create for idempotency within the session context
                        attempt, created = UserQuestionAttempt.objects.update_or_create(
                            user=user,
                            question=current_question,
                            conversation_session=session,
                            defaults={
                                "selected_answer": submitted_choice,
                                "mode": UserQuestionAttempt.Mode.CONVERSATION,
                                "attempted_at": timezone.now(),
                                "is_correct": None,  # Let model calculate
                            },
                        )
                        # We don't strictly *need* the result here unless logging correctness
                        # attempt.refresh_from_db(fields=['is_correct'])
                        logger.info(
                            f"{'Created' if created else 'Updated'} UserQuestionAttempt {attempt.id} based on AI interpretation."
                        )
                    except Exception as attempt_err:
                        # Log error but continue to save AI message and return feedback
                        logger.error(
                            f"Failed to save UserQuestionAttempt for session {session.id}, Q {current_question.id} despite AI indicating answer. Error: {attempt_err}",
                            exc_info=True,
                        )
                        # Modify feedback slightly?
                        ai_response_data["feedback_text"] += _(
                            " (Note: There was an issue recording this attempt.)"
                        )

                # 4. Save AI response message (always happens if AI call didn't critically fail)
                ai_msg = ConversationMessage.objects.create(
                    session=session,
                    sender_type=ConversationMessage.SenderType.AI,
                    message_text=ai_response_data["feedback_text"],
                    # related_question is null here, message is feedback/response
                )
                logger.info(
                    f"AI response message saved (ID: {ai_msg.id}) for session {session.id}"
                )

            # 5. Return the saved AI message
            output_serializer = ConversationMessageSerializer(
                ai_msg, context=self.get_serializer_context()
            )
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:  # Catch broader exceptions during the whole process
            logger.exception(f"Error processing message for session {session.id}: {e}")
            return Response(
                {"detail": _("An error occurred while processing your message.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
            response_data = conversation.generate_ai_question_and_message(session, user)

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
        test_question = conversation.select_test_question_for_concept(
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
        responses={
            200: ConversationTestResultSerializer,
            400: {"description": "Session completed or invalid input."},
            404: {"description": "Question not found."},
            500: {"description": "Internal server error."},
            503: {"description": "AI service unavailable (for feedback generation)."},
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
    @action(detail=True, methods=["post"], url_path="submit-test-answer")
    def submit_test_answer(self, request, pk=None):
        """
        Submits the user's answer to the test question presented after 'Got It'.
        Records the attempt, gets AI feedback, saves feedback, and returns results.
        """
        session = self.get_object()
        if session.status == ConversationSession.Status.COMPLETED:
            return Response(
                {"detail": _("This conversation session is completed.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        test_question_instance = serializer.validated_data["question_id"]
        selected_answer = serializer.validated_data["selected_answer"]
        user = request.user
        ai_feedback_text = _("Feedback generation pending.")  # Default message

        try:
            # 1. Record the attempt (atomic transaction within the service)
            attempt = conversation.record_conversation_test_attempt(
                user=user,
                session=session,
                test_question=test_question_instance,
                selected_answer=selected_answer,
            )

            # 2. Get AI Feedback (outside the attempt recording transaction potentially)
            try:
                ai_feedback_text = conversation.get_ai_feedback_on_answer(
                    session=session,
                    attempt=attempt,
                )
            except Exception as feedback_error:
                # Log the feedback error but don't fail the whole request,
                # as the answer *was* recorded.
                logger.error(
                    f"Failed to get AI feedback for attempt {attempt.id}: {feedback_error}",
                    exc_info=True,
                )
                ai_feedback_text = _(
                    "Answer recorded, but an error occurred while generating feedback."
                )

            # 3. Save AI Feedback as a Conversation Message (separate transaction)
            # Use atomic=True to ensure this save succeeds or fails cleanly.
            try:
                with transaction.atomic():
                    ai_msg = ConversationMessage.objects.create(
                        session=session,
                        sender_type=ConversationMessage.SenderType.AI,
                        message_text=ai_feedback_text,
                        # Do NOT link this feedback message to the original question via related_question
                        # It's feedback ABOUT the attempt.
                    )
                    logger.info(
                        f"AI feedback message saved (ID: {ai_msg.id}) for attempt {attempt.id}"
                    )
            except Exception as msg_save_error:
                # Log error saving the message, but proceed with response
                logger.error(
                    f"Failed to save AI feedback message for attempt {attempt.id}: {msg_save_error}",
                    exc_info=True,
                )
                # The ai_feedback_text variable still holds the generated text for the response

            # 4. Prepare and return the response
            # Serialize the attempt result first
            result_serializer = ConversationTestResultSerializer(
                attempt, context=self.get_serializer_context()
            )
            response_data = result_serializer.data
            # Add the generated AI feedback text to the response dictionary
            response_data["ai_feedback"] = ai_feedback_text

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            q_id = test_question_instance.id if test_question_instance else "UNKNOWN"
            logger.exception(
                f"Error during submit_test_answer for session {session.id}, question {q_id}: {e}"
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
