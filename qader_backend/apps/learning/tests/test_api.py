import factory
import pytest
from django.urls import reverse
from rest_framework import status

from ..models import LearningSection, LearningSubSection, Skill, UserStarredQuestion


from .factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    SkillFactory,
    QuestionFactory,
    UserStarredQuestionFactory,
)

# Assuming UserFactory is accessible via conftest fixtures (user, admin_user)

# Apply django_db marker to all tests in this module
pytestmark = pytest.mark.django_db


# Helper function to clean tables before test setup
def clean_learning_models():
    LearningSection.objects.all().delete()
    LearningSubSection.objects.all().delete()
    Skill.objects.all().delete()


# --- Test Learning Sections API ---


def test_list_sections_unauthenticated(api_client):
    """Verify unauthenticated users cannot list sections."""
    LearningSectionFactory.create_batch(3)
    url = reverse("api:v1:learning:section-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_sections_authenticated(subscribed_client):
    """Verify authenticated users can list sections."""
    sections = LearningSectionFactory.create_batch(3, order=factory.Iterator([2, 1, 0]))
    url = reverse("api:v1:learning:section-list")
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 3
    # Check default ordering by 'order'
    assert response.data[0]["slug"] == sections[2].slug  # order 0
    assert response.data[1]["slug"] == sections[1].slug  # order 1
    assert response.data[2]["slug"] == sections[0].slug  # order 2
    assert (
        "subsections" not in response.data[0]
    )  # Default serializer doesn't nest subsections


def test_retrieve_section_by_slug(subscribed_client):
    """Verify retrieving a specific section by its slug."""
    section = LearningSectionFactory(name="Specific Section")
    url = reverse("api:v1:learning:section-detail", kwargs={"slug": section.slug})
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["slug"] == section.slug
    assert response.data["name"] == section.name


def test_retrieve_section_not_found(subscribed_client):
    """Verify 404 is returned for a non-existent section slug."""
    url = reverse(
        "api:v1:learning:section-detail", kwargs={"slug": "non-existent-slug"}
    )
    response = subscribed_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Test Learning SubSections API ---


def test_list_subsections_authenticated(subscribed_client):
    """Verify listing subsections."""
    section1 = LearningSectionFactory()
    section2 = LearningSectionFactory()
    sub1 = LearningSubSectionFactory(section=section1, order=1)
    sub2 = LearningSubSectionFactory(section=section2, order=0)
    sub3 = LearningSubSectionFactory(section=section1, order=0)

    url = reverse("api:v1:learning:subsection-list")
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 3
    # Check default ordering (section order, then sub order)
    assert response.data[0]["slug"] == sub3.slug  # section1, order 0
    assert response.data[1]["slug"] == sub1.slug  # section1, order 1
    assert response.data[2]["slug"] == sub2.slug  # section2, order 0


def test_filter_subsections_by_section(subscribed_client):
    """Verify filtering subsections by parent section slug."""
    section1 = LearningSectionFactory()
    section2 = LearningSectionFactory()
    LearningSubSectionFactory(section=section1)
    sub2 = LearningSubSectionFactory(section=section2)
    LearningSubSectionFactory(section=section1)

    url = reverse("api:v1:learning:subsection-list")
    response = subscribed_client.get(f"{url}?section__slug={section2.slug}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["slug"] == sub2.slug


def test_retrieve_subsection_by_slug(authenticated_client):
    """Verify retrieving a specific subsection."""
    clean_learning_models()  # Add cleanup here too for consistency
    subsection = LearningSubSectionFactory(name="My Sub Section")
    SkillFactory(subsection=subsection)
    SkillFactory(subsection=subsection)

    url = reverse("api:v1:learning:subsection-detail", kwargs={"slug": subsection.slug})
    response = authenticated_client.get(url)

    # --- Check every access to response.data ---
    assert response.status_code == status.HTTP_200_OK
    assert response.data["slug"] == subsection.slug
    assert response.data["name"] == subsection.name

    # This line caused the original error if it was response.data[0]['skills']
    # Ensure it's now correctly checking the dict directly
    assert "skills" in response.data
    assert isinstance(response.data["skills"], list)
    assert len(response.data["skills"]) == 2


# --- Test Skills API ---


def test_list_skills_authenticated(subscribed_client):
    """Verify listing skills."""
    skill1 = SkillFactory()
    SkillFactory()
    url = reverse("api:v1:learning:skill-list")
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    assert response.data[0]["slug"] == skill1.slug


def test_filter_skills_by_subsection(subscribed_client):
    """Verify filtering skills by parent subsection slug."""
    sub1 = LearningSubSectionFactory()
    sub2 = LearningSubSectionFactory()
    SkillFactory(subsection=sub1)
    skill2 = SkillFactory(subsection=sub2)
    SkillFactory(subsection=sub1)

    url = reverse("api:v1:learning:skill-list")
    response = subscribed_client.get(f"{url}?subsection__slug={sub2.slug}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["slug"] == skill2.slug


def test_search_skills(subscribed_client):
    """Verify searching skills by name."""
    SkillFactory(name="Unique Skill Name Alpha")
    SkillFactory(name="Another Skill Beta")
    SkillFactory(name="Unique Name Gamma")

    url = reverse("api:v1:learning:skill-list")
    response = subscribed_client.get(f"{url}?search=Unique Name")  # Search term

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2  # Should match Alpha and Gamma
    slugs_found = {item["slug"] for item in response.data}
    assert "unique-skill-name-alpha" in slugs_found
    assert "unique-name-gamma" in slugs_found


def test_retrieve_skill_by_slug(subscribed_client):
    """Verify retrieving a specific skill."""
    skill = SkillFactory(name="Detail Skill Test")
    url = reverse("api:v1:learning:skill-detail", kwargs={"slug": skill.slug})
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["slug"] == skill.slug
    assert response.data["name"] == skill.name


# --- Test Questions API ---

# Placeholder for IsSubscribed - assumes authenticated user is subscribed for now
# Replace `subscribed_client` with a dedicated `subscribed_client` fixture later
# For now, IsSubscribed just checks authentication


def test_list_questions_requires_authentication(api_client):
    """Verify listing questions requires authentication (and subscription eventually)."""
    QuestionFactory()
    url = reverse("api:v1:learning:question-list")
    response = api_client.get(url)
    assert (
        response.status_code == status.HTTP_401_UNAUTHORIZED
    )  # Or 403 if IsSubscribed checks sub


def test_list_questions_success(subscribed_client):
    """Verify subscribed user can list questions (basic fields only)."""
    q1 = QuestionFactory()
    q2 = QuestionFactory()
    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) >= 2  # Assuming pagination, check results list
    # Check first question data
    first_q_data = response.data["results"][0]
    assert "id" in first_q_data
    assert "question_text" in first_q_data
    assert "option_a" in first_q_data
    assert "correct_answer" not in first_q_data  # List view shouldn't expose answer
    assert "explanation" not in first_q_data
    assert "hint" in first_q_data
    assert "is_starred" in first_q_data  # Should be present


def test_retrieve_question_detail_success(subscribed_client):
    """Verify subscribed user can get question details (including answer/explanation)."""
    question = QuestionFactory(
        correct_answer="C", explanation="Detailed C explanation."
    )
    url = reverse("api:v1:learning:question-detail", kwargs={"pk": question.pk})
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == question.pk
    assert response.data["correct_answer"] == "C"
    assert response.data["explanation"] == "Detailed C explanation."
    assert "is_starred" in response.data
    # Check nested subsection/skill data is present in detail view
    assert isinstance(response.data["subsection"], dict)
    assert response.data["subsection"]["slug"] == question.subsection.slug
    assert isinstance(response.data["skill"], dict)
    assert response.data["skill"]["slug"] == question.skill.slug


def test_retrieve_question_detail_not_found(subscribed_client):
    """Verify 404 for non-existent question."""
    url = reverse("api:v1:learning:question-detail", kwargs={"pk": 99999})
    response = subscribed_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Question Filtering Tests ---


def test_filter_questions_by_subsection(subscribed_client):
    sub1 = LearningSubSectionFactory()
    sub2 = LearningSubSectionFactory()
    q1 = QuestionFactory(subsection=sub1)
    QuestionFactory(subsection=sub2)
    QuestionFactory(subsection=sub1)

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?subsection__slug={sub1.slug}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == q1.id


def test_filter_questions_by_skill(subscribed_client):
    skill1 = SkillFactory()
    skill2 = SkillFactory()
    q1 = QuestionFactory(skill=skill1)
    QuestionFactory(skill=skill2)
    QuestionFactory(skill=skill1)

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?skill__slug={skill1.slug}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == q1.id


def test_filter_questions_by_difficulty(subscribed_client):
    q_easy = QuestionFactory(difficulty=2)
    QuestionFactory(difficulty=4)
    QuestionFactory(difficulty=2)

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?difficulty=2")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == q_easy.id


def test_filter_questions_exclude_ids(subscribed_client):
    q1 = QuestionFactory()
    q2 = QuestionFactory()
    q3 = QuestionFactory()

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?exclude_ids={q1.id},{q3.id}")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["id"] == q2.id


def test_search_questions(subscribed_client):
    QuestionFactory(question_text="Find the value of X here.")
    q2 = QuestionFactory(question_text="What is the primary value?")
    QuestionFactory(hint="Consider the value carefully.")

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?search=value")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 3  # Matches text and hint
    # Check if expected question is in results (order isn't guaranteed)
    assert any(item["id"] == q2.id for item in response.data["results"])


def test_order_questions_by_difficulty(subscribed_client):
    q_hard = QuestionFactory(difficulty=5)
    q_easy = QuestionFactory(difficulty=1)
    q_medium = QuestionFactory(difficulty=3)

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(f"{url}?ordering=difficulty")  # Ascending

    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) == 3
    assert results[0]["id"] == q_easy.id
    assert results[1]["id"] == q_medium.id
    assert results[2]["id"] == q_hard.id

    response_desc = subscribed_client.get(f"{url}?ordering=-difficulty")  # Descending
    assert response_desc.status_code == status.HTTP_200_OK
    results_desc = response_desc.data["results"]
    assert results_desc[0]["id"] == q_hard.id
    assert results_desc[1]["id"] == q_medium.id
    assert results_desc[2]["id"] == q_easy.id


# --- Question Star/Unstar Tests ---


def test_question_star_success(subscribed_client):
    """Verify starring a question."""
    user = subscribed_client.user
    question = QuestionFactory()
    assert not UserStarredQuestion.objects.filter(user=user, question=question).exists()

    url = reverse("api:v1:learning:question-star", kwargs={"pk": question.pk})
    response = subscribed_client.post(url)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == {"status": "starred"}
    assert UserStarredQuestion.objects.filter(user=user, question=question).exists()


def test_question_star_already_starred(subscribed_client):
    """Verify starring an already starred question."""
    user = subscribed_client.user
    starred_link = UserStarredQuestionFactory(
        user=user
    )  # Creates question and stars it
    question = starred_link.question

    url = reverse("api:v1:learning:question-star", kwargs={"pk": question.pk})
    response = subscribed_client.post(url)

    assert response.status_code == status.HTTP_200_OK  # Should be OK, not created
    assert response.data == {"status": "already starred"}
    # Ensure only one entry exists
    assert UserStarredQuestion.objects.filter(user=user, question=question).count() == 1


def test_question_star_unauthenticated(api_client):
    """Verify unauthenticated users cannot star questions."""
    question = QuestionFactory()
    url = reverse("api:v1:learning:question-star", kwargs={"pk": question.pk})
    response = api_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_question_unstar_success(subscribed_client):
    """Verify unstarring a question."""
    user = subscribed_client.user
    starred_link = UserStarredQuestionFactory(user=user)
    question = starred_link.question
    assert UserStarredQuestion.objects.filter(user=user, question=question).exists()

    url = reverse("api:v1:learning:question-unstar", kwargs={"pk": question.pk})
    response = subscribed_client.delete(url)

    assert (
        response.status_code == status.HTTP_200_OK
    )  # Or 204 No Content if view returns that
    assert response.data == {"status": "unstarred"}
    assert not UserStarredQuestion.objects.filter(user=user, question=question).exists()


def test_question_unstar_not_starred(subscribed_client):
    """Verify unstarring a question that wasn't starred."""
    user = subscribed_client.user
    question = QuestionFactory()  # Not starred by this user
    assert not UserStarredQuestion.objects.filter(user=user, question=question).exists()

    url = reverse("api:v1:learning:question-unstar", kwargs={"pk": question.pk})
    response = subscribed_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {"status": "not starred"}


def test_question_unstar_unauthenticated(api_client):
    """Verify unauthenticated users cannot unstar questions."""
    question = QuestionFactory()
    url = reverse("api:v1:learning:question-unstar", kwargs={"pk": question.pk})
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- Check is_starred in Question List/Detail ---


def test_question_list_shows_is_starred_correctly(subscribed_client):
    """Verify the 'is_starred' field is correct in list view."""
    user = subscribed_client.user
    q_starred = QuestionFactory()
    q_not_starred = QuestionFactory()
    UserStarredQuestionFactory(user=user, question=q_starred)

    url = reverse("api:v1:learning:question-list")
    response = subscribed_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    starred_found = False
    not_starred_found = False
    for item in results:
        if item["id"] == q_starred.id:
            assert item["is_starred"] is True
            starred_found = True
        elif item["id"] == q_not_starred.id:
            assert item["is_starred"] is False
            not_starred_found = True
    assert (
        starred_found and not_starred_found
    )  # Make sure both questions were in the response


def test_question_detail_shows_is_starred_correctly(subscribed_client):
    """Verify the 'is_starred' field is correct in detail view."""
    user = subscribed_client.user
    q_starred = QuestionFactory()
    q_not_starred = QuestionFactory()
    UserStarredQuestionFactory(user=user, question=q_starred)

    # Check starred question detail
    url_starred = reverse(
        "api:v1:learning:question-detail", kwargs={"pk": q_starred.pk}
    )
    response_starred = subscribed_client.get(url_starred)
    assert response_starred.status_code == status.HTTP_200_OK
    assert response_starred.data["is_starred"] is True

    # Check not-starred question detail
    url_not_starred = reverse(
        "api:v1:learning:question-detail", kwargs={"pk": q_not_starred.pk}
    )
    response_not_starred = subscribed_client.get(url_not_starred)
    assert response_not_starred.status_code == status.HTTP_200_OK
    assert response_not_starred.data["is_starred"] is False


def test_filter_questions_by_starred(subscribed_client):
    """Verify filtering questions based on starred status."""
    user = subscribed_client.user
    q_starred1 = QuestionFactory()
    q_starred2 = QuestionFactory()
    q_not_starred = QuestionFactory()
    UserStarredQuestionFactory(user=user, question=q_starred1)
    UserStarredQuestionFactory(user=user, question=q_starred2)

    url = reverse("api:v1:learning:question-list")

    # Test ?starred=true
    response_true = subscribed_client.get(f"{url}?starred=true")
    assert response_true.status_code == status.HTTP_200_OK
    assert len(response_true.data["results"]) == 2
    result_ids_true = {item["id"] for item in response_true.data["results"]}
    assert q_starred1.id in result_ids_true
    assert q_starred2.id in result_ids_true

    # Test ?starred=false
    response_false = subscribed_client.get(f"{url}?starred=false")
    assert response_false.status_code == status.HTTP_200_OK
    assert len(response_false.data["results"]) == 1
    assert response_false.data["results"][0]["id"] == q_not_starred.id
