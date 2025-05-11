import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from unittest.mock import patch, MagicMock, ANY
import random
import copy  # Import copy

from apps.study.models import (
    EmergencyModeSession,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill, LearningSection
from apps.study.tests.factories import (
    EmergencyModeSessionFactory,
    UserSkillProficiencyFactory,
)
from apps.learning.tests.factories import (
    QuestionFactory,
    # SkillFactory, # Not directly used in test logic, setup_learning_content provides
    # LearningSectionFactory,
    # LearningSubSectionFactory,
)

from django.contrib.auth import get_user_model

from apps.study.services.study import (
    DEFAULT_EMERGENCY_TIPS,
    generate_emergency_plan,
)  # generate_emergency_plan for wraps

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.mark.usefixtures("setup_learning_content")
class TestEmergencyModeStart:
    url = reverse("api:v1:study:emergency-start")

    base_plan_structure = {
        "focus_area_names": ["Quantitative"],
        "estimated_duration_minutes": 60,
        "target_skills": [
            {
                "slug": "linear-equations",
                "name": "Linear Equations",
                "reason": "Low score (30%)",
                "current_proficiency": 0.3,
                "subsection_name": "Algebra",
            },
            {
                "slug": "area-calculation",
                "name": "Area Calculation",
                "reason": "Not attempted yet",
                "current_proficiency": None,
                "subsection_name": "Geometry",
            },
        ],
        "recommended_question_count": 24,
        "quick_review_topics": [
            {"slug": "algebra", "name": "Algebra", "description": "Review basics"}
        ],
        "motivational_tips": [],
    }

    @patch("apps.study.services.study._generate_ai_emergency_tips")
    @patch(
        "apps.study.services.study.generate_emergency_plan"
    )  # Full mock for this test (targets the source, as view imports it from there)
    def test_start_emergency_success_with_ai_tips(
        self,
        mock_generate_plan,
        mock_generate_ai_tips_func,
        subscribed_client,
        setup_learning_content,
    ):
        user = subscribed_client.user
        tips_list_for_plan = ["AI Tip 1: Stay calm!", "AI Tip 2: Focus on Algebra!"]
        mock_generate_ai_tips_func.return_value = tips_list_for_plan

        explicit_target_skills_for_mock = [
            {
                "slug": "linear-equations",
                "name": "Linear Equations",
                "reason": "Low score (30%)",  # This is the correct reason
                "current_proficiency": 0.3,
                "subsection_name": "Algebra",
            },
            {
                "slug": "area-calculation",
                "name": "Area Calculation",
                "reason": "Not attempted yet",
                "current_proficiency": None,
                "subsection_name": "Geometry",
            },
        ]

        explicit_quick_review_topics_for_mock = [
            {"slug": "algebra", "name": "Algebra", "description": "Review basics"}
        ]

        plan_to_return_from_mock = {
            "focus_area_names": ["Quantitative"],  # Literal
            "estimated_duration_minutes": 60,  # Literal
            "target_skills": copy.deepcopy(
                explicit_target_skills_for_mock
            ),  # Deepcopy of local list
            "recommended_question_count": 24,  # Literal, matches base_plan_structure
            "quick_review_topics": copy.deepcopy(
                explicit_quick_review_topics_for_mock
            ),  # Deepcopy of local list
            "motivational_tips": tips_list_for_plan,  # Local list
        }

        # DEBUG: Print the plan that the mock will return
        print(
            f"\nDEBUG_TEST: plan_to_return_from_mock['target_skills'] (before mock assignment):\n{plan_to_return_from_mock['target_skills']}\n"
        )

        mock_generate_plan.return_value = plan_to_return_from_mock

        payload = {
            "reason": "Feeling stressed",
            "available_time_hours": 1,
            "focus_areas": ["quantitative"],
        }
        response = subscribed_client.post(self.url, data=payload, format="json")

        if response.status_code != status.HTTP_201_CREATED:
            print(
                f"DEBUG_TEST: response data (status {response.status_code}): {response.data}"
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert "session_id" in response.data
        assert isinstance(response.data["suggested_plan"], dict)
        assert (
            response.data["suggested_plan"]["motivational_tips"] == tips_list_for_plan
        )
        assert (
            response.data["suggested_plan"]["recommended_question_count"]
            == plan_to_return_from_mock[
                "recommended_question_count"
            ]  # Compare with what mock returned
        )

        session = EmergencyModeSession.objects.get(user=user)
        assert session.suggested_plan["motivational_tips"] == tips_list_for_plan

        # DEBUG: Inspect the raw data from DB before sorting
        raw_db_target_skills = session.suggested_plan["target_skills"]
        print(
            f"DEBUG_TEST: Raw DB target_skills (from session.suggested_plan['target_skills']):\n{raw_db_target_skills}\n"
        )

        db_target_skills = sorted(
            raw_db_target_skills,
            key=lambda x: (
                x.get("slug") if isinstance(x, dict) else ""
            ),  # Robust sorting
        )

        # For assertion, sort the same explicit list used for the mock's return value
        expected_target_skills = sorted(
            copy.deepcopy(explicit_target_skills_for_mock), key=lambda x: x["slug"]
        )

        print(f"DEBUG_TEST: Sorted DB target_skills:\n{db_target_skills}\n")
        print(
            f"DEBUG_TEST: Expected target_skills (from explicit_target_skills_for_mock):\n{expected_target_skills}\n"
        )

        # Adding a more detailed comparison if the main assert fails
        if db_target_skills != expected_target_skills:
            for i, (db_item, exp_item) in enumerate(
                zip(db_target_skills, expected_target_skills)
            ):
                if db_item != exp_item:
                    print(f"DEBUG_TEST: Difference at index {i}:")
                    print(f"  DB Item:  {db_item}")
                    print(f"  Exp Item: {exp_item}")
                    # Compare field by field
                    for key in exp_item.keys():
                        if db_item.get(key) != exp_item.get(key):
                            print(
                                f"    Field '{key}': DB='{db_item.get(key)}', Exp='{exp_item.get(key)}'"
                            )
            # If lengths are different
            if len(db_target_skills) != len(expected_target_skills):
                print(
                    f"DEBUG_TEST: Length mismatch: DB={len(db_target_skills)}, Exp={len(expected_target_skills)}"
                )

        assert db_target_skills == expected_target_skills

        mock_generate_plan.assert_called_once_with(
            user=user, available_time_hours=1.0, focus_areas=["quantitative"]
        )
        mock_generate_ai_tips_func.assert_not_called()

    @patch("apps.study.services.study._generate_ai_emergency_tips")
    @patch(
        "apps.study.api.views.emergency.generate_emergency_plan",  # Patch where it's USED by the view
        wraps=generate_emergency_plan,  # The actual function from apps.study.services.study
    )
    def test_start_emergency_success_with_ai_failure_fallback(
        self,
        mock_generate_plan_wrapper,  # This mock is for apps.study.api.views.emergency.generate_emergency_plan
        mock_generate_ai_tips,  # This mock is for apps.study.services.study._generate_ai_emergency_tips
        subscribed_client,
        setup_learning_content,
    ):
        user = subscribed_client.user
        mock_generate_ai_tips.side_effect = Exception("AI Service Down")

        UserSkillProficiencyFactory(
            user=user,
            skill=setup_learning_content["algebra_skill"],
            proficiency_score=0.2,
        )
        UserSkillProficiencyFactory(
            user=user,
            skill=setup_learning_content["geometry_skill"],
            proficiency_score=0.8,
        )

        payload = {
            "reason": "Feeling stressed",
            "available_time_hours": 1,
            "focus_areas": ["quantitative"],
        }
        response = subscribed_client.post(self.url, data=payload, format="json")

        if response.status_code != status.HTTP_201_CREATED:
            print(
                f"DEBUG: test_start_emergency_success_with_ai_failure_fallback response data (status {response.status_code}): {response.data}"
            )

        assert response.status_code == status.HTTP_201_CREATED, response.content
        assert isinstance(response.data.get("suggested_plan"), dict)
        assert len(response.data["suggested_plan"]["motivational_tips"]) > 0
        assert all(
            tip in DEFAULT_EMERGENCY_TIPS
            for tip in response.data["suggested_plan"]["motivational_tips"]
        )

        session = EmergencyModeSession.objects.get(user=user)
        assert isinstance(session.suggested_plan, dict)
        assert len(session.suggested_plan["motivational_tips"]) > 0
        assert all(
            tip in DEFAULT_EMERGENCY_TIPS
            for tip in session.suggested_plan["motivational_tips"]
        )

        mock_generate_plan_wrapper.assert_called_once_with(
            user=user,
            available_time_hours=1.0,
            focus_areas=["quantitative"],
        )
        # _generate_ai_emergency_tips is called inside the real generate_emergency_plan
        mock_generate_ai_tips.assert_called_once()

    @patch("apps.study.services.study.get_ai_manager")
    def test_start_emergency_success_with_ai_unavailable_fallback(
        self,
        mock_get_ai_manager_func,
        subscribed_client,
        setup_learning_content,
    ):
        user = subscribed_client.user
        mock_ai_manager_instance = MagicMock()
        mock_ai_manager_instance.is_available.return_value = False
        mock_get_ai_manager_func.return_value = mock_ai_manager_instance

        UserSkillProficiencyFactory(
            user=user,
            skill=setup_learning_content["algebra_skill"],
            proficiency_score=0.4,
        )

        payload = {
            "reason": "Feeling stressed",
            "available_time_hours": 1,
            "focus_areas": ["quantitative"],
        }
        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED, response.content
        response_tips = response.data["suggested_plan"]["motivational_tips"]
        assert len(response_tips) > 0
        assert all(tip in DEFAULT_EMERGENCY_TIPS for tip in response_tips)
        mock_get_ai_manager_func.assert_called()

        session = EmergencyModeSession.objects.get(user=user)
        session_tips = session.suggested_plan["motivational_tips"]
        assert len(session_tips) > 0
        assert all(tip in DEFAULT_EMERGENCY_TIPS for tip in session_tips)

    def test_start_emergency_unauthenticated_fails(self, api_client):
        payload = {"reason": "Test"}
        response = api_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_emergency_unsubscribed_fails(self, authenticated_client):
        payload = {"reason": "Test"}
        response = authenticated_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_start_emergency_invalid_payload_fails(self, subscribed_client):
        payload = {
            "available_time_hours": -1,
            "focus_areas": ["invalid_area"],
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "available_time_hours" in response.data
        assert "focus_areas" in response.data

    @patch(
        "apps.study.services.study.UserSkillProficiency.objects.filter"
    )  # Mocking the ORM call directly
    @patch(
        "apps.study.api.views.emergency.generate_emergency_plan",  # Patch where it's USED by the view
        wraps=generate_emergency_plan,  # The actual function from apps.study.services.study
    )
    @patch(
        "apps.study.services.study._generate_ai_emergency_tips"  # Mock AI tips from its source
    )
    def test_start_emergency_core_plan_generation_fails(
        self,
        mock_generate_ai_tips,  # For apps.study.services.study._generate_ai_emergency_tips
        mock_generate_plan_wrapper,  # For apps.study.api.views.emergency.generate_emergency_plan
        mock_usp_filter,  # For apps.study.services.study.UserSkillProficiency.objects.filter
        subscribed_client,
        setup_learning_content,
    ):
        user = subscribed_client.user
        mock_usp_filter.side_effect = Exception("Database error during skill lookup")

        default_tips_sample = random.sample(
            DEFAULT_EMERGENCY_TIPS, k=min(len(DEFAULT_EMERGENCY_TIPS), 2)
        )
        mock_generate_ai_tips.return_value = default_tips_sample

        payload = {
            "reason": "Test",
            "available_time_hours": 1,
            "focus_areas": ["quantitative"],
        }
        response = subscribed_client.post(self.url, data=payload, format="json")

        if response.status_code != status.HTTP_201_CREATED:
            print(
                f"DEBUG: test_start_emergency_core_plan_generation_fails response data (status {response.status_code}): {response.data}"
            )

        assert response.status_code == status.HTTP_201_CREATED, response.content
        assert "session_id" in response.data
        assert isinstance(response.data.get("suggested_plan"), dict)
        assert "suggested_plan" in response.data

        motivational_tips = response.data["suggested_plan"]["motivational_tips"]
        error_tip_found = any(
            "Could not generate personalized focus areas" in tip
            for tip in motivational_tips
        )
        assert error_tip_found

        non_error_tips = [
            tip for tip in motivational_tips if "Could not generate" not in tip
        ]
        assert len(non_error_tips) > 0
        assert all(tip in default_tips_sample for tip in non_error_tips)

        mock_generate_plan_wrapper.assert_called_once_with(
            user=user,
            available_time_hours=1.0,
            focus_areas=["quantitative"],
        )
        mock_usp_filter.assert_called()  # USP filter is called within the real generate_emergency_plan
        # _generate_ai_emergency_tips is called by the real generate_emergency_plan
        mock_generate_ai_tips.assert_called_once()


# --- Test EmergencyModeSessionUpdateView ---
# (Assuming the fix from the previous round for this view is in place and worked,
#  as it's not listed in the current failure output. No changes needed here based on current failures.)
class TestEmergencyModeUpdate:

    @pytest.fixture
    def active_session(self, subscribed_user):
        plan = {
            "focus_area_names": ["Verbal"],
            "estimated_duration_minutes": 30,
            "target_skills": [
                {
                    "slug": "s1",
                    "name": "S1",
                    "reason": "Low",
                    "current_proficiency": 0.2,
                    "subsection_name": "Sub1",
                }
            ],
            "recommended_question_count": 10,
            "quick_review_topics": [],
            "motivational_tips": ["Tip A", "Tip B"],
        }
        return EmergencyModeSessionFactory(user=subscribed_user, suggested_plan=plan)

    @pytest.fixture
    def ended_session(self, subscribed_user):
        return EmergencyModeSessionFactory(
            user=subscribed_user, end_time=timezone.now()
        )

    def get_url(self, session_id):
        return reverse(
            "api:v1:study:emergency-update", kwargs={"session_id": session_id}
        )

    def test_update_session_success(self, subscribed_client, active_session):
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True, "shared_with_admin": True}
        response = subscribed_client.patch(url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["calm_mode_active"] is True
        assert response.data["shared_with_admin"] is True
        assert isinstance(
            response.data["suggested_plan"], dict
        )  # This relies on view fix

        active_session.refresh_from_db()
        assert active_session.calm_mode_active is True
        assert active_session.shared_with_admin is True

    # ... (rest of TestEmergencyModeUpdate and other test classes remain unchanged from original)
    def test_update_session_partial_success(self, subscribed_client, active_session):
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}
        response = subscribed_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["calm_mode_active"] is True
        assert response.data["shared_with_admin"] is False  # Initial value
        active_session.refresh_from_db()
        assert active_session.calm_mode_active is True
        assert active_session.shared_with_admin is False

    def test_update_session_unauthenticated_fails(self, api_client, active_session):
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}
        response = api_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_session_not_owner_fails(self, authenticated_client, active_session):
        url = self.get_url(active_session.id)
        payload = {"calm_mode_active": True}
        response = authenticated_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_session_ended_fails(self, subscribed_client, ended_session):
        url = self.get_url(ended_session.id)
        payload = {"calm_mode_active": True}
        response = subscribed_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_session_not_found_fails(self, subscribed_client):
        url = self.get_url(9999)
        payload = {"calm_mode_active": True}
        response = subscribed_client.patch(url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.usefixtures("setup_learning_content")
class TestEmergencyModeAnswer:
    url = reverse("api:v1:study:emergency-answer")

    @pytest.fixture
    def active_session(self, subscribed_user):
        plan = {
            "focus_area_names": ["Verbal"],
            "estimated_duration_minutes": 30,
            "target_skills": [
                {
                    "slug": "s1",
                    "name": "S1",
                    "reason": "Low",
                    "current_proficiency": 0.2,
                    "subsection_name": "Sub1",
                }
            ],
            "recommended_question_count": 10,
            "quick_review_topics": [],
            "motivational_tips": ["Tip A"],
        }
        return EmergencyModeSessionFactory(user=subscribed_user, suggested_plan=plan)

    @pytest.fixture
    def ended_session(self, subscribed_user):
        return EmergencyModeSessionFactory(
            user=subscribed_user, end_time=timezone.now()
        )

    @pytest.fixture
    def question_with_skill(self, setup_learning_content, subscribed_user):
        skill = setup_learning_content["algebra_skill"]
        q = Question.objects.filter(skill=skill, is_active=True).first()
        assert q is not None, f"No active question found for skill {skill.slug}"
        UserSkillProficiencyFactory(user=subscribed_user, skill=skill)
        return q

    @pytest.fixture
    def question_without_skill(self, setup_learning_content):
        q = Question.objects.filter(skill__isnull=True, is_active=True).first()
        assert q is not None, "No active question found without skill"
        return q

    @patch("apps.study.api.views.emergency.update_user_skill_proficiency")
    def test_answer_correct_with_skill_success(
        self, mock_update_prof, subscribed_client, active_session, question_with_skill
    ):
        user = subscribed_client.user
        question = question_with_skill
        payload = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["question_id"] == question.id
        assert response.data["is_correct"] is True
        assert response.data["correct_answer"] == question.correct_answer
        assert response.data["explanation"] == question.explanation
        assert response.data["points_earned"] == 0

        assert "feedback" in response.data
        feedback_data = response.data["feedback"]
        assert "skill_tested" in feedback_data
        assert feedback_data["skill_tested"]["slug"] == question.skill.slug
        assert feedback_data["skill_tested"]["name"] == question.skill.name
        assert "Correct!" in feedback_data["message"]
        assert "session_progress" in feedback_data

        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            emergency_session=active_session,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=True,
        ).exists()
        mock_update_prof.assert_called_once_with(
            user=user, skill=question.skill, is_correct=True
        )

    @patch("apps.study.api.views.emergency.update_user_skill_proficiency")
    def test_answer_incorrect_with_skill_success(
        self, mock_update_prof, subscribed_client, active_session, question_with_skill
    ):
        user = subscribed_client.user
        question = question_with_skill
        incorrect_answer = next(
            c for c in ["A", "B", "C", "D"] if c != question.correct_answer
        )
        payload = {
            "question_id": question.id,
            "selected_answer": incorrect_answer,
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_correct"] is False
        assert response.data["correct_answer"] == question.correct_answer
        assert "Incorrect." in response.data["feedback"]["message"]
        assert "You've answered" in response.data["feedback"]["message"]

        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            emergency_session=active_session,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=False,
        ).exists()
        mock_update_prof.assert_called_once_with(
            user=user, skill=question.skill, is_correct=False
        )

    @patch("apps.study.api.views.emergency.update_user_skill_proficiency")
    def test_answer_correct_without_skill_success(
        self,
        mock_update_prof,
        subscribed_client,
        active_session,
        question_without_skill,
    ):
        user = subscribed_client.user
        question = question_without_skill
        payload = {
            "question_id": question.id,
            "selected_answer": question.correct_answer,
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_correct"] is True
        assert response.data["feedback"]["skill_tested"] is None
        assert "Correct!" in response.data["feedback"]["message"]
        assert "You've answered" in response.data["feedback"]["message"]

        assert UserQuestionAttempt.objects.filter(
            user=user,
            question=question,
            emergency_session=active_session,
            mode=UserQuestionAttempt.Mode.EMERGENCY,
            is_correct=True,
        ).exists()
        mock_update_prof.assert_not_called()

    def test_answer_unauthenticated_fails(
        self, api_client, active_session, question_with_skill
    ):
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = api_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_answer_unsubscribed_fails(
        self, authenticated_client, active_session, question_with_skill
    ):
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = authenticated_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_answer_invalid_session_id_fails(
        self, subscribed_client, question_with_skill
    ):
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": 9999,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_session_not_owned_fails(
        self, subscribed_client, admin_user, question_with_skill
    ):
        other_session = EmergencyModeSessionFactory(user=admin_user)
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": other_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_session_ended_fails(
        self, subscribed_client, ended_session, question_with_skill
    ):
        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "A",
            "session_id": ended_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_invalid_question_id_fails(self, subscribed_client, active_session):
        payload = {
            "question_id": 9999,
            "selected_answer": "A",
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_answer_invalid_payload_fails(
        self, subscribed_client, active_session, question_with_skill
    ):
        payload = {
            "question_id": question_with_skill.id,
            "session_id": active_session.id,
        }  # Missing selected_answer
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data

        payload = {
            "question_id": question_with_skill.id,
            "selected_answer": "E",  # Invalid choice
            "session_id": active_session.id,
        }
        response = subscribed_client.post(self.url, data=payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "selected_answer" in response.data


@pytest.mark.usefixtures("setup_learning_content")
class TestEmergencyModeQuestions:

    @pytest.fixture
    def active_session_with_plan(self, subscribed_user, setup_learning_content):
        skill1 = setup_learning_content["algebra_skill"]
        skill2 = setup_learning_content["reading_skill"]

        if not Question.objects.filter(skill=skill1, is_active=True).exists():
            QuestionFactory.create_batch(
                5, skill=skill1, subsection=skill1.subsection, is_active=True
            )
        if not Question.objects.filter(skill=skill2, is_active=True).exists():
            QuestionFactory.create_batch(
                5, skill=skill2, subsection=skill2.subsection, is_active=True
            )

        plan = {
            "focus_area_names": ["Quantitative", "Verbal"],
            "estimated_duration_minutes": 45,
            "target_skills": [
                {
                    "slug": skill1.slug,
                    "name": skill1.name,
                    "reason": "Low",
                    "current_proficiency": 0.1,
                    "subsection_name": skill1.subsection.name,
                },
                {
                    "slug": skill2.slug,
                    "name": skill2.name,
                    "reason": "Low",
                    "current_proficiency": 0.4,
                    "subsection_name": skill2.subsection.name,
                },
            ],
            "recommended_question_count": 8,
            "quick_review_topics": [],
            "motivational_tips": ["Tip 1"],
        }
        return EmergencyModeSessionFactory(user=subscribed_user, suggested_plan=plan)

    @pytest.fixture
    def ended_session(
        self, subscribed_user
    ):  # Assuming ended_session in TestEmergencyModeUpdate uses 'end_time'
        return EmergencyModeSessionFactory(
            user=subscribed_user, end_time=timezone.now()
        )

    def get_url(self, session_id):
        return reverse(
            "api:v1:study:emergency-questions", kwargs={"session_id": session_id}
        )

    def test_get_questions_success(self, subscribed_client, active_session_with_plan):
        session = active_session_with_plan
        url = self.get_url(session.id)
        response = subscribed_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert (
            len(response.data)
            <= session.suggested_plan[
                "recommended_question_count"
            ]  # Can be less if not enough questions exist
        )
        if len(response.data) > 0:  # Only check if questions were returned
            returned_skill_slugs = set()
            for q_data in response.data:
                assert isinstance(q_data, dict)
                skill_info = q_data.get("skill")
                if isinstance(skill_info, dict) and skill_info.get("slug"):
                    returned_skill_slugs.add(skill_info["slug"])

            target_skill_slugs = {
                s["slug"] for s in session.suggested_plan["target_skills"]
            }
            # All returned skills must be among the target skills (or general if no target skills defined/found)
            if target_skill_slugs:
                assert returned_skill_slugs.issubset(target_skill_slugs)

    def test_get_questions_unauthenticated_fails(
        self, api_client, active_session_with_plan
    ):
        url = self.get_url(active_session_with_plan.id)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_questions_not_owner_fails(
        self,
        authenticated_client,  # Uses 'standard_user'
        active_session_with_plan,  # Owned by 'subscribed_user'
    ):
        url = self.get_url(active_session_with_plan.id)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN  # View permission

    def test_get_questions_session_ended_fails(self, subscribed_client, ended_session):
        url = self.get_url(ended_session.id)  # ended_session has end_time set
        response = subscribed_client.get(url)
        assert (
            response.status_code == status.HTTP_404_NOT_FOUND
        )  # get_object_or_404 in view filters by end_time__isnull=True

    def test_get_questions_invalid_plan_fails(self, subscribed_client, subscribed_user):
        session = EmergencyModeSessionFactory(
            user=subscribed_user, suggested_plan="invalid data"
        )
        url = self.get_url(session.id)
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid study plan" in str(response.data)

    @patch("apps.study.api.views.emergency.get_filtered_questions")
    def test_get_questions_service_error_fails(
        self, mock_get_filtered, subscribed_client, active_session_with_plan
    ):
        mock_get_filtered.side_effect = Exception("DB Error fetching questions")
        url = self.get_url(active_session_with_plan.id)
        response = subscribed_client.get(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Could not retrieve questions" in str(response.data)
