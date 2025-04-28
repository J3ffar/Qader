from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, Question
from apps.learning.models import LearningSubSection, Skill
from apps.learning.api.serializers import QuestionListSerializer
from apps.api.utils import get_user_from_context
from apps.study.services import get_filtered_questions
from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter

logger = logging.getLogger(__name__)


class TraditionalPracticeStartSerializer(serializers.Serializer):
    """Serializer for starting a traditional practice session."""

    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSubSection.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_("Optional: Filter questions by these subsection slugs."),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=Skill.objects.filter(is_active=True)
        ),
        required=False,
        allow_empty=True,
        help_text=_("Optional: Filter questions by these active skill slugs."),
    )
    num_questions = serializers.IntegerField(
        min_value=1,
        max_value=50,  # Sensible max for an initial batch in traditional mode
        default=10,  # Default number of questions
        required=False,
        help_text=_("Number of questions to fetch initially for the session."),
    )
    starred = serializers.BooleanField(
        default=False, required=False, help_text=_("Include only starred questions?")
    )
    not_mastered = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Include questions from skills not yet mastered?"),
    )

    def validate(self, data):
        """Validates input, checks limits, and checks for existing active sessions."""
        user = get_user_from_context(self.context)

        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("You already have an ongoing test or practice session.")
                    ]
                }
            )

        # --- Usage Limit Check (Attempt Limit Only) ---
        try:
            limiter = UsageLimiter(user)
            attempt_type = UserTestAttempt.AttemptType.TRADITIONAL
            limiter.check_can_start_test_attempt(attempt_type)
            # No question limit check here, as it's handled by fetching batches

        except UsageLimitExceeded as e:
            raise serializers.ValidationError({"non_field_errors": [str(e)]})
        except ValueError as e:  # Catch UsageLimiter init error
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            raise serializers.ValidationError(
                {"non_field_errors": ["Could not verify account limits."]}
            )
        # --- End Usage Limit Check ---

        # Store filters for use in create method
        self.context["subsection_slugs"] = [s.slug for s in data.get("subsections", [])]
        self.context["skill_slugs"] = [s.slug for s in data.get("skills", [])]
        self.context["starred"] = data.get("starred", False)
        self.context["not_mastered"] = data.get("not_mastered", False)
        self.context["num_questions_requested"] = data.get("num_questions", 10)

        return data

    def create(self, validated_data):
        """Creates the Traditional UserTestAttempt and fetches initial questions."""
        # ... (logic for fetching initial questions remains the same) ...
        user = get_user_from_context(self.context)
        num_questions_requested = self.context["num_questions_requested"]
        subsection_slugs = self.context["subsection_slugs"]
        skill_slugs = self.context["skill_slugs"]
        starred = self.context["starred"]
        not_mastered = self.context["not_mastered"]

        selected_question_ids = []
        actual_num_selected = 0
        if num_questions_requested > 0:
            try:
                questions_queryset = get_filtered_questions(
                    user=user,
                    limit=num_questions_requested,
                    subsections=subsection_slugs,
                    skills=skill_slugs,
                    starred=starred,
                    not_mastered=not_mastered,
                    exclude_ids=None,
                )
                selected_question_ids = list(
                    questions_queryset.values_list("id", flat=True)
                )
                actual_num_selected = len(selected_question_ids)

                if actual_num_selected < num_questions_requested:
                    logger.warning(
                        f"Requested {num_questions_requested} traditional questions, but only found {actual_num_selected} matching filters for user {user.id}."
                    )
            except Exception as e:
                logger.exception(
                    f"Error fetching initial questions for traditional session for user {user.id}: {e}"
                )
                # Proceed without initial questions if fetching fails

        config_snapshot = {
            "subsections_requested": subsection_slugs,
            "skills_requested": skill_slugs,
            "starred_requested": starred,
            "not_mastered_requested": not_mastered,
            "num_questions_requested_initial": num_questions_requested,
            "num_questions_selected_initial": actual_num_selected,
            "test_type": UserTestAttempt.AttemptType.TRADITIONAL,
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
                test_configuration=config_snapshot,
                question_ids=selected_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
            logger.info(
                f"Started Traditional Practice Session (Attempt ID: {test_attempt.id}) for user {user.id} with {actual_num_selected} initial questions."
            )
        except Exception as e:
            logger.exception(
                f"Error creating Traditional UserTestAttempt for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Failed to start the traditional practice session.")
                    ]
                }
            )

        final_questions_queryset = test_attempt.get_questions_queryset()

        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.status,
            "questions": final_questions_queryset,
        }


class TraditionalPracticeStartResponseSerializer(serializers.Serializer):
    """Response after starting a traditional practice session."""

    attempt_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)  # e.g., "started"
    questions = QuestionListSerializer(
        many=True, read_only=True
    )  # List of initial questions


class RevealAnswerResponseSerializer(serializers.Serializer):
    """Response for revealing answer/explanation in traditional mode."""

    question_id = serializers.IntegerField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(allow_null=True)
    # Add hints here if applicable
    # hint1 = serializers.CharField(allow_null=True)
