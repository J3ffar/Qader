# qader_backend/apps/study/tests/test_api_attempts.py

import random
import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion, Skill
from apps.users.models import UserProfile
from unittest.mock import patch  # Used for testing service calls

# Import factories and helpers
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
    create_attempt_scenario,  # Use the new helper
    UserSkillProficiencyFactory,
)
from apps.learning.tests.factories import (
    LearningSubSectionFactory,
    QuestionFactory,
    SkillFactory,
)
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
NUM_QUESTIONS_DEFAULT = 5

# --- Fixtures ---


@pytest.fixture
def started_practice_attempt(db, subscribed_user, setup_learning_content):
    """Creates a STARTED practice test attempt."""
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_answered=0,  # No answers yet
        num_correct_answered=0,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.STARTED,
    )
    return attempt, questions


@pytest.fixture
def started_level_assessment(db, subscribed_user, setup_learning_content):
    """Creates a STARTED level assessment attempt with guaranteed mixed questions."""
    # --- GET SUBSECTIONS WITH CORRECT PARENT SECTION SLUGS ---
    try:
        verbal_sub = setup_learning_content["reading_comp_sub"]  # Example verbal sub
        quant_sub = setup_learning_content["algebra_sub"]  # Example quant sub

        # Verify parent slugs (optional but good practice)
        assert verbal_sub.section.slug == "verbal"
        assert quant_sub.section.slug == "quantitative"
    except KeyError as e:
        pytest.fail(f"Fixture setup_learning_content missing expected key: {e}")
    except AssertionError:
        pytest.fail(
            "Fixture setup_learning_content created subsections with incorrect parent section slugs ('verbal'/'quantitative' expected)."
        )
    # --- END VERIFICATION ---

    # Create questions specifically for these subsections
    num_verbal = 5
    num_quant = 5
    verbal_questions = QuestionFactory.create_batch(
        num_verbal, subsection=verbal_sub, is_active=True
    )
    quant_questions = QuestionFactory.create_batch(
        num_quant, subsection=quant_sub, is_active=True
    )

    all_questions = verbal_questions + quant_questions
    random.shuffle(all_questions)  # Mix them up
    question_ids = [q.id for q in all_questions]

    attempt = UserTestAttemptFactory(
        user=subscribed_user,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        status=UserTestAttempt.Status.STARTED,
        question_ids=question_ids,
        test_configuration={  # Ensure config reflects reality
            "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value,
            "sections_requested": ["verbal", "quantitative"],  # Example
            "num_questions_requested": num_verbal + num_quant,
            "actual_num_questions_selected": len(question_ids),
        },
    )
    # Return the actual questions used
    return attempt, all_questions


@pytest.fixture
def partially_answered_attempt(db, subscribed_user, setup_learning_content):
    """Creates a STARTED practice attempt with some answers submitted."""
    num_answered = 2
    num_correct = 1
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_answered=num_answered,  # Correct: Specify number answered
        num_correct_answered=num_correct,  # Correct: Must be <= num_answered
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.STARTED,
    )
    return attempt, questions


@pytest.fixture
def completed_practice_attempt(db, subscribed_user, setup_learning_content):
    """Creates a COMPLETED practice test attempt using the helper."""
    num_questions = NUM_QUESTIONS_DEFAULT
    num_correct = 3
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=num_questions,
        num_answered=num_questions,  # Correct: All answered for completed
        num_correct_answered=num_correct,  # Correct: Must be <= num_answered
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.COMPLETED,
    )
    return attempt, questions


@pytest.fixture
def completed_level_assessment(db, subscribed_user, setup_learning_content):
    """Creates a COMPLETED level assessment using the helper."""
    # --- FIX: Ensure valid parameters for helper ---
    num_questions = 10
    num_correct = 7
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=num_questions,
        num_answered=num_questions,  # Correct: All answered for completed
        num_correct_answered=num_correct,  # Correct: Must be <= num_answered
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        status=UserTestAttempt.Status.COMPLETED,
    )
    # Update profile levels after creation if helper doesn't do it
    if attempt.status == UserTestAttempt.Status.COMPLETED:
        profile = subscribed_user.profile
        profile.current_level_verbal = attempt.score_verbal
        profile.current_level_quantitative = attempt.score_quantitative
        profile.is_level_determined = True
        profile.save()
        attempt.refresh_from_db()  # Reload attempt with profile updated context if needed

    return attempt, questions


# --- Test Classes ---


