import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone

# Import models from study and learning apps
from apps.study.models import UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import LearningSection, Question

# Import factories
from apps.learning.tests.factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    QuestionFactory,
)

# Import existing user fixtures (implicitly available via conftest.py)
# from apps.users.tests.factories import UserFactory, SubscribedUserFactory (Not needed directly)

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


@pytest.fixture
def setup_learning_content():
    """Fixture to create necessary learning sections, subsections, and questions."""
    verbal_section = LearningSectionFactory(name="Verbal Section", slug="verbal")
    quant_section = LearningSectionFactory(
        name="Quantitative Section", slug="quantitative"
    )

    verbal_sub1 = LearningSubSectionFactory(
        section=verbal_section, name="Reading Comp", slug="reading-comp"
    )
    verbal_sub2 = LearningSubSectionFactory(
        section=verbal_section, name="Analogy", slug="analogy"
    )
    quant_sub1 = LearningSubSectionFactory(
        section=quant_section, name="Algebra", slug="algebra"
    )
    quant_sub2 = LearningSubSectionFactory(
        section=quant_section, name="Geometry", slug="geometry"
    )

    # Create enough questions for testing pagination and selection
    # Make sure they are active
    QuestionFactory.create_batch(15, subsection=verbal_sub1, is_active=True)
    QuestionFactory.create_batch(15, subsection=verbal_sub2, is_active=True)
    QuestionFactory.create_batch(15, subsection=quant_sub1, is_active=True)
    QuestionFactory.create_batch(15, subsection=quant_sub2, is_active=True)

    return {
        "verbal_section": verbal_section,
        "quant_section": quant_section,
    }


