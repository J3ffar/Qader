import pytest
from django.urls import reverse
from rest_framework import status
from unittest.mock import patch, MagicMock  # Keep MagicMock for other patches

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill
from apps.study.tests.factories import UserQuestionAttemptFactory
from apps.learning.tests.factories import QuestionFactory, SkillFactory

# Use fixtures from conftest files
pytestmark = pytest.mark.django_db


# --- Helper Functions (keep as is) ---
def create_session(client, data=None):
    """Helper to create a conversation session."""
    url = reverse("api:v1:study:conversation-list")
    return client.post(url, data=data or {})


def create_question_with_skill(subsection, correct_answer="A"):
    """Helper to create a question associated with a new skill."""
    skill = SkillFactory(subsection=subsection)
    question = QuestionFactory(
        subsection=subsection, skill=skill, correct_answer=correct_answer
    )
    return question, skill


# --- Test Classes (Permissions, CRUD remain the same) ---


class TestConversationPermissions:
    """Tests access control for the Conversation API."""

    list_url = reverse("api:v1:study:conversation-list")

    # ... (tests remain the same) ...
    def test_unauthenticated_user_cannot_access(self, api_client):
        response = api_client.get(self.list_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = api_client.post(self.list_url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unsubscribed_user_cannot_access(self, authenticated_client):
        # authenticated_client uses the unsubscribed_user fixture
        response = authenticated_client.get(self.list_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "subscription" in response.data.get("detail", "").lower()

        response = authenticated_client.post(self.list_url, {})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "subscription" in response.data.get("detail", "").lower()

    def test_subscribed_user_can_access_list(self, subscribed_client):
        response = subscribed_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK

    def test_subscribed_user_can_create_session(self, subscribed_client):
        response = create_session(subscribed_client)
        assert response.status_code == status.HTTP_201_CREATED


class TestConversationSessionCRUD:
    """Tests creating, listing, and retrieving sessions."""

    list_url = reverse("api:v1:study:conversation-list")

    # ... (tests remain the same) ...
    def test_create_session_default_tone(self, subscribed_client):
        response = create_session(subscribed_client)
        assert response.status_code == status.HTTP_201_CREATED
        assert ConversationSession.objects.count() == 1
        session = ConversationSession.objects.first()
        assert session.user == subscribed_client.user
        assert session.ai_tone == ConversationSession.AiTone.SERIOUS  # Default
        assert session.status == ConversationSession.Status.ACTIVE
        assert "id" in response.data
        assert response.data["ai_tone"] == ConversationSession.AiTone.SERIOUS

    def test_create_session_specific_tone(self, subscribed_client):
        response = create_session(subscribed_client, data={"ai_tone": "cheerful"})
        assert response.status_code == status.HTTP_201_CREATED
        assert ConversationSession.objects.count() == 1
        session = ConversationSession.objects.first()
        assert session.ai_tone == ConversationSession.AiTone.CHEERFUL
        assert response.data["ai_tone"] == ConversationSession.AiTone.CHEERFUL

    def test_list_sessions(self, subscribed_client, standard_user):
        # Create sessions for the subscribed user and another user
        create_session(subscribed_client)
        create_session(subscribed_client)
        ConversationSession.objects.create(
            user=standard_user
        )  # Session for another user

        response = subscribed_client.get(self.list_url)
        assert response.status_code == status.HTTP_200_OK
        # Should only list sessions for the subscribed_client's user
        # Check pagination structure if PageNumberPagination is used
        assert "results" in response.data
        assert len(response.data["results"]) == 2
        for item in response.data["results"]:
            # Access user id within the nested user serializer structure if applicable
            user_data = item.get("user", {})
            assert user_data.get("id") == subscribed_client.user.id

    def test_retrieve_own_session(self, subscribed_client):
        create_response = create_session(subscribed_client)
        session_id = create_response.data["id"]
        # Correct URL name
        detail_url = reverse(
            "api:v1:study:conversation-detail", kwargs={"pk": session_id}
        )

        response = subscribed_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == session_id
        assert "messages" in response.data  # Detail view should include messages

    def test_cannot_retrieve_other_user_session(self, subscribed_client, standard_user):
        other_session = ConversationSession.objects.create(user=standard_user)
        # Correct URL name
        detail_url = reverse(
            "api:v1:study:conversation-detail", kwargs={"pk": other_session.id}
        )

        response = subscribed_client.get(detail_url)
        # Should not find it as it filters by user in get_queryset
        assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Messaging Tests ---
@patch("apps.study.conversation_service.process_user_message_with_ai")
class TestConversationMessaging:
    """Tests sending messages and AI interaction within a session."""

    def test_send_message_ai_interprets_as_conversation(
        self, mock_process_ai, subscribed_client, setup_learning_content
    ):
        """Test when AI processes the message as non-answer."""
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        # Setup a current question context
        current_q, _ = create_question_with_skill(setup_learning_content["algebra_sub"])
        session.current_topic_question = current_q
        session.save()

        user_message = "Can you explain this concept more?"
        ai_response_text = "Sure, this concept involves..."

        # Mock the AI service response (not an answer)
        mock_process_ai.return_value = {
            "processed_as_answer": False,
            "user_choice": None,
            "feedback_text": ai_response_text,
        }

        response = subscribed_client.post(
            messages_url, data={"message_text": user_message}
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Verify messages saved: User + AI
        assert ConversationMessage.objects.filter(session=session).count() == 2
        ai_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.AI
        )
        assert ai_msg_obj.message_text == ai_response_text
        # Verify attempt was NOT created
        assert not UserQuestionAttempt.objects.filter(
            conversation_session=session
        ).exists()
        # Verify the service was called correctly
        mock_process_ai.assert_called_once_with(
            session=session,
            user_message_text=user_message,
            current_topic_question=current_q,
        )
        # Check response data
        assert response.data["sender_type"] == "ai"
        assert response.data["message_text"] == ai_response_text  # Use message_text now

    def test_send_message_ai_interprets_as_incorrect_answer(
        self, mock_process_ai, subscribed_client, setup_learning_content
    ):
        """Test when AI processes as incorrect answer and provides hint."""
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        current_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"], correct_answer="A"
        )
        session.current_topic_question = current_q
        session.save()

        user_message = "B"  # Incorrect answer
        ai_hint_text = "Not quite! Remember the formula for..."

        # Mock the AI service response (incorrect answer)
        mock_process_ai.return_value = {
            "processed_as_answer": True,
            "user_choice": "B",  # AI detected 'B'
            "feedback_text": ai_hint_text,
        }

        response = subscribed_client.post(
            messages_url, data={"message_text": user_message}
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Verify messages saved: User + AI Hint
        assert ConversationMessage.objects.filter(session=session).count() == 2
        ai_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.AI
        )
        assert ai_msg_obj.message_text == ai_hint_text
        # Verify attempt WAS created and marked incorrect
        attempt = UserQuestionAttempt.objects.filter(
            conversation_session=session, question=current_q
        ).first()
        assert attempt is not None
        assert attempt.selected_answer == "B"
        assert attempt.is_correct is False
        # Verify the service was called correctly
        mock_process_ai.assert_called_once_with(
            session=session,
            user_message_text=user_message,
            current_topic_question=current_q,
        )
        # Check response data
        assert response.data["sender_type"] == "ai"
        assert response.data["message_text"] == ai_hint_text

    def test_send_message_ai_interprets_as_correct_answer(
        self, mock_process_ai, subscribed_client, setup_learning_content
    ):
        """Test when AI processes as correct answer and provides confirmation."""
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        current_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"], correct_answer="C"
        )
        session.current_topic_question = current_q
        session.save()

        user_message = "c."  # Correct answer with variation
        ai_confirm_text = "That's right! Nicely done."

        # Mock the AI service response (correct answer)
        mock_process_ai.return_value = {
            "processed_as_answer": True,
            "user_choice": "C",  # AI detected 'C'
            "feedback_text": ai_confirm_text,
        }

        response = subscribed_client.post(
            messages_url, data={"message_text": user_message}
        )

        assert response.status_code == status.HTTP_201_CREATED
        # Verify messages saved: User + AI Confirmation
        assert ConversationMessage.objects.filter(session=session).count() == 2
        ai_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.AI
        )
        assert ai_msg_obj.message_text == ai_confirm_text
        # Verify attempt WAS created and marked correct
        attempt = UserQuestionAttempt.objects.filter(
            conversation_session=session, question=current_q
        ).first()
        assert attempt is not None
        assert attempt.selected_answer == "C"
        assert attempt.is_correct is True
        # Verify the service was called correctly
        mock_process_ai.assert_called_once_with(
            session=session,
            user_message_text=user_message,
            current_topic_question=current_q,
        )
        # Check response data
        assert response.data["sender_type"] == "ai"
        assert response.data["message_text"] == ai_confirm_text

    def test_send_message_ai_fails_json_parsing(
        self, mock_process_ai, subscribed_client, setup_learning_content
    ):
        """Test view's handling of AI service returning invalid JSON."""
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )
        current_q, _ = create_question_with_skill(setup_learning_content["algebra_sub"])
        session.current_topic_question = current_q
        session.save()

        user_message = "A"
        # Simulate the service function raising an error during parsing or returning error dict
        mock_process_ai.return_value = {
            "processed_as_answer": False,
            "user_choice": None,
            "feedback_text": "Sorry, I had a little trouble structuring my response.",  # Example fallback text
        }
        # OR mock_process_ai.side_effect = json.JSONDecodeError("Expecting property name enclosed in double quotes", doc="", pos=0)
        # The view should catch exceptions from the service call

        response = subscribed_client.post(
            messages_url, data={"message_text": user_message}
        )

        assert (
            response.status_code == status.HTTP_201_CREATED
        )  # View saves fallback msg
        # Verify messages saved: User + AI Fallback
        assert ConversationMessage.objects.filter(session=session).count() == 2
        ai_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.AI
        )
        assert "trouble structuring" in ai_msg_obj.message_text  # Check fallback saved
        # Verify attempt was NOT created
        assert not UserQuestionAttempt.objects.filter(
            conversation_session=session
        ).exists()

    def test_send_message_ai_service_unavailable(
        self, mock_process_ai, subscribed_client
    ):
        """Test view's handling of AI service unavailability indicated by response."""
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        # Simulate the service returning an unavailability message
        mock_process_ai.return_value = {
            "processed_as_answer": False,
            "user_choice": None,
            "feedback_text": "Sorry, the AI assistant is currently unavailable.",
        }

        response = subscribed_client.post(messages_url, data={"message_text": "Hello?"})

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "unavailable" in response.data["detail"]
        # Only user message should be saved
        assert ConversationMessage.objects.filter(session_id=session_id).count() == 1
        assert (
            ConversationMessage.objects.filter(
                session_id=session_id, sender_type=ConversationMessage.SenderType.AI
            ).count()
            == 0
        )


