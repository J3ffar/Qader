import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.study.models import UserTestAttempt, UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import (
    Question,
    UserStarredQuestion,
    LearningSubSection,
    Skill,
)
from apps.users.models import UserProfile

# Import factories (assuming correct paths)
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
    create_completed_attempt,  # Use the helper
    UserSkillProficiencyFactory,
)
from apps.learning.tests.factories import (
    QuestionFactory,
    LearningSubSectionFactory,
    SkillFactory,
)
from apps.users.tests.factories import UserFactory  # Needed for direct creation

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

# Constants
NUM_QUESTIONS_DEFAULT = 5

# --- Fixtures specific to this test file ---


@pytest.fixture
def started_test_attempt(db, subscribed_user, setup_learning_content):
    """Creates a STARTED test attempt for the subscribed_user."""
    questions = Question.objects.filter(is_active=True)[:NUM_QUESTIONS_DEFAULT]
    attempt = UserTestAttemptFactory(
        user=subscribed_user,
        status=UserTestAttempt.Status.STARTED,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        question_ids=[q.id for q in questions],
    )
    return attempt, list(questions)


@pytest.fixture
def completed_test_attempt(db, subscribed_user, setup_learning_content):
    """Creates a COMPLETED test attempt for the subscribed_user using the helper."""
    attempt, questions = create_completed_attempt(
        user=subscribed_user,
        num_questions=NUM_QUESTIONS_DEFAULT,
        num_correct=3,
        attempt_type=UserTestAttempt.AttemptType.PRACTICE,
    )
    return attempt, questions


# --- Test Classes ---