class TestLevelAssessmentAPI:
    # --- Tests for POST /api/v1/study/level-assessment/start/ ---

    def test_start_assessment_unauthenticated(self, api_client, setup_learning_content):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_assessment_not_subscribed(
        self, authenticated_client, setup_learning_content
    ):
        # `authenticated_client` uses a user who is not subscribed by default
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "subscription is required" in response.data["detail"].lower()

    def test_start_assessment_success(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        assert not user.profile.level_determined  # Pre-condition

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
        assert len(response.data["questions"]) == num_questions_requested

        attempt_id = response.data["attempt_id"]
        attempt = UserTestAttempt.objects.get(pk=attempt_id)
        assert attempt.user == user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.test_configuration["assessment_type"] == "level"
        assert set(attempt.test_configuration["sections"]) == {
            "verbal",
            "quantitative",
        }
        assert (
            attempt.test_configuration["requested_num_questions"]
            == num_questions_requested
        )
        assert len(attempt.question_ids) == num_questions_requested
        assert set(attempt.question_ids) == {
            q["id"] for q in response.data["questions"]
        }

        # Check profile hasn't been updated yet
        user.profile.refresh_from_db()
        assert not user.profile.level_determined

    def test_start_assessment_level_already_determined(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        user.profile.current_level_verbal = 85.0
        user.profile.current_level_quantitative = 75.0
        user.profile.save()

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already completed" in response.data["non_field_errors"][0]

    def test_start_assessment_invalid_section_slug(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "invalid-slug"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data
        assert "invalid-slug" in response.data["sections"][0]  # Check error message

    def test_start_assessment_missing_sections(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"num_questions": 10}  # Missing 'sections'
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data

    def test_start_assessment_invalid_num_questions(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 2}  # Below min_value
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "num_questions" in response.data

    def test_start_assessment_no_questions_available(
        self, subscribed_client, setup_learning_content
    ):
        # Deactivate all questions
        Question.objects.update(is_active=False)

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        # The serializer's create method handles this case
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No active questions found" in response.data["non_field_errors"][0]

    def test_start_assessment_ongoing_attempt_exists(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        # Manually create an ongoing assessment attempt
        UserTestAttempt.objects.create(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            test_configuration={"assessment_type": "level"},  # Needs the marker
        )

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already have an ongoing" in response.data["non_field_errors"][0]

    # --- Tests for POST /api/v1/study/level-assessment/{attempt_id}/submit/ ---

    @pytest.fixture
    def started_assessment(self, subscribed_client, setup_learning_content):
        """Fixture to start an assessment and return its details."""
        start_url = reverse("api:v1:study:level-assessment-start")
        num_questions = 5  # Use a small number for easier testing
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions,
        }
        start_response = subscribed_client.post(start_url, payload, format="json")
        assert start_response.status_code == status.HTTP_201_CREATED

        attempt_id = start_response.data["attempt_id"]
        questions = Question.objects.filter(
            id__in=[q["id"] for q in start_response.data["questions"]]
        )
        return {
            "attempt_id": attempt_id,
            "questions": questions,
            "attempt": UserTestAttempt.objects.get(pk=attempt_id),
        }

    def test_submit_assessment_success(self, subscribed_client, started_assessment):
        user = subscribed_client.user
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        attempt = started_assessment["attempt"]

        assert attempt.status == UserTestAttempt.Status.STARTED
        assert not user.profile.level_determined

        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        # Prepare answers (let's make some correct, some incorrect)
        answers_payload = []
        correct_count = 0
        for i, q in enumerate(questions):
            selected = (
                q.correct_answer
                if i % 2 == 0
                else ("A" if q.correct_answer != "A" else "B")
            )
            answers_payload.append(
                {
                    "question_id": q.id,
                    "selected_answer": selected,
                    "time_taken_seconds": 30 + i,
                }
            )
            if selected == q.correct_answer:
                correct_count += 1

        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempt_id"] == attempt_id
        assert "results" in response.data
        assert "updated_profile" in response.data

        # Check results structure (scores might vary slightly due to rounding)
        results = response.data["results"]
        expected_overall = (
            round((correct_count / len(questions) * 100), 2) if questions else 0.0
        )
        assert (
            abs(results["overall_score"] - expected_overall) < 0.1
        )  # Allow for float tolerance
        assert "verbal_score" in results
        assert "quantitative_score" in results
        assert "proficiency_summary" in results

        # Check profile update response
        updated_profile = response.data["updated_profile"]
        assert updated_profile["level_determined"] is True
        assert (
            abs(updated_profile["current_level_verbal"] - results["verbal_score"]) < 0.1
        )
        assert (
            abs(
                updated_profile["current_level_quantitative"]
                - results["quantitative_score"]
            )
            < 0.1
        )

        # Check database state: UserTestAttempt
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert abs(attempt.score_percentage - expected_overall) < 0.1
        assert attempt.results_summary is not None

        # Check database state: UserQuestionAttempt
        question_attempts = UserQuestionAttempt.objects.filter(test_attempt=attempt)
        assert question_attempts.count() == len(questions)
        for i, q_attempt in enumerate(
            question_attempts.order_by("pk")
        ):  # Order for consistency
            assert q_attempt.user == user
            assert (
                q_attempt.question == questions[i]
            )  # Assuming order is maintained or test fails
            assert q_attempt.selected_answer == answers_payload[i]["selected_answer"]
            assert q_attempt.is_correct == (
                q_attempt.selected_answer == q_attempt.question.correct_answer
            )
            assert q_attempt.mode == UserQuestionAttempt.Mode.LEVEL_ASSESSMENT

        # Check database state: UserProfile
        user.profile.refresh_from_db()
        assert user.profile.level_determined is True
        assert abs(user.profile.current_level_verbal - results["verbal_score"]) < 0.1
        assert (
            abs(user.profile.current_level_quantitative - results["quantitative_score"])
            < 0.1
        )

    def test_submit_assessment_unauthenticated(self, api_client, started_assessment):
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]  # Get questions from fixture
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )
        # Create a structurally valid payload matching the expected questions
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        payload = {"answers": answers_payload}  # Use the valid structure
        response = api_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_assessment_not_subscribed(
        self, authenticated_client, started_assessment
    ):
        # Need to create the attempt for the *non-subscribed* user first
        user = authenticated_client.user
        attempt = UserTestAttempt.objects.create(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            question_ids=[q.id for q in started_assessment["questions"]],
            test_configuration={"assessment_type": "level"},
        )

        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        # Create minimal valid payload structure
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"}
            for q in started_assessment["questions"]
        ]
        payload = {"answers": answers_payload}

        response = authenticated_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_assessment_not_owner(
        self, authenticated_client, subscribed_client, started_assessment
    ):
        # `started_assessment` belongs to `subscribed_client.user` (the owner)
        attempt_id = started_assessment["attempt_id"]
        # *** Get the questions associated with the owner's attempt ***
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        # *** Create a structurally valid payload matching the questions ***
        # The content of selected_answer doesn't matter here, just the structure
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        payload = {"answers": answers_payload}  # Use the valid structure

        # Use a different authenticated client (who is NOT the owner)
        # Ensure this client is *subscribed* if IsSubscribed runs first,
        # otherwise the 403 might mask the ownership error. If authenticated_client
        # fixture is unsubscribed, create a separate subscribed user/client for this test.
        # For now, let's assume authenticated_client might work if IsSubscribed check isn't the issue.
        response = authenticated_client.post(submit_url, payload, format="json")

        # The serializer validation should now fail on the ownership check
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # print("Response Data (Not Owner):", response.data) # Optional: Keep for debug

        # Now, check for the specific ownership error message.
        # It's raised as a simple string, likely ending up in 'detail'.
        error_message = response.data.get("detail")
        if error_message:
            assert (
                "not found or does not belong to you" in error_message
            ), f"Expected owner error message but got: {error_message}"
        else:
            # Fallback check if it somehow landed in non_field_errors
            error_list = response.data.get("non_field_errors", [])
            assert (
                len(error_list) > 0
            ), "Expected owner error in 'detail' or 'non_field_errors'"
            assert (
                "not found or does not belong to you" in error_list[0]
            ), f"Expected owner error message but got: {error_list}"

    def test_submit_assessment_invalid_attempt_id(self, subscribed_client):
        invalid_id = 99999
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": invalid_id}
        )
        payload = {"answers": []}
        response = subscribed_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_submit_assessment_already_completed(
        self, subscribed_client, started_assessment
    ):
        attempt = started_assessment["attempt"]
        attempt.status = UserTestAttempt.Status.COMPLETED
        attempt.save()

        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        payload = {"answers": []}
        response = subscribed_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "not active or has already been submitted"
            in response.data["non_field_errors"][0]
        )

    def test_submit_assessment_missing_answers_field(
        self, subscribed_client, started_assessment
    ):
        attempt_id = started_assessment["attempt_id"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )
        payload = {}  # Missing "answers" key
        response = subscribed_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data

    def test_submit_assessment_missing_one_answer(
        self, subscribed_client, started_assessment
    ):
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        # Prepare payload with one less answer than expected
        questions_list = list(questions)  # <-- Convert to list
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"}
            for q in questions_list[:-1]  # <-- Slice the list
        ]
        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        assert "Mismatch between submitted answers" in response.data["answers"][0]
        assert (
            "missing_answers_for_ids" in response.data
        )  # Check the detailed error keys

    def test_submit_assessment_extra_answer(
        self, subscribed_client, started_assessment
    ):
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        # Prepare payload with all expected answers plus one extra invalid one
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        answers_payload.append({"question_id": 99999, "selected_answer": "B"})  # Extra
        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        assert "Mismatch between submitted answers" in response.data["answers"][0]
        assert (
            "unexpected_answers_for_ids" in response.data
        )  # Check the detailed error keys

    def test_submit_assessment_invalid_answer_choice(
        self, subscribed_client, started_assessment
    ):
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        answers_payload[0]["selected_answer"] = "E"  # Invalid choice

        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        # Error structure might be nested like: {'answers': [ {'selected_answer': ['"E" is not a valid choice.']} ]}
        assert "selected_answer" in response.data["answers"][0]
        assert "not a valid choice" in response.data["answers"][0]["selected_answer"][0]
