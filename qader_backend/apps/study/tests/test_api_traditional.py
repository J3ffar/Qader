from django.conf import settings
import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.study.models import UserQuestionAttempt, UserSkillProficiency
from apps.learning.models import Question, UserStarredQuestion, Skill
from apps.users.models import UserProfile
from apps.learning.tests.factories import (
    QuestionFactory,
    SkillFactory,
    LearningSubSectionFactory,
)
from apps.study.tests.factories import UserSkillProficiencyFactory
from apps.study.api.views import (
    TraditionalLearningQuestionListView,
)  # Import for threshold

pytestmark = pytest.mark.django_db


class TestTraditionalQuestionsList:

    # Autouse fixture ensures setup_learning_content runs for all tests in this class
    @pytest.fixture(autouse=True)
    def _setup_content(self, setup_learning_content):
        self.learning_content = setup_learning_content
        # Ensure skills used in tests are available
        self.skill_algebra = setup_learning_content.get("algebra_skill")
        self.skill_reading = setup_learning_content.get("reading_skill")
        # Assign skills to some questions if not already done in fixture
        if self.skill_algebra:
            Question.objects.filter(subsection__slug="algebra").update(
                skill=self.skill_algebra
            )
        if self.skill_reading:
            Question.objects.filter(subsection__slug="reading-comp").update(
                skill=self.skill_reading
            )

    def test_get_questions_unauthenticated(self, api_client):
        url = reverse("api:v1:study:traditional-questions-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_questions_not_subscribed(
        self, authenticated_client
    ):  # Uses unsubscribed user
        url = reverse("api:v1:study:traditional-questions-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_questions_default_limit(self, subscribed_client):
        url = reverse("api:v1:study:traditional-questions-list")
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # ListAPIView without pagination returns a list directly
        assert isinstance(response.data, list)
        assert len(response.data) <= 10  # Default limit
        if response.data:
            assert "question_text" in response.data[0]
            assert "is_starred" in response.data[0]  # Check serializer field

    def test_get_questions_custom_limit(self, subscribed_client):
        url = reverse("api:v1:study:traditional-questions-list") + "?limit=5"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) <= 5

    def test_get_questions_filter_by_subsection(self, subscribed_client):
        algebra_slug = self.learning_content["algebra_sub"].slug
        geometry_slug = self.learning_content["geometry_sub"].slug
        url = (
            reverse("api:v1:study:traditional-questions-list")
            + f"?subsection__slug__in={algebra_slug},{geometry_slug}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Check if all returned questions belong to the specified subsections
        returned_sub_slugs = {q["subsection"] for q in response.data}
        assert (
            returned_sub_slugs.issubset({algebra_slug, geometry_slug})
            or not response.data
        )

    def test_get_questions_filter_by_skill(self, subscribed_client):
        if not self.skill_algebra:
            pytest.skip("Algebra skill not available")
        algebra_skill_slug = self.skill_algebra.slug
        url = (
            reverse("api:v1:study:traditional-questions-list")
            + f"?skill__slug__in={algebra_skill_slug}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        returned_skill_slugs = {q["skill"] for q in response.data if q.get("skill")}
        assert returned_skill_slugs.issubset({algebra_skill_slug}) or not response.data

    def test_get_questions_filter_starred(self, subscribed_client):
        user = subscribed_client.user
        q_to_star = Question.objects.filter(is_active=True).first()
        if not q_to_star:
            pytest.skip("No active questions to star.")
        UserStarredQuestion.objects.create(user=user, question=q_to_star)

        url = reverse("api:v1:study:traditional-questions-list") + "?starred=true"
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0  # At least the starred one should be returned
        # Verify all returned questions are indeed starred (as filter is exclusive)
        returned_ids = {q["id"] for q in response.data}
        starred_ids_in_db = set(
            UserStarredQuestion.objects.filter(
                user=user, question_id__in=returned_ids
            ).values_list("question_id", flat=True)
        )
        assert returned_ids == starred_ids_in_db
        assert all(q["is_starred"] for q in response.data)  # Check serializer flag

    def test_get_questions_filter_not_mastered(self, subscribed_client):
        user = subscribed_client.user
        if not self.skill_algebra or not self.skill_reading:
            pytest.skip("Required skills not available")
        # Make user weak in reading (score < threshold)
        UserSkillProficiencyFactory(
            user=user, skill=self.skill_reading, proficiency_score=0.4
        )
        # Make user proficient in algebra (score >= threshold)
        UserSkillProficiencyFactory(
            user=user, skill=self.skill_algebra, proficiency_score=0.9
        )
        # Create another skill user hasn't attempted
        unattempted_skill = SkillFactory(
            subsection=self.learning_content["geometry_sub"]
        )
        q_unattempted = QuestionFactory(skill=unattempted_skill, is_active=True)

        url = (
            reverse("api:v1:study:traditional-questions-list")
            + "?not_mastered=true&limit=50"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        returned_skill_slugs = {q["skill"] for q in response.data if q.get("skill")}
        # Should include weak skill (reading) and unattempted skill, but not proficient skill (algebra)
        assert self.skill_reading.slug in returned_skill_slugs
        assert unattempted_skill.slug in returned_skill_slugs
        assert self.skill_algebra.slug not in returned_skill_slugs

    def test_get_questions_exclude_ids(self, subscribed_client):
        active_questions = list(
            Question.objects.filter(is_active=True).order_by("id")[:2]
        )
        if len(active_questions) < 2:
            pytest.skip("Need at least 2 active questions.")
        q1, q2 = active_questions
        exclude_str = f"{q1.id},{q2.id}"

        url = (
            reverse("api:v1:study:traditional-questions-list")
            + f"?exclude_ids={exclude_str}"
        )
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        returned_ids = {q["id"] for q in response.data}
        assert q1.id not in returned_ids
        assert q2.id not in returned_ids


class TestTraditionalAnswerSubmit:

    @pytest.fixture(autouse=True)
    def _ensure_profile_and_content(self, subscribed_client, setup_learning_content):
        """Ensure user profile exists and content is set up."""
        self.user = subscribed_client.user
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.learning_content = setup_learning_content
        # Get a default question for tests
        self.question = Question.objects.filter(is_active=True).first()
        if not self.question:
            pytest.skip("No active question found for testing submit.")

    def test_submit_answer_unauthenticated(self, api_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": "A"}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_submit_answer_not_subscribed(
        self, authenticated_client
    ):  # Uses unsubscribed user
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": "A"}
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_submit_correct_answer(self, subscribed_client):
        initial_points = self.profile.points
        initial_streak = self.profile.current_streak_days
        initial_prof_score = 0.0
        if self.question.skill:
            prof, _ = UserSkillProficiency.objects.get_or_create(
                user=self.user, skill=self.question.skill
            )
            initial_prof_score = prof.proficiency_score

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {
            "question_id": self.question.id,
            "selected_answer": self.question.correct_answer,
        }
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["is_correct"] is True
        expected_points = getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
        assert res_data["points_earned"] == expected_points
        assert res_data["current_total_points"] == initial_points + expected_points

        # Check DB state
        self.profile.refresh_from_db()
        assert self.profile.points == initial_points + expected_points
        assert UserQuestionAttempt.objects.filter(
            user=self.user, question=self.question, mode="traditional", is_correct=True
        ).exists()
        if res_data["streak_updated"]:
            assert (
                self.profile.current_streak_days > initial_streak
                or self.profile.current_streak_days == 1
            )
        else:
            assert (
                self.profile.current_streak_days == initial_streak
            )  # Activity already today

        # Check proficiency update
        if self.question.skill:
            prof.refresh_from_db()
            assert (
                prof.proficiency_score >= initial_prof_score
            )  # Should increase or stay 1.0

    def test_submit_incorrect_answer(self, subscribed_client):
        initial_points = self.profile.points
        incorrect_answer = "A" if self.question.correct_answer != "A" else "B"
        initial_prof_score = 0.0
        if self.question.skill:
            prof, _ = UserSkillProficiency.objects.get_or_create(
                user=self.user, skill=self.question.skill
            )
            initial_prof_score = prof.proficiency_score

        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id, "selected_answer": incorrect_answer}
        response = subscribed_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        res_data = response.data
        assert res_data["is_correct"] is False
        expected_points = getattr(settings, "POINTS_TRADITIONAL_INCORRECT", 0)
        assert res_data["points_earned"] == expected_points
        assert (
            res_data["current_total_points"] == initial_points + expected_points
        )  # Points might be 0

        # Check DB state
        self.profile.refresh_from_db()
        assert self.profile.points == initial_points + expected_points
        assert UserQuestionAttempt.objects.filter(
            user=self.user, question=self.question, mode="traditional", is_correct=False
        ).exists()
        # Check proficiency update (should decrease or stay 0.0)
        if self.question.skill:
            prof.refresh_from_db()
            assert prof.proficiency_score <= initial_prof_score

    def test_submit_answer_invalid_question_id(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": 99999, "selected_answer": "A"}
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "question_id" in response.data and "does not exist" in str(
            response.data["question_id"]
        )

    def test_submit_answer_missing_field(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {"question_id": self.question.id}  # Missing selected_answer
        response = subscribed_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data and "required" in str(
            response.data["selected_answer"]
        )

    def test_streak_update_logic(self, subscribed_client):
        url = reverse("api:v1:study:traditional-answer-submit")
        payload = {
            "question_id": self.question.id,
            "selected_answer": self.question.correct_answer,
        }

        # Scenario 1: First activity today (Streak reset)
        self.profile.last_study_activity_at = timezone.now() - timedelta(days=2)
        self.profile.current_streak_days = 5
        self.profile.save()
        response1 = subscribed_client.post(url, payload, format="json")
        assert response1.status_code == status.HTTP_200_OK
        assert response1.data["streak_updated"] is True
        assert response1.data["current_streak"] == 1
        self.profile.refresh_from_db()
        assert self.profile.current_streak_days == 1

        # Scenario 2: Continuing streak from yesterday
        self.profile.last_study_activity_at = timezone.now() - timedelta(days=1)
        self.profile.current_streak_days = 1  # From previous step
        self.profile.save()
        response2 = subscribed_client.post(url, payload, format="json")
        assert response2.status_code == status.HTTP_200_OK
        assert response2.data["streak_updated"] is True
        assert response2.data["current_streak"] == 2
        self.profile.refresh_from_db()
        assert self.profile.current_streak_days == 2

        # Scenario 3: Second activity on the same day
        self.profile.last_study_activity_at = timezone.now() - timedelta(
            minutes=10
        )  # Already active today
        self.profile.current_streak_days = 2
        self.profile.save()
        response3 = subscribed_client.post(url, payload, format="json")
        assert response3.status_code == status.HTTP_200_OK
        assert response3.data["streak_updated"] is False  # No update to streak count
        assert response3.data["current_streak"] == 2
        self.profile.refresh_from_db()
        assert self.profile.current_streak_days == 2
