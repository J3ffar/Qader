import random
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.learning.models import LearningSubSection, Question, LearningSection
from apps.users.models import UserProfile
from apps.users.api.serializers import UserProfileSerializer  # Used in result response
from apps.learning.api.serializers import QuestionListSerializer
from apps.api.utils import get_user_from_context
from apps.study.services import get_filtered_questions

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "DEFAULT_QUESTIONS_LEVEL_ASSESSMENT", 30
)

# --- Level Assessment Serializers ---


# Keep LevelAssessmentStartSerializer
class LevelAssessmentStartSerializer(serializers.Serializer):
    # ... (Keep existing code) ...
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
        # Removed profile level check - allow retakes
        # Removed check for existing level assessment - allow multiple attempts (maybe add time limit later)

        # Check for ANY active 'started' attempt (can be simplified later if needed)
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            # attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT, # Check any active?
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": [_("You already have an ongoing test attempt.")]}
            )

        sections = data["sections"]
        num_questions_requested = data["num_questions"]
        min_required = self.fields["num_questions"].min_value

        # Use get_filtered_questions to check availability
        question_pool = get_filtered_questions(
            user=user,
            limit=num_questions_requested + 1,  # Check if > requested exist
            subsections=None,
            skills=None,
            starred=False,
            not_mastered=False,
            exclude_ids=None,
        )
        pool_count = question_pool.filter(subsection__section__in=sections).count()

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

        self.context["sections_validated"] = sections
        return data

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        sections = self.context["sections_validated"]
        num_questions_requested = validated_data["num_questions"]
        actual_num_questions = self.context["actual_num_questions"]

        # Select final questions using get_filtered_questions with section filter
        selected_section_ids = [sec.id for sec in sections]
        # Correctly get subsection slugs based on selected sections
        subsection_slugs = list(
            LearningSubSection.objects.filter(
                section_id__in=selected_section_ids
            ).values_list("slug", flat=True)
        )

        if not subsection_slugs:
            logger.warning(
                f"No subsection slugs found for sections: {[s.slug for s in sections]}"
            )
            # Depending on requirements, either raise error or allow proceeding (get_filtered_questions might handle empty list)
            # raise serializers.ValidationError(_("No subsections found for the selected sections."))

        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=None,
            starred=False,
            not_mastered=False,
        )
        selected_question_ids = list(questions_queryset.values_list("id", flat=True))

        # Ensure the final selected count matches the intended number
        if len(selected_question_ids) != actual_num_questions:
            logger.error(
                f"Failed to select required {actual_num_questions} level assessment questions after filtering. Found {len(selected_question_ids)}."
            )
            # This might indicate an issue in get_filtered_questions or filtering logic
            raise serializers.ValidationError(
                _("Could not select the exact number of required questions.")
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


# Keep LevelAssessmentAnswerSerializer (conceptually useful, but not directly used by new endpoint)
class LevelAssessmentAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


# Keep LevelAssessmentResponseSerializer (for Start endpoint)
class LevelAssessmentResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(many=True, read_only=True)


# Keep LevelAssessmentResultSerializer (Now used by Completion endpoint)
class LevelAssessmentResultSerializer(serializers.Serializer):
    # This will be used by the Complete endpoint, structure matches service output
    attempt_id = serializers.IntegerField(read_only=True)
    results = serializers.SerializerMethodField()
    updated_profile = UserProfileSerializer(read_only=True, allow_null=True)

    def get_results(self, obj):
        # 'obj' is the dictionary returned by the complete_test_attempt service
        return {
            "overall_score": obj.get("score_percentage"),
            "verbal_score": obj.get("score_verbal"),
            "quantitative_score": obj.get("score_quantitative"),
            "proficiency_summary": obj.get("results_summary"),
            "answered_question_count": obj.get("answered_question_count"),
            "total_questions": obj.get("total_questions"),
            "message": obj.get("message"),
            "smart_analysis": obj.get("smart_analysis"),
        }
