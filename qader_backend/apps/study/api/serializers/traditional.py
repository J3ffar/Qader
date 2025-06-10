from django.conf import settings
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, Question, UserQuestionAttempt
from apps.learning.models import LearningSubSection, Skill

# Use unified serializers where appropriate
from apps.learning.api.serializers import UnifiedQuestionSerializer
from apps.study.api.serializers.attempts import UserTestAttemptStartResponseSerializer
from apps.api.utils import get_user_from_context

logger = logging.getLogger(__name__)

# --- Constants ---
MIN_QUESTIONS_TRADITIONAL_INITIAL = getattr(
    settings, "MIN_QUESTIONS_TRADITIONAL_INITIAL", 0
)  # Can start with 0 initial
MAX_QUESTIONS_TRADITIONAL_INITIAL = getattr(
    settings, "MAX_QUESTIONS_TRADITIONAL_INITIAL", 50
)  # Max initial fetch
DEFAULT_QUESTIONS_TRADITIONAL_INITIAL = getattr(
    settings, "DEFAULT_QUESTIONS_TRADITIONAL_INITIAL", 10
)


class TraditionalPracticeStartSerializer(serializers.Serializer):
    """Serializer for validating input to start a traditional practice session."""

    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSubSection.objects.all(),
            help_text=_("Slug of the subsection."),
        ),
        required=False,
        allow_empty=True,
        help_text=_("Optional: Filter initial questions by these subsection slugs."),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=Skill.objects.filter(is_active=True),
            help_text=_("Slug of the active skill."),
        ),
        required=False,
        allow_empty=True,
        help_text=_("Optional: Filter initial questions by these active skill slugs."),
    )
    num_questions = serializers.IntegerField(
        min_value=MIN_QUESTIONS_TRADITIONAL_INITIAL,
        max_value=MAX_QUESTIONS_TRADITIONAL_INITIAL,
        default=DEFAULT_QUESTIONS_TRADITIONAL_INITIAL,
        required=False,
        help_text=_(
            "Number of questions to fetch initially for the session (can be 0)."
        ),
    )
    starred = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Filter initial questions to only starred ones?"),
    )
    not_mastered = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Filter initial questions to skills not yet mastered?"),
    )

    def validate(self, data):
        """Performs basic validation and checks for active attempts."""
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

        # Validate skill/subsection relationship if both provided (similar to Practice/Sim)
        subsections = data.get("subsections", [])
        skills = data.get("skills", [])
        if subsections and skills:
            subsection_ids = {s.id for s in subsections}
            provided_skill_slugs = {sk.slug for sk in skills}
            valid_skills_in_subsections = Skill.objects.filter(
                slug__in=provided_skill_slugs,
                is_active=True,
                subsection_id__in=subsection_ids,
            ).values_list("slug", flat=True)
            invalid_skill_slugs = provided_skill_slugs - set(
                valid_skills_in_subsections
            )
            if invalid_skill_slugs:
                invalid_skills_names = Skill.objects.filter(
                    slug__in=invalid_skill_slugs
                ).values_list("name", flat=True)
                raise serializers.ValidationError(
                    {
                        "skills": _(
                            "Selected skills do not belong to the selected subsections: {}"
                        ).format(", ".join(invalid_skills_names))
                    }
                )

        # Further validation (usage limits) handled by the service.
        return data


# Response uses the unified UserTestAttemptStartResponseSerializer structure


class TraditionalPracticeStartResponseSerializer(serializers.Serializer):
    """Specific response structure after starting a traditional practice session."""

    attempt_id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)  # e.g., "started"
    attempt_number_for_type = serializers.IntegerField(
        read_only=True,
        help_text=_("The sequence number of this attempt for traditional practice."),
    )
    # The initial list of questions fetched (can be empty)
    questions = UnifiedQuestionSerializer(many=True, read_only=True)


# --- Serializers for Traditional Actions (Hints/Reveals) ---


class HintResponseSerializer(serializers.Serializer):
    """Response containing the hint for a question."""

    question_id = serializers.IntegerField(read_only=True)
    hint = serializers.CharField(read_only=True, allow_null=True)


class RevealCorrectAnswerResponseSerializer(serializers.Serializer):
    """Response containing only the correct answer choice."""

    question_id = serializers.IntegerField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)  # e.g., "A", "B"


class RevealExplanationResponseSerializer(serializers.Serializer):
    """Response containing only the explanation."""

    question_id = serializers.IntegerField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
