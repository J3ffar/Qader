import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from unittest.mock import patch, MagicMock

# improt timezone from djnago
from django.utils import timezone
from apps.study.models import (
    EmergencyModeSession,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill
from apps.study.tests.factories import EmergencyModeSessionFactory
from apps.learning.tests.factories import QuestionFactory, SkillFactory


# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


# --- Test EmergencyModeStartView ---


@pytest.mark.usefixtures("setup_learning_content")  # Ensure skills exist
class TestEmergencyModeStart:
    url = reverse("api:v1:study:emergency-start")

    @patch("apps.study.services.study.generate_emergency_plan")
    def test_start_emergency_success(
        self, mock_generate_plan, subscribed_client, setup_learning_content
    ):
        """Verify successful start of emergency mode for subscribed user."""
        user = subscribed_client.user
        mock_plan = {
            "focus_skills": ["algebra", "geometry"],  # Use slugs from setup
            "recommended_questions": 20,
            "quick_review_topics": ["Algebra Basics Review"],
        }
        mock_generate_plan.return_value = mock_plan

        payload = {
            "reason": "Feeling stressed",
            "available_time_hours": 1,
            "focus_areas": ["quantitative"],
        }

        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert "session_id" in response.data
        assert response.data["suggested_plan"] == mock_plan

        # Check database
        assert EmergencyModeSession.objects.filter(user=user).exists()
        session = EmergencyModeSession.objects.get(user=user)
        assert session.id == response.data["session_id"]
        assert session.reason == payload["reason"]
        assert session.suggested_plan == mock_plan
        assert not session.calm_mode_active
        assert not session.shared_with_admin
        assert session.end_time is None

        # Verify service call
        mock_generate_plan.assert_called_once_with(
            user=user,
            available_time_hours=payload["available_time_hours"],
            focus_areas=payload["focus_areas"],
        )

    def test_start_emergency_unauthenticated_fails(self, api_client):
        """Verify unauthenticated users cannot start emergency mode."""
        payload = {"reason": "Test"}
        response = api_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_emergency_unsubscribed_fails(self, authenticated_client):
        """Verify non-subscribed users cannot start emergency mode."""
        payload = {"reason": "Test"}
        response = authenticated_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_emergency_invalid_payload_fails(self, subscribed_client):
        """Verify invalid payload returns 400."""
        payload = {
            "available_time_hours": -1,  # Invalid
            "focus_areas": ["invalid_area"],  # Invalid choice
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "available_time_hours" in response.data
        assert "focus_areas" in response.data

    @patch("apps.study.services.study")
    def test_start_emergency_plan_generation_fails(
        self, mock_generate_plan, subscribed_client
    ):
        """Verify failure if plan generation service fails."""
        mock_generate_plan.side_effect = Exception("Service error")
        payload = {"reason": "Test"}
        response = subscribed_client.post(self.url, data=payload)
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        )  # View catches and returns 400
        error_msg = "Could not generate study plan. Please try again later."
        assert isinstance(response.data, list) or isinstance(response.data, dict)
        if isinstance(response.data, list):  # Might be just a list with one error
            assert len(response.data) > 0
            assert error_msg in str(response.data[0])
        elif "detail" in response.data:
            assert isinstance(response.data["detail"], (list, ErrorDetail))
            details = (
                response.data["detail"]
                if isinstance(response.data["detail"], list)
                else [response.data["detail"]]
            )
            assert any(error_msg in str(detail) for detail in details)
        elif "non_field_errors" in response.data:
            assert isinstance(response.data["non_field_errors"], list)
            assert any(
                error_msg in str(err) for err in response.data["non_field_errors"]
            )
        else:
            pytest.fail(f"Unexpected error response structure: {response.data}")


# --- Test EmergencyModeSessionUpdateView ---


class TestEmergencyModeUpdate:

    @pytest.fixture
    def active_session(self, subscribed_user):
        """Fixture for an active session owned by the subscribed user."""
        return EmergencyModeSessionFactory(user=subscribed_user)

    @pytest.fixture
    def ended_session(self, subscribed_user):
        """Fixture for an ended session owned by the subscribed user."""
        return EmergencyModeSessionFactory(
            user=subscribed_user, end_time=timezone.now()
        )

    def get_url(self, session_id):
        return reverse(
            "api:v1:study:emergency-update", kwargs={"session_id": session_id}
        )

    def test_update_session_success(self, subscribed_client, active_session):
        """Verify successful update of session settings."""
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True, "shared_with_admin": True}

        assert not active_session.calm_mode_active
        assert not active_session.shared_with_admin

        response = subscribed_client.patch(url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["calm_mode_active"] is True
        assert response.data["shared_with_admin"] is True

        active_session.refresh_from_db()
        assert active_session.calm_mode_active is True
        assert active_session.shared_with_admin is True

    def test_update_session_partial_success(self, subscribed_client, active_session):
        """Verify partial update works."""
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}  # Only update one field

        response = subscribed_client.patch(url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["calm_mode_active"] is True
        assert response.data["shared_with_admin"] is False  # Should not change

        active_session.refresh_from_db()
        assert active_session.calm_mode_active is True
        assert active_session.shared_with_admin is False

    def test_update_session_unauthenticated_fails(self, api_client, active_session):
        """Verify unauthenticated users cannot update."""
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}
        response = api_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_session_not_owner_fails(self, authenticated_client, active_session):
        """Verify non-owners cannot update."""
        # active_session owned by subscribed_user, client is authenticated_client (unsubscribed)
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}
        response = authenticated_client.patch(url, data=payload)
        # Should fail permission check (IsSubscribed first, then ownership in get_object)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_session_ended_fails(self, subscribed_client, ended_session):
        """Verify updating an ended session fails."""
        url = self.get_url(ended_session.id)
        payload = {"calm_mode_active": True}
        response = subscribed_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        # Convert the ErrorDetail object to string and check content
        assert "ended" in str(response.data[0]).lower()

    def test_update_session_not_found_fails(self, subscribed_client):
        """Verify updating a non-existent session returns 404."""
        url = self.get_url(9999)
        payload = {"calm_mode_active": True}
        response = subscribed_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Test EmergencyModeAnswerView ---


