from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import logging

from apps.study.models import (
    UserTestAttempt,
    UserQuestionAttempt,
    Test,
    Question,
)  # Added Question
from apps.learning.models import LearningSubSection, Skill
from apps.learning.api.serializers import (
    QuestionListSerializer,
    LearningSubSectionSerializer,
    SkillSerializer,
)  # Added more imports
from apps.api.utils import get_user_from_context
from apps.study.services import get_filtered_questions

logger = logging.getLogger(__name__)

# Point constants handled by gamification signals/services


# Keep TestConfigSerializer
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
        ),
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


# Keep TestStartSerializer
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
        min_required = self.fields["config"].fields["num_questions"].min_value
        subsection_slugs = [s.slug for s in config.get("subsections", [])]
        skill_slugs = [s.slug for s in config.get("skills", [])]

        try:
            question_pool = get_filtered_questions(
                user=user,
                limit=requested_num + 1,
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

        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=config.get("starred", False),
            not_mastered=config.get("not_mastered", False),
        )
        question_ids = list(questions_queryset.values_list("id", flat=True))

        if len(question_ids) != actual_num_questions:
            logger.error(
                f"Failed to select required {actual_num_questions} questions for test start. Found {len(question_ids)}."
            )
            raise serializers.ValidationError(
                _("Could not select the exact number of required questions.")
            )

        config_snapshot_data = {
            k: v for k, v in config.items() if k not in ["subsections", "skills"]
        }
        config_snapshot_data["subsections"] = subsection_slugs
        config_snapshot_data["skills"] = skill_slugs
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

        final_questions_queryset = test_attempt.get_questions_queryset()
        return {"attempt_id": test_attempt.id, "questions": final_questions_queryset}


class TestStartResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(many=True, read_only=True)


class UserTestAttemptListSerializer(serializers.ModelSerializer):
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    answered_question_count = serializers.IntegerField(read_only=True)
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
            "answered_question_count",  # Added
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


class UserQuestionAttemptBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for answered questions within the detail view."""

    question_id = serializers.IntegerField(source="question.id")
    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )  # Added for context

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "question_id",
            "question_text",  # Added
            "selected_answer",
            "is_correct",
            "attempted_at",
        ]
        read_only_fields = fields


class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )  # Added display
    config_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    answered_question_count = serializers.IntegerField(read_only=True)  # Added
    # Show all questions included in the attempt
    included_questions = QuestionListSerializer(
        source="get_questions_queryset", many=True, read_only=True
    )
    # Show questions already answered by the user (for ongoing tests)
    attempted_questions = UserQuestionAttemptBriefSerializer(
        source="question_attempts", many=True, read_only=True  # Use the related name
    )
    results_summary = serializers.JSONField(
        read_only=True
    )  # Only populated if COMPLETED
    configuration = serializers.JSONField(source="test_configuration", read_only=True)

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "status",  # Keep raw status
            "status_display",  # Add display status
            "config_name",
            "date",
            "start_time",  # Added for clarity
            "end_time",  # Added for clarity
            "num_questions",
            "answered_question_count",  # Added
            "score_percentage",  # Only populated if COMPLETED
            "score_verbal",
            "score_quantitative",
            "included_questions",  # Renamed from 'questions'
            "attempted_questions",  # Added
            "results_summary",
            "configuration",
        ]
        read_only_fields = fields

    def get_config_name(self, obj):
        config = obj.test_configuration or {}
        # Adjust path based on actual snapshot structure
        return (
            config.get("config", {}).get("name")
            or config.get("name")
            or _("Unnamed Test")
        )
