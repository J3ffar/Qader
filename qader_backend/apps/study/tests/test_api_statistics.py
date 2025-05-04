import random
import factory
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from decimal import Decimal

from apps.study.models import (
    UserTestAttempt,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.users.models import UserProfile
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
    UserSkillProficiencyFactory,
    create_attempt_scenario,  # Using updated helper
)
from apps.learning.models import Skill, LearningSection, LearningSubSection
from apps.study.api.serializers.statistics import RECENT_TESTS_LIMIT

pytestmark = pytest.mark.django_db


@pytest.fixture
def statistics_url():
    """Fixture for the statistics endpoint URL."""
    return reverse("api:v1:study:user-statistics")  # No change to URL name


@pytest.fixture
def setup_stats_data(subscribed_user, setup_learning_content):
    """Fixture to create comprehensive data for statistics testing."""
    user = subscribed_user
    profile = user.profile

    # 1. Update Profile Data (Remains same)
    profile.current_level_verbal = 75.5
    profile.current_level_quantitative = 60.0
    profile.current_streak_days = 5
    profile.longest_streak_days = 10
    profile.save()

    # 2. Create User Question Attempts (Remains same - stats reads these attempts)
    reading_comp_sub = setup_learning_content["reading_comp_sub"]
    reading_skill = setup_learning_content["reading_skill"]
    reading_questions = list(reading_comp_sub.questions.filter(is_active=True)[:5])
    UserQuestionAttemptFactory.create_batch(
        3,
        user=user,
        question=factory.Iterator(reading_questions),
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=True,
    )
    UserQuestionAttemptFactory.create_batch(
        2,
        user=user,
        question=factory.Iterator(reading_questions[3:]),
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=False,
    )

    algebra_sub = setup_learning_content["algebra_sub"]
    algebra_skill = setup_learning_content["algebra_skill"]
    algebra_questions = list(algebra_sub.questions.filter(is_active=True)[:3])
    UserQuestionAttemptFactory.create_batch(
        2,
        user=user,
        question=factory.Iterator(algebra_questions),
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=True,
    )
    UserQuestionAttemptFactory.create_batch(
        1,
        user=user,
        question=algebra_questions[2],
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=False,
    )

    # 3. Create User Skill Proficiency (Remains same)
    UserSkillProficiencyFactory(
        user=user,
        skill=reading_skill,
        attempts_count=5,
        correct_count=3,
        proficiency_score=0.6,
    )
    UserSkillProficiencyFactory(
        user=user,
        skill=algebra_skill,
        attempts_count=3,
        correct_count=2,
        proficiency_score=0.6667,
    )
    geometry_skill = setup_learning_content["geometry_skill"]
    UserSkillProficiencyFactory(
        user=user,
        skill=geometry_skill,
        attempts_count=0,
        correct_count=0,
        proficiency_score=0.0,
    )

    # 4. Create Completed Test Attempts (Using updated helper)
    completed_tests = []
    for i in range(RECENT_TESTS_LIMIT + 2):
        # Use the scenario helper, ensuring it's completed
        attempt, _ = create_attempt_scenario(
            user=user,
            num_questions=5,
            num_answered=5,  # Ensure all are answered for completed state
            num_correct_answered=random.randint(2, 5),
            attempt_type=random.choice(
                [
                    UserTestAttempt.AttemptType.PRACTICE,
                    UserTestAttempt.AttemptType.SIMULATION,
                ]
            ),
            status=UserTestAttempt.Status.COMPLETED,  # Explicitly set status
        )
        # Manually set end_time and scores for history test variation
        attempt.end_time = timezone.now() - timezone.timedelta(days=i)
        # Assign scores based on structure (assuming calc_and_save updated them)
        attempt.score_verbal = (
            round(random.uniform(40, 90), 1) if random.random() > 0.3 else None
        )
        attempt.score_quantitative = (
            round(random.uniform(40, 90), 1) if random.random() > 0.3 else None
        )
        attempt.save()
        completed_tests.append(attempt)

    # Create one non-completed attempt (should NOT appear in history)
    create_attempt_scenario(user=user, status=UserTestAttempt.Status.STARTED)

    return {
        "user": user,
        "profile": profile,
        "verbal_section": setup_learning_content["verbal_section"],
        "quant_section": setup_learning_content["quant_section"],
        "reading_comp_sub": reading_comp_sub,
        "algebra_sub": algebra_sub,
        "reading_skill": reading_skill,
        "algebra_skill": algebra_skill,
        "geometry_skill": geometry_skill,
        "completed_tests": completed_tests,
    }


