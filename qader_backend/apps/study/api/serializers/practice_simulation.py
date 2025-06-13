from django.conf import settings
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, Question
from apps.learning.models import LearningSubSection, Skill
from apps.api.utils import get_user_from_context


logger = logging.getLogger(__name__)

# --- Constants ---
MIN_QUESTIONS_PRACTICE = getattr(settings, "MIN_QUESTIONS_PRACTICE", 1)
MAX_QUESTIONS_PRACTICE = getattr(settings, "MAX_QUESTIONS_PRACTICE", 100)


class PracticeSimulationConfigSerializer(serializers.Serializer):
    """Configuration options for starting a Practice or Simulation Test."""

    name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text=_("Optional name for this custom test configuration."),
    )
    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSubSection.objects.all(),
            help_text=_("Slug of the subsection."),
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of subsection slugs to filter questions by."),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=Skill.objects.filter(is_active=True),
            help_text=_("Slug of the active skill."),
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of specific active skill slugs to filter questions by."),
    )
    num_questions = serializers.IntegerField(
        min_value=MIN_QUESTIONS_PRACTICE,
        max_value=MAX_QUESTIONS_PRACTICE,
        required=True,
        help_text=_("Number of questions for the test."),
    )
    starred = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Include only questions starred by the user?"),
    )
    not_mastered = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Include only questions from skills the user hasn't mastered?"),
    )

    def validate(self, data):
        """Ensures valid combination of filters and checks skill/subsection relationship."""
        subsections = data.get("subsections", [])
        skills = data.get("skills", [])
        is_starred = data.get("starred", False)
        is_not_mastered = data.get("not_mastered", False)

        # Must have at least one filter criteria if not relying solely on num_questions
        # (get_filtered_questions handles no filters, returning random questions)
        # This check might be too strict depending on desired behavior. Let's allow no filters.
        # if not subsections and not skills and not is_starred and not is_not_mastered:
        #     raise serializers.ValidationError(
        #         _("Must specify at least one filter criteria: subsections, skills, starred, or not mastered questions.")
        #     )

        # Validate skills belong to selected subsections if both are provided
        if subsections and skills:
            subsection_ids = {s.id for s in subsections}
            provided_skill_slugs = {sk.slug for sk in skills}

            # Fetch skills that match slugs AND belong to the selected subsections
            valid_skills_in_subsections = Skill.objects.filter(
                slug__in=provided_skill_slugs,
                is_active=True,  # Already filtered by SlugRelatedField queryset, but double check
                subsection_id__in=subsection_ids,
            ).values_list("slug", flat=True)

            invalid_skill_slugs = provided_skill_slugs - set(
                valid_skills_in_subsections
            )

            if invalid_skill_slugs:
                # Fetch names for a more user-friendly error message
                invalid_skill_details = Skill.objects.filter(
                    slug__in=invalid_skill_slugs
                ).values("name", "subsection__name")
                error_details = [
                    f"'{d['name']}' (in subsection '{d['subsection__name']}')"
                    for d in invalid_skill_details
                ]
                raise serializers.ValidationError(
                    {
                        "skills": _(
                            "Selected skills do not belong to the selected subsections: {}"
                        ).format(", ".join(error_details))
                    }
                )
        return data


class PracticeSimulationStartSerializer(serializers.Serializer):
    """Serializer for validating input to start a Practice or Simulation test."""

    test_type = serializers.ChoiceField(
        choices=[
            (
                UserTestAttempt.AttemptType.PRACTICE,
                UserTestAttempt.AttemptType.PRACTICE.label,
            ),
            (
                UserTestAttempt.AttemptType.SIMULATION,
                UserTestAttempt.AttemptType.SIMULATION.label,
            ),
        ],
        required=True,
        help_text=_("Specify whether this is a 'practice' or 'simulation' test."),
    )
    # Embed the configuration options using the nested serializer
    config = PracticeSimulationConfigSerializer(required=True)

    def validate(self, data):
        """Performs basic validation and checks for active attempts."""

        # Further validation (limits, question availability) handled by the service.
        return data
