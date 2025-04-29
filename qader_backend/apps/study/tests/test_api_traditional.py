# qader_backend/apps/study/tests/test_api_traditional.py

# Tests for Traditional Learning remain unchanged as the core logic
# for this specific feature was not part of the refactoring.
# Ensure assertions about points/streaks in the response are removed (already done in provided code).

from django.conf import settings
import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.study.models import UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion, Skill
from apps.users.models import UserProfile
from apps.learning.tests.factories import (
    QuestionFactory,
    SkillFactory,
    LearningSubSectionFactory,
)
from apps.study.tests.factories import UserSkillProficiencyFactory

pytestmark = pytest.mark.django_db


# TestTraditionalQuestionsList (No Changes Needed)
class TestTraditionalQuestionsList:
    # ... (keep existing tests for list view) ...
    pass


# TestTraditionalAnswerSubmit (No Changes Needed - Ensure points/streak assertions are removed)
class TestTraditionalAnswerSubmit:
    @pytest.fixture(autouse=True)
    def _ensure_profile_and_content(self, subscribed_client, setup_learning_content):
        self.user = subscribed_client.user
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.learning_content = setup_learning_content
        self.question = Question.objects.filter(is_active=True).first()
        if not self.question:
            pytest.skip("No active question found for testing submit.")

    # Tests for unauthenticated, not subscribed remain the same
    def test_submit_answer_unauthenticated(self, api_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": "A"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_answer_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": "A"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Success tests (ensure no assertions about points/streak in response)
    def test_submit_correct_answer(self, subscribed_client):
        initial_prof_score = 0.0
        prof = None
        if self.question.skill:
            prof, _ = UserSkillProficiency.objects.get_or_create(
                user=self.user, skill=self.question.skill
            )
            initial_prof_score = prof.proficiency_score

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {
            "question_id": self.question.id,
            "selected_answer": self.question.correct_answer,
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["question_id"] == self.question.id
        assert res_data["is_correct"] is True
        assert "feedback_message" in res_data  # Check feedback message exists
        # NO assertions about points/streak in response data

        # Check DB state
        assert UserQuestionAttempt.objects.filter(
            user=self.user, question=self.question, mode="traditional", is_correct=True
        ).exists()
        if prof:
            prof.refresh_from_db()
            assert (
                prof.proficiency_score >= initial_prof_score
            )  # Or more specific check

    def test_submit_incorrect_answer(self, subscribed_client):
        incorrect_answer = "A" if self.question.correct_answer != "A" else "B"
        initial_prof_score = 0.0
        prof = None
        if self.question.skill:
            prof, _ = UserSkillProficiency.objects.get_or_create(
                user=self.user, skill=self.question.skill
            )
            initial_prof_score = prof.proficiency_score

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": incorrect_answer}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["is_correct"] is False
        assert "feedback_message" in res_data
        # NO assertions about points/streak in response data

        # Check DB state
        assert UserQuestionAttempt.objects.filter(
            user=self.user, question=self.question, mode="traditional", is_correct=False
        ).exists()
        if prof:
            prof.refresh_from_db()
            assert (
                prof.proficiency_score <= initial_prof_score
            )  # Or more specific check

    # Failure tests remain the same
    def test_submit_answer_invalid_question_id(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": 99999, "selected_answer": "A"}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "question_id" in response.data

    def test_submit_answer_missing_field(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data
