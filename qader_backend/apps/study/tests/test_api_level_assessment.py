# qader_backend/apps/study/tests/test_api_level_assessment.py

import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import LearningSection, Question
from apps.users.models import UserProfile
from apps.study.tests.factories import UserTestAttemptFactory
from apps.learning.tests.factories import QuestionFactory

pytestmark = pytest.mark.django_db

# --- Tests for Level Assessment Start Endpoint Only ---


class TestLevelAssessmentStartAPI:

    # Tests for starting an assessment remain largely the same
    def test_start_assessment_unauthenticated(self, api_client, setup_learning_content):
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_assessment_not_subscribed(
        self, authenticated_client, setup_learning_content
    ):
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_assessment_success(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = None
        profile.current_level_quantitative = None
        profile.save()

        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        num_questions_requested = 20
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions_requested,
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "attempt_id" in response.data
        assert "questions" in response.data
        attempt = UserTestAttempt.objects.get(pk=response.data["attempt_id"])
        assert attempt.user == user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
        assert (
            attempt.test_configuration["num_questions_requested"]
            == num_questions_requested
        )
        assert len(attempt.question_ids) == len(response.data["questions"])
        # Check response structure
        assert "attempt_id" in response.data
        assert "questions" in response.data and isinstance(
            response.data["questions"], list
        )

    def test_start_assessment_ongoing_attempt_exists(
        self, subscribed_client, setup_learning_content
    ):
        # Create *any* started attempt
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check for generic ongoing attempt message
        assert "You already have an ongoing test attempt." in str(response.data)

    # Other start failure tests (invalid section, num_questions, no questions) remain valid
    def test_start_assessment_invalid_section_slug(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal", "invalid-slug"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data

    def test_start_assessment_invalid_num_questions(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal"], "num_questions": 2}  # Below min value
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "num_questions" in response.data

    def test_start_assessment_no_active_questions_available(
        self, subscribed_client, setup_learning_content
    ):
        Question.objects.update(is_active=False)
        url = reverse("api:v1:study:attempt-start-level-assessment")  # Updated URL name
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Not enough active questions" in str(response.data)


# --- REMOVED Submit Tests ---
# Class TestLevelAssessmentSubmitAPI and its methods are removed.
# The functionality is now tested within the new unified attempt lifecycle tests.
