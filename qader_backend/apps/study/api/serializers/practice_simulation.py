from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import logging

from apps.study.models import UserTestAttempt, Question
from apps.learning.models import LearningSubSection, Skill
from apps.api.utils import get_user_from_context
from apps.study.services import get_filtered_questions

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
        """Validates input and checks question availability."""
        user = get_user_from_context(self.context)

        # Check for ANY active 'started' attempt
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
        ).exists():
            raise serializers.ValidationError(
                {"non_field_errors": [_("You already have an ongoing test attempt.")]}
            )

        config = data["config"]
        requested_num = config["num_questions"]
        min_required = (
            self.fields["config"].fields["num_questions"].min_value
        )  # Access nested field min_value

        # Extract filter criteria from config
        subsection_slugs = [s.slug for s in config.get("subsections", [])]
        skill_slugs = [s.slug for s in config.get("skills", [])]
        starred = config.get("starred", False)
        not_mastered = config.get("not_mastered", False)

        try:
            # Use service to check question availability
            # Fetch one more than requested to gauge availability
            question_pool_qs = get_filtered_questions(
                user=user,
                limit=requested_num + 1,
                subsections=subsection_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
            )
            pool_count = question_pool_qs.count()  # Count the results

            if pool_count == 0:
                raise serializers.ValidationError(
                    {
                        "config": [
                            _(
                                "No active questions found matching the specified criteria."
                            )
                        ]
                    }
                )
            if pool_count < min_required:
                raise serializers.ValidationError(
                    {
                        "config": {
                            "num_questions": _(  # Target specific field
                                "Not enough questions ({count}) available for the minimum test size ({min_req}). Please adjust filters or number of questions."
                            ).format(count=pool_count, min_req=min_required)
                        }
                    }
                )

            actual_num_questions = min(pool_count, requested_num)
            self.context["actual_num_questions"] = actual_num_questions
            if pool_count < requested_num:
                logger.warning(
                    f"User {user.id} requested {requested_num} questions for {data['test_type']} but only {pool_count} available for config {config}. Proceeding with {actual_num_questions}."
                )

            # Pass validated config details for creation
            self.context["subsection_slugs"] = subsection_slugs
            self.context["skill_slugs"] = skill_slugs
            self.context["starred"] = starred
            self.context["not_mastered"] = not_mastered

        except serializers.ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(
                f"Error validating question availability for Practice/Simulation Start: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(
                _("Could not verify question availability. An internal error occurred.")
            )

        return data

    def create(self, validated_data):
        """Creates the UserTestAttempt record for the Practice/Simulation."""
        user = get_user_from_context(self.context)
        config = validated_data["config"]
        test_type = validated_data["test_type"]
        actual_num_questions = self.context["actual_num_questions"]

        # Use validated context filters
        subsection_slugs = self.context["subsection_slugs"]
        skill_slugs = self.context["skill_slugs"]
        starred = self.context["starred"]
        not_mastered = self.context["not_mastered"]

        # Fetch final questions using the service
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
        )
        question_ids = list(questions_queryset.values_list("id", flat=True))

        # Double-check count consistency
        if len(question_ids) != actual_num_questions:
            logger.error(
                f"Practice/Simulation Start: Failed to select required {actual_num_questions} questions after filtering for user {user.id}. Found {len(question_ids)}."
            )
            raise serializers.ValidationError(
                _(
                    "Could not select the exact number of required questions. Please try again."
                )
            )

        # Prepare configuration snapshot for the attempt record
        # Store slugs instead of full objects in JSON
        config_snapshot_data = {
            k: v for k, v in config.items() if k not in ["subsections", "skills"]
        }
        config_snapshot_data["subsections"] = subsection_slugs
        config_snapshot_data["skills"] = skill_slugs
        config_snapshot_data["actual_num_questions_selected"] = len(question_ids)

        # Nest the config under a 'config' key for consistency with Detail serializer
        full_snapshot = {
            "test_type": test_type,  # Store the specific type (practice/sim)
            "config": config_snapshot_data,
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=test_type,  # Set the attempt type on the model
                test_configuration=full_snapshot,
                question_ids=question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
            logger.info(
                f"Started {test_type.label} (Attempt ID: {test_attempt.id}) for user {user.id} with {len(question_ids)} questions."
            )
        except Exception as e:
            logger.exception(
                f"Error creating UserTestAttempt (Type: {test_type}) for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the test.")]}
            )

        # Fetch the actual Question objects for the response
        final_questions_queryset = test_attempt.get_questions_queryset()

        # Return data structured for the standard start response serializer
        return {
            "attempt_id": test_attempt.id,
            "questions": final_questions_queryset,
        }
