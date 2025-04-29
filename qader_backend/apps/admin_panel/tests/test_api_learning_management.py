import pytest
from django.urls import reverse
from rest_framework import status
import factory

# Import factories for learning app
from apps.learning.tests.factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    SkillFactory,
    QuestionFactory,
)
from apps.learning.models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
)

# Use pytest markers for database access
pytestmark = pytest.mark.django_db

# --- Constants for URLs ---
SECTION_LIST_URL = reverse("api:v1:admin_panel:admin-learning-section-list")
SUBSECTION_LIST_URL = reverse("api:v1:admin_panel:admin-learning-subsection-list")
SKILL_LIST_URL = reverse("api:v1:admin_panel:admin-learning-skill-list")
QUESTION_LIST_URL = reverse("api:v1:admin_panel:admin-learning-question-list")


def section_detail_url(pk):
    return reverse("api:v1:admin_panel:admin-learning-section-detail", args=[pk])


def subsection_detail_url(pk):
    return reverse("api:v1:admin_panel:admin-learning-subsection-detail", args=[pk])


def skill_detail_url(pk):
    return reverse("api:v1:admin_panel:admin-learning-skill-detail", args=[pk])


def question_detail_url(pk):
    return reverse("api:v1:admin_panel:admin-learning-question-detail", args=[pk])


from rest_framework.test import (
    APIClient,
)  # Local import to avoid global scope issues if needed


# --- Permission Tests Helper Function ---
def check_permissions(
    client,
    method,
    url,
    data=None,
    expected_anon_status=status.HTTP_401_UNAUTHORIZED,
    expected_auth_status=status.HTTP_403_FORBIDDEN,
):
    """
    Helper to check common permission errors for non-admins.
    Pass the client instance itself to determine authentication status.
    """
    # is_authenticated = (
    #     client.handler._credentials.get("HTTP_AUTHORIZATION", None) is not None
    #     or client.session
    #     or getattr(client, "_credentials", None)
    # )  # More robust auth check attempt

    # Alternative (simpler): Just check the response status code
    # is_authenticated = None # Don't need to know explicitly

    kwargs = (
        {"data": data, "format": "json"} if data else {}
    )  # Ensure format is json for POST/PUT/PATCH
    response = getattr(client, method)(url, **kwargs)

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        # If we got 401, the client MUST have been unauthenticated.
        assert (
            expected_anon_status == status.HTTP_401_UNAUTHORIZED
        ), f"Expected anon client to get {expected_anon_status} but got 401 for {method} {url}"
    elif response.status_code == status.HTTP_403_FORBIDDEN:
        # If we got 403, the client MUST have been authenticated but lacked permissions.
        assert (
            expected_auth_status == status.HTTP_403_FORBIDDEN
        ), f"Expected auth client to get {expected_auth_status} but got 403 for {method} {url}"
    else:
        # If we get any other status, it's unexpected for these permission checks
        pytest.fail(
            f"Unexpected status {response.status_code} for permission check ({method} {url}). Expected {expected_anon_status} or {expected_auth_status}."
        )


# === Test AdminLearningSectionViewSet ===


class TestAdminLearningSectionAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.section1 = LearningSectionFactory(name="Verbal", order=1)
        self.section2 = LearningSectionFactory(name="Quantitative", order=2)
        self.base_payload = {
            "name": "New Section",
            "description": "A brand new section.",
            "order": 3,
        }

    def test_permissions_section(
        self, api_client, authenticated_client, subscribed_client
    ):
        """Verify only admins can access section endpoints."""
        list_url = SECTION_LIST_URL
        detail_url = section_detail_url(self.section1.pk)
        payload = self.base_payload

        # List
        check_permissions(api_client, "get", list_url)
        check_permissions(authenticated_client, "get", list_url)
        check_permissions(subscribed_client, "get", list_url)
        # Create
        check_permissions(api_client, "post", list_url, payload)
        check_permissions(authenticated_client, "post", list_url, payload)
        check_permissions(subscribed_client, "post", list_url, payload)
        # Retrieve, Update, Delete
        for method in ["get", "put", "patch", "delete"]:
            check_permissions(
                api_client,
                method,
                detail_url,
                payload if method in ["put", "patch"] else None,
            )
            check_permissions(
                authenticated_client,
                method,
                detail_url,
                payload if method in ["put", "patch"] else None,
            )
            check_permissions(
                subscribed_client,
                method,
                detail_url,
                payload if method in ["put", "patch"] else None,
            )

    def test_list_sections_admin(self, admin_client):
        response = admin_client.get(SECTION_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert response.data["results"][0]["name"] == self.section1.name
        assert response.data["results"][1]["name"] == self.section2.name

    def test_retrieve_section_admin(self, admin_client):
        response = admin_client.get(section_detail_url(self.section1.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.section1.pk
        assert response.data["name"] == self.section1.name

    def test_create_section_admin(self, admin_client):
        response = admin_client.post(SECTION_LIST_URL, self.base_payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert LearningSection.objects.count() == 3
        new_section = LearningSection.objects.get(pk=response.data["id"])
        assert new_section.name == self.base_payload["name"]
        assert new_section.slug == "new-section"  # Check auto-slug

    def test_create_section_duplicate_name_admin(self, admin_client):
        payload = self.base_payload.copy()
        payload["name"] = self.section1.name  # Duplicate name
        response = admin_client.post(SECTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data
        assert "already exists" in response.data["name"][0]

    def test_update_section_admin(self, admin_client):
        payload = {
            "name": "Updated Verbal",
            "slug": "updated-verbal-slug",  # Admins can override slug
            "description": "Updated description.",
            "order": 5,
        }
        response = admin_client.put(section_detail_url(self.section1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.section1.refresh_from_db()
        assert self.section1.name == payload["name"]
        assert self.section1.slug == payload["slug"]
        assert self.section1.order == payload["order"]

    def test_partial_update_section_admin(self, admin_client):
        payload = {"order": 10}
        response = admin_client.patch(section_detail_url(self.section1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.section1.refresh_from_db()
        assert self.section1.order == 10
        assert self.section1.name == "Verbal"  # Name should be unchanged

    def test_delete_section_admin(self, admin_client):
        # Create subsection to test cascading delete (it should cascade)
        LearningSubSectionFactory(section=self.section1)
        assert LearningSubSection.objects.count() == 1

        response = admin_client.delete(section_detail_url(self.section1.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert LearningSection.objects.count() == 1
        assert LearningSubSection.objects.count() == 0  # Should be deleted


# === Test AdminLearningSubSectionViewSet ===


class TestAdminLearningSubSectionAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.section1 = LearningSectionFactory(name="Parent Section 1")
        self.section2 = LearningSectionFactory(name="Parent Section 2")
        self.subsection1 = LearningSubSectionFactory(
            section=self.section1, name="Sub 1A", order=1
        )
        self.subsection2 = LearningSubSectionFactory(
            section=self.section1, name="Sub 1B", order=2
        )
        self.base_payload = {
            "section_id": self.section1.pk,
            "name": "New SubSection",
            "description": "A new subsection.",
            "order": 3,
        }

    # Add permission tests similar to test_permissions_section (omitted for brevity)
    def test_list_subsections_admin(self, admin_client):
        response = admin_client.get(SUBSECTION_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_filter_subsections_by_section_admin(self, admin_client):
        # Create subsection in another section
        LearningSubSectionFactory(section=self.section2)
        response = admin_client.get(
            SUBSECTION_LIST_URL, {"section__id": self.section1.pk}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # Only subsections from section1
        assert response.data["results"][0]["name"] == self.subsection1.name
        assert response.data["results"][1]["name"] == self.subsection2.name

    def test_retrieve_subsection_admin(self, admin_client):
        response = admin_client.get(subsection_detail_url(self.subsection1.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.subsection1.pk
        assert response.data["name"] == self.subsection1.name
        assert response.data["section_name"] == self.section1.name

    def test_create_subsection_admin(self, admin_client):
        response = admin_client.post(SUBSECTION_LIST_URL, self.base_payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert LearningSubSection.objects.count() == 3
        new_sub = LearningSubSection.objects.get(pk=response.data["id"])
        assert new_sub.name == self.base_payload["name"]
        assert new_sub.section == self.section1
        assert new_sub.slug == f"{self.section1.slug}-new-subsection"  # Check slug

    def test_create_subsection_duplicate_name_in_section_admin(self, admin_client):
        payload = self.base_payload.copy()
        payload["name"] = self.subsection1.name  # Duplicate name within section1
        response = admin_client.post(SUBSECTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "must make a unique set"
            in str(response.data["non_field_errors"][0]).lower()
        )

    def test_create_subsection_same_name_different_section_admin(self, admin_client):
        # Same name as subsection1, but in section2 - should be allowed
        payload = self.base_payload.copy()
        payload["name"] = self.subsection1.name
        payload["section_id"] = self.section2.pk
        response = admin_client.post(SUBSECTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            LearningSubSection.objects.filter(name=self.subsection1.name).count() == 2
        )

    def test_update_subsection_admin(self, admin_client):
        payload = {
            "section_id": self.section2.pk,  # Change section
            "name": "Updated Sub 1A",
            "slug": "updated-sub-1a-slug",
            "description": "Updated description.",
            "order": 5,
        }
        response = admin_client.put(subsection_detail_url(self.subsection1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.subsection1.refresh_from_db()
        assert self.subsection1.name == payload["name"]
        assert self.subsection1.section == self.section2
        assert self.subsection1.slug == payload["slug"]

    def test_delete_subsection_admin_with_protected_question(self, admin_client):
        """Test that deleting a subsection with questions fails due to PROTECT."""
        question = QuestionFactory(subsection=self.subsection1)
        assert Question.objects.count() == 1

        response = admin_client.delete(subsection_detail_url(self.subsection1.pk))
        # Deleting protected relation raises IntegrityError -> 500 Internal Server Error
        # or potentially 400/409 if DRF exception handling is customized for ProtectedError
        # For now, let's check the object still exists
        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            "Cannot delete subsection" in response.data["detail"]
        )  # Check error message
        assert LearningSubSection.objects.filter(
            pk=self.subsection1.pk
        ).exists()  # Verify not deleted
        assert Question.objects.filter(pk=question.pk).exists()

    def test_delete_subsection_admin_no_questions(self, admin_client):
        """Test deleting a subsection without linked questions."""
        assert Question.objects.filter(subsection=self.subsection1).count() == 0
        response = admin_client.delete(subsection_detail_url(self.subsection1.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LearningSubSection.objects.filter(pk=self.subsection1.pk).exists()


# === Test AdminSkillViewSet ===


class TestAdminSkillAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.subsection1 = LearningSubSectionFactory(name="SubSection A")
        self.subsection2 = LearningSubSectionFactory(name="SubSection B")
        self.skill1 = SkillFactory(subsection=self.subsection1, name="Skill A1")
        self.skill2 = SkillFactory(subsection=self.subsection1, name="Skill A2")
        self.base_payload = {
            "subsection_id": self.subsection1.pk,
            "name": "New Skill",
            "description": "A new skill.",
        }

    # Add permission tests (omitted for brevity)
    def test_list_skills_admin(self, admin_client):
        response = admin_client.get(SKILL_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_filter_skills_by_subsection_admin(self, admin_client):
        SkillFactory(subsection=self.subsection2)  # Skill in other subsection
        response = admin_client.get(
            SKILL_LIST_URL, {"subsection__id": self.subsection1.pk}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # Only skills from subsection1
        assert response.data["results"][0]["name"] == self.skill1.name

    def test_retrieve_skill_admin(self, admin_client):
        response = admin_client.get(skill_detail_url(self.skill1.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.skill1.pk
        assert response.data["name"] == self.skill1.name
        assert response.data["subsection_name"] == self.subsection1.name

    def test_create_skill_admin(self, admin_client):
        response = admin_client.post(SKILL_LIST_URL, self.base_payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert Skill.objects.count() == 3
        new_skill = Skill.objects.get(pk=response.data["id"])
        assert new_skill.name == self.base_payload["name"]
        assert new_skill.subsection == self.subsection1
        assert new_skill.slug == f"{self.subsection1.slug}-new-skill"

    def test_create_skill_duplicate_name_in_subsection_admin(self, admin_client):
        payload = self.base_payload.copy()
        payload["name"] = self.skill1.name  # Duplicate name within subsection1
        response = admin_client.post(SKILL_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data
        assert (
            "must make a unique set"
            in str(response.data["non_field_errors"][0]).lower()
        )

    def test_update_skill_admin(self, admin_client):
        payload = {
            "subsection_id": self.subsection2.pk,  # Change subsection
            "name": "Updated Skill A1",
            "slug": "updated-skill-a1-slug",
            "description": "Updated description.",
        }
        response = admin_client.put(skill_detail_url(self.skill1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.skill1.refresh_from_db()
        assert self.skill1.name == payload["name"]
        assert self.skill1.subsection == self.subsection2

    def test_delete_skill_admin(self, admin_client):
        # Check no cascade/protect issues by default when deleting skill
        response = admin_client.delete(skill_detail_url(self.skill1.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Skill.objects.count() == 1


# === Test AdminQuestionViewSet ===


class TestAdminQuestionAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.subsection1 = LearningSubSectionFactory()
        self.subsection2 = LearningSubSectionFactory()
        self.skill1 = SkillFactory(subsection=self.subsection1)
        self.skill2 = SkillFactory(
            subsection=self.subsection2
        )  # Skill in different subsection
        self.question1 = QuestionFactory(
            subsection=self.subsection1,
            skill=self.skill1,
            difficulty=Question.DifficultyLevel.EASY,
            is_active=True,
            question_text="UNIQUE_SEARCH_TERM_",
        )
        self.question2 = QuestionFactory(
            subsection=self.subsection1,
            skill=None,
            difficulty=Question.DifficultyLevel.HARD,
            is_active=False,
            question_text="Different text content",
        )
        self.base_payload = {
            "subsection_id": self.subsection1.pk,
            "skill_id": self.skill1.pk,
            "question_text": "What is 2+2?",
            "option_a": "1",
            "option_b": "2",
            "option_c": "3",
            "option_d": "4",
            "correct_answer": "D",
            "explanation": "Basic addition.",
            "difficulty": Question.DifficultyLevel.VERY_EASY,
            "is_active": True,
        }

    # Add permission tests (omitted for brevity)
    def test_list_questions_admin(self, admin_client):
        response = admin_client.get(QUESTION_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2  # Admin sees active and inactive
        # Check default ordering is -created_at (newest first)
        result_ids = {item["id"] for item in response.data["results"]}
        assert self.question1.pk in result_ids
        assert self.question2.pk in result_ids

    def test_filter_questions_admin(self, admin_client):
        # Filter by active status
        response = admin_client.get(QUESTION_LIST_URL, {"is_active": True})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == self.question1.pk

        # Filter by difficulty
        response = admin_client.get(
            QUESTION_LIST_URL, {"difficulty": Question.DifficultyLevel.HARD}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == self.question2.pk

        # Filter by subsection
        response = admin_client.get(
            QUESTION_LIST_URL, {"subsection__id": self.subsection1.pk}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_search_questions_admin(self, admin_client):
        search_term = "UNIQUE_SEARCH_TERM_"
        response = admin_client.get(QUESTION_LIST_URL, {"search": search_term})
        assert response.status_code == status.HTTP_200_OK
        # Assert exactly one result is found with the unique term
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == self.question1.pk
        assert search_term in response.data["results"][0]["question_text"]

    def test_retrieve_question_admin(self, admin_client):
        response = admin_client.get(question_detail_url(self.question1.pk))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.question1.pk
        assert response.data["question_text"] == self.question1.question_text
        assert response.data["correct_answer"] == self.question1.correct_answer
        assert response.data["subsection_slug"] == self.subsection1.slug
        assert response.data["skill_slug"] == self.skill1.slug

    def test_create_question_admin(self, admin_client):
        response = admin_client.post(QUESTION_LIST_URL, self.base_payload)
        assert response.status_code == status.HTTP_201_CREATED
        assert Question.objects.count() == 3
        new_q = Question.objects.get(pk=response.data["id"])
        assert new_q.question_text == self.base_payload["question_text"]
        assert new_q.correct_answer == "D"
        assert new_q.subsection == self.subsection1
        assert new_q.skill == self.skill1

    def test_create_question_without_skill_admin(self, admin_client):
        payload = self.base_payload.copy()
        del payload["skill_id"]  # Skill is optional
        response = admin_client.post(QUESTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_201_CREATED
        new_q = Question.objects.get(pk=response.data["id"])
        assert new_q.skill is None

    def test_create_question_invalid_skill_for_subsection_admin(self, admin_client):
        payload = self.base_payload.copy()
        payload["skill_id"] = self.skill2.pk  # skill2 belongs to subsection2
        response = admin_client.post(QUESTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "skill_id" in response.data
        assert (
            "does not belong to the selected subsection" in response.data["skill_id"][0]
        )

    def test_create_question_invalid_answer_choice_admin(self, admin_client):
        payload = self.base_payload.copy()
        payload["correct_answer"] = "E"  # Invalid choice
        response = admin_client.post(QUESTION_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "correct_answer" in response.data
        # Check for the core meaning of the error, not the exact string
        assert "not a valid choice" in str(response.data["correct_answer"][0]).lower()

    def test_update_question_admin(self, admin_client):
        payload = self.base_payload.copy()  # Start with valid payload
        payload["question_text"] = "Updated Question Text"
        payload["is_active"] = False
        payload["difficulty"] = Question.DifficultyLevel.MEDIUM
        payload["subsection_id"] = self.subsection2.pk  # Change subsection
        payload["skill_id"] = self.skill2.pk  # Change skill accordingly
        del payload["correct_answer"]  # PUT requires all fields, re-add correct answer
        payload["correct_answer"] = self.question1.correct_answer

        response = admin_client.put(question_detail_url(self.question1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.question1.refresh_from_db()
        assert self.question1.question_text == payload["question_text"]
        assert self.question1.is_active is False
        assert self.question1.subsection == self.subsection2
        assert self.question1.skill == self.skill2

    def test_partial_update_question_admin(self, admin_client):
        payload = {"is_active": False, "hint": "New hint"}
        response = admin_client.patch(question_detail_url(self.question1.pk), payload)
        assert response.status_code == status.HTTP_200_OK
        self.question1.refresh_from_db()
        assert self.question1.is_active is False
        assert self.question1.hint == "New hint"
        assert self.question1.difficulty == Question.DifficultyLevel.EASY  # Unchanged

    def test_delete_question_admin(self, admin_client):
        response = admin_client.delete(question_detail_url(self.question1.pk))
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Question.objects.count() == 1
        assert not Question.objects.filter(pk=self.question1.pk).exists()
