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
from apps.users.models import UserProfile

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

    # test_start_assessment_unauthenticated - remains the same
    def test_start_assessment_unauthenticated(self, api_client, setup_learning_content):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # test_start_assessment_not_subscribed - remains the same
    def test_start_assessment_not_subscribed(
        self, authenticated_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "subscription is required" in response.data["detail"].lower()

    def test_start_assessment_success(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        # Ensure profile exists and level is not determined
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = None
        profile.current_level_quantitative = None
        profile.save()
        assert not profile.level_determined  # Pre-condition check via property

        url = reverse("api:v1:study:level-assessment-start")
        num_questions_requested = 20
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions_requested,
        }
        response = subscribed_client.post(url, payload, format="json")

        print("Start Assessment Success Response:", response.data)  # Debug output

        assert response.status_code == status.HTTP_201_CREATED
        assert "attempt_id" in response.data
        assert "questions" in response.data
        assert isinstance(response.data["questions"], list)
        assert len(response.data["questions"]) == num_questions_requested
        # Check structure of a question item
        if num_questions_requested > 0:
            first_q = response.data["questions"][0]
            assert "id" in first_q
            assert "question_text" in first_q
            assert "option_a" in first_q
            assert "is_starred" in first_q  # Check field from QuestionListSerializer

        attempt_id = response.data["attempt_id"]
        attempt = UserTestAttempt.objects.get(pk=attempt_id)
        assert attempt.user == user
        assert attempt.status == UserTestAttempt.Status.STARTED
        # Check the NEW attempt_type field
        assert attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
        # Check configuration snapshot content
        assert attempt.test_configuration["sections_requested"] == [
            "verbal",
            "quantitative",
        ]
        assert (
            attempt.test_configuration["num_questions_requested"]
            == num_questions_requested
        )
        assert len(attempt.question_ids) == num_questions_requested
        assert set(attempt.question_ids) == {
            q["id"] for q in response.data["questions"]
        }

        # Check profile hasn't been updated yet
        profile.refresh_from_db()
        assert not profile.level_determined

    def test_start_assessment_level_already_determined(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        # Ensure profile exists and set levels
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.current_level_verbal = 85.0
        profile.current_level_quantitative = 75.0
        profile.save()
        assert profile.level_determined  # Verify property works

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert "already completed" in response.data["non_field_errors"][0]

    # test_start_assessment_invalid_section_slug - remains the same
    def test_start_assessment_invalid_section_slug(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "invalid-slug"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data
        assert "invalid-slug" in response.data["sections"][0]

    # test_start_assessment_missing_sections - remains the same
    def test_start_assessment_missing_sections(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"num_questions": 10}  # Missing 'sections'
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "sections" in response.data

    # test_start_assessment_invalid_num_questions - remains the same
    def test_start_assessment_invalid_num_questions(
        self, subscribed_client, setup_learning_content
    ):
        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 2}  # Below min_value
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "num_questions" in response.data

    def test_start_assessment_no_active_questions_available(
        self, subscribed_client, setup_learning_content
    ):
        # Deactivate all questions AFTER setup
        Question.objects.update(is_active=False)

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal", "quantitative"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        # Validation should now catch this definitively if count is too low
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "Not enough active questions available"
            in response.data["non_field_errors"][0]
        )

    def test_start_assessment_ongoing_attempt_exists(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        # Manually create an ongoing assessment attempt with the correct type
        UserTestAttempt.objects.create(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Correct type
            question_ids=[1, 2, 3],  # Add some dummy IDs
        )

        url = reverse("api:v1:study:level-assessment-start")
        payload = {"sections": ["verbal"], "num_questions": 10}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert "already have an ongoing" in response.data["non_field_errors"][0]

    # --- Tests for POST /api/v1/study/level-assessment/{attempt_id}/submit/ ---

    @pytest.fixture
    def started_assessment(self, subscribed_client, setup_learning_content):
        """Fixture to start an assessment and return its details."""
        user = subscribed_client.user
        # Ensure profile exists for the user
        UserProfile.objects.get_or_create(user=user)

        start_url = reverse("api:v1:study:level-assessment-start")
        num_questions = 5  # Use a small number for easier testing
        payload = {
            "sections": ["verbal", "quantitative"],
            "num_questions": num_questions,
        }
        start_response = subscribed_client.post(start_url, payload, format="json")
        assert start_response.status_code == status.HTTP_201_CREATED

        attempt_id = start_response.data["attempt_id"]
        attempt = UserTestAttempt.objects.get(pk=attempt_id)
        # Fetch questions based on the attempt's question_ids
        questions = Question.objects.filter(id__in=attempt.question_ids)

        return {
            "attempt_id": attempt_id,
            "questions": list(questions),  # Return as list
            "attempt": attempt,
            "user": user,
        }

    def test_submit_assessment_success(self, subscribed_client, started_assessment):
        user = started_assessment["user"]
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        attempt = started_assessment["attempt"]

        profile = user.profile
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert not profile.level_determined  # Check via property

        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )

        # Prepare answers (make some correct, some incorrect)
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

        print("Submit Response Data:", response.data)  # Debug output

        assert response.status_code == status.HTTP_200_OK
        assert response.data["attempt_id"] == attempt_id
        assert "results" in response.data
        assert "updated_profile" in response.data

        # Check results structure
        results = response.data["results"]
        expected_overall = (
            round((correct_count / len(questions) * 100), 2) if questions else 0.0
        )
        assert abs(results["overall_score"] - expected_overall) < 0.1  # Float tolerance
        assert "verbal_score" in results
        assert "quantitative_score" in results
        assert "proficiency_summary" in results
        assert isinstance(results["proficiency_summary"], dict)  # Check it's a dict

        # Check updated_profile structure (uses UserProfileSerializer)
        updated_profile_resp = response.data["updated_profile"]
        assert updated_profile_resp["user"]["id"] == user.id
        assert updated_profile_resp["user"]["username"] == user.username
        assert (
            updated_profile_resp["level_determined"] is True
        )  # Check property in response
        assert (
            abs(updated_profile_resp["current_level_verbal"] - results["verbal_score"])
            < 0.1
        )
        assert (
            abs(
                updated_profile_resp["current_level_quantitative"]
                - results["quantitative_score"]
            )
            < 0.1
        )
        assert "subscription" in updated_profile_resp  # Check nested serializer data
        assert (
            updated_profile_resp["subscription"]["is_active"] is True
        )  # Assuming user is subscribed

        # Check database state: UserTestAttempt
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert abs(attempt.score_percentage - expected_overall) < 0.1
        assert attempt.results_summary is not None
        assert isinstance(attempt.results_summary, dict)

        # Check database state: UserQuestionAttempt
        question_attempts = UserQuestionAttempt.objects.filter(test_attempt=attempt)
        assert question_attempts.count() == len(questions)
        # Check one attempt in detail
        first_q_attempt = question_attempts.order_by("pk").first()
        if first_q_attempt:
            assert first_q_attempt.user == user
            assert first_q_attempt.test_attempt == attempt
            assert first_q_attempt.mode == UserQuestionAttempt.Mode.LEVEL_ASSESSMENT
            assert first_q_attempt.is_correct is not None  # Should be calculated

        # Check database state: UserProfile
        profile.refresh_from_db()
        assert profile.level_determined is True  # Check property again
        assert abs(profile.current_level_verbal - results["verbal_score"]) < 0.1
        assert (
            abs(profile.current_level_quantitative - results["quantitative_score"])
            < 0.1
        )

    # Test 2: Unauthenticated (No change needed, uses api_client)
    def test_submit_assessment_unauthenticated(self, api_client, started_assessment):
        attempt_id = started_assessment["attempt_id"]
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        payload = {"answers": answers_payload}
        response = api_client.post(submit_url, payload, format="json")
        # Now this assertion should pass
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Test 3: Not Subscribed (Use the unsubscribed client)
    def test_submit_assessment_not_subscribed(
        self,
        authenticated_client,  # This client fixture is now the unsubscribed user
        started_assessment,  # This attempt belongs to the subscribed_user
    ):
        # Create a new attempt for the *non-subscribed* user first
        non_sub_user = authenticated_client.user  # User from the fixture
        # Profile creation is handled in the fixture now
        questions_for_attempt = Question.objects.filter(is_active=True)[:5]
        attempt = UserTestAttempt.objects.create(
            user=non_sub_user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            question_ids=[q.id for q in questions_for_attempt],
        )

        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions_for_attempt
        ]
        payload = {"answers": answers_payload}

        response = authenticated_client.post(submit_url, payload, format="json")
        # Now this assertion should pass (IsSubscribed should block)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test 4: Not Owner (Use the unsubscribed client against the subscribed user's attempt)
    def test_submit_assessment_not_owner(
        self,
        authenticated_client,  # This client is distinct and unsubscribed
        started_assessment,  # This attempt belongs to subscribed_user
    ):
        attempt_id = started_assessment[
            "attempt_id"
        ]  # Attempt belongs to subscribed_user
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        payload = {"answers": answers_payload}

        # Use the distinct authenticated_client
        response = authenticated_client.post(submit_url, payload, format="json")

        # Serializer validation should now catch ownership issue
        # Now this assertion should pass
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "not found or does not belong to you"
            in response.data["non_field_errors"][0]
        )

    def test_submit_assessment_invalid_attempt_id(self, subscribed_client):
        invalid_id = 99999
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": invalid_id}
        )
        # Need a valid-looking payload structure even if ID is wrong
        payload = {"answers": [{"question_id": 1, "selected_answer": "A"}]}
        response = subscribed_client.post(submit_url, payload, format="json")
        # Serializer validation catches this
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "not found or does not belong to you"
            in response.data["non_field_errors"][0]
        )

    # test_submit_assessment_already_completed - remains the same logic
    def test_submit_assessment_already_completed(
        self, subscribed_client, started_assessment
    ):
        attempt = started_assessment["attempt"]
        attempt.status = UserTestAttempt.Status.COMPLETED
        attempt.save()
        questions = started_assessment["questions"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt.id}
        )
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions
        ]
        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "not active or has already been submitted"
            in response.data["non_field_errors"][0]
        )

    # test_submit_assessment_missing_answers_field - remains the same
    def test_submit_assessment_missing_answers_field(
        self, subscribed_client, started_assessment
    ):
        attempt_id = started_assessment["attempt_id"]
        submit_url = reverse(
            "api:v1:study:level-assessment-submit", kwargs={"attempt_id": attempt_id}
        )
        payload = {}
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
        answers_payload = [
            {"question_id": q.id, "selected_answer": "A"} for q in questions[:-1]
        ]
        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        assert (
            isinstance(response.data["answers"], list)
            and len(response.data["answers"]) > 0
        )
        first_error = response.data["answers"][0]
        assert "Mismatch between submitted answers" in first_error
        # Check nested detail structure if available
        if len(response.data["answers"]) > 1 and isinstance(
            response.data["answers"][1], dict
        ):
            assert "missing_answers_for_question_ids" in response.data["answers"][1]

    def test_submit_assessment_extra_answer(
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
        answers_payload.append({"question_id": 99999, "selected_answer": "B"})  # Extra
        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        assert (
            isinstance(response.data["answers"], list)
            and len(response.data["answers"]) > 0
        )
        first_error = response.data["answers"][0]
        assert "Mismatch between submitted answers" in first_error
        if len(response.data["answers"]) > 1 and isinstance(
            response.data["answers"][1], dict
        ):
            assert "unexpected_answers_for_question_ids" in response.data["answers"][1]

    # test_submit_assessment_invalid_answer_choice - remains the same
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
        if answers_payload:  # Ensure list is not empty
            answers_payload[0]["selected_answer"] = "E"  # Invalid choice

        payload = {"answers": answers_payload}
        response = subscribed_client.post(submit_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "answers" in response.data
        # Error structure is nested: {'answers': [ {'selected_answer': ['"E" is not a valid choice.']} ]}
        assert (
            isinstance(response.data["answers"], list)
            and len(response.data["answers"]) > 0
        )
        assert "selected_answer" in response.data["answers"][0]
        assert "not a valid choice" in response.data["answers"][0]["selected_answer"][0]
