from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
import logging

from apps.study.models import UserQuestionAttempt, UserTestAttempt, Question
from apps.users.api.serializers import UserProfileSerializer
from apps.api.utils import get_user_from_context
from apps.learning.models import (
    LearningSubSection,
    Skill,
)
from apps.learning.api.serializers import (
    QuestionListSerializer,
)
from apps.study.services import get_filtered_questions

logger = logging.getLogger(__name__)


# --- Serializers for Incremental Test Attempt Flow ---


class TestAttemptAnswerSerializer(serializers.Serializer):
    """Serializer for submitting a single answer during an ongoing test attempt."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(is_active=True),  # Basic validation
        required=True,
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )
    # Add other flags if needed (used_hint, etc.)
    # used_hint = serializers.BooleanField(default=False, required=False)
    # used_elimination = serializers.BooleanField(default=False, required=False)

    def validate_question_id(self, value):
        """Ensure the question belongs to the specific test attempt (validated in view/service)."""
        # Basic validation happens via PrimaryKeyRelatedField.
        # Specific check against test_attempt.question_ids happens in the service.
        return value

    def validate_selected_answer(self, value):
        """Ensure the selected answer is valid."""
        if value not in UserQuestionAttempt.AnswerChoice.values:
            raise serializers.ValidationError(_("Invalid answer choice."))
        return value


class TestAttemptAnswerResponseSerializer(serializers.Serializer):
    """Response after submitting a single answer."""

    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    feedback_message = serializers.CharField(read_only=True)


class TestAttemptCompletionResponseSerializer(serializers.Serializer):
    """Response after successfully completing a test attempt."""

    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    answered_question_count = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    smart_analysis = serializers.CharField(allow_blank=True)
    message = serializers.CharField()
    # Include profile only if it was updated (level assessment)
    updated_profile = UserProfileSerializer(
        read_only=True, allow_null=True, required=False
    )


class TraditionalAttemptStartSerializer(serializers.Serializer):
    """Serializer for starting a traditional practice session."""

    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSubSection.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_(
            "Optional: Filter questions by these subsection slugs during the session."
        ),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=Skill.objects.filter(is_active=True)
        ),
        required=False,
        allow_empty=True,
        help_text=_(
            "Optional: Filter questions by these skill slugs during the session."
        ),
    )
    num_questions = serializers.IntegerField(  # <-- ADDED
        min_value=1,
        max_value=50,  # Sensible max for an initial batch
        default=10,  # Default number of questions
        required=False,
        help_text=_("Number of questions to fetch initially for the session."),
    )
    # Add other filters if needed (e.g., starred, not_mastered)
    # starred = serializers.BooleanField(default=False, required=False)
    # not_mastered = serializers.BooleanField(default=False, required=False)

    def validate(self, data):
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

        # Optional: Validate that *some* criteria is provided if needed, or allow empty filters
        # if not data.get('subsections') and not data.get('skills'):
        #     logger.info("Starting traditional session with no initial filters.")

        return data

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        num_questions_requested = validated_data.get("num_questions", 10)
        subsection_slugs = [s.slug for s in validated_data.get("subsections", [])]
        skill_slugs = [s.slug for s in validated_data.get("skills", [])]
        # Extract other filters if added (starred, not_mastered)
        # starred = validated_data.get('starred', False)
        # not_mastered = validated_data.get('not_mastered', False)

        # --- Fetch Initial Questions ---
        try:
            questions_queryset = get_filtered_questions(
                user=user,
                limit=num_questions_requested,
                subsections=subsection_slugs,
                skills=skill_slugs,
                # Pass other filters here if added
                # starred=starred,
                # not_mastered=not_mastered,
                exclude_ids=None,  # No exclusions when starting
            )
            selected_question_ids = list(
                questions_queryset.values_list("id", flat=True)
            )

            if not selected_question_ids:
                # Don't fail, just start session with empty questions. User can fetch later.
                logger.warning(
                    f"No questions found matching initial filters for traditional session start for user {user.id}. Starting empty session."
                )
                # Or raise ValidationError if initial questions are mandatory:
                # raise serializers.ValidationError(_("No questions found matching the specified criteria."))

            actual_num_selected = len(selected_question_ids)
            if actual_num_selected < num_questions_requested:
                logger.warning(
                    f"Requested {num_questions_requested} traditional questions, but only found {actual_num_selected} matching filters for user {user.id}."
                )

        except Exception as e:
            logger.exception(
                f"Error fetching initial questions for traditional session for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                _("Failed to retrieve initial questions for the session.")
            )

        # --- Create the Attempt ---
        config_snapshot = {
            "subsections_requested": subsection_slugs,
            "skills_requested": skill_slugs,
            "num_questions_requested_initial": num_questions_requested,
            "num_questions_selected_initial": actual_num_selected,
            "test_type": UserTestAttempt.AttemptType.TRADITIONAL,
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
                test_configuration=config_snapshot,
                question_ids=selected_question_ids,  # Store the initially selected IDs
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

        # Fetch the actual Question objects for the response using the reliable model method
        final_questions_queryset = test_attempt.get_questions_queryset()

        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.status,
            "questions": final_questions_queryset,  # Return the questions
        }


class TraditionalAttemptStartResponseSerializer(serializers.Serializer):
    """Response after starting a traditional practice session."""

    attempt_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)  # e.g., "started"
    questions = QuestionListSerializer(many=True, read_only=True)


# --- NEW Serializer for revealing answer ---
class RevealAnswerResponseSerializer(serializers.Serializer):
    """Response for revealing answer/explanation in traditional mode."""

    question_id = serializers.IntegerField()
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(allow_null=True)
