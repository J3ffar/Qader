# qader_backend/apps/study/tests/test_api_general_tests.py

from django.conf import settings
import pytest
from django.urls import reverse
from rest_framework import status
from apps.study.models import UserTestAttempt, UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion, Skill
from apps.users.models import UserProfile
from unittest.mock import (
    ANY,
)  # Import ANY if needed for complex mocks, not strictly needed here now

# Import factories and helpers
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    create_completed_attempt,
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

# --- Fixtures (remain the same) ---


@pytest.fixture
def started_test_attempt(db, subscribed_user, setup_learning_content):
    """Creates a STARTED practice test attempt for the subscribed_user."""
    questions = list(
        Question.objects.filter(is_active=True, subsection__isnull=False)[
            :NUM_QUESTIONS_DEFAULT
        ]
    )
    if len(questions) < NUM_QUESTIONS_DEFAULT:
        pytest.skip(
            f"Not enough active questions with subsections found ({len(questions)}/{NUM_QUESTIONS_DEFAULT})."
        )
    first_q_sub_slug = questions[0].subsection.slug
    config = {
        "test_type": UserTestAttempt.AttemptType.PRACTICE.value,  # Add type to snapshot
        "config": {
            "name": "Started Practice Test",
            "subsections": [first_q_sub_slug],
            "skills": [],
            "num_questions": len(questions),
            "actual_num_questions_selected": len(questions),
            "starred": False,
            "not_mastered": False,
            "full_simulation": False,
        },
    }
    attempt = UserTestAttemptFactory(
        user=subscribed_user,
        status=UserTestAttempt.Status.STARTED,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        question_ids=[q.id for q in questions],
        test_configuration=config,
    )
    return attempt, questions


@pytest.fixture
def completed_test_attempt(db, subscribed_user, setup_learning_content):
    """Creates a COMPLETED practice test attempt using the helper."""
    attempt, questions = create_completed_attempt(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_correct=3,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
    )
    return attempt, questions


# --- Test Classes ---