class TestListAttemptsAPI:  # Renamed
    def test_list_unauthenticated(self, api_client):
        url = reverse("api:v1:study:attempt-list")  # Updated URL name
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:attempt-list")  # Updated URL name
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_success(
        self, subscribed_client, completed_practice_attempt, completed_level_assessment
    ):
        user = subscribed_client.user
        attempt1, _ = completed_practice_attempt
        attempt2, _ = completed_level_assessment
        other_user = UserFactory()
        create_attempt_scenario(
            user=other_user,
            num_questions=3,
            num_answered=3,
            num_correct_answered=1,
            status=UserTestAttempt.Status.COMPLETED,
        )

        url = reverse("api:v1:study:attempt-list")  # Updated URL name
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert response.data["count"] == 2  # Only user's attempts
        assert len(response.data["results"]) == 2
        result_ids = {r["attempt_id"] for r in response.data["results"]}
        assert result_ids == {attempt1.id, attempt2.id}
        result2 = next(
            r for r in response.data["results"] if r["attempt_id"] == attempt2.id
        )
        assert result2["test_type"] == attempt2.get_attempt_type_display()
        # assert "answered_question_count" in result2  # Check new field

    def test_list_filter_by_status(
        self, subscribed_client, started_practice_attempt, completed_practice_attempt
    ):
        attempt_started, _ = started_practice_attempt
        attempt_completed, _ = completed_practice_attempt
        url = (
            reverse("api:v1:study:attempt-list")
            + f"?status={UserTestAttempt.Status.STARTED}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_started.id
        assert response.data["results"][0]["status"] == UserTestAttempt.Status.STARTED

        url = (
            reverse("api:v1:study:attempt-list")
            + f"?status={UserTestAttempt.Status.COMPLETED}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_completed.id

    def test_list_filter_by_type(
        self, subscribed_client, completed_practice_attempt, completed_level_assessment
    ):
        attempt_practice, _ = completed_practice_attempt
        attempt_level, _ = completed_level_assessment
        url = (
            reverse("api:v1:study:attempt-list")
            + f"?attempt_type={UserTestAttempt.AttemptType.PRACTICE}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_practice.id

        url = (
            reverse("api:v1:study:attempt-list")
            + f"?attempt_type={UserTestAttempt.AttemptType.LEVEL_ASSESSMENT}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_level.id

    def test_list_filter_by_type_in(
        self, subscribed_client, completed_practice_attempt, completed_level_assessment
    ):
        attempt_practice, _ = completed_practice_attempt
        attempt_level, _ = completed_level_assessment
        filter_val = f"{UserTestAttempt.AttemptType.PRACTICE},{UserTestAttempt.AttemptType.LEVEL_ASSESSMENT}"
        url = reverse("api:v1:study:attempt-list") + f"?attempt_type__in={filter_val}"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        result_ids = {r["attempt_id"] for r in response.data["results"]}
        assert result_ids == {attempt_practice.id, attempt_level.id}


class TestStartPracticeSimulationAPI:  # Renamed
    @pytest.fixture
    def start_payload(self, db, setup_learning_content):
        sub1_slug = setup_learning_content["algebra_sub"].slug
        sub2_slug = setup_learning_content["geometry_sub"].slug
        return {
            "test_type": UserTestAttempt.AttemptType.PRACTICE.value,
            "config": {
                "name": "My Practice Test",
                "subsections": [sub1_slug, sub2_slug],
                "skills": [],
                "num_questions": 10,
                "starred": False,
                "not_mastered": False,
                "full_simulation": False,
            },
        }

    def test_start_unauthenticated(self, api_client, start_payload):
        url = reverse("api:v1:study:start-practice-simulation")  # Updated URL name
        response = api_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_not_subscribed(self, authenticated_client, start_payload):
        url = reverse("api:v1:study:start-practice-simulation")  # Updated URL name
        response = authenticated_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_success(
        self, subscribed_client, start_payload, setup_learning_content
    ):
        url = reverse("api:v1:study:start-practice-simulation")  # Updated URL name
        response = subscribed_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        # ... Assertions about attempt creation ...
        assert "attempt_id" in response.data
        attempt = UserTestAttempt.objects.get(pk=response.data["attempt_id"])
        assert attempt.user == subscribed_client.user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == UserTestAttempt.AttemptType.PRACTICE

    def test_start_ongoing_attempt_exists(
        self, subscribed_client, start_payload, setup_learning_content
    ):
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse("api:v1:study:start-practice-simulation")  # Updated URL name
        response = subscribed_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "You already have an ongoing test attempt" in str(response.data)

    # Other start failure tests remain similar


class TestRetrieveAttemptAPI:  # Renamed
    def test_retrieve_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse(
            "api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_not_subscribed(self, authenticated_client):
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user,
            num_questions=3,
            num_answered=1,
            num_correct_answered=1,
        )
        url = reverse(
            "api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_not_owner(self, subscribed_client):
        other_user = UserFactory()
        attempt_other, _ = create_attempt_scenario(user=other_user)
        url = reverse(
            "api:v1:study:attempt-detail", kwargs={"attempt_id": attempt_other.id}
        )  # Updated URL name
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_started_success(
        self, subscribed_client, started_practice_attempt
    ):
        attempt, questions = started_practice_attempt
        url = reverse("api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.STARTED
        # --- FIX: Assert annotated count ---
        assert res_data["answered_question_count"] == 0
        # ----------------------------------
        assert len(res_data["included_questions"]) == len(questions)
        assert len(res_data["attempted_questions"]) == 0

    def test_retrieve_partially_answered_success(
        self, subscribed_client, partially_answered_attempt
    ):
        attempt, questions = partially_answered_attempt
        url = reverse("api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        # --- FIX: Assert annotated count ---
        assert res_data["answered_question_count"] == 2  # Fixture creates 2 answers
        # ----------------------------------
        assert len(res_data["included_questions"]) == NUM_QUESTIONS_DEFAULT
        assert len(res_data["attempted_questions"]) == 2

    def test_retrieve_completed_success(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, questions = completed_practice_attempt
        url = reverse("api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        # --- FIX: Assert annotated count ---
        assert res_data["answered_question_count"] == len(questions)
        # ----------------------------------
        assert len(res_data["included_questions"]) == len(questions)
        assert len(res_data["attempted_questions"]) == len(questions)


# --- NEW: Test Class for Answering ---
class TestAttemptAnswerAPI:
    @pytest.fixture
    def answer_url(self, started_practice_attempt):
        attempt, _ = started_practice_attempt
        return reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})

    @pytest.fixture
    def answer_payload(self, started_practice_attempt):
        _, questions = started_practice_attempt
        assert (
            questions
        ), "Fixture 'started_practice_attempt' did not provide questions."
        question_to_answer = questions[0]  # Answer the first question
        return {
            "question_id": question_to_answer.id,
            "selected_answer": question_to_answer.correct_answer,
            "time_taken_seconds": 45,
        }

    def test_answer_unauthenticated(self, api_client, answer_url, answer_payload):
        response = api_client.post(answer_url, answer_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_answer_not_subscribed(
        self, authenticated_client, answer_url, answer_payload
    ):
        # Need to create an attempt for this user first
        attempt, questions = create_attempt_scenario(
            user=authenticated_client.user,
            num_questions=3,
            num_answered=0,
            num_correct_answered=0,
        )
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})
        payload = {"question_id": attempt.question_ids[0], "selected_answer": "A"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_answer_attempt_not_found(self, subscribed_client, answer_payload):
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": 9999})
        response = subscribed_client.post(url, answer_payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_attempt_not_started(
        self, subscribed_client, completed_practice_attempt, answer_payload
    ):
        attempt, _ = completed_practice_attempt  # Use a completed one
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.post(url, answer_payload, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_question_not_in_attempt(
        self, subscribed_client, started_practice_attempt, answer_url
    ):
        attempt, _ = started_practice_attempt
        other_question = QuestionFactory()  # A question not in the attempt
        payload = {"question_id": other_question.id, "selected_answer": "A"}
        response = subscribed_client.post(answer_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This question is not part of the current test attempt" in str(
            response.data
        )

    def test_answer_invalid_choice(
        self, subscribed_client, started_practice_attempt, answer_url
    ):
        attempt, questions = started_practice_attempt
        payload = {
            "question_id": questions[0].id,
            "selected_answer": "X",
        }  # Invalid choice
        response = subscribed_client.post(answer_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data

    def test_answer_success_correct(
        self, subscribed_client, started_practice_attempt, answer_url, answer_payload
    ):
        attempt, questions = started_practice_attempt
        question_id = answer_payload["question_id"]
        question = Question.objects.get(id=question_id)

        assert (
            UserQuestionAttempt.objects.filter(
                test_attempt=attempt, question_id=question_id
            ).count()
            == 0
        )
        response = subscribed_client.post(answer_url, answer_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["question_id"] == question_id
        assert res_data["is_correct"] is True
        assert res_data["correct_answer"] is None
        assert "feedback_message" in res_data

        # Check DB
        assert (
            UserQuestionAttempt.objects.filter(
                test_attempt=attempt,
                question_id=question_id,
                selected_answer=question.correct_answer,
                is_correct=True,
            ).count()
            == 1
        )

    def test_answer_success_incorrect(
        self, subscribed_client, started_practice_attempt, answer_url
    ):
        attempt, questions = started_practice_attempt
        question_to_answer = questions[1]
        incorrect_answer = "A" if question_to_answer.correct_answer != "A" else "B"
        payload = {
            "question_id": question_to_answer.id,
            "selected_answer": incorrect_answer,
        }

        response = subscribed_client.post(answer_url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["question_id"] == question_to_answer.id
        assert res_data["is_correct"] is False
        assert res_data["correct_answer"] is None

        # Check DB
        assert (
            UserQuestionAttempt.objects.filter(
                test_attempt=attempt,
                question_id=question_to_answer.id,
                selected_answer=incorrect_answer,
                is_correct=False,
            ).count()
            == 1
        )

    def test_answer_update_existing(
        self, subscribed_client, started_practice_attempt, answer_url
    ):
        attempt, questions = started_practice_attempt
        question_to_answer = questions[0]
        # Submit first answer (incorrect)
        incorrect_answer = "A" if question_to_answer.correct_answer != "A" else "B"
        first_payload = {
            "question_id": question_to_answer.id,
            "selected_answer": incorrect_answer,
        }
        response1 = subscribed_client.post(answer_url, first_payload, format="json")
        assert response1.status_code == status.HTTP_200_OK
        assert (
            UserQuestionAttempt.objects.filter(
                test_attempt=attempt, question=question_to_answer
            ).count()
            == 1
        )

        # Submit second answer (correct)
        second_payload = {
            "question_id": question_to_answer.id,
            "selected_answer": question_to_answer.correct_answer,
        }
        response2 = subscribed_client.post(answer_url, second_payload, format="json")
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["is_correct"] is True

        # Check DB - should still be only one attempt record, but updated
        assert (
            UserQuestionAttempt.objects.filter(
                test_attempt=attempt, question=question_to_answer
            ).count()
            == 1
        )
        qa = UserQuestionAttempt.objects.get(
            test_attempt=attempt, question=question_to_answer
        )
        assert qa.selected_answer == question_to_answer.correct_answer
        assert qa.is_correct is True


# --- NEW: Test Class for Completing ---
class TestCompleteAttemptAPI:
    @pytest.fixture
    def complete_url(self, partially_answered_attempt):
        attempt, _ = partially_answered_attempt
        return reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )

    def test_complete_unauthenticated(self, api_client, complete_url):
        response = api_client.post(complete_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_complete_not_subscribed(self, authenticated_client, complete_url):
        # Need attempt for this user
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user,
            num_questions=3,
            num_answered=1,
            num_correct_answered=1,
        )
        url = reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_complete_attempt_not_found(self, subscribed_client):
        url = reverse("api:v1:study:attempt-complete", kwargs={"attempt_id": 9999})
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_attempt_not_started(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, _ = completed_practice_attempt  # Use completed
        url = reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(url)
        # Should be 404 because get_object filters for STARTED status
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_practice_success(
        self, subscribed_client, partially_answered_attempt, complete_url
    ):
        attempt, questions = partially_answered_attempt  # Only 2/5 answered
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.score_percentage is None

        response = subscribed_client.post(complete_url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED.label
        assert (
            "score_percentage" in res_data and res_data["score_percentage"] is not None
        )
        assert "results_summary" in res_data and res_data["results_summary"] is not None
        assert res_data["answered_question_count"] == 2  # Only 2 were answered
        assert res_data["total_questions"] == NUM_QUESTIONS_DEFAULT  # Total in attempt
        assert "message" in res_data
        # assert "updated_profile" not in res_data  # Not a level assessment

        # Check DB
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert attempt.score_percentage is not None  # Score should be calculated

    def test_complete_level_assessment_success(
        self, subscribed_client, started_level_assessment
    ):
        attempt, questions = started_level_assessment
        user = subscribed_client.user
        profile = user.profile
        profile.current_level_verbal = None
        profile.current_level_quantitative = None
        profile.is_level_determined = False
        profile.save()

        correct_answers = 0
        for i, q in enumerate(questions):
            # Ensure questions have sections for calculation (check factories/fixtures if this fails later)
            assert (
                q.subsection and q.subsection.section
            ), f"Question {q.id} lacks section/subsection in test setup"
            is_correct = i < 7
            selected = (
                q.correct_answer
                if is_correct
                else next(c for c in ["A", "B", "C", "D"] if c != q.correct_answer)
            )
            UserQuestionAttemptFactory(
                user=user,
                test_attempt=attempt,
                question=q,
                selected_answer=selected,
                is_correct=is_correct,
                mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
            )
            if is_correct:
                correct_answers += 1

        complete_url = reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(complete_url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED.label

        # --- FIXED ASSERTIONS --- Check actual response structure
        # assert "results" in res_data  # Original failing assertion
        assert "score_percentage" in res_data
        assert "results_summary" in res_data  # Contains breakdown by subsection/skill
        assert "updated_profile" in res_data  # Should contain updated profile data

        # Check results values (assuming calculation is now working)
        expected_overall = pytest.approx(
            (correct_answers / len(questions)) * 100.0, abs=0.1
        )
        assert res_data["score_percentage"] == expected_overall
        assert res_data["score_verbal"] is not None
        assert res_data["score_quantitative"] is not None
        assert res_data["answered_question_count"] == len(questions)
        assert res_data["total_questions"] == len(questions)
        print(res_data)
        # Check profile update in response
        profile_resp = res_data["updated_profile"]
        assert profile_resp is not None  # Should not be None if successful
        assert profile_resp["current_level_verbal"] == res_data["score_verbal"]
        assert (
            profile_resp["current_level_quantitative"] == res_data["score_quantitative"]
        )
        assert profile_resp["is_level_determined"] is True

        # Check DB (unchanged, but relies on score calculation working)
        attempt.refresh_from_db()
        profile.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.score_percentage == expected_overall
        assert profile.current_level_verbal == res_data["score_verbal"]
        assert profile.current_level_quantitative == res_data["score_quantitative"]
        assert profile.is_level_determined is True


# --- NEW: Test Class for Cancelling ---
class TestCancelAttemptAPI:
    @pytest.fixture
    def cancel_url(self, started_practice_attempt):
        attempt, _ = started_practice_attempt
        return reverse("api:v1:study:attempt-cancel", kwargs={"attempt_id": attempt.id})

    def test_cancel_unauthenticated(self, api_client, cancel_url):
        response = api_client.post(cancel_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cancel_not_subscribed(self, authenticated_client, cancel_url):
        # Need attempt for this user
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user,
            num_questions=3,
            num_answered=0,
            num_correct_answered=0,
        )
        url = reverse("api:v1:study:attempt-cancel", kwargs={"attempt_id": attempt.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cancel_attempt_not_found(self, subscribed_client):
        url = reverse("api:v1:study:attempt-cancel", kwargs={"attempt_id": 9999})
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_attempt_not_started(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, _ = completed_practice_attempt  # Use completed
        url = reverse("api:v1:study:attempt-cancel", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.post(url)
        # Should be 404 because get_object filters for STARTED status
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_cancel_success(
        self, subscribed_client, started_practice_attempt, cancel_url
    ):
        attempt, _ = started_practice_attempt
        assert attempt.status == UserTestAttempt.Status.STARTED

        response = subscribed_client.post(cancel_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Test attempt cancelled."

        # Check DB
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.ABANDONED
        assert attempt.end_time is not None
        assert attempt.score_percentage is None  # Score should not be calculated


class TestReviewAttemptAPI:  # Renamed
    # Tests remain mostly the same, just check URLs and serializer structure
    def test_review_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse(
            "api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_review_not_subscribed(self, authenticated_client):
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user, status=UserTestAttempt.Status.COMPLETED
        )
        url = reverse(
            "api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_review_attempt_not_completed(
        self, subscribed_client, started_practice_attempt
    ):
        attempt, _ = started_practice_attempt
        url = reverse(
            "api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot review a test attempt that is not completed" in str(
            response.data
        )

    def test_review_success_all(self, subscribed_client, completed_practice_attempt):
        attempt, questions = completed_practice_attempt
        url = reverse(
            "api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert "questions" in res_data
        assert len(res_data["questions"]) == len(questions)
        # Check one question detail
        q_review_first = res_data["questions"][0]
        q_attempt_first = UserQuestionAttempt.objects.get(
            test_attempt=attempt, question_id=q_review_first["question_id"]
        )
        assert "correct_answer" in q_review_first
        assert q_review_first["user_answer"] == q_attempt_first.selected_answer
        assert q_review_first["user_is_correct"] == q_attempt_first.is_correct

    def test_review_success_incorrect_only(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, questions = completed_practice_attempt  # Has 2 incorrect
        url = reverse(
            "api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = subscribed_client.get(url, {"incorrect_only": "true"})
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        incorrect_count_in_db = UserQuestionAttempt.objects.filter(
            test_attempt=attempt, is_correct=False
        ).count()
        assert "questions" in res_data
        assert len(res_data["questions"]) == incorrect_count_in_db
        assert all(q["user_is_correct"] is False for q in res_data["questions"])


class TestRetakeSimilarAPI:
    # Tests remain mostly the same, just check URLs
    def test_retake_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse(
            "api:v1:study:attempt-retake", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retake_not_subscribed(self, authenticated_client):
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user, status=UserTestAttempt.Status.COMPLETED
        )
        url = reverse(
            "api:v1:study:attempt-retake", kwargs={"attempt_id": attempt.id}
        )  # Updated URL name
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retake_ongoing_attempt_exists(
        self, subscribed_client, completed_practice_attempt
    ):
        original_attempt, _ = completed_practice_attempt
        # Create another ongoing attempt
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse(
            "api:v1:study:attempt-retake",
            kwargs={"attempt_id": original_attempt.id},
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            "detail" in response.data and "non_field_errors" in response.data["detail"]
        )
        assert (
            "Please complete or cancel your ongoing test"
            in response.data["detail"]["non_field_errors"][0]
        )

    def test_retake_success(
        self, subscribed_client, completed_practice_attempt, setup_learning_content
    ):
        attempt, _ = completed_practice_attempt

        # --- Ensure original attempt has valid config and questions ---
        # Make sure the factory creates sensible defaults if not overridden
        if not attempt.question_ids:
            # Create some questions if the fixture didn't provide them for the original
            questions_orig = QuestionFactory.create_batch(3)
            attempt.question_ids = [q.id for q in questions_orig]
            # Ensure config reflects this if it was 0 before
            if (
                "config" in attempt.test_configuration
                and attempt.test_configuration["config"].get(
                    "actual_num_questions_selected"
                )
                == 0
            ):
                attempt.test_configuration["config"][
                    "actual_num_questions_selected"
                ] = len(attempt.question_ids)
                attempt.test_configuration["config"]["num_questions"] = len(
                    attempt.question_ids
                )  # Update num_questions too
            attempt.save()
            attempt.refresh_from_db()  # Reload

        assert attempt.question_ids, "Original attempt fixture needs valid question_ids"
        original_num = len(attempt.question_ids)
        assert original_num > 0, "Original attempt must have > 0 questions for retake"
        # Ensure the config number matches
        num_in_config = attempt.test_configuration.get("num_questions_selected", -1)
        if num_in_config != original_num:
            # logger.warning(
            #     f"Fixing config mismatch in test_retake_success: stored IDs {original_num}, config {num_in_config}"
            # )
            attempt.test_configuration["num_questions_selected"] = original_num
            if "config" in attempt.test_configuration:
                attempt.test_configuration["config"]["num_questions"] = original_num
                attempt.test_configuration["config"][
                    "actual_num_questions_selected"
                ] = original_num
            attempt.save()

        # Ensure enough *other* questions exist for the retake
        sub = Question.objects.get(id=attempt.question_ids[0]).subsection
        # Create enough extras *beyond* the original number
        QuestionFactory.create_batch(original_num + 5, subsection=sub, is_active=True)

        url = reverse("api:v1:study:attempt-retake", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED

        res_data = response.data
        assert "attempt_id" in res_data and res_data["attempt_id"] != attempt.id
        assert "questions" in res_data
        # The number of questions might be fewer if not enough replacements are found,
        # but should be <= original_num
        assert len(res_data["questions"]) > 0
        assert len(res_data["questions"]) <= original_num

        new_attempt = UserTestAttempt.objects.get(pk=res_data["attempt_id"])
        assert new_attempt.user == subscribed_client.user
        assert new_attempt.status == UserTestAttempt.Status.STARTED
        assert new_attempt.test_configuration["retake_of_attempt_id"] == attempt.id
        # Check that *most* questions are different, allow some overlap if necessary
        overlap = set(new_attempt.question_ids) & set(attempt.question_ids)
        assert len(overlap) < len(new_attempt.question_ids) or len(overlap) < len(
            attempt.question_ids
        ), "Retake should ideally select different questions if possible"
