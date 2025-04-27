import random
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction  # Keep transaction import if used in serializer save
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import LearningSubSection, Question, LearningSection
from apps.users.models import UserProfile
from apps.users.api.serializers import UserProfileSerializer  # Used in response
from apps.learning.api.serializers import QuestionListSerializer
from apps.api.utils import get_user_from_context

# Import the specific service function needed
from apps.study.services import (
    record_test_submission,  # Use the same service function
    get_filtered_questions,  # Used by start serializer
)

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "DEFAULT_QUESTIONS_LEVEL_ASSESSMENT", 30
)

# --- Level Assessment Serializers ---


# LevelAssessmentStartSerializer remains largely the same
class LevelAssessmentStartSerializer(serializers.Serializer):
    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSection.objects.all()
        ),
        min_length=1,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        min_value=5,
        max_value=100,
        default=DEFAULT_QUESTIONS_LEVEL_ASSESSMENT,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        user = get_user_from_context(self.context)
        try:
            profile = user.profile
            # Allow retake for now, remove check for existing levels
            # if profile.current_level_verbal is not None or profile.current_level_quantitative is not None:
            #     pass # raise serializers.ValidationError(...)
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile missing for user ID: {user.id}.")
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile could not be found.")]}
            )

        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("You already have an ongoing level assessment.")
                    ]
                }
            )

        sections = data["sections"]
        num_questions_requested = data["num_questions"]
        min_required = self.fields["num_questions"].min_value

        # Use get_filtered_questions to check availability
        question_pool = get_filtered_questions(
            user=user,
            limit=num_questions_requested + 1,
            subsections=None,
            skills=None,
            starred=False,
            not_mastered=False,
            exclude_ids=None,
        )  # Base pool check
        pool_count = question_pool.filter(
            subsection__section__in=sections
        ).count()  # Filter by sections after getting base pool

        if pool_count < min_required:
            raise serializers.ValidationError(
                {
                    "num_questions": [
                        _(
                            "Not enough active questions ({count}) in selected sections (minimum {min_req})."
                        ).format(count=pool_count, min_req=min_required)
                    ]
                }
            )

        actual_num_questions = min(pool_count, num_questions_requested)
        self.context["actual_num_questions"] = actual_num_questions
        if pool_count < num_questions_requested:
            logger.warning(
                f"User {user.id} requested {num_questions_requested} level assessment qs, only {pool_count} available. Using {actual_num_questions}."
            )

        self.context["sections_validated"] = sections  # Pass validated sections
        return data

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        sections = self.context["sections_validated"]
        num_questions_requested = validated_data["num_questions"]
        actual_num_questions = self.context["actual_num_questions"]

        # Select final questions using get_filtered_questions with section filter
        selected_section_ids = [sec.id for sec in sections]
        subsection_slugs = list(
            LearningSubSection.objects.filter(
                section_id__in=selected_section_ids
            ).values_list("slug", flat=True)
        )

        # Check if any subsection slugs were found
        if not subsection_slugs:
            logger.warning(
                f"No subsection slugs found for the selected sections: {[s.slug for s in sections]}"
            )
            # Decide how to handle this: maybe raise validation error earlier?
            # Or proceed with an empty list, which get_filtered_questions should handle.

        # Select final questions using get_filtered_questions with the collected subsection slugs
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,  # Pass the list of slugs
            skills=None,  # Assuming no skill filter here
            starred=False,
            not_mastered=False,
        )
        selected_question_ids = list(questions_queryset.values_list("id", flat=True))

        if len(selected_question_ids) < actual_num_questions:
            logger.error(
                f"Failed to select required {actual_num_questions} level assessment questions. Found {len(selected_question_ids)}."
            )
            raise serializers.ValidationError(
                _("Insufficient questions found for selection.")
            )

        config_snapshot = {
            "sections_requested": [s.slug for s in sections],
            "num_questions_requested": num_questions_requested,
            "actual_num_questions_selected": len(selected_question_ids),
            "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
                test_configuration=config_snapshot,
                question_ids=selected_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating Level Assessment UserTestAttempt for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the assessment.")]}
            )

        final_questions_queryset = test_attempt.get_questions_queryset()
        return {"attempt_id": test_attempt.id, "questions": final_questions_queryset}


class LevelAssessmentAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


# --- REFACTORED LevelAssessmentSubmitSerializer ---
class LevelAssessmentSubmitSerializer(serializers.Serializer):
    """Handles submission for Level Assessment tests."""

    answers = LevelAssessmentAnswerSerializer(many=True, min_length=1)

    def validate(self, data):
        """Validates the attempt and answer structure."""
        user = get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = view.kwargs.get("attempt_id") if view else None

        if not attempt_id:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Assessment attempt ID missing.")]}
            )

        try:
            # Need profile later if updating, so select_related it here
            test_attempt = UserTestAttempt.objects.select_related(
                "user", "user__profile"
            ).get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Must be this type
            )
        except UserTestAttempt.DoesNotExist:
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                existing = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                if existing.status != UserTestAttempt.Status.STARTED:
                    error_msg = _(
                        "This assessment attempt has already been submitted or abandoned."
                    )
                elif (
                    existing.attempt_type
                    != UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
                ):
                    error_msg = _("This attempt is not a level assessment.")
                else:
                    error_msg = _("Cannot submit this assessment attempt.")
                raise serializers.ValidationError({"non_field_errors": [error_msg]})
            else:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Assessment attempt not found or does not belong to you.")
                        ]
                    }
                )
        except UserProfile.DoesNotExist:  # Catch if profile is somehow missing
            logger.error(
                f"UserProfile missing for user {user.id} during assessment submission validation."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error during submission.")]}
            )

        # Validate Answers (same logic as TestSubmitSerializer)
        submitted_answers_data = data["answers"]
        submitted_qids = {a["question_id"] for a in submitted_answers_data}
        expected_qids = set(test_attempt.question_ids)

        if len(submitted_answers_data) != len(expected_qids):
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Incorrect number of answers submitted. Expected {e}, got {a}."
                        ).format(e=len(expected_qids), a=len(submitted_answers_data))
                    ]
                }
            )
        if submitted_qids != expected_qids:
            missing = sorted(list(expected_qids - submitted_qids))
            extra = sorted(list(submitted_qids - expected_qids))
            errors = {"detail": _("Mismatch between submitted answers and questions.")}
            if missing:
                errors["missing_answers_for_qids"] = missing
            if extra:
                errors["unexpected_answers_for_qids"] = extra
            raise serializers.ValidationError({"answers": errors})

        self.context["test_attempt"] = test_attempt
        return data

    # save() now delegates to the service function
    def save(self, **kwargs):
        """Calls the service function to process the assessment submission."""
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]

        try:
            # Call the *same* service function (transaction handled within the service)
            # The service function now handles profile update based on attempt_type
            result_data = record_test_submission(
                test_attempt=test_attempt, answers_data=answers_data
            )
            # The service returns 'updated_profile' only for level assessments
            return result_data
        except serializers.ValidationError as e:
            # Re-raise validation errors from the service
            raise e
        except Exception as e:
            # Catch unexpected errors from the service
            logger.exception(
                f"Unexpected error during assessment submission service call for attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("An internal error occurred during submission.")
                    ]
                }
            )


# LevelAssessmentResponseSerializer remains the same
class LevelAssessmentResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(many=True, read_only=True)


# LevelAssessmentResultSerializer: structure depends on service output dict
class LevelAssessmentResultSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    # Mirror the structure returned by the service's result dict
    results = (
        serializers.SerializerMethodField()
    )  # Use method field to structure sub-dict
    updated_profile = UserProfileSerializer(
        read_only=True, allow_null=True
    )  # Profile might be null if error occurred

    def get_results(self, obj):
        # 'obj' here is the dictionary returned by the service
        return {
            "overall_score": obj.get("score_percentage"),
            "verbal_score": obj.get("score_verbal"),
            "quantitative_score": obj.get("score_quantitative"),
            "proficiency_summary": obj.get("results_summary"),
            "message": obj.get("message"),
            "smart_analysis": obj.get(
                "smart_analysis"
            ),  # Include if service returns it
        }