class TestListGeneralTestsAPI:

    def test_list_unauthenticated(self, api_client):
        url = reverse("api:v1:study:test-attempt-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_not_subscribed(
        self, authenticated_client
    ):  # Uses unsubscribed user fixture
        url = reverse("api:v1:study:test-attempt-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_success(self, subscribed_client, completed_test_attempt):
        user = subscribed_client.user
        attempt1, _ = completed_test_attempt  # Fixture creates one
        # Create another attempt of a different type for the same user
        attempt2 = UserTestAttemptFactory(
            user=user, completed=True, level_assessment=True
        )
        # Create attempt for another user
        other_user = UserFactory()
        UserTestAttemptFactory(user=other_user, completed=True)

        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        res_data = response.json()
        assert res_data["count"] == 2  # Only attempts for subscribed_client.user
        assert len(res_data["results"]) == 2

        # Check structure (example of one result) - order depends on default ordering (-start_time)
        result_ids = {r["attempt_id"] for r in res_data["results"]}
        assert result_ids == {attempt1.id, attempt2.id}

        first_result = next(
            r for r in res_data["results"] if r["attempt_id"] == attempt2.id
        )  # Find attempt2 result
        assert first_result["test_type"] == attempt2.get_attempt_type_display()
        assert "date" in first_result
        assert first_result["num_questions"] == attempt2.num_questions
        assert first_result["score_percentage"] == attempt2.score_percentage
        assert first_result["status"] == UserTestAttempt.Status.COMPLETED
        assert "performance" in first_result  # Check optional field presence

    def test_list_empty(self, subscribed_client):
        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.json()
        assert res_data["count"] == 0
        assert len(res_data["results"]) == 0

    def test_list_pagination(self, subscribed_client):
        user = subscribed_client.user
        UserTestAttemptFactory.create_batch(25, user=user, completed=True)

        url = reverse("api:v1:study:test-attempt-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.json()
        assert res_data["count"] == 25
        assert len(res_data["results"]) == 20  # Default page size
        assert res_data["next"] is not None

        response_page2 = subscribed_client.get(res_data["next"])
        assert response_page2.status_code == status.HTTP_200_OK
        assert len(response_page2.json()["results"]) == 5


class TestStartGeneralTestAPI:

    @pytest.fixture
    def start_payload(self, db, setup_learning_content):
        """Provides a valid payload for starting a custom test."""
        sub1 = LearningSubSection.objects.get(slug="algebra")
        sub2 = LearningSubSection.objects.get(slug="geometry")
        return {
            "test_type": UserTestAttempt.AttemptType.PRACTICE,
            "config": {
                "name": "My Custom Test",
                "subsections": [sub1.slug, sub2.slug],
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
        res_data = response.data
        assert "attempt_id" in res_data
        assert "questions" in res_data
        assert isinstance(res_data["questions"], list)
        # Check if num questions matches request (or available pool if fewer)
        assert len(res_data["questions"]) <= start_payload["config"]["num_questions"]
        assert len(res_data["questions"]) > 0  # Should select some

        # Verify DB
        attempt = UserTestAttempt.objects.get(pk=res_data["attempt_id"])
        assert attempt.user == subscribed_client.user
        assert attempt.status == UserTestAttempt.Status.STARTED
        assert attempt.attempt_type == start_payload["test_type"]  # Check type stored
        assert len(attempt.question_ids) == len(res_data["questions"])
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
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Error likely in config sub-serializer or main serializer validate
        assert "Must specify subsections, skills, or filter by starred" in str(
            response.data
        )

    def test_start_no_questions_match(self, subscribed_client, start_payload):
        url = reverse("api:v1:study:test-attempt-start")
        payload = start_payload.copy()
        invalid_slug = "non-existent-slug-123"
        payload["config"]["subsections"] = [invalid_slug]
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # FIX: Modify assertion to check error content
        assert "config" in response.data
        error_str = str(response.data["config"])  # Convert error detail to string
        assert f"slug={invalid_slug}" in error_str  # Check if invalid slug is mentioned
        assert "does_not_exist" in error_str  # Check for the specific error code

    def test_start_with_starred_filter(self, subscribed_client, setup_learning_content):
        user = subscribed_client.user
        # Star some questions
        questions_to_star = Question.objects.filter(
            subsection__slug="algebra"
        ).order_by("?")[:3]
        starred_ids = []
        for q in questions_to_star:
            UserStarredQuestion.objects.create(user=user, question=q)
            starred_ids.append(q.id)

        url = reverse("api:v1:study:test-attempt-start")
        payload = {
            "test_type": UserTestAttempt.AttemptType.PRACTICE,
            "config": {
                "subsections": [],  # No subsections specified
                "skills": [],
                "num_questions": 3,
                "starred": True,  # Filter ONLY by starred
                "not_mastered": False,
                "full_simulation": False,
            },
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert len(res_data["questions"]) == 3
        returned_ids = {q["id"] for q in res_data["questions"]}
        assert returned_ids == set(
            starred_ids
        )  # Should only return the starred questions

    def test_start_with_not_mastered_filter(
        self, subscribed_client, setup_learning_content
    ):
        user = subscribed_client.user
        skill1 = Skill.objects.filter(subsection__slug="algebra").first()
        skill2 = Skill.objects.filter(subsection__slug="geometry").first()
        # Create proficiency records: one low, one high
        UserSkillProficiencyFactory(
            user=user, skill=skill1, proficiency_score=0.2, attempts_count=10
        )
        UserSkillProficiencyFactory(
            user=user, skill=skill2, proficiency_score=0.9, attempts_count=10
        )
        # Create questions for these skills
        q_low_prof = QuestionFactory.create_batch(5, skill=skill1)
        QuestionFactory.create_batch(5, skill=skill2)

        url = reverse("api:v1:study:test-attempt-start")
        payload = {
            "test_type": UserTestAttempt.AttemptType.PRACTICE,
            "config": {
                "subsections": [],
                "skills": [],
                "num_questions": 5,
                "starred": False,
                "not_mastered": True,  # Filter by low proficiency
                "full_simulation": False,
            },
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        res_data = response.data
        assert len(res_data["questions"]) == 5
        returned_skill_ids = {
            q["skill"] for q in res_data["questions"] if q.get("skill")
        }  # Get skill ID from response
        # Should only contain the skill with low proficiency
        assert returned_skill_ids == {skill1.id}


class TestRetrieveGeneralTestAPI:

    def test_retrieve_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_not_subscribed(
        self, authenticated_client, completed_test_attempt
    ):
        # Need to create an attempt for the *authenticated_client*'s user
        attempt = UserTestAttemptFactory(user=authenticated_client.user, completed=True)
        url = reverse(
            "api:v1:study:test-attempt-detail", kwargs={"attempt_id": attempt.id}
        )
        response = authenticated_client.get(url)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # Permission denies access

    def test_retrieve_not_owner(self, subscribed_client, completed_test_attempt):
        other_user = UserFactory()
        attempt_other_user = UserTestAttemptFactory(user=other_user, completed=True)
        url = reverse(
            "api:v1:study:test-attempt-detail",
            kwargs={"attempt_id": attempt_other_user.id},
        )
        response = subscribed_client.get(url)
        # RetrieveAPIView's get_queryset filters, resulting in 404 for non-owners
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
        assert (
            "correct_answer" not in res_data["questions"][0]
        )  # Verify sensitive info hidden

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


class TestSubmitGeneralTestAPI:

    @pytest.fixture
    def submit_payload(self, started_test_attempt):
        """Creates a valid payload for submitting the started_test_attempt."""
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

    def test_submit_unauthenticated(
        self, api_client, started_test_attempt, submit_payload
    ):
        attempt, _ = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.post(url, submit_payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_not_subscribed(
        self, authenticated_client, started_test_attempt, submit_payload
    ):
        # Create attempt for the non-subscribed user
        attempt = UserTestAttemptFactory(
            user=authenticated_client.user, status=UserTestAttempt.Status.STARTED
        )
        # Adjust payload for this attempt's questions
        questions = Question.objects.filter(id__in=attempt.question_ids)
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
        attempt_other_user = UserTestAttemptFactory(
            user=other_user, status=UserTestAttempt.Status.STARTED
        )
        url = reverse(
            "api:v1:study:test-attempt-submit",
            kwargs={"attempt_id": attempt_other_user.id},
        )
        # Need payload matching other user's questions, difficult here.
        # Focus on the 400 error from serializer validation.
        # Use a generic payload structure.
        generic_payload = {"answers": [{"question_id": 1, "selected_answer": "A"}]}
        response = subscribed_client.post(url, generic_payload, format="json")
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        )  # Serializer validation fails ownership
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_not_found(self, subscribed_client, submit_payload):
        url = reverse("api:v1:study:test-attempt-submit", kwargs={"attempt_id": 9999})
        response = subscribed_client.post(url, submit_payload, format="json")
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        )  # Serializer validation catches 404
        assert "not found or does not belong to you" in str(response.data)

    def test_submit_already_completed(
        self, subscribed_client, completed_test_attempt, submit_payload
    ):
        attempt, _ = completed_test_attempt  # This attempt is already completed
        # Adjust payload to match questions of the completed attempt
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
        assert "not active or has already been submitted" in str(response.data)

    def test_submit_wrong_number_of_answers(
        self, subscribed_client, started_test_attempt, submit_payload
    ):
        attempt, _ = started_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        payload = submit_payload.copy()
        payload["answers"] = payload["answers"][:-1]  # Remove one answer
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Incorrect number of answers submitted" in str(response.data)

    def test_submit_success(
        self, subscribed_client, started_test_attempt, submit_payload
    ):
        attempt, questions = started_test_attempt
        user = subscribed_client.user
        profile = user.profile
        initial_points = profile.points
        # Ensure proficiency records exist or are created
        for q in questions:
            if q.skill:
                UserSkillProficiencyFactory(
                    user=user, skill=q.skill, attempts_count=5, proficiency_score=0.5
                )

        url = reverse(
            "api:v1:study:test-attempt-submit", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.post(url, submit_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data

        assert res_data["attempt_id"] == attempt.id
        assert res_data["status"] == UserTestAttempt.Status.COMPLETED
        assert res_data["score_percentage"] == 100.0  # Payload used correct answers
        assert "results_summary" in res_data
        assert "smart_analysis" in res_data
        assert res_data["points_earned"] == 10  # Default points
        assert res_data["current_total_points"] == initial_points + 10

        # Verify DB
        attempt.refresh_from_db()
        profile.refresh_from_db()
        assert attempt.status == UserTestAttempt.Status.COMPLETED
        assert attempt.end_time is not None
        assert attempt.score_percentage == 100.0
        assert profile.points == initial_points + 10
        assert UserQuestionAttempt.objects.filter(test_attempt=attempt).count() == len(
            questions
        )
        # Check proficiency update (example for one skill if present)
        first_skill = questions[0].skill
        if first_skill:
            prof = UserSkillProficiency.objects.get(user=user, skill=first_skill)
            assert prof.attempts_count == 5 + 1  # Initial + 1 from test
            # Accuracy should improve as payload answers were correct
            assert prof.proficiency_score > 0.5


class TestReviewGeneralTestAPI:

    def test_review_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_review_not_subscribed(self, authenticated_client, completed_test_attempt):
        # Create completed attempt for non-subscribed user
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
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # get_object raises 404

    def test_review_not_found(self, subscribed_client):
        url = reverse("api:v1:study:test-attempt-review", kwargs={"attempt_id": 9999})
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_review_attempt_not_completed(
        self, subscribed_client, started_test_attempt
    ):
        attempt, _ = started_test_attempt  # Attempt is STARTED
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

        # Check details of one question
        q_review = res_data["review_questions"][0]
        q_obj = Question.objects.get(id=q_review["id"])
        q_attempt = UserQuestionAttempt.objects.get(
            test_attempt=attempt, question=q_obj
        )

        assert "correct_answer" in q_review
        assert "explanation" in q_review
        assert "user_selected_answer" in q_review
        assert "is_correct" in q_review
        assert q_review["user_selected_answer"] == q_attempt.selected_answer
        assert q_review["is_correct"] == q_attempt.is_correct

    def test_review_success_incorrect_only(
        self, subscribed_client, completed_test_attempt
    ):
        attempt, questions = completed_test_attempt  # Has 3 correct, 2 incorrect
        url = reverse(
            "api:v1:study:test-attempt-review", kwargs={"attempt_id": attempt.id}
        )
        response = subscribed_client.get(url, {"incorrect_only": "true"})

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert len(res_data["review_questions"]) == 2  # Only incorrect ones
        for q_review in res_data["review_questions"]:
            assert q_review["is_correct"] is False


class TestRetakeSimilarAPI:

    def test_retake_unauthenticated(self, api_client, completed_test_attempt):
        attempt, _ = completed_test_attempt
        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retake_not_subscribed(self, authenticated_client, completed_test_attempt):
        # Create completed attempt for non-subscribed user
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
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # get_object raises 404

    def test_retake_not_found(self, subscribed_client):
        url = reverse(
            "api:v1:study:test-attempt-retake-similar", kwargs={"attempt_id": 9999}
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retake_invalid_original_config(self, subscribed_client):
        attempt = UserTestAttemptFactory(
            user=subscribed_client.user, completed=True, test_configuration=None
        )  # No config
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
        # Delete all other questions that might match the config
        Question.objects.exclude(id__in=attempt.question_ids).delete()

        url = reverse(
            "api:v1:study:test-attempt-retake-similar",
            kwargs={"attempt_id": attempt.id},
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No suitable questions found" in str(response.data)

    def test_retake_success(self, subscribed_client, completed_test_attempt):
        attempt, original_questions = completed_test_attempt
        # Create more questions matching the config to ensure different ones can be selected
        QuestionFactory.create_batch(10)  # General pool

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

        assert "new_attempt_id" in res_data
        assert res_data["new_attempt_id"] != attempt.id
        assert "message" in res_data
        assert "questions" in res_data
        assert len(res_data["questions"]) == len(
            original_questions
        )  # Should match num_questions

        # Verify DB
        assert (
            UserTestAttempt.objects.filter(user=subscribed_client.user).count()
            == initial_attempt_count + 1
        )
        new_attempt = UserTestAttempt.objects.get(pk=res_data["new_attempt_id"])
        assert new_attempt.status == UserTestAttempt.Status.STARTED
        assert new_attempt.attempt_type == attempt.attempt_type
        # Check config copied (ignoring question selection part)
        assert (
            new_attempt.test_configuration["config"]["num_questions"]
            == attempt.test_configuration["config"]["num_questions"]
        )
        # Check questions are different (highly likely)
        assert set(new_attempt.question_ids) != set(attempt.question_ids)
