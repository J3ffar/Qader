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


def create_question_with_skill(subsection):
    """Helper to create a question associated with a new skill."""
    skill = SkillFactory(subsection=subsection)
    question = QuestionFactory(subsection=subsection, skill=skill, correct_answer="A")
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

    def test_list_sessions(self, subscribed_client, base_user):
        # Create sessions for the subscribed user and another user
        create_session(subscribed_client)
        create_session(subscribed_client)
        ConversationSession.objects.create(user=base_user)  # Session for another user

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

    def test_cannot_retrieve_other_user_session(self, subscribed_client, base_user):
        other_session = ConversationSession.objects.create(user=base_user)
        # Correct URL name
        detail_url = reverse(
            "api:v1:study:conversation-detail", kwargs={"pk": other_session.id}
        )

        response = subscribed_client.get(detail_url)
        # Should not find it as it filters by user in get_queryset
        assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Messaging Tests ---
@patch(
    "apps.study.conversation_service.get_ai_response", return_value="Mocked AI Response"
)
class TestConversationMessaging:
    """Tests sending messages and AI interaction within a session."""

    def test_send_message_success(self, mock_get_ai_response, subscribed_client):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        user_message = "Tell me about analogies."
        response = subscribed_client.post(
            messages_url, data={"message_text": user_message}
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert ConversationMessage.objects.filter(session=session).count() == 2

        user_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.USER
        )
        ai_msg_obj = ConversationMessage.objects.get(
            session=session, sender_type=ConversationMessage.SenderType.AI
        )

        assert user_msg_obj.message_text == user_message
        assert ai_msg_obj.message_text == "Mocked AI Response"
        mock_get_ai_response.assert_called_once()
        assert response.data["sender_type"] == "ai"
        assert response.data["message_text_display"] == "Mocked AI Response"

    def test_send_message_updates_session_context(
        self, mock_get_ai_response, subscribed_client, setup_learning_content
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        question = Question.objects.filter(
            subsection=setup_learning_content["reading_comp_sub"]
        ).first()
        assert question is not None
        assert session.current_topic_question is None

        user_message = f"Explain question {question.id}"
        response = subscribed_client.post(
            messages_url,
            data={"message_text": user_message, "related_question_id": question.id},
        )

        # Check the response first for the TypeError origin
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            response.data["sender_type"] == "ai"
        )  # Ensure basic AI response serialization works

        # Now check the DB state
        session.refresh_from_db()
        assert session.current_topic_question == question
        mock_get_ai_response.assert_called_once()

    def test_send_message_to_completed_session(
        self, mock_get_ai_response, subscribed_client
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        session.end_session()
        assert session.status == ConversationSession.Status.COMPLETED

        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(
            messages_url, data={"message_text": "One more thing"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "completed" in response.data.get("detail", "").lower()
        mock_get_ai_response.assert_not_called()

    @patch("apps.study.conversation_service.logger")
    def test_send_message_ai_error(
        self, mock_logger, mock_get_ai_response, subscribed_client
    ):
        mock_get_ai_response.side_effect = Exception("Simulated AI API Error")

        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        messages_url = reverse(
            "api:v1:study:conversation-send-message", kwargs={"pk": session_id}
        )

        response = subscribed_client.post(
            messages_url, data={"message_text": "Cause an error"}
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error occurred" in response.data.get("detail", "").lower()

        # FIX: Assert count is 0 due to transaction rollback
        assert ConversationMessage.objects.filter(session_id=session_id).count() == 0


# --- Testing Flow Tests ---
@patch("apps.study.conversation_service.select_test_question_for_concept")
# REMOVE patch for record_conversation_test_attempt to let it create real objects
# @patch('apps.study.conversation_service.record_conversation_test_attempt')
# Optional: Patch proficiency update if needed for isolation
@patch.object(UserSkillProficiency, "record_attempt", return_value=None)
class TestConversationTestingFlow:
    """Tests the 'Got It' confirmation and test answer submission flow."""

    # Pass the mocked record_attempt (now patching UserSkillProficiency method)
    def test_confirm_understanding_no_context(
        self, mock_record_prof_attempt, mock_select_question, subscribed_client
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

    def test_confirm_understanding_success_with_test_question(
        self,
        mock_record_prof_attempt,
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
        assert test_q.id != original_q.id
        mock_select_question.return_value = test_q

        confirm_url = reverse(
            "api:v1:study:conversation-confirm-understanding", kwargs={"pk": session_id}
        )
        response = subscribed_client.post(confirm_url)

        assert response.status_code == status.HTTP_200_OK
        mock_select_question.assert_called_once_with(original_q, subscribed_client.user)
        assert response.data["id"] == test_q.id
        assert "question_text" in response.data
        assert "correct_answer" not in response.data

    def test_confirm_understanding_no_suitable_test_question(
        self,
        mock_record_prof_attempt,
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

    def test_submit_test_answer_success(
        self,
        mock_record_prof_attempt,
        mock_select_question,
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        test_q, test_skill = create_question_with_skill(
            setup_learning_content["algebra_sub"]
        )
        test_q.correct_answer = "C"
        test_q.explanation = "Test Explanation"
        test_q.save()
        # Ensure the skill exists for proficiency check later
        assert test_skill is not None

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "C"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_200_OK

        # Verify the attempt was actually created in DB
        attempt = UserQuestionAttempt.objects.filter(
            user=subscribed_client.user,
            question=test_q,
            conversation_session=session,  # Ensure it's linked to the session if model changes
            mode=UserQuestionAttempt.Mode.CONVERSATION,
        ).first()
        assert attempt is not None
        assert attempt.is_correct is True
        assert attempt.selected_answer == "C"

        # Check response contains result details from the REAL attempt object
        assert response.data["id"] == attempt.id
        assert response.data["is_correct"] is True
        assert response.data["selected_answer"] == "C"
        assert response.data["correct_answer"] == "C"
        assert response.data["explanation"] == "Test Explanation"
        assert response.data["question"]["id"] == test_q.id

        # Verify the mocked proficiency update was called
        mock_record_prof_attempt.assert_called_once_with(is_correct=True)

    def test_submit_test_answer_incorrect(
        self,
        mock_record_prof_attempt,
        mock_select_question,
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)

        test_q, test_skill = create_question_with_skill(
            setup_learning_content["algebra_sub"]
        )
        test_q.correct_answer = "A"
        test_q.explanation = "Explanation B"
        test_q.save()
        assert test_skill is not None

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "B"}  # Incorrect answer
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_200_OK

        # Verify the attempt was created
        attempt = UserQuestionAttempt.objects.filter(
            user=subscribed_client.user,
            question=test_q,
            conversation_session=session,  # Future-proofing if model changes
            mode=UserQuestionAttempt.Mode.CONVERSATION,
        ).first()
        assert attempt is not None
        assert attempt.is_correct is False
        assert attempt.selected_answer == "B"

        # Check response
        assert response.data["id"] == attempt.id
        assert response.data["is_correct"] is False
        assert response.data["selected_answer"] == "B"
        assert response.data["correct_answer"] == "A"  # Show correct answer
        assert response.data["explanation"] == "Explanation B"
        assert response.data["question"]["id"] == test_q.id

        # Verify the mocked proficiency update was called
        mock_record_prof_attempt.assert_called_once_with(is_correct=False)

    # Pass the mocked record_attempt even if not used directly in this test's assertions
    def test_submit_test_answer_invalid_question(
        self, mock_record_prof_attempt, mock_select_question, subscribed_client
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]

        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        invalid_q_id = 99999
        data = {"question_id": invalid_q_id, "selected_answer": "A"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "question_id" in response.data
        assert "Invalid pk" in str(response.data["question_id"])
        # Ensure proficiency wasn't called
        mock_record_prof_attempt.assert_not_called()

    def test_submit_test_answer_to_completed_session(
        self,
        mock_record_prof_attempt,
        mock_select_question,
        subscribed_client,
        setup_learning_content,
    ):
        session_resp = create_session(subscribed_client)
        session_id = session_resp.data["id"]
        session = ConversationSession.objects.get(pk=session_id)
        session.end_session()

        test_q, _ = create_question_with_skill(setup_learning_content["algebra_sub"])
        submit_url = reverse(
            "api:v1:study:conversation-submit-test-answer", kwargs={"pk": session_id}
        )
        data = {"question_id": test_q.id, "selected_answer": "A"}
        response = subscribed_client.post(submit_url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "completed" in response.data.get("detail", "").lower()
        mock_record_prof_attempt.assert_not_called()


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
