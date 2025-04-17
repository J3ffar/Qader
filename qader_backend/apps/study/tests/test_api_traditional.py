# qader_backend/apps/study/tests/test_api_traditional.py
import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.study.models import UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion
from apps.users.models import (
    UserProfile,
    # UserSkillProficiency,
    # UserStarredQuestion,
    # PointLog,
)
from apps.learning.tests.factories import QuestionFactory, SkillFactory
from apps.study.api.views import TraditionalLearningQuestionListView
from apps.study.tests.factories import UserSkillProficiencyFactory

# from .factories import (
#     UserSkillProficiencyFactory,
# )  # Assuming this factory exists or create it

# Import common fixtures like subscribed_client, setup_learning_content
# These might be defined in apps/study/tests/conftest.py or root conftest.py

pytestmark = pytest.mark.django_db

# --- Tests for GET /api/v1/study/traditional/questions/ ---


class TestTraditionalQuestionsList:

    @pytest.fixture(autouse=True)
    def _setup_content(
        self, setup_learning_content
    ):  # This fixture now comes from conftest.py
        """Ensure learning content is set up for all tests in this class."""
        self.learning_content = setup_learning_content
        # Create some skills for testing skill-based filtering
        # Ensure subsections exist before creating skills attached to them
        algebra_subsection = (
            Question.objects.filter(subsection__slug="algebra").first().subsection
        )
        reading_subsection = (
            Question.objects.filter(subsection__slug="reading-comp").first().subsection
        )

        # Ensure subsections were found before proceeding
        if not algebra_subsection:
            pytest.skip("Algebra subsection not found during skill setup.")
        if not reading_subsection:
            pytest.skip("Reading Comp subsection not found during skill setup.")

        self.skill_algebra = SkillFactory(
            name="Algebra Skill", slug="algebra-skill", subsection=algebra_subsection
        )
        self.skill_reading = SkillFactory(
            name="Reading Skill", slug="reading-skill", subsection=reading_subsection
        )

        # Assign skills to some questions
        Question.objects.filter(subsection=algebra_subsection).update(
            skill=self.skill_algebra
        )
        Question.objects.filter(subsection=reading_subsection).update(
            skill=self.skill_reading
        )

    def test_get_questions_unauthenticated(self, api_client):
        url = reverse("api:v1:study:traditional-questions-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_questions_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:traditional-questions-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_questions_default_limit(self, subscribed_client):
        url = reverse("api:v1:study:traditional-questions-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Check for dict and access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        assert isinstance(response.data["results"], list)
        assert len(response.data["results"]) <= 10  # Default limit is 10
        if response.data["results"]:
            assert "question_text" in response.data["results"][0]
            assert "is_starred" in response.data["results"][0]  # Field from serializer
        # --- END FIX ---

    def test_get_questions_custom_limit(self, subscribed_client):
        url = reverse("api:v1:study:traditional-questions-list") + "?limit=5"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        assert len(response.data["results"]) <= 5
        # --- END FIX ---

    def test_get_questions_filter_by_subsection(self, subscribed_client):
        url = (
            reverse("api:v1:study:traditional-questions-list")
            + "?subsection__slug__in=algebra,geometry"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        results = response.data["results"]
        all_quant = all(q["subsection"] in ["algebra", "geometry"] for q in results)
        # --- END FIX ---
        assert all_quant or not results  # Ensure all returned questions match

    def test_get_questions_filter_by_skill(self, subscribed_client):
        url = (
            reverse("api:v1:study:traditional-questions-list")
            + "?skill__slug__in=algebra-skill"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        results = response.data["results"]
        all_skill_match = all(q["skill"] == "algebra-skill" for q in results)
        # --- END FIX ---
        assert all_skill_match or not results

    def test_get_questions_filter_starred(self, subscribed_client):
        user = subscribed_client.user
        q_to_star = Question.objects.filter(is_active=True).first()
        if not q_to_star:
            pytest.skip("No active questions to star.")
        UserStarredQuestion.objects.create(user=user, question=q_to_star)

        url = reverse("api:v1:study:traditional-questions-list") + "?starred=true"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        results = response.data["results"]
        assert len(results) > 0  # Assuming starred question is returned
        found_starred = any(q["id"] == q_to_star.id for q in results)
        all_are_starred_in_response = all(
            q["is_starred"] for q in results
        )  # Serializer adds this flag
        # --- END FIX ---

        # This assertion depends on whether the filter *only* returns starred,
        # or just includes them. The current filter implementation fetches *only* starred.
        assert found_starred
        assert all_are_starred_in_response

    def test_get_questions_filter_not_mastered(self, subscribed_client):
        user = subscribed_client.user
        # Use the threshold defined in the view for consistency
        prof_threshold = TraditionalLearningQuestionListView.PROFICIENCY_THRESHOLD

        # Ensure skills exist from _setup_content before creating proficiency
        if not hasattr(self, "skill_algebra") or not hasattr(self, "skill_reading"):
            pytest.skip("Skills not properly set up in fixture.")

        # Make user proficient in algebra
        UserSkillProficiencyFactory(
            user=user, skill=self.skill_algebra, proficiency_score=0.9
        )
        # Make user weak in reading
        UserSkillProficiencyFactory(
            user=user, skill=self.skill_reading, proficiency_score=0.4
        )
        # Assume another skill exists that user hasn't attempted

        url = (
            reverse("api:v1:study:traditional-questions-list")
            + "?not_mastered=true&limit=50"
        )  # High limit to get more results
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        results = response.data["results"]
        returned_skill_slugs = {
            q["skill"] for q in results if q.get("skill")
        }  # Use .get for safety
        # --- END FIX ---

        # Should contain reading skill, maybe unttempted skills, but NOT algebra skill
        assert self.skill_reading.slug in returned_skill_slugs
        assert self.skill_algebra.slug not in returned_skill_slugs
        # Can't easily check for unattempted skills without knowing all possible skills

    def test_get_questions_exclude_ids(self, subscribed_client):
        q1 = Question.objects.filter(is_active=True).order_by("id").first()
        q2 = Question.objects.filter(is_active=True).order_by("-id").first()
        if not q1 or not q2 or q1.id == q2.id:
            pytest.skip("Need at least two distinct active questions.")

        exclude_str = f"{q1.id},{q2.id}"

        url = (
            reverse("api:v1:study:traditional-questions-list")
            + f"?exclude_ids={exclude_str}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # --- FIX: Access 'results' ---
        assert isinstance(response.data, dict)
        assert "results" in response.data
        results = response.data["results"]
        returned_ids = {q["id"] for q in results}
        # --- END FIX ---
        assert q1.id not in returned_ids
        assert q2.id not in returned_ids


# --- Tests for POST /api/v1/study/traditional/answer/ ---


class TestTraditionalAnswerSubmit:

    @pytest.fixture(autouse=True)
    def _setup_content(
        self, setup_learning_content
    ):  # This fixture now comes from conftest.py
        """Ensure learning content is set up."""
        self.learning_content = setup_learning_content

    def test_submit_answer_unauthenticated(self, api_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        # Need a valid question ID even for unauthenticated test
        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found.")
        payload = {"question_id": question.id, "selected_answer": "A"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_answer_not_subscribed(self, authenticated_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        # Need a valid question ID first
        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found to test with.")
        payload = {"question_id": question.id, "selected_answer": "A"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_correct_answer(self, subscribed_client):
        user = subscribed_client.user
        # --- FIX: Ensure profile exists before accessing points ---
        profile, _ = UserProfile.objects.get_or_create(user=user)
        initial_points = profile.points
        initial_streak = profile.current_streak_days

        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found.")

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
            "time_taken_seconds": 25,
        }
        response = subscribed_client.post(url, payload, format="json")

        print("Correct Answer Response:", response.data)  # Debug

        assert response.status_code == status.HTTP_200_OK
        # ... (rest of the assertions remain the same, they should pass after NameError fix) ...
        assert response.data["question_id"] == question.id
        assert response.data["is_correct"] is True
        assert response.data["correct_answer"] == question.correct_answer
        assert response.data["explanation"] == question.explanation
        assert response.data["points_earned"] > 0  # Should earn points
        assert (
            response.data["current_total_points"]
            == initial_points + response.data["points_earned"]
        )
        assert (
            response.data["current_streak"] >= initial_streak
        )  # Streak should increase or stay same

        # Check DB: UserQuestionAttempt
        attempt = (
            UserQuestionAttempt.objects.filter(
                user=user, question=question, mode="traditional"
            )
            .order_by("-attempted_at")
            .first()
        )
        assert attempt is not None
        assert attempt.is_correct is True
        assert attempt.selected_answer == question.correct_answer
        assert attempt.time_taken_seconds == 25

        # Check DB: UserProfile
        profile.refresh_from_db()
        assert profile.points == initial_points + response.data["points_earned"]
        assert profile.last_study_activity_at is not None
        # Check streak logic more carefully
        if response.data["streak_updated"]:
            # If it was updated, it must be > initial OR == 1 (if reset)
            assert (
                profile.current_streak_days > initial_streak
                or profile.current_streak_days == 1
            )
        else:
            # If not updated, must be same as initial (meaning second activity today)
            assert profile.current_streak_days == initial_streak

        # Check DB: PointLog
        # log_entry = PointLog.objects.filter(user=user).order_by("-timestamp").first()
        # assert log_entry is not None
        # assert log_entry.points_change == response.data["points_earned"]
        # assert log_entry.reason_code == "TRADITIONAL_CORRECT"

        # Check DB: Proficiency (basic check)
        if question.skill:
            prof = UserSkillProficiency.objects.filter(
                user=user, skill=question.skill
            ).first()
            assert prof is not None
            assert prof.attempts_count >= 1
            assert prof.correct_count >= 1

    def test_submit_incorrect_answer(self, subscribed_client):
        user = subscribed_client.user
        # --- FIX: Ensure profile exists ---
        profile, _ = UserProfile.objects.get_or_create(user=user)
        initial_points = profile.points

        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found.")
        incorrect_answer = "A" if question.correct_answer != "A" else "B"

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {
            "question_id": question.id,
            "selected_answer": incorrect_answer,
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        # ... (rest of the assertions remain the same) ...
        assert response.data["is_correct"] is False
        assert response.data["correct_answer"] == question.correct_answer
        assert (
            response.data["explanation"] == question.explanation
        )  # Should still get explanation
        assert response.data["points_earned"] == 0  # Assuming 0 points for incorrect
        assert (
            response.data["current_total_points"] == initial_points
        )  # Points shouldn't change

        # Check DB: UserQuestionAttempt
        attempt = (
            UserQuestionAttempt.objects.filter(
                user=user, question=question, mode="traditional"
            )
            .order_by("-attempted_at")
            .first()
        )
        assert attempt is not None
        assert attempt.is_correct is False
        assert attempt.selected_answer == incorrect_answer

        # Check DB: PointLog (should not have a new entry if points_earned is 0)
        # log_entry = PointLog.objects.filter(user=user).order_by('-timestamp').first()
        # assert log_entry.points_change != 0 # Or check count increased only if points != 0

    def test_submit_answer_invalid_question_id(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": 99999, "selected_answer": "A"}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "question_id" in response.data

    def test_submit_answer_missing_field(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found.")
        payload = {"question_id": question.id}  # Missing selected_answer
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data

    def test_streak_update_logic(self, subscribed_client):
        user = subscribed_client.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        question = Question.objects.filter(is_active=True).first()
        if not question:
            pytest.skip("No active questions found.")
        url = reverse("api:v1:study:traditional-answer-submit")

        # Scenario 1: First activity today (Streak reset)
        profile.last_study_activity_at = timezone.now() - timedelta(
            days=2
        )  # Clearly more than 1 day ago
        profile.current_streak_days = 5  # Assume previous streak
        profile.save()
        initial_streak_s1 = profile.current_streak_days
        payload1 = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
        }
        response1 = subscribed_client.post(url, payload1, format="json")
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["streak_updated"] is True
        assert response1.data["current_streak"] == 1
        profile.refresh_from_db()
        assert profile.current_streak_days == 1

        # Scenario 2: Continuing streak from yesterday
        yesterday_dt = timezone.now() - timedelta(days=1)
        profile.last_study_activity_at = yesterday_dt
        profile.current_streak_days = 1  # Set from previous step result
        profile.save()
        initial_streak_s2 = profile.current_streak_days
        payload2 = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
        }
        response2 = subscribed_client.post(url, payload2, format="json")
        assert response2.status_code == status.HTTP_200_OK
        print("DEBUG: Response 2 Data:", response2.data)  # Keep for debugging if needed
        # This assertion should now pass with the serializer fix
        assert response2.data["streak_updated"] is True
        assert response2.data["current_streak"] == 2
        profile.refresh_from_db()
        assert profile.current_streak_days == 2

        # Scenario 3: Second activity on the same day
        profile.last_study_activity_at = timezone.now() - timedelta(minutes=10)
        profile.current_streak_days = 2
        profile.save()
        initial_streak_s3 = profile.current_streak_days
        payload3 = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
        }
        response3 = subscribed_client.post(url, payload3, format="json")
        assert response3.status_code == status.HTTP_200_OK
        assert response3.data["streak_updated"] is False
        assert response3.data["current_streak"] == 2
        profile.refresh_from_db()
        assert profile.current_streak_days == 2
