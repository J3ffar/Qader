# qader_backend/apps/study/tests/test_statistics_api.py

import random
import factory
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from decimal import Decimal  # For precise comparisons if needed

from apps.study.models import (
    UserTestAttempt,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.users.models import UserProfile  # For direct profile manipulation
from apps.study.tests.factories import (
    UserTestAttemptFactory,
    UserQuestionAttemptFactory,
    UserSkillProficiencyFactory,
    create_completed_attempt,
)
from apps.learning.models import Skill, LearningSection, LearningSubSection
from apps.study.api.serializers.statistics import RECENT_TESTS_LIMIT  # Import constant

# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db


@pytest.fixture
def statistics_url():
    """Fixture for the statistics endpoint URL."""
    return reverse("api:v1:study:user-statistics")


@pytest.fixture
def setup_stats_data(subscribed_user, setup_learning_content):
    """Fixture to create comprehensive data for statistics testing."""
    user = subscribed_user
    profile = user.profile

    # 1. Update Profile Data
    profile.current_level_verbal = 75.5
    profile.current_level_quantitative = 60.0
    profile.current_streak_days = 5
    profile.longest_streak_days = 10
    profile.save()

    # 2. Create User Question Attempts
    # Verbal Attempts (Reading Comp)
    reading_comp_sub = setup_learning_content["reading_comp_sub"]
    reading_skill = setup_learning_content["reading_skill"]
    reading_questions = list(reading_comp_sub.questions.filter(is_active=True)[:5])
    UserQuestionAttemptFactory.create_batch(
        3,  # 3 correct
        user=user,
        question=factory.Iterator(reading_questions),
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=True,
    )
    UserQuestionAttemptFactory.create_batch(
        2,  # 2 incorrect
        user=user,
        question=factory.Iterator(reading_questions[3:]),  # Use remaining questions
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=False,
    )
    # Total reading comp attempts = 5

    # Quantitative Attempts (Algebra)
    algebra_sub = setup_learning_content["algebra_sub"]
    algebra_skill = setup_learning_content["algebra_skill"]
    algebra_questions = list(algebra_sub.questions.filter(is_active=True)[:3])
    UserQuestionAttemptFactory.create_batch(
        2,  # 2 correct
        user=user,
        question=factory.Iterator(algebra_questions),
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=True,
    )
    UserQuestionAttemptFactory.create_batch(
        1,  # 1 incorrect
        user=user,
        question=algebra_questions[2],
        mode=UserQuestionAttempt.Mode.TRADITIONAL,
        correct=False,
    )
    # Total algebra attempts = 3

    # 3. Create User Skill Proficiency (matching some attempts)
    # Reading Skill Proficiency (3 correct / 5 attempts -> 60%)
    UserSkillProficiencyFactory(
        user=user,
        skill=reading_skill,
        attempts_count=5,
        correct_count=3,
        proficiency_score=0.6,
    )
    # Algebra Skill Proficiency (2 correct / 3 attempts -> ~66.7%)
    UserSkillProficiencyFactory(
        user=user,
        skill=algebra_skill,
        attempts_count=3,
        correct_count=2,
        proficiency_score=0.6667,
    )
    # A skill with no attempts for this user (should still appear if exists)
    geometry_skill = setup_learning_content["geometry_skill"]
    UserSkillProficiencyFactory(
        user=user,
        skill=geometry_skill,
        attempts_count=0,
        correct_count=0,
        proficiency_score=0.0,
    )

    # 4. Create Completed Test Attempts (more than limit to test slicing)
    # Note: create_completed_attempt also creates UserQuestionAttempts linked to the test
    completed_tests = []
    for i in range(RECENT_TESTS_LIMIT + 2):
        attempt, _ = create_completed_attempt(
            user=user,
            num_questions=5,
            num_correct=random.randint(2, 5),
            attempt_type=random.choice(
                [
                    UserTestAttempt.AttemptType.PRACTICE,
                    UserTestAttempt.AttemptType.SIMULATION,
                ]
            ),
        )
        # Ensure end_time varies for ordering test
        attempt.end_time = timezone.now() - timezone.timedelta(days=i)
        # Manually assign some verbal/quant scores for testing history summary
        if attempt.results_summary:
            first_section = next(iter(attempt.results_summary.values()), {})
            if (
                first_section.get("name", "").lower().startswith("verbal")
                or "reading" in first_section.get("name", "").lower()
            ):
                attempt.score_verbal = attempt.score_percentage
                attempt.score_quantitative = (
                    None if random.random() > 0.5 else round(random.uniform(40, 80), 1)
                )
            else:
                attempt.score_quantitative = attempt.score_percentage
                attempt.score_verbal = (
                    None if random.random() > 0.5 else round(random.uniform(40, 80), 1)
                )

        attempt.save()
        completed_tests.append(attempt)

    # Create one non-completed attempt (should NOT appear in history)
    UserTestAttemptFactory(user=user, status=UserTestAttempt.Status.STARTED)

    # Return structure for easy access in tests
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

    def test_statistics_requires_authentication(self, api_client, statistics_url):
        """Verify unauthenticated users cannot access statistics."""
        response = api_client.get(statistics_url)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_statistics_requires_subscription(
        self, authenticated_client, statistics_url
    ):
        """Verify authenticated but unsubscribed users cannot access statistics."""
        # authenticated_client uses the 'unsubscribed_user' fixture
        response = authenticated_client.get(statistics_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
        assert "active subscription" in response.data["detail"].lower()

    def test_statistics_success_subscribed_user(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        """Verify subscribed user gets a 200 OK and correct top-level structure."""
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        assert "overall" in response.data
        assert "performance_by_section" in response.data
        assert "skill_proficiency_summary" in response.data
        assert "test_history_summary" in response.data

    def test_statistics_overall_section(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        """Verify the 'overall' section contains correct aggregated data."""
        profile = setup_stats_data["profile"]
        user = setup_stats_data["user"]

        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK

        overall = response.data.get("overall")
        assert overall is not None

        # Check Mastery Level (from profile)
        mastery = overall.get("mastery_level")
        assert mastery is not None
        assert mastery.get("verbal") == profile.current_level_verbal
        assert mastery.get("quantitative") == profile.current_level_quantitative

        # Check Study Streaks (from profile)
        streaks = overall.get("study_streaks")
        assert streaks is not None
        assert streaks.get("current_days") == profile.current_streak_days
        assert streaks.get("longest_days") == profile.longest_streak_days

        # Check Activity Summary (calculated)
        activity = overall.get("activity_summary")
        assert activity is not None
        # Calculate expected counts
        expected_question_attempts = UserQuestionAttempt.objects.filter(
            user=user
        ).count()
        expected_completed_tests = UserTestAttempt.objects.filter(
            user=user, status=UserTestAttempt.Status.COMPLETED
        ).count()

        assert activity.get("total_questions_answered") == expected_question_attempts
        assert activity.get("total_tests_completed") == expected_completed_tests

    def test_statistics_performance_by_section(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        """Verify 'performance_by_section' calculation and structure."""
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK

        performance = response.data.get("performance_by_section")
        assert performance is not None
        assert isinstance(performance, dict)

        # Check Verbal Section (based on Reading Comp attempts)
        verbal_section_slug = setup_stats_data["verbal_section"].slug
        reading_comp_slug = setup_stats_data["reading_comp_sub"].slug
        assert verbal_section_slug in performance
        verbal_perf = performance[verbal_section_slug]
        assert verbal_perf["name"] == setup_stats_data["verbal_section"].name
        # Overall Verbal Accuracy (3 correct / 5 total attempts = 60.0%)
        assert verbal_perf["overall_accuracy"] == 60.0
        assert isinstance(verbal_perf["subsections"], dict)
        assert reading_comp_slug in verbal_perf["subsections"]
        reading_perf = verbal_perf["subsections"][reading_comp_slug]
        assert reading_perf["name"] == setup_stats_data["reading_comp_sub"].name
        assert reading_perf["accuracy"] == 60.0  # (3 correct / 5 total)
        assert reading_perf["attempts"] == 5

        # Check Quantitative Section (based on Algebra attempts)
        quant_section_slug = setup_stats_data["quant_section"].slug
        algebra_slug = setup_stats_data["algebra_sub"].slug
        assert quant_section_slug in performance
        quant_perf = performance[quant_section_slug]
        assert quant_perf["name"] == setup_stats_data["quant_section"].name
        # Overall Quant Accuracy (2 correct / 3 total attempts = 66.7%)
        assert quant_perf["overall_accuracy"] == 66.7
        assert isinstance(quant_perf["subsections"], dict)
        assert algebra_slug in quant_perf["subsections"]
        algebra_perf = quant_perf["subsections"][algebra_slug]
        assert algebra_perf["name"] == setup_stats_data["algebra_sub"].name
        assert algebra_perf["accuracy"] == 66.7  # (2 correct / 3 total)
        assert algebra_perf["attempts"] == 3

    def test_statistics_performance_by_section_no_attempts(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        """Verify 'performance_by_section' returns empty dict if no attempts exist."""
        # setup_learning_content creates sections/subs, but no attempts are made by subscribed_client
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        performance = response.data.get("performance_by_section")
        assert performance == {}

    def test_statistics_skill_proficiency_summary(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        """Verify 'skill_proficiency_summary' structure and data."""
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK

        summary = response.data.get("skill_proficiency_summary")
        assert summary is not None
        assert isinstance(summary, list)
        # Expecting 3 skills: reading, algebra, geometry (order might vary based on score)
        assert len(summary) == 3

        # Find specific skills in the response (order is not guaranteed)
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

        assert reading_skill_data is not None
        assert (
            reading_skill_data["skill_name"] == setup_stats_data["reading_skill"].name
        )
        assert reading_skill_data["proficiency_score"] == 0.6
        assert reading_skill_data["accuracy"] == 60.0  # 3/5 * 100
        assert reading_skill_data["attempts"] == 5

        assert algebra_skill_data is not None
        assert (
            algebra_skill_data["skill_name"] == setup_stats_data["algebra_skill"].name
        )
        # Use pytest.approx for float comparison if needed, or check score range
        assert algebra_skill_data["proficiency_score"] == pytest.approx(
            0.6667, abs=1e-4
        )
        assert algebra_skill_data["accuracy"] == 66.7  # 2/3 * 100 rounded
        assert algebra_skill_data["attempts"] == 3

        assert geometry_skill_data is not None
        assert (
            geometry_skill_data["skill_name"] == setup_stats_data["geometry_skill"].name
        )
        assert geometry_skill_data["proficiency_score"] == 0.0
        assert geometry_skill_data["accuracy"] is None  # 0 attempts
        assert geometry_skill_data["attempts"] == 0

    def test_statistics_skill_proficiency_summary_no_proficiencies(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        """Verify 'skill_proficiency_summary' returns empty list if no proficiencies recorded."""
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        summary = response.data.get("skill_proficiency_summary")
        assert summary == []

    def test_statistics_test_history_summary(
        self, subscribed_client, statistics_url, setup_stats_data
    ):
        """Verify 'test_history_summary' shows recent completed tests correctly."""
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK

        history = response.data.get("test_history_summary")
        assert history is not None
        assert isinstance(history, list)

        # Check limit enforcement
        assert len(history) == RECENT_TESTS_LIMIT

        # Check ordering (most recent first based on end_time)
        # Get the actual end times from the DB for comparison
        db_tests = UserTestAttempt.objects.filter(
            user=setup_stats_data["user"], status=UserTestAttempt.Status.COMPLETED
        ).order_by("-end_time")[:RECENT_TESTS_LIMIT]
        expected_order_ids = [t.id for t in db_tests]
        actual_order_ids = [item["attempt_id"] for item in history]
        assert actual_order_ids == expected_order_ids

        # Check structure of a single item (the most recent one)
        first_item = history[0]
        db_first_test = db_tests[0]
        assert first_item["attempt_id"] == db_first_test.id
        # Compare timezone-aware datetimes carefully
        assert first_item["date"] == db_first_test.end_time.isoformat().replace(
            "+00:00", "Z"
        )
        assert first_item["type"] == db_first_test.get_attempt_type_display()
        assert first_item["overall_score"] == db_first_test.score_percentage
        assert first_item["verbal_score"] == db_first_test.score_verbal
        assert first_item["quantitative_score"] == db_first_test.score_quantitative

    def test_statistics_test_history_summary_no_completed_tests(
        self, subscribed_client, statistics_url, setup_learning_content
    ):
        """Verify 'test_history_summary' returns empty list if no completed tests."""
        UserTestAttemptFactory(
            user=subscribed_client.user, status=UserTestAttempt.Status.STARTED
        )
        response = subscribed_client.get(statistics_url)
        assert response.status_code == status.HTTP_200_OK
        history = response.data.get("test_history_summary")
        assert history == []

    def test_statistics_missing_profile_handled(
        self, api_client, base_user, statistics_url
    ):
        """
        Verify the view handles cases where a profile might be missing (should return 400 Bad Request).
        Simulate by deleting the profile after authentication.
        """
        # Authenticate the user first
        api_client.force_authenticate(user=base_user)

        # Explicitly delete the profile (signals usually create it)
        try:
            profile = UserProfile.objects.get(user=base_user)
            profile_pk = profile.pk
            profile.delete()
            # Verify deletion
            with pytest.raises(UserProfile.DoesNotExist):
                UserProfile.objects.get(pk=profile_pk)
        except UserProfile.DoesNotExist:
            # Profile didn't exist anyway, which is the state we want to test
            pass

        response = api_client.get(statistics_url)

        # Expecting the view's try/except or serializer's validation to catch this
        # The serializer's _get_user_profile_safe logs a warning and returns None,
        # which might cause validation errors in nested serializers expecting data,
        # or the view's main try/except might catch it.
        # The UserStatisticsView catches general exceptions and returns 500,
        # but the serializer methods returning None could lead to validation errors
        # if the nested serializers *require* data. Let's check for 400 first, then 500.
        # Update based on UserStatisticsView's explicit try/except: It returns 400 on validation error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check for a meaningful error message if possible
        assert (
            "profile" in str(response.data).lower()
            or "error processing" in str(response.data).lower()
        )

        # Clean up authentication
        api_client.force_authenticate(user=None)
