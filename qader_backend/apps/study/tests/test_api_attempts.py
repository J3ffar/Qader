# qader_backend/apps/study/tests/test_api_attempts.py
import random
import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion, Skill
from apps.users.models import UserProfile
from unittest.mock import patch

from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
    create_attempt_scenario,
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
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_answered=0,
        num_correct_answered=0,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.STARTED,
    )
    return attempt, questions


@pytest.fixture
def started_traditional_attempt(db, subscribed_user, setup_learning_content):
    """Creates a STARTED traditional test attempt with a few initial questions."""
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=3,  # Traditional can start with some or 0 questions
        num_answered=0,
        num_correct_answered=0,
        attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        status=UserTestAttempt.Status.STARTED,
    )
    return attempt, questions


@pytest.fixture
def started_level_assessment(db, subscribed_user, setup_learning_content):
    try:
        verbal_sub = setup_learning_content["reading_comp_sub"]
        quant_sub = setup_learning_content["algebra_sub"]
        assert verbal_sub.section.slug == "verbal"
        assert quant_sub.section.slug == "quantitative"
    except (KeyError, AssertionError) as e:
        pytest.fail(f"Fixture setup_learning_content issue: {e}")

    num_verbal = 3  # Reduced for faster tests
    num_quant = 2  # Reduced for faster tests
    verbal_questions = QuestionFactory.create_batch(
        num_verbal, subsection=verbal_sub, is_active=True
    )
    quant_questions = QuestionFactory.create_batch(
        num_quant, subsection=quant_sub, is_active=True
    )
    all_questions = verbal_questions + quant_questions
    random.shuffle(all_questions)
    question_ids = [q.id for q in all_questions]

    attempt = UserTestAttemptFactory(
        user=subscribed_user,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        status=UserTestAttempt.Status.STARTED,
        question_ids=question_ids,
        test_configuration={
            "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value,
            "sections_requested": ["verbal", "quantitative"],
            "num_questions_requested": num_verbal + num_quant,
            "num_questions_selected": len(question_ids),  # Use actual selected
        },
    )
    return attempt, all_questions


@pytest.fixture
def partially_answered_attempt(db, subscribed_user, setup_learning_content):
    num_answered = 2
    num_correct = 1
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_answered=num_answered,
        num_correct_answered=num_correct,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.STARTED,
    )
    return attempt, questions


@pytest.fixture
def completed_practice_attempt(db, subscribed_user, setup_learning_content):
    num_questions = NUM_QUESTIONS_DEFAULT
    num_correct = 3
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=num_questions,
        num_answered=num_questions,
        num_correct_answered=num_correct,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        status=UserTestAttempt.Status.COMPLETED,  # create_attempt_scenario handles score calculation
    )
    return attempt, questions


@pytest.fixture
def completed_level_assessment(db, subscribed_user, setup_learning_content):
    num_questions = 5  # Reduced for faster tests
    num_correct = 3
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=num_questions,
        num_answered=num_questions,
        num_correct_answered=num_correct,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        status=UserTestAttempt.Status.COMPLETED,  # create_attempt_scenario handles score calculation
    )
    # Profile update is now handled by the service, not fixture
    return attempt, questions


@pytest.fixture
def completed_traditional_attempt(db, subscribed_user, setup_learning_content):
    """Creates a COMPLETED traditional attempt."""
    num_questions = 3
    num_answered = 2  # User might not answer all in traditional
    num_correct = 1
    attempt, questions = create_attempt_scenario(
        user=subscribed_user,
        num_questions=num_questions,
        num_answered=num_answered,
        num_correct_answered=num_correct,
        attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        status=UserTestAttempt.Status.COMPLETED,
        # For traditional, scores are not auto-calculated by create_attempt_scenario
        # and will be null in the response, which is expected.
    )
    return attempt, questions


# --- Test Classes ---