# TestListGeneralTestsAPI (remains the same)
class TestListGeneralTestsAPI:
    def test_list_unauthenticated(self, api_client):
        url = reverse("api:v1:study:test-attempt-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:test-attempt-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_success(self, subscribed_client, completed_test_attempt):
        user = subscribed_client.user
        attempt1, _ = completed_test_attempt
        attempt2, _ = create_completed_attempt(
            user=user,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            num_questions=10,
            num_correct=7,
        )
        other_user = UserFactory()
        create_completed_attempt(user=other_user)
        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2
        result_ids = {r["attempt_id"] for r in response.data["results"]}
        assert result_ids == {attempt1.id, attempt2.id}
        result2 = next(
            r for r in response.data["results"] if r["attempt_id"] == attempt2.id
        )
        assert result2["test_type"] == attempt2.get_attempt_type_display()
        assert "date" in result2
        assert result2["num_questions"] == attempt2.num_questions
        assert result2["score_percentage"] == pytest.approx(attempt2.score_percentage)
        assert result2["status"] == UserTestAttempt.Status.COMPLETED
        assert "performance" in result2

    def test_list_empty(self, subscribed_client):
        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0

    def test_list_pagination(self, subscribed_client):
        user = subscribed_client.user
        for _ in range(25):
            create_completed_attempt(user=user)
        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 20
        assert response.data.get("next") is not None
        response_page2 = subscribed_client.get(response.data["next"])
        assert response_page2.status_code == status.HTTP_200_OK
        assert len(response_page2.json()["results"]) == 5


# TestStartGeneralTestAPI (remains the same)
class TestStartGeneralTestAPI:
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
        url = reverse("api:v1:study:test-attempt-start")
        response = api_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_not_subscribed(self, authenticated_client, start_payload):
        url = reverse("api:v1:study:test-attempt-start")
        response = authenticated_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_success(self, subscribed_client, start_payload):
        url = reverse("api:v1:study:test-attempt-start")
        response = subscribed_client.post(url, start_payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert "attempt_id" in response.data
        assert "questions" in response.data
        assert isinstance(response.data["questions"], list)
        num_selected = len(response.data["questions"])
        assert num_selected > 0
        assert num_selected <= start_payload["config"]["num_questions"]
        attempt = UserTestAttempt.objects.get(pk=response.data["attempt_id"])
        assert attempt.user == subscribed_client.user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == UserTestAttempt.AttemptType.PRACTICE
        assert len(attempt.question_ids) == num_selected
        assert (
            attempt.test_configuration["config"]["name"]
            == start_payload["config"]["name"]
        )
        assert set(attempt.test_configuration["config"]["subsections"]) == set(
            start_payload["config"]["subsections"]
        )

    def test_start_invalid_payload_no_criteria(self, subscribed_client, start_payload):
        url = reverse("api:v1:study:test-attempt-start")
        payload = start_payload.copy()
        payload["config"]["subsections"] = []
        payload["config"]["skills"] = []
        payload["config"]["starred"] = False
        payload["config"]["not_mastered"] = False
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "config" in response.data
        assert "non_field_errors" in response.data["config"]
        expected_error = "Must specify subsections, skills, filter by starred, or filter by not mastered questions."
        assert any(
            expected_error in str(err)
            for err in response.data["config"]["non_field_errors"]
        )

    def test_start_no_questions_match(
        self, subscribed_client, start_payload, setup_learning_content
    ):
        empty_sub = LearningSubSectionFactory(
            section=setup_learning_content["verbal_section"], name="Empty Sub"
        )
        url = reverse("api:v1:study:test-attempt-start")
        payload = start_payload.copy()
        payload["config"]["subsections"] = [empty_sub.slug]
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No active questions found matching" in str(
            response.data
        ) or "Could not verify question availability" in str(response.data)

    def test_start_with_starred_filter(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        questions_to_star = list(
            Question.objects.filter(
                subsection__slug="algebra", is_active=True
            ).order_by("?")[:3]
        )
        if len(questions_to_star) < 3:
            pytest.skip("Need at least 3 active algebra questions to star.")
        starred_ids = {q.id for q in questions_to_star}
        for q in questions_to_star:
            UserStarredQuestion.objects.create(user=user, question=q)
        url = reverse("api:v1:study:test-attempt-start")
        payload = {
            "test_type": UserTestAttempt.AttemptType.PRACTICE.value,
            "config": {"num_questions": 3, "starred": True},
        }
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data["questions"]) == 3
        returned_ids = {q["id"] for q in response.data["questions"]}
        assert returned_ids == starred_ids

    def test_start_with_not_mastered_filter(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        skill1 = setup_learning_content["algebra_skill"]
        skill2 = setup_learning_content["geometry_skill"]
        UserSkillProficiencyFactory(user=user, skill=skill1, proficiency_score=0.2)
        UserSkillProficiencyFactory(user=user, skill=skill2, proficiency_score=0.9)
        q_low_prof_ids = set(
            Question.objects.filter(skill=skill1, is_active=True).values_list(
                "id", flat=True
            )
        )
        url = reverse("api:v1:study:test-attempt-start")
        payload = {
            "test_type": UserTestAttempt.AttemptType.PRACTICE.value,
            "config": {
                "num_questions": 5,
                "not_mastered": True,
                "subsections": [
                    setup_learning_content["algebra_sub"].slug,
                    setup_learning_content["geometry_sub"].slug,
                ],
            },
        }
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert len(res_data["questions"]) > 0
        assert len(res_data["questions"]) <= 5
        returned_skill_slugs = {
            q["skill"] for q in res_data["questions"] if q.get("skill")
        }
        assert skill2.slug not in returned_skill_slugs
        if q_low_prof_ids:
            assert skill1.slug in returned_skill_slugs


# TestRetrieveGeneralTestAPI (remains the same)
class TestRetrieveGeneralTestAPI:
    def test_retrieve_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_not_subscribed(self, authenticated_client):
        attempt, _ = create_completed_attempt(user=authenticated_client.user)
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_not_owner(self, subscribed_client):
        other_user = UserFactory()
        attempt_other, _ = create_completed_attempt(user=other_user)
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt_other.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_not_found(self, subscribed_client):
        url = reverse("api:v1:study:test-attempt-detail", kwargs={"attempt_id": 9999})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_started_success(self, subscribed_client, started_test_attempt):
        attempt, questions = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.STARTED
        assert res_data["score_percentage"] is None
        assert res_data["results_summary"] is None
        assert len(res_data["questions"]) == len(questions)
        assert "correct_answer" not in res_data["questions"][0]
        assert "explanation" not in res_data["questions"][0]

    def test_retrieve_completed_success(
        self, subscribed_client, completed_test_attempt
    ):
        attempt, questions = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED
        assert res_data["score_percentage"] is not None
        assert res_data["results_summary"] is not None
        assert len(res_data["questions"]) == len(questions)


# TestSubmitGeneralTestAPI (MODIFIED)
class TestSubmitGeneralTestAPI:

    @pytest.fixture
    def submit_payload(self, started_test_attempt):
        attempt, questions = started_test_attempt
        return {
            "answers": [
                {
                    "question_id": q.id,
                    "selected_answer": q.correct_answer,
                    "time_taken_seconds": 30 + i,
                }
                for i, q in enumerate(questions)
            ]
        }

    # Tests for unauthenticated, not subscribed, not owner, not found, already completed, wrong number remain the same
    def test_submit_unauthenticated(
        self, api_client, started_test_attempt, submit_payload
    ):
        attempt, _ = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.post(url, submit_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_not_subscribed(self, authenticated_client):
        attempt, questions = create_completed_attempt(user=authenticated_client.user)
        attempt.status = UserTestAttempt.Status.STARTED
        attempt.score_percentage = None
        attempt.end_time = None
        attempt.save()
        payload = {
            "answers": [
                {"question_id": q.id, "selected_answer": "A"} for q in questions
            ]
        }
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_not_owner(self, subscribed_client, submit_payload):
        other_user = UserFactory()
        attempt_other, _ = create_completed_attempt(user=other_user)
        attempt_other.status = UserTestAttempt.Status.STARTED
        attempt_other.save()
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt_other.id}
        )
        response = subscribed_client.post(
            url,
            {"answers": [{"question_id": 1, "selected_answer": "A"}]},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_not_found(self, subscribed_client, submit_payload):
        url = reverse("api:v1:study:test-attempt-submit", kwargs={"attempt_id": 9999})
        response = subscribed_client.post(url, submit_payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_already_completed(
        self, subscribed_client, completed_test_attempt, submit_payload
    ):
        attempt, _ = completed_test_attempt
        questions = Question.objects.filter(id__in=attempt.question_ids)
        payload = {
            "answers": [
                {"question_id": q.id, "selected_answer": "A"} for q in questions
            ]
        }
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "This test attempt has already been submitted or abandoned" in str(
            response.data
        )

    def test_submit_wrong_number_of_answers(
        self, subscribed_client, started_test_attempt, submit_payload
    ):
        attempt, _ = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        payload = submit_payload.copy()
        payload["answers"] = payload["answers"][:-1]
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect number of answers submitted" in str(response.data)

    # MODIFIED success test
    def test_submit_success(
        self, subscribed_client, started_test_attempt, submit_payload
    ):
        attempt, questions = started_test_attempt
        user = subscribed_client.user

        # --- Setup Skill Proficiency & Capture Initial State (Optional but good) ---
        skills_in_test = {q.skill for q in questions if q.skill}
        initial_skill_states = {}
        for skill in skills_in_test:
            prof, created = UserSkillProficiency.objects.get_or_create(
                user=user, skill=skill
            )
            initial_skill_states[skill.id] = {
                "attempts": prof.attempts_count,
                "correct": prof.correct_count,
            }

        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(url, submit_payload, format="json")

        # --- Assertions ---
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED
        assert res_data["score_percentage"] == pytest.approx(
            100.0
        )  # Payload has all correct
        assert "results_summary" in res_data
        assert "smart_analysis" in res_data
        assert "message" in res_data  # Check for the new message field
        # REMOVED: Assertions for points_earned and current_total_points in response

        # --- Check DB state (still important) ---
        attempt.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert attempt.score_percentage == pytest.approx(100.0)
        assert UserQuestionAttempt.objects.filter(test_attempt=attempt).count() == len(
            questions
        )
        # Check proficiency update still happens synchronously
        for skill in skills_in_test:
            prof = UserSkillProficiency.objects.get(user=user, skill=skill)
            initial_state = initial_skill_states[skill.id]
            new_attempts = sum(1 for q in questions if q.skill == skill)
            new_correct = new_attempts  # All answers correct in payload
            expected_attempts = initial_state["attempts"] + new_attempts
            expected_correct = initial_state["correct"] + new_correct
            assert prof.attempts_count == expected_attempts
            assert prof.correct_count == expected_correct
            if expected_attempts > 0:
                assert prof.proficiency_score == pytest.approx(
                    expected_correct / expected_attempts, abs=1e-4
                )
            else:
                assert prof.proficiency_score == 0.0
        # REMOVED: Direct check of profile.points update (handled by signal)


# TestReviewGeneralTestAPI (remains the same)
class TestReviewGeneralTestAPI:
    def test_review_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_review_not_subscribed(self, authenticated_client):
        attempt, _ = create_completed_attempt(user=authenticated_client.user)
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_review_not_owner(self, subscribed_client):
        other_user = UserFactory()
        attempt_other, _ = create_completed_attempt(user=other_user)
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt_other.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_review_not_found(self, subscribed_client):
        url = reverse("api:v1:study:test-attempt-review", kwargs={"attempt_id": 9999})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_review_attempt_not_completed(
        self, subscribed_client, started_test_attempt
    ):
        attempt, _ = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Cannot review an ongoing" in str(response.data)

    def test_review_success_all(self, subscribed_client, completed_test_attempt):
        attempt, questions = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["attempt_id"] == attempt.id
        assert "review_questions" in res_data
        assert len(res_data["review_questions"]) == len(questions)
        q_review_first = res_data["review_questions"][0]
        q_obj_first = Question.objects.get(id=q_review_first["id"])
        q_attempt_first = UserQuestionAttempt.objects.get(
            test_attempt=attempt, question=q_obj_first
        )
        assert "correct_answer" in q_review_first
        assert "explanation" in q_review_first
        assert q_review_first["user_selected_answer"] == q_attempt_first.selected_answer
        assert q_review_first["is_correct"] == q_attempt_first.is_correct

    def test_review_success_incorrect_only(
        self, subscribed_client, completed_test_attempt
    ):
        attempt, questions = completed_test_attempt  # Has 2 incorrect
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url, {"incorrect_only": "true"})
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert len(res_data["review_questions"]) == 2  # Only the 2 incorrect ones
        for q_review in res_data["review_questions"]:
            assert q_review["is_correct"] is False


# TestRetakeSimilarAPI (remains the same)
class TestRetakeSimilarAPI:
    def test_retake_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retake_not_subscribed(self, authenticated_client):
        attempt, _ = create_completed_attempt(user=authenticated_client.user)
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retake_not_owner(self, subscribed_client):
        other_user = UserFactory()
        attempt_other, _ = create_completed_attempt(user=other_user)
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt_other.id},
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retake_not_found(self, subscribed_client):
        url = reverse(
            "api:v1:study:test-attempt-retake-similar", kwargs={"attempt_id": 9999}
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retake_invalid_original_config(self, subscribed_client):
        attempt = UserTestAttemptFactory(
            user=subscribed_client.user,
            completed=True,
            test_configuration={"invalid": "structure"},
        )
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "configuration is missing or invalid" in str(response.data)

    def test_retake_no_new_questions_available(
        self, subscribed_client, completed_test_attempt
    ):
        attempt, questions = completed_test_attempt
        original_num_questions = attempt.test_configuration["config"]["num_questions"]
        Question.objects.exclude(id__in=attempt.question_ids).delete()
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert "attempt_id" in res_data
        assert "questions" in res_data
        assert isinstance(res_data["attempt_id"], int)
        assert res_data["attempt_id"] > 0
        assert res_data["attempt_id"] != attempt.id
        num_selected = len(res_data["questions"])
        assert num_selected > 0
        assert num_selected <= original_num_questions
        selected_ids = {q["id"] for q in res_data["questions"]}
        assert selected_ids.issubset(set(attempt.question_ids))
        new_attempt = UserTestAttempt.objects.get(pk=res_data["attempt_id"])
        assert new_attempt.user == subscribed_client.user
        assert new_attempt.status == UserTestAttempt.Status.STARTED
        assert new_attempt.test_configuration["retake_of_attempt_id"] == attempt.id
        assert len(new_attempt.question_ids) == num_selected

    def test_retake_success(
        self, subscribed_client, completed_test_attempt, setup_learning_content
    ):
        attempt, original_questions = completed_test_attempt
        original_config = attempt.test_configuration["config"]
        original_sub_slugs = original_config.get("subsections", [])
        if original_sub_slugs:
            sub = Question.objects.get(id=original_questions[0].id).subsection
            QuestionFactory.create_batch(10, subsection=sub, is_active=True)
        else:
            QuestionFactory.create_batch(10, is_active=True)
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        initial_attempt_count = UserTestAttempt.objects.filter(
            user=subscribed_client.user
        ).count()
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert "attempt_id" in res_data
        assert "questions" in res_data
        assert isinstance(res_data["attempt_id"], int)
        assert res_data["attempt_id"] > 0
        assert res_data["attempt_id"] != attempt.id
        assert len(res_data["questions"]) == original_config["num_questions"]
        assert (
            UserTestAttempt.objects.filter(user=subscribed_client.user).count()
            == initial_attempt_count + 1
        )
        new_attempt = UserTestAttempt.objects.get(pk=res_data["attempt_id"])
        assert new_attempt.status == UserTestAttempt.Status.STARTED
        assert new_attempt.attempt_type == attempt.attempt_type
        assert (
            new_attempt.test_configuration["config"]["num_questions"]
            == original_config["num_questions"]
        )
        assert new_attempt.test_configuration["retake_of_attempt_id"] == attempt.id
        assert set(new_attempt.question_ids) != set(attempt.question_ids)
