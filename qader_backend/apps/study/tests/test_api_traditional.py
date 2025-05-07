import pytest
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from unittest import mock
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.users.models import UserProfile
from apps.study.models import UserTestAttempt, UserQuestionAttempt, Question
from apps.learning.models import LearningSubSection, Skill
from apps.study.services.study import UsageLimitExceeded  # Import for mocking
from apps.learning.tests.factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    SkillFactory,
    QuestionFactory,
)
from apps.study.tests.factories import UserTestAttemptFactory
from apps.api.exceptions import (
    UsageLimitExceeded as APIUsageLimitExceeded,
)  # The one view expects from service

# Constants for Traditional Practice Start
MIN_QUESTIONS = getattr(settings, "MIN_QUESTIONS_TRADITIONAL_INITIAL", 0)
MAX_QUESTIONS = getattr(settings, "MAX_QUESTIONS_TRADITIONAL_INITIAL", 50)
DEFAULT_QUESTIONS = getattr(settings, "DEFAULT_QUESTIONS_TRADITIONAL_INITIAL", 10)


@pytest.fixture
def drf_validation_error_insufficient_questions():
    return DRFValidationError("Not enough questions found matching your criteria.")


@pytest.mark.django_db
class TestTraditionalPracticeStartView:
    """Tests for TraditionalPracticeStartView."""

    def get_url(self):
        # Assuming your traditional.py URLs are included without a further app-level namespace
        # If apps.study.urls has app_name = 'study', it might be 'study:start-traditional'
        return reverse("api:v1:study:start-traditional")

    def test_start_traditional_unauthenticated(self, api_client):
        response = api_client.post(self.get_url(), data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_start_traditional_authenticated_not_subscribed(self, authenticated_client):
        response = authenticated_client.post(self.get_url(), data={})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # The IsSubscribed permission class has a specific message
        assert (
            str(response.data["detail"])
            == "An active subscription is required to access this resource."
        )

    @mock.patch(
        "apps.study.api.views.traditional.study_services.start_traditional_practice"
    )
    def test_start_traditional_subscribed_success_default_questions(
        self, mock_start_service, subscribed_client
    ):
        user = subscribed_client.user
        mock_service_response_questions = QuestionFactory.create_batch(
            DEFAULT_QUESTIONS
        )
        mock_start_service.return_value = {
            "attempt_id": 1,
            "status": UserTestAttempt.Status.STARTED.value,
            "attempt_number_for_type": 1,
            "questions": mock_service_response_questions,
        }
        payload = {}

        response = subscribed_client.post(self.get_url(), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["attempt_id"] == 1
        assert response.data["status"] == UserTestAttempt.Status.STARTED.value
        assert response.data["attempt_number_for_type"] == 1
        assert len(response.data["questions"]) == DEFAULT_QUESTIONS

        mock_start_service.assert_called_once_with(
            user=user,
            subsections=[],
            skills=[],
            num_questions_initial=DEFAULT_QUESTIONS,
            starred=False,
            not_mastered=False,
        )

    @mock.patch(
        "apps.study.api.views.traditional.study_services.start_traditional_practice"
    )
    def test_start_traditional_subscribed_success_with_filters(
        self, mock_start_service, subscribed_client
    ):
        user = subscribed_client.user
        subsection1 = LearningSubSectionFactory()
        skill1 = SkillFactory(subsection=subsection1)
        num_q = 5
        mock_service_response_questions = QuestionFactory.create_batch(num_q)

        mock_start_service.return_value = {
            "attempt_id": 2,
            "status": UserTestAttempt.Status.STARTED.value,
            "attempt_number_for_type": 1,
            "questions": mock_service_response_questions,
        }
        payload = {
            "subsections": [subsection1.slug],
            "skills": [skill1.slug],
            "num_questions": num_q,
            "starred": True,
            "not_mastered": True,
        }

        response = subscribed_client.post(self.get_url(), data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["attempt_id"] == 2
        assert len(response.data["questions"]) == num_q

        called_args, called_kwargs = mock_start_service.call_args
        assert called_kwargs["user"] == user
        assert len(called_kwargs["subsections"]) == 1
        assert called_kwargs["subsections"][0].slug == subsection1.slug
        assert len(called_kwargs["skills"]) == 1
        assert called_kwargs["skills"][0].slug == skill1.slug
        assert called_kwargs["num_questions_initial"] == num_q
        assert called_kwargs["starred"] is True
        assert called_kwargs["not_mastered"] is True

    @mock.patch(
        "apps.study.api.views.traditional.study_services.start_traditional_practice"
    )
    def test_start_traditional_subscribed_zero_initial_questions(
        self, mock_start_service, subscribed_client
    ):
        user = subscribed_client.user
        mock_start_service.return_value = {
            "attempt_id": 3,
            "status": UserTestAttempt.Status.STARTED.value,
            "attempt_number_for_type": 1,
            "questions": [],
        }
        payload = {"num_questions": 0}

        response = subscribed_client.post(self.get_url(), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["attempt_id"] == 3
        assert len(response.data["questions"]) == 0
        mock_start_service.assert_called_once_with(
            user=user,
            subsections=[],
            skills=[],
            num_questions_initial=0,
            starred=False,
            not_mastered=False,
        )

    def test_start_traditional_invalid_payload_num_questions_range(
        self, subscribed_client
    ):
        payload_too_low = {"num_questions": -1}  # Since MIN_QUESTIONS is 0

        response_low = subscribed_client.post(self.get_url(), data=payload_too_low)
        assert response_low.status_code == status.HTTP_400_BAD_REQUEST
        assert "num_questions" in response_low.data["detail"]
        assert "Ensure this value is greater than or equal to 0." in str(
            response_low.data["detail"]["num_questions"][0]
        )

        payload_too_high = {"num_questions": MAX_QUESTIONS + 1}
        response_high = subscribed_client.post(self.get_url(), data=payload_too_high)
        assert response_high.status_code == status.HTTP_400_BAD_REQUEST
        assert "num_questions" in response_high.data["detail"]
        assert f"Ensure this value is less than or equal to {MAX_QUESTIONS}." in str(
            response_high.data["detail"]["num_questions"][0]
        )

    def test_start_traditional_invalid_subsection_slug(self, subscribed_client):
        payload = {"subsections": ["non-existent-slug"]}
        response = subscribed_client.post(self.get_url(), data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "subsections" in response.data["detail"]
        assert "Object with slug=non-existent-slug does not exist." in str(
            response.data["detail"]["subsections"][0]
        )

    def test_start_traditional_skill_not_in_subsection(self, subscribed_client):
        section1 = LearningSectionFactory()
        subsection1 = LearningSubSectionFactory(
            section=section1, name="Sub1 For Skill Test"
        )
        subsection2 = LearningSubSectionFactory(
            section=section1, name="Sub2 For Skill Test"
        )
        skill_in_sub2 = SkillFactory(subsection=subsection2, name="Skill In Sub2 Test")

        payload = {"subsections": [subsection1.slug], "skills": [skill_in_sub2.slug]}
        response = subscribed_client.post(self.get_url(), data=payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "skills" in response.data["detail"]
        assert (
            f"Selected skills do not belong to the selected subsections: {skill_in_sub2.name}"
            in str(response.data["detail"]["skills"][0])
        )

    def test_start_traditional_already_active_session(self, subscribed_client):
        user = subscribed_client.user
        UserTestAttemptFactory(user=user, status=UserTestAttempt.Status.STARTED)

        payload = {}
        response = subscribed_client.post(self.get_url(), data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert "already have an ongoing test or practice session." in str(
            response.data["detail"]["non_field_errors"][0]
        )

    @mock.patch(
        "apps.study.api.views.traditional.study_services.start_traditional_practice"
    )
    def test_start_traditional_usage_limit_exceeded(
        self, mock_start_service, subscribed_client
    ):
        mock_start_service.side_effect = APIUsageLimitExceeded(
            "Limit reached for traditional practice."
        )
        payload = {}

        response = subscribed_client.post(self.get_url(), data=payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
        assert "Limit reached" in str(response.data["detail"])

    @mock.patch(
        "apps.study.api.views.traditional.study_services.start_traditional_practice"
    )
    def test_start_traditional_insufficient_questions_error(
        self,
        mock_start_service,
        subscribed_client,
        drf_validation_error_insufficient_questions,
    ):
        mock_start_service.side_effect = drf_validation_error_insufficient_questions
        payload = {"num_questions": 10}

        response = subscribed_client.post(self.get_url(), data=payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "Not enough questions found" in str(response.data["detail"])


@pytest.mark.django_db
class TestTraditionalQuestionListView:
    """Tests for TraditionalQuestionListView."""

    def get_url(self):
        return reverse("api:v1:study:traditional-question-list")

    def test_list_questions_unauthenticated(self, api_client):
        response = api_client.get(self.get_url())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_questions_authenticated_not_subscribed(self, authenticated_client):
        response = authenticated_client.get(self.get_url())
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @mock.patch(
        "apps.study.api.views.traditional.study_services.get_filtered_questions"
    )
    def test_list_questions_subscribed_success_default_limit(
        self, mock_get_questions, subscribed_client
    ):
        user = subscribed_client.user
        mock_questions = QuestionFactory.create_batch(10)
        mock_get_questions.return_value = Question.objects.filter(
            id__in=[q.id for q in mock_questions]
        )

        response = subscribed_client.get(self.get_url())
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 10
        mock_get_questions.assert_called_once()
        call_kwargs = mock_get_questions.call_args.kwargs
        assert call_kwargs["user"] == user
        assert call_kwargs["limit"] == 10
        assert call_kwargs["subsections"] is None
        assert call_kwargs["skills"] is None
        assert call_kwargs["starred"] is False
        assert call_kwargs["not_mastered"] is False
        assert call_kwargs["exclude_ids"] is None

    @mock.patch(
        "apps.study.api.views.traditional.study_services.get_filtered_questions"
    )
    def test_list_questions_subscribed_success_with_filters_and_limit(
        self, mock_get_questions, subscribed_client
    ):
        user = subscribed_client.user
        sub1 = LearningSubSectionFactory()
        skill1 = SkillFactory(subsection=sub1)
        q_to_exclude = QuestionFactory()

        mock_questions = QuestionFactory.create_batch(3)
        mock_get_questions.return_value = Question.objects.filter(
            id__in=[q.id for q in mock_questions]
        )

        query_params = {
            "limit": 5,
            "subsection__slug__in": sub1.slug,
            "skill__slug__in": skill1.slug,
            "starred": "true",
            "not_mastered": "1",
            "exclude_ids": str(q_to_exclude.id),
        }
        response = subscribed_client.get(self.get_url(), query_params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
        mock_get_questions.assert_called_once()
        call_kwargs = mock_get_questions.call_args.kwargs
        assert call_kwargs["user"] == user
        assert call_kwargs["limit"] == 5
        assert call_kwargs["subsections"] == [sub1.slug]
        assert call_kwargs["skills"] == [skill1.slug]
        assert call_kwargs["starred"] is True
        assert call_kwargs["not_mastered"] is True
        assert call_kwargs["exclude_ids"] == [q_to_exclude.id]

    @mock.patch(
        "apps.study.api.views.traditional.study_services.get_filtered_questions"
    )
    def test_list_questions_subscribed_no_questions_found(
        self, mock_get_questions, subscribed_client
    ):
        mock_get_questions.return_value = Question.objects.none()
        response = subscribed_client.get(self.get_url())
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_list_questions_invalid_filter_params_bad_exclude_ids(
        self, subscribed_client
    ):
        query_params = {"exclude_ids": "abc,def"}
        response = subscribed_client.get(self.get_url(), query_params)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # DRF typically wraps field errors under 'detail' if a custom exception handler is in place
        # or directly as the response.data if it's a simple validation error from the serializer/view.
        # Let's assume a common structure where field errors are keys in response.data or response.data['detail']

        error_data = response.data
        if "detail" in error_data and isinstance(
            error_data["detail"], dict
        ):  # Common custom handler structure
            error_data = error_data["detail"]

        assert "exclude_ids" in error_data
        assert "Invalid value 'abc'. All IDs must be integers." in str(
            error_data["exclude_ids"][0]
        )

    @mock.patch(
        "apps.study.api.views.traditional.study_services.get_filtered_questions"
    )
    def test_list_questions_service_raises_validation_error_for_insufficient_questions(
        self,
        mock_get_questions,
        subscribed_client,
        drf_validation_error_insufficient_questions,
    ):
        # This test assumes the view is modified to catch DRFValidationError from the service
        # and let DRF handle it as a 400 response.
        mock_get_questions.side_effect = drf_validation_error_insufficient_questions
        response = subscribed_client.get(
            self.get_url(), {"limit": 1}
        )  # Request 1 question
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Not enough questions found" in str(response.data)


@pytest.mark.django_db
class TestTraditionalActionViews:
    """Base setup and tests for Hint, Eliminate, RevealAnswer, RevealExplanation views."""

    @pytest.fixture(autouse=True)
    def setup_data(self, subscribed_client):
        self.user = subscribed_client.user  # This is the 'subscribed_user'
        self.active_traditional_attempt = UserTestAttemptFactory(
            user=self.user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        )
        self.question = QuestionFactory(
            is_active=True,
            hint="A hint.",
            explanation="An explanation.",
            correct_answer="A",
        )
        self.non_active_attempt = UserTestAttemptFactory(
            user=self.user, status=UserTestAttempt.Status.COMPLETED
        )
        self.non_traditional_attempt = UserTestAttemptFactory(
            user=self.user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.PRACTICE,
        )
        self.inactive_question = QuestionFactory(is_active=False)

    def _get_action_url(self, action_name, attempt_id, question_id):
        # action_name would be 'traditional-use-hint', etc.
        return reverse(
            action_name, kwargs={"attempt_id": attempt_id, "question_id": question_id}
        )

    # --- TraditionalUseHintView ---
    @mock.patch(
        "apps.study.api.views.traditional.study_services.record_traditional_action_and_get_data"
    )
    def test_use_hint_success(self, mock_record_action, subscribed_client):
        mock_record_action.return_value = self.question.hint
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            self.active_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["question_id"] == self.question.id
        assert response.data["hint"] == self.question.hint
        mock_record_action.assert_called_once_with(
            user=self.user,
            test_attempt=self.active_traditional_attempt,
            question=self.question,
            action_type="hint",
        )

    def test_use_hint_unauthenticated(self, api_client):
        # Use IDs from a shared context if needed, or dummy IDs if 401 is expected before ID validation
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint", 1, 1
        )  # Dummy IDs
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_use_hint_not_subscribed(self, authenticated_client):
        # authenticated_client's user ('standard_user') is not subscribed
        # Create an attempt for this non-subscribed user
        attempt_for_non_subscribed = UserTestAttemptFactory(
            user=authenticated_client.user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        )
        question_for_test = QuestionFactory(is_active=True)
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            attempt_for_non_subscribed.id,
            question_for_test.id,
        )
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_use_hint_attempt_not_found(self, subscribed_client):
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint", 9999, self.question.id
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_use_hint_question_not_found(self, subscribed_client):
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            self.active_traditional_attempt.id,
            9999,
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Question not found" in str(response.data["detail"])

    def test_use_hint_attempt_not_active(self, subscribed_client):
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            self.non_active_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "only valid for active traditional practice sessions" in str(
            response.data["detail"]
        )

    def test_use_hint_attempt_not_traditional(self, subscribed_client):
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            self.non_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    # --- TraditionalUseEliminationView ---
    @mock.patch(
        "apps.study.api.views.traditional.study_services.record_traditional_action_and_get_data"
    )
    def test_use_elimination_success(self, mock_record_action, subscribed_client):
        mock_record_action.return_value = True
        url = self._get_action_url(
            "api:v1:study:traditional-use-eliminate",
            self.active_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["detail"] == "Elimination usage recorded."
        mock_record_action.assert_called_once_with(
            user=self.user,
            test_attempt=self.active_traditional_attempt,
            question=self.question,
            action_type="eliminate",
        )

    # --- TraditionalRevealAnswerView ---
    @mock.patch(
        "apps.study.api.views.traditional.study_services.record_traditional_action_and_get_data"
    )
    def test_reveal_answer_success(self, mock_record_action, subscribed_client):
        mock_record_action.return_value = self.question.correct_answer
        url = self._get_action_url(
            "api:v1:study:traditional-reveal-answer",
            self.active_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["question_id"] == self.question.id
        assert response.data["correct_answer"] == self.question.correct_answer
        mock_record_action.assert_called_once_with(
            user=self.user,
            test_attempt=self.active_traditional_attempt,
            question=self.question,
            action_type="reveal_answer",
        )

    # --- TraditionalRevealExplanationView ---
    @mock.patch(
        "apps.study.api.views.traditional.study_services.record_traditional_action_and_get_data"
    )
    def test_reveal_explanation_success(self, mock_record_action, subscribed_client):
        mock_record_action.return_value = self.question.explanation
        url = self._get_action_url(
            "api:v1:study:traditional-reveal-explanation",
            self.active_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["question_id"] == self.question.id
        assert response.data["explanation"] == self.question.explanation
        mock_record_action.assert_called_once_with(
            user=self.user,
            test_attempt=self.active_traditional_attempt,
            question=self.question,
            action_type="reveal_explanation",
        )

    @mock.patch(
        "apps.study.api.views.traditional.study_services.record_traditional_action_and_get_data"
    )
    def test_action_view_service_error(self, mock_record_action, subscribed_client):
        from rest_framework.exceptions import APIException as DRFAPIException

        mock_record_action.side_effect = DRFAPIException("Service unavailable.")
        url = self._get_action_url(
            "api:v1:study:traditional-use-hint",
            self.active_traditional_attempt.id,
            self.question.id,
        )
        response = subscribed_client.post(url)

        assert (
            response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        )  # View catches generic Exception
        assert "Failed to record hint usage" in str(response.data["detail"])
