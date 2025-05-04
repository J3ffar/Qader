from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt
from apps.learning.models import LearningSection, LearningSubSection, Question

# Use the unified response serializer
from apps.study.api.serializers.attempts import (
    UserTestAttemptCompletionResponseSerializer,
)
from apps.api.utils import get_user_from_context  # Helper to get user

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "DEFAULT_QUESTIONS_LEVEL_ASSESSMENT", 30
)
MIN_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "MIN_QUESTIONS_LEVEL_ASSESSMENT", 5
)  # Example minimum
MAX_QUESTIONS_LEVEL_ASSESSMENT = getattr(
    settings, "MAX_QUESTIONS_LEVEL_ASSESSMENT", 100
)  # Example maximum

# --- Level Assessment Specific Serializers ---


class LevelAssessmentStartSerializer(serializers.Serializer):
    """Serializer for validating input to start a Level Assessment test."""

    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSection.objects.all(),  # Validate against existing sections
            help_text=_("Slug of the learning section (e.g., 'verbal')."),
        ),
        min_length=1,
        required=True,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        min_value=MIN_QUESTIONS_LEVEL_ASSESSMENT,
        max_value=MAX_QUESTIONS_LEVEL_ASSESSMENT,
        default=DEFAULT_QUESTIONS_LEVEL_ASSESSMENT,
        required=False,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        """Performs basic validation and checks for active attempts."""
        user = get_user_from_context(self.context)

        # Check for ANY active 'started' attempt right away (quick check)
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "You already have an ongoing test attempt. Please complete or cancel it first."
                        )
                    ]
                }
            )

        # Further validation (like usage limits, question availability)
        # will be handled by the service function called by the view.
        # Keep serializer validation focused on input shape and basic constraints.

        return data


class LevelAssessmentCompletionResponseSerializer(
    UserTestAttemptCompletionResponseSerializer
):
    """
    Specific response for Level Assessment completion.
    Inherits from the base completion response. No extra fields needed here,
    but defining it helps with documentation/schema generation.
    The `updated_profile` field from the base class will be populated by the service/view.
    """

    pass
