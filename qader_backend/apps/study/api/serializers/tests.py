from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError,
from django.db import transaction  # Keep transaction import if used in serializer save
from django.utils import timezone
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import Question, LearningSubSection, Skill
from apps.learning.api.serializers import QuestionListSerializer
from apps.users.models import UserProfile
from apps.api.utils import get_user_from_context

# Import the specific service function needed
from apps.study.services import (
    get_filtered_questions,
    record_test_submission,  # Import the new service function
)

logger = logging.getLogger(__name__)

# --- Constants ---
# Point constants handled by gamification signals/services

# --- General Test Serializers ---


# TestConfigSerializer remains the same
class TestConfigSerializer(serializers.Serializer):
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
        ),  # Ensure Skill has is_active field or adjust filter
        required=False,
        allow_empty=True,
        help_text=_("List of specific active skill slugs to include"),
    )
    num_questions = serializers.IntegerField(
        min_value=1,
        max_value=150,
        required=True,
        help_text=_("Number of questions for the test"),
    )
    starred = serializers.BooleanField(
        default=False, help_text=_("Include only questions starred by the user?")
    )
    not_mastered = serializers.BooleanField(
        default=False,
        help_text=_("Include questions from skills the user hasn't mastered?"),
    )
    full_simulation = serializers.BooleanField(
        default=False, help_text=_("Is this a full timed simulation test?")
    )

    def validate(self, data):
        has_subsections = bool(data.get("subsections"))
        has_skills = bool(data.get("skills"))
        is_starred = data.get("starred", False)
        is_not_mastered = data.get("not_mastered", False)

        if (
            not has_subsections
            and not has_skills
            and not is_starred
            and not is_not_mastered
        ):
            raise serializers.ValidationError(
                _(
                    "Must specify subsections, skills, filter by starred, or filter by not mastered questions."
                )
            )

        if has_subsections and has_skills:
            subsection_ids = {s.id for s in data["subsections"]}
            invalid_skills = [
                skill.name
                for skill in data["skills"]
                if skill.subsection_id not in subsection_ids
            ]
            if invalid_skills:
                raise serializers.ValidationError(
                    {
                        "skills": _(
                            "Selected skills do not belong to the selected subsections: {}"
                        ).format(", ".join(invalid_skills))
                    }
                )
        return data


# TestStartSerializer remains the same (uses get_filtered_questions service)
class TestStartSerializer(serializers.Serializer):
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
    )
    config = TestConfigSerializer(required=True)

    def validate(self, data):
        user = get_user_from_context(self.context)
        config = data["config"]
        requested_num = config["num_questions"]
        min_required = self.fields["config"].fields["num_questions"].min_value
        subsection_slugs = [s.slug for s in config.get("subsections", [])]
        skill_slugs = [s.slug for s in config.get("skills", [])]

        try:
            # Use service to check availability
            question_pool = get_filtered_questions(
                user=user,
                limit=requested_num + 1,  # Check if > requested exist
                subsections=subsection_slugs,
                skills=skill_slugs,
                starred=config.get("starred", False),
                not_mastered=config.get("not_mastered", False),
            )
            pool_count = question_pool.count()

            if pool_count == 0:
                raise serializers.ValidationError(
                    _("No active questions found matching the specified criteria.")
                )
            if pool_count < min_required:
                raise serializers.ValidationError(
                    _(
                        "Not enough questions ({count}) available for the minimum test size ({min_req})."
                    ).format(count=pool_count, min_req=min_required)
                )

            actual_num_questions = min(pool_count, requested_num)
            self.context["actual_num_questions"] = actual_num_questions
            if pool_count < requested_num:
                logger.warning(
                    f"User {user.id} requested {requested_num} questions but only {pool_count} available for config {config}. Proceeding with {actual_num_questions}."
                )

        except serializers.ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Error validating question availability for TestStartSerializer: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(
                _("Could not verify question availability.")
            )

        return data

    def create(self, validated_data):
        user = get_user_from_context(self.context)
        config = validated_data["config"]
        test_type = validated_data["test_type"]
        actual_num_questions = self.context["actual_num_questions"]
        subsection_slugs = [s.slug for s in config.get("subsections", [])]
        skill_slugs = [s.slug for s in config.get("skills", [])]

        # Select final questions using the service
        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=config.get("starred", False),
            not_mastered=config.get("not_mastered", False),
        )
        question_ids = list(questions_queryset.values_list("id", flat=True))

        if len(question_ids) < actual_num_questions:
            logger.error(
                f"Failed to select the required number of questions ({actual_num_questions}) for test start. Found {len(question_ids)}."
            )
            raise serializers.ValidationError(
                _("Failed to select sufficient questions.")
            )

        # Create config snapshot
        config_snapshot_data = {
            k: v for k, v in config.items() if k != "subsections" and k != "skills"
        }  # Copy basic config
        config_snapshot_data["subsections"] = subsection_slugs  # Store slugs
        config_snapshot_data["skills"] = skill_slugs  # Store slugs
        config_snapshot_data["actual_num_questions_selected"] = len(question_ids)
        full_snapshot = {"test_type": test_type, "config": config_snapshot_data}

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=test_type,
                test_configuration=full_snapshot,
                question_ids=question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating UserTestAttempt (Type: {test_type}) for user {user.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the test.")]}
            )

        # Reload queryset based on final IDs for the response
        final_questions_queryset = test_attempt.get_questions_queryset()
        return {"attempt_id": test_attempt.id, "questions": final_questions_queryset}


