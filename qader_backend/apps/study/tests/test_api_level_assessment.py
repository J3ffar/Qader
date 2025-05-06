# qader_backend/apps/study/tests/test_api_level_assessment.py

import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import LearningSection, Question
from apps.users.models import UserProfile
from apps.study.tests.factories import (
    UserTestAttemptFactory,
)  # create_attempt_scenario no longer used here directly
from apps.learning.tests.factories import QuestionFactory

pytestmark = pytest.mark.django_db

# --- Tests for Level Assessment Start Endpoint Only ---


class TestLevelAssessmentStartAPI:

    # Tests for starting an assessment remain largely the same
    def test_start_assessment_unauthenticated(self, api_client, setup_learning_content):
        url = reverse("api:v1:study:start-level-assessment")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_assessment_not_subscribed(
        self, authenticated_client, setup_learning_content
    ):
        url = reverse("api:v1:study:start-level-assessment")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_assessment_success(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = None
        profile.current_level_quantitative = None
        profile.save()

        url = reverse("api:v1:study:start-level-assessment")
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

        # Check configuration snapshot for requested questions
        # FIX: Correct way to check for attribute existence and its value
        assert hasattr(
            attempt, "test_configuration"
        ), "UserTestAttempt instance should have 'test_configuration' attribute"
        assert (
            attempt.test_configuration is not None
        ), "'test_configuration' should not be None"

        # Now it's safe to access it as a dictionary
        assert (
            "num_questions_requested" in attempt.test_configuration
        ), "'num_questions_requested' key should be in test_configuration"
        assert (
            attempt.test_configuration.get("num_questions_requested")
            == num_questions_requested
        ), "The 'num_questions_requested' in config should match the input"

        # Also good to check 'num_questions_selected' reflects what's in question_ids
        # and the response questions count
        assert "num_questions_selected" in attempt.test_configuration
        assert attempt.test_configuration.get("num_questions_selected") == len(
            attempt.question_ids
        )
        assert attempt.test_configuration.get("num_questions_selected") == len(
            response.data["questions"]
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
        url = reverse("api:v1:study:start-level-assessment")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check for generic ongoing attempt message within the 'detail' key
        assert "detail" in response.data
        assert "You already have an ongoing test attempt." in str(
            response.data["detail"]
        ) or "Please complete or cancel your ongoing test" in str(
            response.data["detail"]
        )

    def test_start_assessment_invalid_section_slug(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:start-level-assessment")
        payload = {"sections": ["verbal", "invalid-slug"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # FIX: Check for 'sections' key within response.data['detail']
        assert "detail" in response.data
        assert "sections" in response.data["detail"]
        # Optionally, check the specific error message content
        error_message = str(response.data["detail"]["sections"])
        assert "Object with slug=invalid-slug does not exist." in error_message

    def test_start_assessment_invalid_num_questions(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:start-level-assessment")
        payload = {
            "sections": ["verbal"],
            "num_questions": 2,
        }  # Below min value (e.g. 5)
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # FIX: Check for 'num_questions' key within response.data['detail']
        assert "detail" in response.data
        assert "num_questions" in response.data["detail"]
        # Optionally, check the specific error message content
        error_message = str(response.data["detail"]["num_questions"])
        assert (
            "Ensure this value is greater than or equal to" in error_message
        )  # Check part of the message

    def test_start_assessment_no_active_questions_available(
        self, subscribed_client, setup_learning_content
    ):
        Question.objects.update(is_active=False)
        url = reverse("api:v1:study:start-level-assessment")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # FIX: Check for the specific error message within response.data['detail']
        assert "detail" in response.data
        error_message = str(response.data["detail"])
        assert "Not enough questions found matching your criteria" in error_message
        assert "need at least 1" in error_message


# --- REMOVED Submit Tests ---
# Class TestLevelAssessmentSubmitAPI and its methods are removed.
# The functionality is now tested within the new unified attempt lifecycle tests.
