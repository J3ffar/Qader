import random
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt
from apps.learning.models import LearningSection, LearningSubSection, Question
from apps.users.api.serializers import UserProfileSerializer
from apps.api.utils import get_user_from_context
from apps.study.services.study import get_filtered_questions
from apps.study.api.serializers.attempts import (
    UserTestAttemptCompletionResponseSerializer,
)
from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "DEFAULT_QUESTIONS_LEVEL_ASSESSMENT", 30
)

# --- Level Assessment Specific Serializers ---


class LevelAssessmentStartSerializer(serializers.Serializer):
    """Serializer for starting a Level Assessment test."""

    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSection.objects.all()
        ),
        min_length=1,
        required=True,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        min_value=5,  # Keep reasonable min/max
        max_value=100,
        default=DEFAULT_QUESTIONS_LEVEL_ASSESSMENT,
        required=False,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        """Validates input, checks limits, and checks question availability."""
        user = get_user_from_context(self.context)

        # Check for ANY active 'started' attempt (moved from view)
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": [_("You already have an ongoing test attempt.")]}
            )

        # --- Usage Limit Checks ---
        try:
            limiter = UsageLimiter(user)
            attempt_type = UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            # 1. Check if allowed to start this type of attempt
            limiter.check_can_start_test_attempt(attempt_type)

            # 2. Check and cap number of questions
            requested_questions = data.get(
                "num_questions", DEFAULT_QUESTIONS_LEVEL_ASSESSMENT
            )
            max_allowed_questions = limiter.get_max_questions_per_attempt()

            if (
                max_allowed_questions is not None
                and requested_questions > max_allowed_questions
            ):
                logger.info(
                    f"User {user.id} requested {requested_questions} level assessment questions, capped at {max_allowed_questions} due to plan limits."
                )
                # Override the requested number with the capped value
                data["num_questions"] = max_allowed_questions
                self.context["capped_num_questions"] = (
                    True  # Flag for logging in create
                )

        except UsageLimitExceeded as e:
            # Convert to ValidationError for serializer context
            raise serializers.ValidationError({"non_field_errors": [str(e)]})
        except ValueError as e:  # Catch UsageLimiter init error
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            raise serializers.ValidationError(
                {"non_field_errors": ["Could not verify account limits."]}
            )
        # --- End Usage Limit Checks ---

        sections = data["sections"]
        # Use the potentially capped number of questions for availability check
        num_questions_to_check = data["num_questions"]
        min_required = self.fields["num_questions"].min_value

        # Determine subsection slugs based on selected sections
        selected_section_ids = [sec.id for sec in sections]
        relevant_subsection_slugs = list(
            LearningSubSection.objects.filter(
                section_id__in=selected_section_ids
            ).values_list("slug", flat=True)
        )
        if not relevant_subsection_slugs:
            raise serializers.ValidationError(
                {"sections": [_("No subsections found for the selected sections.")]}
            )

        # Use get_filtered_questions to check availability within the selected sections/subsections
        # Check if *more* than requested exist to ensure randomness potential
        question_pool_qs = get_filtered_questions(
            user=user,
            limit=num_questions_to_check + 1,  # Check if slightly more exist
            subsections=relevant_subsection_slugs,
            skills=None,
            starred=False,
            not_mastered=False,
            exclude_ids=None,
        )
        pool_count = question_pool_qs.count()

        if pool_count < min_required:
            raise serializers.ValidationError(
                {
                    "num_questions": [
                        _(
                            "Not enough active questions ({count}) found in the selected sections to meet the minimum requirement ({min_req}). Please select fewer questions or different sections."
                        ).format(count=pool_count, min_req=min_required)
                    ]
                }
            )

        # Determine the final actual number based on availability and the (potentially capped) request
        actual_num_questions = min(pool_count, num_questions_to_check)
        self.context["actual_num_questions"] = actual_num_questions
        if pool_count < num_questions_to_check:
            logger.warning(
                f"User {user.id} requested {num_questions_to_check} level assessment qs, only {pool_count} available in selected sections. Using {actual_num_questions}."
            )

        self.context["sections_validated"] = sections
        self.context["relevant_subsection_slugs"] = relevant_subsection_slugs
        return data

    def create(self, validated_data):
        """Creates the UserTestAttempt record for the Level Assessment."""
        user = get_user_from_context(self.context)
        sections = self.context["sections_validated"]
        # Use the final validated/capped number of questions
        actual_num_questions = self.context["actual_num_questions"]
        subsection_slugs = self.context["relevant_subsection_slugs"]
        num_questions_originally_requested = (
            validated_data.get(
                "num_questions"  # This reflects the *original* request before potential capping in validate
            )
            if not self.context.get("capped_num_questions")
            else self.initial_data.get(
                "num_questions", DEFAULT_QUESTIONS_LEVEL_ASSESSMENT
            )
        )

        attempt_type = UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
        previous_attempts_count = UserTestAttempt.objects.filter(
            user=user, attempt_type=attempt_type
        ).count()
        attempt_number_for_type = previous_attempts_count + 1

        # Select final questions using get_filtered_questions
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=None,
            starred=False,
            not_mastered=False,
        )
        selected_question_ids = list(questions_queryset.values_list("id", flat=True))

        if len(selected_question_ids) != actual_num_questions:
            logger.error(
                f"Level Assessment Start: Failed to select required {actual_num_questions} questions after filtering for user {user.id}. Found {len(selected_question_ids)}."
            )
            raise serializers.ValidationError(
                _(
                    "Could not select the exact number of required questions. Please try again."
                )
            )

        # Create configuration snapshot for the attempt record
        config_snapshot = {
            "sections_requested": [s.slug for s in sections],
            "num_questions_requested": num_questions_originally_requested,  # Store original request
            "num_questions_used": actual_num_questions,  # Store actual used number
            "test_type": attempt_type,
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=attempt_type,
                test_configuration=config_snapshot,
                question_ids=selected_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
            logger.info(
                f"Started Level Assessment (Attempt ID: {test_attempt.id}) for user {user.id} with {len(selected_question_ids)} questions."
            )
        except Exception as e:
            logger.exception(
                f"Error creating Level Assessment UserTestAttempt for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the assessment.")]}
            )

        final_questions_queryset = test_attempt.get_questions_queryset()

        return {
            "attempt_id": test_attempt.id,
            "attempt_number_for_type": attempt_number_for_type,
            "questions": final_questions_queryset,
        }


class LevelAssessmentCompletionResponseSerializer(
    UserTestAttemptCompletionResponseSerializer
):
    """
    Specific response for Level Assessment completion.
    Inherits from the base completion response and ensures the profile is included.
    Mostly for documentation clarity, as the service populates the data.
    """

    # Inherits all fields from UserTestAttemptCompletionResponseSerializer
    # The 'updated_profile' field is already defined there as potentially nullable.
    # No additional fields needed unless specific level assessment outputs are required.
    pass