# TestStartResponseSerializer remains the same
class TestStartResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(many=True, read_only=True)


# UserTestAttemptListSerializer remains the same
class UserTestAttemptListSerializer(serializers.ModelSerializer):
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    date = serializers.DateTimeField(source="start_time", read_only=True)
    performance = serializers.SerializerMethodField()
    attempt_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "date",
            "num_questions",
            "score_percentage",
            "status",
            "performance",
        ]
        read_only_fields = fields

    def get_performance(self, obj):
        perf = {}
        if obj.score_percentage is not None:
            perf["overall"] = round(obj.score_percentage, 1)
        if obj.score_verbal is not None:
            perf["verbal"] = round(obj.score_verbal, 1)
        if obj.score_quantitative is not None:
            perf["quantitative"] = round(obj.score_quantitative, 1)
        return perf if perf else None


# UserTestAttemptDetailSerializer remains the same
class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    config_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(
        source="get_questions_queryset", many=True, read_only=True
    )
    results_summary = serializers.JSONField(read_only=True)
    configuration = serializers.JSONField(source="test_configuration", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "config_name",
            "date",
            "num_questions",
            "score_percentage",
            "status",
            "questions",
            "results_summary",
            "configuration",
        ]
        read_only_fields = fields

    def get_config_name(self, obj):
        config = obj.test_configuration or {}
        return config.get("config", {}).get("name", None)


# TestAnswerSerializer remains the same
class TestAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


class TestSubmitSerializer(serializers.Serializer):
    """Handles submission for Practice and Simulation tests."""

    answers = TestAnswerSerializer(many=True, min_length=1)

    def validate(self, data):
        """Validates the attempt and answer structure."""
        user = get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = view.kwargs.get("attempt_id") if view else None

        if not attempt_id:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Test attempt ID missing.")]}
            )

        try:
            test_attempt = UserTestAttempt.objects.select_related(
                "user"
            ).get(  # user needed for logs/profile
                pk=attempt_id, user=user, status=UserTestAttempt.Status.STARTED
            )
            # Prevent submitting level assessments via this endpoint
            if (
                test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Use the level assessment submission endpoint.")
                        ]
                    }
                )
        except UserTestAttempt.DoesNotExist:
            # Check if attempt exists but wrong status/owner/type
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                existing = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                if existing.status != UserTestAttempt.Status.STARTED:
                    error_msg = _(
                        "This test attempt has already been submitted or abandoned."
                    )
                elif (
                    existing.attempt_type
                    == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
                ):
                    error_msg = _("Use the level assessment submission endpoint.")
                else:
                    error_msg = _(
                        "Cannot submit this test attempt."
                    )  # Should not happen
                raise serializers.ValidationError({"non_field_errors": [error_msg]})
            else:
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Test attempt not found or does not belong to you.")
                        ]
                    }
                )

        # Validate Answers count and IDs
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
        """Calls the service function to process the test submission."""
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]

        try:
            # Call the service function (transaction handled within the service)
            result_data = record_test_submission(
                test_attempt=test_attempt, answers_data=answers_data
            )
            return result_data
        except ValidationError as e:
            # Re-raise validation errors from the service
            raise e
        except Exception as e:
            # Catch unexpected errors from the service
            logger.exception(
                f"Unexpected error during test submission service call for attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("An internal error occurred during submission.")
                    ]
                }
            )


# TestSubmitResponseSerializer remains the same
class TestSubmitResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    smart_analysis = serializers.CharField()
    message = serializers.CharField()
