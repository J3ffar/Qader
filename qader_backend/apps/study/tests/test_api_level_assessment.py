import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import Question
from apps.users.models import UserProfile
from apps.study.tests.factories import UserTestAttemptFactory

# Factories and fixtures are assumed available via conftest files

pytestmark = pytest.mark.django_db


class TestLevelAssessmentAPI:

    # --- Tests for Start Endpoint ---

    def test_start_assessment_unauthenticated(self, api_client, setup_learning_content):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_assessment_not_subscribed(
        self, authenticated_client, setup_learning_content
    ):  # Uses unsubscribed user
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "subscription is required" in str(response.data).lower()

    def test_start_assessment_success(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = None  # Ensure level not set
        profile.current_level_quantitative = None
        profile.save()
        assert not profile.level_determined  # Pre-condition

        url = reverse("api:v1:study:level-assessment-start")
        num_questions_requested = 20
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions_requested,
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "attempt_id" in response.data
        assert "questions" in response.data
        assert isinstance(response.data["questions"], list)
        assert (
            len(response.data["questions"]) == num_questions_requested
        )  # Assume enough questions exist from setup
        if response.data["questions"]:
            assert (
                "is_starred" in response.data["questions"][0]
            )  # Check serializer field

        # Verify DB
        attempt = UserTestAttempt.objects.get(pk=response.data["attempt_id"])
        assert attempt.user == user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
        assert (
            attempt.test_configuration["num_questions_requested"]
            == num_questions_requested
        )
        assert len(attempt.question_ids) == num_questions_requested

    def test_start_assessment_level_already_determined(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = 80.0  # Set levels
        profile.current_level_quantitative = 70.0
        profile.save()
        assert profile.level_determined  # Pre-condition

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Your level has already been determined" in str(response.data)

    def test_start_assessment_invalid_section_slug(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "invalid-slug"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data
        # DRF error structure for invalid SlugRelatedField
        assert "object with slug=invalid-slug does not exist" in str(
            response.data["sections"]
        )

    def test_start_assessment_missing_sections(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data and "required" in str(
            response.data["sections"]
        )

    def test_start_assessment_invalid_num_questions(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 2}  # Below min_value=5
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # --- ADJUSTED ASSERTION ---
        assert "num_questions" in response.data
        assert "Ensure this value is greater than or equal to 5." in str(
            response.data["num_questions"]
        )
        # --- END ADJUSTED ASSERTION ---

    def test_start_assessment_no_active_questions_available(
        self, subscribed_client, setup_learning_content
    ):
        Question.objects.update(is_active=False)  # Deactivate all
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Not enough active questions available" in str(response.data)

    def test_start_assessment_ongoing_attempt_exists(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        UserTestAttempt.objects.create(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            question_ids=[1],
        )  # Create ongoing LA attempt
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already have an ongoing level assessment" in str(response.data)

    # --- Tests for Submit Endpoint ---

    @pytest.fixture
    def started_assessment(self, subscribed_client, setup_learning_content):
        """Fixture to start a level assessment and return its details."""
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = None  # Ensure level not set
        profile.current_level_quantitative = None
        profile.save()

        start_url = reverse("api:v1:study:level-assessment-start")
        num_questions = 5
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions,
        }
        start_response = subscribed_client.post(start_url, payload, format="json")
        assert start_response.status_code == status.HTTP_201_CREATED

        attempt = UserTestAttempt.objects.get(pk=start_response.data["attempt_id"])
        questions = list(Question.objects.filter(id__in=attempt.question_ids))
        return {"attempt": attempt, "questions": questions, "user": user}

    def test_submit_assessment_success(self, subscribed_client, started_assessment):
        attempt = started_assessment["attempt"]
        questions = started_assessment["questions"]
        user = started_assessment["user"]
        profile = user.profile
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )

        # Prepare answers (mix correct/incorrect)
        answers_payload = []
        correct_count = 0
        for i, q in enumerate(questions):
            selected = (
                q.correct_answer if i < 3 else ("A" if q.correct_answer != "A" else "B")
            )  # 3 correct
            answers_payload.append({"question_id": q.id, "selected_answer": selected})
            if selected == q.correct_answer:
                correct_count += 1

        response = subscribed_client.post(
            submit_url, {"answers": answers_payload}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempt_id"] == attempt.id
        assert "results" in response.data
        assert "updated_profile" in response.data

        # Check results
        results = response.data["results"]
        expected_overall = pytest.approx(
            (correct_count / len(questions)) * 100.0, abs=0.1
        )
        assert results["overall_score"] == expected_overall
        assert results["verbal_score"] is not None
        assert results["quantitative_score"] is not None

        # Check updated profile in response
        profile_resp = response.data["updated_profile"]
        assert profile_resp["level_determined"] is True
        assert profile_resp["current_level_verbal"] == pytest.approx(
            results["verbal_score"], abs=0.1
        )
        assert profile_resp["current_level_quantitative"] == pytest.approx(
            results["quantitative_score"], abs=0.1
        )

        # Check DB state
        attempt.refresh_from_db()
        profile.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.score_percentage == expected_overall
        assert UserQuestionAttempt.objects.filter(test_attempt=attempt).count() == len(
            questions
        )
        assert profile.level_determined is True
        assert profile.current_level_verbal == pytest.approx(
            results["verbal_score"], abs=0.1
        )

    def test_submit_assessment_unauthenticated(self, api_client, started_assessment):
        attempt = started_assessment["attempt"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.post(
            submit_url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_assessment_not_subscribed(
        self, authenticated_client
    ):  # Uses unsubscribed user
        # Create a started LA for this user
        attempt = UserTestAttemptFactory(
            user=authenticated_client.user,
            level_assessment=True,
            status=UserTestAttempt.Status.STARTED,
            question_ids=[1, 2],
        )
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.post(
            submit_url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )  # Payload structure needed
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_assessment_not_owner(
        self, authenticated_client, started_assessment
    ):  # Client != owner
        attempt = started_assessment["attempt"]  # Belongs to subscribed_user
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.post(
            submit_url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_assessment_invalid_attempt_id(self, subscribed_client):
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": 9999}
        )
        response = subscribed_client.post(
            submit_url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_assessment_already_completed(
        self, subscribed_client, started_assessment
    ):
        attempt = started_assessment["attempt"]
        attempt.status = UserTestAttempt.Status.COMPLETED  # Mark as completed
        attempt.save()
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(
            submit_url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "is not active or is not a level assessment" in str(
            response.data
        )  # Error reflects status check

    def test_submit_assessment_mismatched_answers(
        self, subscribed_client, started_assessment
    ):
        attempt = started_assessment["attempt"]
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        # Submit answers for different questions
        wrong_qids = [q.id + 1000 for q in questions]
        answers_payload = [
            {"question_id": qid, "selected_answer": "A"} for qid in wrong_qids
        ]
        response = subscribed_client.post(
            submit_url, {"answers": answers_payload}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Mismatch between submitted answers" in str(response.data)