@pytest.mark.usefixtures("setup_learning_content")
class TestEmergencyModeAnswer:
    url = reverse("api:v1:study:emergency-answer")

    @pytest.fixture
    def active_session(self, subscribed_user):
        """Fixture for an active session owned by the subscribed user."""
        return EmergencyModeSessionFactory(user=subscribed_user)

    @pytest.fixture
    def ended_session(self, subscribed_user):
        """Fixture for an ended session owned by the subscribed user."""
        return EmergencyModeSessionFactory(
            user=subscribed_user, end_time=timezone.now()
        )

    @pytest.fixture
    def question_with_skill(self, setup_learning_content):
        """Returns a question linked to a skill."""
        return Question.objects.filter(skill__isnull=False, is_active=True).first()

    @pytest.fixture
    def question_without_skill(self, setup_learning_content):
        """Returns a question NOT linked to a skill."""
        return Question.objects.filter(skill__isnull=True, is_active=True).first()

    @patch("apps.study.services.study")
    def test_answer_correct_with_skill_success(
        self, mock_update_prof, subscribed_client, active_session, question_with_skill
    ):
        """Verify submitting a correct answer for a question with a skill works."""
        user = subscribed_client.user
        question = question_with_skill
        payload = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
            "session_id": active_session.id,
        }

        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["question_id"] == question.id
        assert response.data["is_correct"] is True
        assert response.data["correct_answer"] == question.correct_answer
        assert response.data["explanation"] == question.explanation
        assert response.data["points_earned"] == 0

        # Check database
        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=True,
        ).exists()

        # Check proficiency update call
        assert question.skill is not None
        mock_update_prof.assert_called_once_with(
            user=user, skill=question.skill, is_correct=True
        )

    @patch("apps.study.services.study")
    def test_answer_incorrect_with_skill_success(
        self, mock_update_prof, subscribed_client, active_session, question_with_skill
    ):
        """Verify submitting an incorrect answer for a question with a skill works."""
        user = subscribed_client.user
        question = question_with_skill
        incorrect_answer = next(
            c for c in ["A", "B", "C", "D"] if c != question.correct_answer
        )
        payload = {
            "question_id": question.id,
            "selected_answer": incorrect_answer,
            "session_id": active_session.id,
        }

        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_correct"] is False
        assert response.data["correct_answer"] == question.correct_answer

        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=False,
        ).exists()
        mock_update_prof.assert_called_once_with(
            user=user, skill=question.skill, is_correct=False
        )

    @patch("apps.study.services.study")
    def test_answer_correct_without_skill_success(
        self,
        mock_update_prof,
        subscribed_client,
        active_session,
        question_without_skill,
    ):
        """Verify submitting a correct answer for a question WITHOUT a skill works."""
        user = subscribed_client.user
        question = question_without_skill
        payload = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
            "session_id": active_session.id,
        }

        assert (
            question is not None
        ), "Fixture question_without_skill failed to provide a question."
        assert question.skill is None

        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_correct"] is True

        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=True,
        ).exists()

        # Ensure proficiency was NOT called
        mock_update_prof.assert_not_called()

    def test_answer_unauthenticated_fails(
        self, api_client, active_session, question_with_skill
    ):
        """Verify unauthenticated users cannot submit answers."""
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = api_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_answer_unsubscribed_fails(
        self, authenticated_client, active_session, question_with_skill
    ):
        """Verify non-subscribed users cannot submit answers."""
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = authenticated_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_answer_invalid_session_id_fails(
        self, subscribed_client, question_with_skill
    ):
        """Verify submitting with an invalid session ID fails."""
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": 9999,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_session_not_owned_fails(
        self, subscribed_client, admin_user, question_with_skill
    ):
        """Verify submitting to a session owned by another user fails."""
        other_session = EmergencyModeSessionFactory(
            user=admin_user
        )  # Session owned by admin
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": other_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # Fails lookup for *this* user

    def test_answer_session_ended_fails(
        self, subscribed_client, ended_session, question_with_skill
    ):
        """Verify submitting to an ended session fails."""
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": ended_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        # Convert the ErrorDetail object to string and check content
        assert "ended" in str(response.data[0]).lower()

    def test_answer_invalid_question_id_fails(self, subscribed_client, active_session):
        """Verify submitting with an invalid question ID fails."""
        payload = {
            "question_id": 9999,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_invalid_payload_fails(
        self, subscribed_client, active_session, question_with_skill
    ):
        """Verify invalid payload returns 400."""
        payload = {  # Missing selected_answer
            "question_id": question_with_skill.id,
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data

        payload = {  # Invalid selected_answer choice
            "question_id": question_with_skill.id,
            "selected_answer": "E",
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data