# --- Testing Flow Tests ---
@patch(
    "apps.study.conversation_service.select_test_question_for_concept"
)  # Creates mock_select_question (arg 3)
@patch(
    "apps.study.conversation_service.get_ai_feedback_on_answer"
)  # Creates mock_get_ai_feedback (arg 2)
@patch.object(
    UserSkillProficiency, "record_attempt", return_value=None
)  # Creates mock_record_prof_attempt (arg 1)
class TestConversationTestingFlowUpdated:
    """Tests the 'Got It' and explicit test answer submission flow with AI feedback."""

    # Method signature order should match decorator order (inner to outer)
    def test_confirm_understanding_no_context(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,
        subscribed_client,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        assert session.current_topic_question is None

        confirm_url = reverse(
            "api:v1:study:conversation-confirm-understanding", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(confirm_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "no specific topic context" in response.data.get("detail", "").lower()
        mock_select_question.assert_not_called()
        mock_get_ai_feedback.assert_not_called()

    def test_confirm_understanding_success_with_test_question(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        original_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"]
        )
        session.current_topic_question = original_q
        session.save()

        test_q, _ = create_question_with_skill(setup_learning_content["algebra_sub"])
        mock_select_question.return_value = test_q

        confirm_url = reverse(
            "api:v1:study:conversation-confirm-understanding", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(confirm_url)

        assert response.status_code == status.HTTP_200_OK
        mock_select_question.assert_called_once_with(original_q, subscribed_client.user)
        assert response.data["id"] == test_q.id
        mock_get_ai_feedback.assert_not_called()

    def test_confirm_understanding_no_suitable_test_question(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        original_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"]
        )
        session.current_topic_question = original_q
        session.save()

        mock_select_question.return_value = None

        confirm_url = reverse(
            "api:v1:study:conversation-confirm-understanding", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(confirm_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_select_question.assert_called_once_with(original_q, subscribed_client.user)
        mock_get_ai_feedback.assert_not_called()  # Also check here

    # FIX: Add mock_select_question to the signature for all methods in this class
    def test_submit_test_answer_success_with_ai_feedback(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,  # <-- ADDED ARGUMENT
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        test_q, test_skill = create_question_with_skill(
            setup_learning_content["algebra_sub"], correct_answer="C"
        )
        test_q.explanation = "Test Explanation"
        test_q.save()

        ai_feedback_text = "Great job! That's exactly right."
        mock_get_ai_feedback.return_value = ai_feedback_text

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "C"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_200_OK

        attempt = UserQuestionAttempt.objects.filter(
            user=subscribed_client.user, question=test_q, conversation_session=session
        ).first()
        assert attempt is not None
        assert attempt.is_correct is True

        mock_get_ai_feedback.assert_called_once_with(session=session, attempt=attempt)
        ai_msg = ConversationMessage.objects.filter(
            session=session, sender_type=ConversationMessage.SenderType.AI
        ).first()
        assert ai_msg is not None
        assert ai_msg.message_text == ai_feedback_text

        assert response.data["id"] == attempt.id
        assert response.data["is_correct"] is True
        assert "ai_feedback" in response.data
        assert response.data["ai_feedback"] == ai_feedback_text
        assert response.data["correct_answer"] == "C"

        mock_record_prof_attempt.assert_called_once_with(is_correct=True)
        mock_select_question.assert_not_called()  # This mock shouldn't be used here

    # FIX: Add mock_select_question to the signature
    def test_submit_test_answer_incorrect_with_ai_feedback(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,  # <-- ADDED ARGUMENT
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        test_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"], correct_answer="A"
        )
        test_q.explanation = "Explanation B"
        test_q.save()

        ai_feedback_text = "Not quite. The correct answer involves..."
        mock_get_ai_feedback.return_value = ai_feedback_text

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "B"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_200_OK

        attempt = UserQuestionAttempt.objects.filter(
            user=subscribed_client.user, question=test_q, conversation_session=session
        ).first()
        assert attempt is not None
        assert attempt.is_correct is False

        mock_get_ai_feedback.assert_called_once_with(session=session, attempt=attempt)
        ai_msg = ConversationMessage.objects.filter(
            session=session, sender_type=ConversationMessage.SenderType.AI
        ).first()
        assert ai_msg is not None
        assert ai_msg.message_text == ai_feedback_text

        assert response.data["is_correct"] is False
        assert "ai_feedback" in response.data
        assert response.data["ai_feedback"] == ai_feedback_text
        assert response.data["correct_answer"] == "A"

        mock_record_prof_attempt.assert_called_once_with(is_correct=False)
        mock_select_question.assert_not_called()  # This mock shouldn't be used here

    # FIX: Add mock_select_question to the signature
    def test_submit_test_answer_ai_feedback_fails(
        self,
        mock_record_prof_attempt,
        mock_get_ai_feedback,
        mock_select_question,  # <-- ADDED ARGUMENT
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        test_q, _ = create_question_with_skill(
            setup_learning_content["algebra_sub"], correct_answer="A"
        )

        fallback_text = (
            "Answer recorded, but an error occurred while generating feedback."
        )
        mock_get_ai_feedback.side_effect = Exception("Simulated feedback error")

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "A"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_200_OK

        attempt = UserQuestionAttempt.objects.filter(
            user=subscribed_client.user, question=test_q, conversation_session=session
        ).first()
        assert attempt is not None
        assert attempt.is_correct is True

        mock_get_ai_feedback.assert_called_once()

        ai_msg = ConversationMessage.objects.filter(
            session=session, sender_type=ConversationMessage.SenderType.AI
        ).first()
        assert ai_msg is not None
        assert fallback_text in ai_msg.message_text

        assert "ai_feedback" in response.data
        assert fallback_text in response.data["ai_feedback"]

        mock_record_prof_attempt.assert_called_once_with(is_correct=True)
        mock_select_question.assert_not_called()  # This mock shouldn't be used here


# --- End Session Tests ---
class TestConversationEndSession:
    """Tests explicitly ending a session."""

    def test_end_active_session(self, subscribed_client):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        assert session.status == ConversationSession.Status.ACTIVE
        assert session.end_time is None

        end_url = reverse(
            "api:v1:study:conversation-end-session-action", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(end_url)

        assert response.status_code == status.HTTP_200_OK
        assert "ended successfully" in response.data.get("detail", "").lower()

        session.refresh_from_db()
        assert session.status == ConversationSession.Status.COMPLETED
        assert session.end_time is not None

    def test_end_already_completed_session(self, subscribed_client):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        session.end_session()
        first_end_time = session.end_time

        end_url = reverse(
            "api:v1:study:conversation-end-session-action", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(end_url)

        assert response.status_code == status.HTTP_200_OK

        session.refresh_from_db()
        assert session.status == ConversationSession.Status.COMPLETED
        assert session.end_time == first_end_time