class TestUserStatisticsAPI:
    """Tests for the User Statistics API Endpoint"""

    # Authentication and Subscription tests remain the same
    def test_statistics_requires_authentication(self, api_client, statistics_url):
        response = api_client.get(statistics_url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_statistics_requires_subscription(
        self, authenticated_client, statistics_url
    ):
        response = authenticated_client.get(statistics_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test structure remains the same
    def test_statistics_success_subscribed_user(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        assert "overall" in response.data
        assert "performance_by_section" in response.data
        assert "skill_proficiency_summary" in response.data
        assert "test_history_summary" in response.data

    # Test overall section remains the same (reads profile and counts)
    def test_statistics_overall_section(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        profile = setup_stats_data["profile"]
        user = setup_stats_data["user"]
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        overall = response.data.get("overall")
        assert overall is not None
        # Check Mastery Level
        assert overall["mastery_level"]["verbal"] == profile.current_level_verbal
        assert (
            overall["mastery_level"]["quantitative"]
            == profile.current_level_quantitative
        )
        # Check Study Streaks
        assert overall["study_streaks"]["current_days"] == profile.current_streak_days
        assert overall["study_streaks"]["longest_days"] == profile.longest_streak_days
        # Check Activity Summary
        expected_question_attempts = UserQuestionAttempt.objects.filter(
            user=user
        ).count()
        expected_completed_tests = UserTestAttempt.objects.filter(
            user=user, status=UserTestAttempt.Status.COMPLETED
        ).count()
        assert (
            overall["activity_summary"]["total_questions_answered"]
            == expected_question_attempts
        )
        assert (
            overall["activity_summary"]["total_tests_completed"]
            == expected_completed_tests
        )

    # Test performance section remains the same (based on UserQuestionAttempt aggregation)
    def test_statistics_performance_by_section(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        performance = response.data.get("performance_by_section")
        assert performance is not None
        # Check Verbal Section (based on Reading Comp attempts: 3 correct / 5 total)
        verbal_section_slug = setup_stats_data["verbal_section"].slug
        reading_comp_slug = setup_stats_data["reading_comp_sub"].slug
        assert verbal_section_slug in performance
        assert performance[verbal_section_slug]["overall_accuracy"] == 60.0
        assert reading_comp_slug in performance[verbal_section_slug]["subsections"]
        assert (
            performance[verbal_section_slug]["subsections"][reading_comp_slug][
                "accuracy"
            ]
            == 60.0
        )
        assert (
            performance[verbal_section_slug]["subsections"][reading_comp_slug][
                "attempts"
            ]
            == 5
        )
        # Check Quantitative Section (based on Algebra attempts: 2 correct / 3 total)
        quant_section_slug = setup_stats_data["quant_section"].slug
        algebra_slug = setup_stats_data["algebra_sub"].slug
        assert quant_section_slug in performance
        assert performance[quant_section_slug]["overall_accuracy"] == 66.7
        assert algebra_slug in performance[quant_section_slug]["subsections"]
        assert (
            performance[quant_section_slug]["subsections"][algebra_slug]["accuracy"]
            == 66.7
        )
        assert (
            performance[quant_section_slug]["subsections"][algebra_slug]["attempts"]
            == 3
        )

    # Test skill proficiency section remains the same (reads UserSkillProficiency)
    def test_statistics_skill_proficiency_summary(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        summary = response.data.get("skill_proficiency_summary")
        assert summary is not None and isinstance(summary, list)
        assert len(summary) == 3  # Reading, Algebra, Geometry from fixture
        reading_skill_data = next(
            (
                s
                for s in summary
                if s["skill_slug"] == setup_stats_data["reading_skill"].slug
            ),
            None,
        )
        algebra_skill_data = next(
            (
                s
                for s in summary
                if s["skill_slug"] == setup_stats_data["algebra_skill"].slug
            ),
            None,
        )
        geometry_skill_data = next(
            (
                s
                for s in summary
                if s["skill_slug"] == setup_stats_data["geometry_skill"].slug
            ),
            None,
        )
        # Check reading skill data
        assert (
            reading_skill_data is not None
            and reading_skill_data["proficiency_score"] == 0.6
            and reading_skill_data["accuracy"] == 60.0
        )
        # Check algebra skill data
        assert (
            algebra_skill_data is not None
            and algebra_skill_data["proficiency_score"]
            == pytest.approx(0.6667, abs=1e-4)
            and algebra_skill_data["accuracy"] == 66.7
        )
        # Check geometry skill data
        assert (
            geometry_skill_data is not None
            and geometry_skill_data["proficiency_score"] == 0.0
            and geometry_skill_data["accuracy"] is None
            and geometry_skill_data["attempts"] == 0
        )

    # Test test history section remains the same (reads completed UserTestAttempt)
    def test_statistics_test_history_summary(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        history = response.data.get("test_history_summary")
        assert history is not None and isinstance(history, list)
        assert len(history) == RECENT_TESTS_LIMIT  # Check limit
        # Check ordering (most recent first based on end_time)
        db_tests = UserTestAttempt.objects.filter(
            user=setup_stats_data["user"], status=UserTestAttempt.Status.COMPLETED
        ).order_by("-end_time")[:RECENT_TESTS_LIMIT]
        expected_order_ids = [t.id for t in db_tests]
        actual_order_ids = [item["attempt_id"] for item in history]
        assert actual_order_ids == expected_order_ids
        # Check structure of first item
        first_item = history[0]
        db_first_test = db_tests[0]
        assert first_item["attempt_id"] == db_first_test.id
        assert first_item["date"] == db_first_test.end_time.isoformat().replace(
            "+00:00", "Z"
        )
        assert first_item["type"] == db_first_test.get_attempt_type_display()
        assert first_item["overall_score"] == db_first_test.score_percentage

    # Edge case tests remain the same
    def test_statistics_performance_by_section_no_attempts(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("performance_by_section") == {}

    def test_statistics_skill_proficiency_summary_no_proficiencies(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("skill_proficiency_summary") == []

    def test_statistics_test_history_summary_no_completed_tests(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        create_attempt_scenario(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("test_history_summary") == []

    # Test missing profile (should be caught by permissions now)
    def test_statistics_missing_profile_handled(
        self, api_client, standard_user, statistics_url
    ):
        api_client.force_authenticate(user=standard_user)
        try:
            profile = UserProfile.objects.get(user=standard_user)
            profile.delete()
        except UserProfile.DoesNotExist:
            pass
        response = api_client.get(statistics_url)
        assert (
            response.status_code == status.HTTP_403_FORBIDDEN
        )  # Permission check fails first