class TestListAttemptsAPI:
    def test_list_unauthenticated(self, api_client):
        url = reverse("api:v1:study:attempt-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:attempt-list")
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
            user=other_user, status=UserTestAttempt.Status.COMPLETED
        )

        url = reverse("api:v1:study:attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        result_ids = {r["attempt_id"] for r in response.data["results"]}
        assert result_ids == {attempt1.id, attempt2.id}

    def test_list_filter_by_status(
        self, subscribed_client, started_practice_attempt, completed_practice_attempt
    ):
        attempt_started, _ = started_practice_attempt
        url = (
            reverse("api:v1:study:attempt-list")
            + f"?status={UserTestAttempt.Status.STARTED}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_started.id

    def test_list_filter_by_type(
        self, subscribed_client, completed_practice_attempt, completed_level_assessment
    ):
        attempt_practice, _ = completed_practice_attempt
        url = (
            reverse("api:v1:study:attempt-list")
            + f"?attempt_type={UserTestAttempt.AttemptType.PRACTICE}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["attempt_id"] == attempt_practice.id


class TestStartPracticeSimulationAPI:
    @pytest.fixture
    def start_payload(self, db, setup_learning_content):
        return {
            "test_type": UserTestAttempt.AttemptType.PRACTICE.value,
            "config": {
                "name": "My Practice Test",
                "subsections": [setup_learning_content["algebra_sub"].slug],
                "num_questions": 5,
            },
        }

    def test_start_unauthenticated(self, api_client, start_payload):
        url = reverse("api:v1:study:start-practice-simulation")
        response = api_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_not_subscribed(self, authenticated_client, start_payload):
        url = reverse("api:v1:study:start-practice-simulation")
        response = authenticated_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_success(self, subscribed_client, start_payload):
        url = reverse("api:v1:study:start-practice-simulation")
        response = subscribed_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "attempt_id" in response.data
        attempt = UserTestAttempt.objects.get(pk=response.data["attempt_id"])
        assert attempt.user == subscribed_client.user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == UserTestAttempt.AttemptType.PRACTICE
        assert (
            len(response.data["questions"]) == start_payload["config"]["num_questions"]
        )

    def test_start_ongoing_attempt_exists(self, subscribed_client, start_payload):
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse("api:v1:study:start-practice-simulation")
        response = subscribed_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]


class TestRetrieveAttemptAPI:
    def test_retrieve_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse("api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_not_subscribed(self, authenticated_client):
        attempt, _ = create_attempt_scenario(user=authenticated_client.user)
        url = reverse("api:v1:study:attempt-detail", kwargs={"attempt_id": attempt.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_not_owner(self, subscribed_client):
        other_user = UserFactory()
        attempt_other, _ = create_attempt_scenario(user=other_user)
        url = reverse(
            "api:v1:study:attempt-detail", kwargs={"attempt_id": attempt_other.id}
        )
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
        assert res_data["answered_question_count"] == 0
        assert len(res_data["included_questions"]) == len(questions)
        assert len(res_data["attempted_questions"]) == 0


class TestAttemptAnswerAPI:
    @pytest.fixture
    def answer_url(self, started_practice_attempt):
        attempt, _ = started_practice_attempt
        return reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})

    @pytest.fixture
    def answer_payload(self, started_practice_attempt):
        _, questions = started_practice_attempt
        question_to_answer = questions[0]
        return {
            "question_id": question_to_answer.id,
            "selected_answer": question_to_answer.correct_answer,
            "time_taken_seconds": 45,
        }

    def test_answer_unauthenticated(self, api_client, answer_url, answer_payload):
        response = api_client.post(answer_url, answer_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_answer_not_subscribed(self, authenticated_client, answer_payload):
        attempt, _ = create_attempt_scenario(user=authenticated_client.user)
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})
        response = authenticated_client.post(url, answer_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_answer_attempt_not_started(
        self, subscribed_client, completed_practice_attempt, answer_payload
    ):
        attempt, _ = completed_practice_attempt
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.post(url, answer_payload, format="json")
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # View checks for STARTED

    def test_answer_question_not_in_attempt(
        self, subscribed_client, started_practice_attempt, answer_url
    ):
        other_question = QuestionFactory()
        payload = {"question_id": other_question.id, "selected_answer": "A"}
        response = subscribed_client.post(answer_url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "question_id" in response.data

    def test_answer_success_correct(
        self, subscribed_client, started_practice_attempt, answer_url, answer_payload
    ):
        attempt, _ = started_practice_attempt
        question_id = answer_payload["question_id"]

        response = subscribed_client.post(answer_url, answer_payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["question_id"] == question_id
        assert res_data["is_correct"] is True
        assert res_data["correct_answer"] is None  # Not traditional mode
        assert UserQuestionAttempt.objects.filter(
            test_attempt=attempt, question_id=question_id, is_correct=True
        ).exists()

    def test_answer_traditional_reveals_answer(
        self, subscribed_client, started_traditional_attempt
    ):
        attempt, questions = started_traditional_attempt
        question_to_answer = questions[0]
        payload = {
            "question_id": question_to_answer.id,
            "selected_answer": "A",
        }  # Any answer
        url = reverse("api:v1:study:attempt-answer", kwargs={"attempt_id": attempt.id})

        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["question_id"] == question_to_answer.id
        assert (
            res_data["correct_answer"] == question_to_answer.correct_answer
        )  # Revealed for traditional
        assert res_data["explanation"] == question_to_answer.explanation


class TestCompleteAttemptAPI:
    @pytest.fixture
    def complete_url_practice(self, partially_answered_attempt):
        attempt, _ = partially_answered_attempt
        return reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )

    @pytest.fixture
    def complete_url_level(self, started_level_assessment):
        attempt, _ = started_level_assessment
        # Answer all questions for level assessment before completing
        for q in attempt.get_questions_queryset():
            UserQuestionAttemptFactory(
                user=attempt.user,
                test_attempt=attempt,
                question=q,
                selected_answer="A",
                is_correct=random.choice([True, False]),
            )
        return reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )

    @pytest.fixture
    def complete_url_traditional(self, started_traditional_attempt):
        attempt, _ = started_traditional_attempt
        # Optionally answer some questions
        if attempt.question_ids:
            UserQuestionAttemptFactory(
                user=attempt.user,
                test_attempt=attempt,
                question_id=attempt.question_ids[0],
                selected_answer="A",
            )
        return reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )

    def test_complete_unauthenticated(self, api_client, complete_url_practice):
        response = api_client.post(complete_url_practice)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_complete_not_subscribed(self, authenticated_client):
        attempt, _ = create_attempt_scenario(
            user=authenticated_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_complete_attempt_not_started(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, _ = completed_practice_attempt
        url = reverse(
            "api:v1:study:attempt-complete", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_practice_success(
        self, subscribed_client, partially_answered_attempt, complete_url_practice
    ):
        attempt, _ = partially_answered_attempt
        original_answered_count = attempt.question_attempts.count()

        response = subscribed_client.post(complete_url_practice)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED.label

        assert "score" in res_data
        print(res_data["score"])
        assert res_data["score"]["overall"] is not None
        assert (
            res_data["score"]["verbal"] is not None
        )  # May be null if no verbal questions
        assert (
            res_data["score"]["quantitative"] is not None
        )  # May be null if no quant questions

        assert "results_summary" in res_data and res_data["results_summary"] is not None
        assert res_data["answered_question_count"] == original_answered_count
        assert res_data["total_questions"] == NUM_QUESTIONS_DEFAULT
        assert "smart_analysis" in res_data
        # No 'message' or 'updated_profile' in the new response structure

        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert attempt.score_percentage is not None

    def test_complete_level_assessment_success(
        self, subscribed_client, complete_url_level
    ):
        # Fixture `complete_url_level` ensures questions are answered
        attempt_id = int(complete_url_level.split("/")[-3])  # Extract ID from URL
        attempt = UserTestAttempt.objects.get(id=attempt_id)
        user = attempt.user
        profile = user.profile
        initial_verbal_level = profile.current_level_verbal
        initial_quant_level = profile.current_level_quantitative
        initial_is_determined = profile.level_determined

        response = subscribed_client.post(complete_url_level)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert "score" in res_data
        assert res_data["score"]["overall"] is not None
        assert res_data["score"]["verbal"] is not None
        assert res_data["score"]["quantitative"] is not None

        # Check DB for profile update
        profile.refresh_from_db()
        attempt.refresh_from_db()  # To get calculated scores from attempt model

        assert profile.current_level_verbal == attempt.score_verbal
        assert profile.current_level_quantitative == attempt.score_quantitative
        assert profile.level_determined is True
        # Ensure levels actually changed if scores were different
        if (
            attempt.score_verbal is not None
        ):  # It's possible all questions were of one type if not set up carefully
            assert (
                profile.current_level_verbal != initial_verbal_level
                or attempt.score_verbal == initial_verbal_level
            )
        if attempt.score_quantitative is not None:
            assert (
                profile.current_level_quantitative != initial_quant_level
                or attempt.score_quantitative == initial_quant_level
            )

    def test_complete_traditional_success(
        self, subscribed_client, complete_url_traditional
    ):
        attempt_id = int(complete_url_traditional.split("/")[-3])
        attempt = UserTestAttempt.objects.get(id=attempt_id)
        original_answered_count = attempt.question_attempts.count()
        original_total_questions = attempt.num_questions

        response = subscribed_client.post(complete_url_traditional)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data

        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED.label

        assert "score" in res_data
        assert (
            res_data["score"]["overall"] is None
        )  # Traditional tests don't calculate overall scores
        assert res_data["score"]["verbal"] is None
        assert res_data["score"]["quantitative"] is None

        assert (
            "results_summary" in res_data and res_data["results_summary"] == {}
        )  # Empty for traditional
        assert res_data["answered_question_count"] == original_answered_count
        assert res_data["total_questions"] == original_total_questions
        assert res_data["smart_analysis"] == "Practice session ended."

        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert attempt.score_percentage is None  # No scores for traditional
        assert attempt.results_summary is None or attempt.results_summary == {}


class TestCancelAttemptAPI:
    @pytest.fixture
    def cancel_url(self, started_practice_attempt):
        attempt, _ = started_practice_attempt
        return reverse("api:v1:study:attempt-cancel", kwargs={"attempt_id": attempt.id})

    def test_cancel_unauthenticated(self, api_client, cancel_url):
        response = api_client.post(cancel_url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cancel_success(
        self, subscribed_client, started_practice_attempt, cancel_url
    ):
        attempt, _ = started_practice_attempt
        response = subscribed_client.post(cancel_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Test attempt cancelled."
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.ABANDONED
        assert attempt.end_time is not None


class TestReviewAttemptAPI:
    def test_review_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse("api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_review_attempt_not_completed(
        self, subscribed_client, started_practice_attempt
    ):
        attempt, _ = started_practice_attempt
        url = reverse("api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_review_success_all(self, subscribed_client, completed_practice_attempt):
        attempt, questions = completed_practice_attempt
        url = reverse("api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert len(res_data["questions"]) == len(questions)
        q_review_first = res_data["questions"][0]
        q_attempt_first = UserQuestionAttempt.objects.get(
            test_attempt=attempt, question_id=q_review_first["question_id"]
        )
        assert q_review_first["user_answer"] == q_attempt_first.selected_answer

    def test_review_success_incorrect_only(
        self, subscribed_client, completed_practice_attempt
    ):
        attempt, _ = completed_practice_attempt
        url = reverse("api:v1:study:attempt-review", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.get(url, {"incorrect_only": "true"})
        assert response.status_code == status.HTTP_200_OK
        incorrect_count_in_db = UserQuestionAttempt.objects.filter(
            test_attempt=attempt, is_correct=False
        ).count()
        assert len(response.data["questions"]) == incorrect_count_in_db


class TestRetakeSimilarAPI:
    def test_retake_unauthenticated(self, api_client, completed_practice_attempt):
        attempt, _ = completed_practice_attempt
        url = reverse("api:v1:study:attempt-retake", kwargs={"attempt_id": attempt.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retake_ongoing_attempt_exists(
        self, subscribed_client, completed_practice_attempt
    ):
        original_attempt, _ = completed_practice_attempt
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse(
            "api:v1:study:attempt-retake", kwargs={"attempt_id": original_attempt.id}
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]

    def test_retake_success(
        self, subscribed_client, completed_practice_attempt, setup_learning_content
    ):
        attempt, _ = completed_practice_attempt
        # Ensure original attempt has valid config for retake
        if (
            not attempt.question_ids
            or attempt.test_configuration.get("num_questions_selected", 0) == 0
        ):
            questions_orig = QuestionFactory.create_batch(
                3, subsection=setup_learning_content["algebra_sub"]
            )
            attempt.question_ids = [q.id for q in questions_orig]
            attempt.test_configuration["num_questions_selected"] = len(questions_orig)
            if "config" in attempt.test_configuration:  # if practice test
                attempt.test_configuration["config"]["num_questions"] = len(
                    questions_orig
                )
                attempt.test_configuration["config"][
                    "actual_num_questions_selected"
                ] = len(questions_orig)
            attempt.save()

        original_num = len(attempt.question_ids)
        assert original_num > 0

        # Create extra questions for retake to pick from
        QuestionFactory.create_batch(
            original_num + 5,
            subsection=Question.objects.get(id=attempt.question_ids[0]).subsection,
            is_active=True,
        )

        url = reverse("api:v1:study:attempt-retake", kwargs={"attempt_id": attempt.id})
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert res_data["attempt_id"] != attempt.id
        assert len(res_data["questions"]) > 0
        assert len(res_data["questions"]) <= original_num
        new_attempt = UserTestAttempt.objects.get(pk=res_data["attempt_id"])
        assert new_attempt.test_configuration["retake_of_attempt_id"] == attempt.id
        # Allow some overlap, but not identical
        if len(new_attempt.question_ids) == len(attempt.question_ids):
            assert (
                set(new_attempt.question_ids) != set(attempt.question_ids)
                or original_num == 1
            )
