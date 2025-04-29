from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, Question
from apps.learning.models import LearningSubSection, Skill
from apps.api.utils import get_user_from_context
from apps.study.services import get_filtered_questions
from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter

logger = logging.getLogger(__name__)


class PracticeSimulationConfigSerializer(serializers.Serializer):
    """Configuration options for starting a Practice or Simulation Test."""

    name = serializers.CharField(
        max_length=255,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text=_("Optional name for a custom test"),
    )
    subsections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=LearningSubSection.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of subsection slugs to include"),
    )
    skills = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug", queryset=Skill.objects.filter(is_active=True)
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of specific active skill slugs to include"),
    )
    num_questions = serializers.IntegerField(
        min_value=1,
        max_value=150,  # Max questions per test
        required=True,
        help_text=_("Number of questions for the test"),
    )
    starred = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Include only questions starred by the user?"),
    )
    not_mastered = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_("Include questions from skills the user hasn't mastered?"),
    )
    # Note: 'full_simulation' flag is part of the parent serializer (TestStartSerializer)

    def validate(self, data):
        """Ensures valid combination of filters."""
        has_subsections = bool(data.get("subsections"))
        has_skills = bool(data.get("skills"))
        is_starred = data.get("starred", False)
        is_not_mastered = data.get("not_mastered", False)

        # Must have at least one filter criteria
        if (
            not has_subsections
            and not has_skills
            and not is_starred
            and not is_not_mastered
        ):
            raise serializers.ValidationError(
                _(
                    "Must specify at least one filter: subsections, skills, starred, or not mastered questions."
                )
            )

        # Validate skills belong to selected subsections if both are provided
        if has_subsections and has_skills:
            subsection_ids = {s.id for s in data["subsections"]}
            # Check if skills are active AND belong to the selected subsections
            valid_skills = Skill.objects.filter(
                slug__in=[sk.slug for sk in data["skills"]],
                is_active=True,
                subsection_id__in=subsection_ids,
            ).values_list("slug", flat=True)

            provided_skill_slugs = {sk.slug for sk in data["skills"]}
            invalid_skill_slugs = provided_skill_slugs - set(valid_skills)

            if invalid_skill_slugs:
                # Fetch names for better error message
                invalid_skills_names = Skill.objects.filter(
                    slug__in=invalid_skill_slugs
                ).values_list("name", flat=True)
                raise serializers.ValidationError(
                    {
                        "skills": _(
                            "Selected skills do not belong to the selected subsections or are inactive: {}"
                        ).format(", ".join(invalid_skills_names))
                    }
                )
        return data


class PracticeSimulationStartSerializer(serializers.Serializer):
    """Serializer for starting a Practice or Simulation test."""

    # Determine if it's Practice or Simulation via this field
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
        help_text=_("Specify whether this is a Practice Test or a Full Simulation."),
    )
    # Embed the configuration options
    config = PracticeSimulationConfigSerializer(required=True)

    def validate(self, data):
        """Validate input, check limits, check question availability."""
        user = get_user_from_context(self.context)

        # Check for ANY active 'started' attempt
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": [_("You already have an ongoing test attempt.")]}
            )

        attempt_type = data["attempt_type"]

        # --- Usage Limit Checks ---
        try:
            limiter = UsageLimiter(user)
            # 1. Check if allowed to start this type of attempt
            limiter.check_can_start_test_attempt(attempt_type)

            # 2. Check and cap number of questions
            requested_questions = data.get("num_questions", 20)
            max_allowed_questions = limiter.get_max_questions_per_attempt()

            if (
                max_allowed_questions is not None
                and requested_questions > max_allowed_questions
            ):
                logger.info(
                    f"User {user.id} requested {requested_questions} practice/sim questions, capped at {max_allowed_questions} due to plan limits."
                )
                data["num_questions"] = max_allowed_questions
                self.context["capped_num_questions"] = True

        except UsageLimitExceeded as e:
            raise serializers.ValidationError({"non_field_errors": [str(e)]})
        except ValueError as e:  # Catch UsageLimiter init error
            logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
            raise serializers.ValidationError(
                {"non_field_errors": ["Could not verify account limits."]}
            )
        # --- End Usage Limit Checks ---

        # Check question availability
        num_questions_to_check = data["num_questions"]  # Use potentially capped number
        min_required = self.fields["num_questions"].min_value

        subsection_slugs = [s.slug for s in data.get("subsections", [])]
        skill_slugs = [s.slug for s in data.get("skills", [])]
        starred = data.get("starred", False)
        not_mastered = data.get("not_mastered", False)

        question_pool_qs = get_filtered_questions(
            user=user,
            limit=num_questions_to_check + 1,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
        )
        pool_count = question_pool_qs.count()

        if pool_count < min_required:
            raise serializers.ValidationError(
                {
                    "num_questions": [
                        _(
                            "Not enough active questions ({count}) found matching your criteria to meet the minimum ({min_req}). Please adjust filters or request fewer questions."
                        ).format(count=pool_count, min_req=min_required)
                    ]
                }
            )

        actual_num_questions = min(pool_count, num_questions_to_check)
        self.context["actual_num_questions"] = actual_num_questions
        if pool_count < num_questions_to_check:
            logger.warning(
                f"User {user.id} requested {num_questions_to_check} practice/sim qs, only {pool_count} available matching filters. Using {actual_num_questions}."
            )

        self.context["subsection_slugs"] = subsection_slugs
        self.context["skill_slugs"] = skill_slugs
        self.context["starred"] = starred
        self.context["not_mastered"] = not_mastered
        self.context["attempt_type"] = attempt_type
        self.context["name"] = data.get("name", "")
        return data

    def create(self, validated_data):
        """Creates the Practice/Simulation UserTestAttempt."""
        user = get_user_from_context(self.context)
        actual_num_questions = self.context["actual_num_questions"]
        subsection_slugs = self.context["subsection_slugs"]
        skill_slugs = self.context["skill_slugs"]
        starred = self.context["starred"]
        not_mastered = self.context["not_mastered"]
        attempt_type = self.context["attempt_type"]
        name = self.context["name"]
        num_questions_originally_requested = (
            validated_data.get("num_questions")
            if not self.context.get("capped_num_questions")
            else self.initial_data.get("num_questions", 20)
        )

        # Fetch final questions
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
        )
        selected_question_ids = list(questions_queryset.values_list("id", flat=True))

        if len(selected_question_ids) != actual_num_questions:
            logger.error(
                f"Practice/Sim Start: Failed to select required {actual_num_questions} questions after filtering for user {user.id}. Found {len(selected_question_ids)}."
            )
            raise serializers.ValidationError(
                _(
                    "Could not select the exact number of required questions. Please try again."
                )
            )

        # Create config snapshot
        # Store the actual config used, not just the request data
        config_used = {
            "name": name,
            "subsections": subsection_slugs,
            "skills": skill_slugs,
            "starred": starred,
            "not_mastered": not_mastered,
            "num_questions_requested": num_questions_originally_requested,
            "num_questions_used": actual_num_questions,
        }
        config_snapshot = {
            "config": config_used,
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
                f"Started {attempt_type.label} (Attempt ID: {test_attempt.id}) for user {user.id} with {len(selected_question_ids)} questions."
            )
        except Exception as e:
            logger.exception(
                f"Error creating {attempt_type.label} UserTestAttempt for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the test.")]}
            )

        final_questions_queryset = test_attempt.get_questions_queryset()

        return {
            "attempt_id": test_attempt.id,
            "questions": final_questions_queryset,
        }
