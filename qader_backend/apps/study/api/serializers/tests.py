# qader_backend/apps/study/api/serializers/tests.py

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging

from apps.study.models import UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import Question, LearningSubSection, Skill
from apps.learning.api.serializers import QuestionListSerializer
from apps.users.models import UserProfile
from apps.api.utils import get_user_from_context

# Import only needed services
from apps.study.services import (
    get_filtered_questions,
    update_user_skill_proficiency,
)

logger = logging.getLogger(__name__)

# --- Constants ---
# Point constants handled by gamification signals/services

# --- General Test Serializers ---


# TestConfigSerializer remains the same
class TestConfigSerializer(serializers.Serializer):
    """Validates the 'config' part of the test start request."""

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
            slug_field="slug",
            queryset=Skill.objects.filter(),  # Filter active skills
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
        # Check if at least one filter criteria is provided
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

        # Check if skills selected belong to subsections selected (if both are provided)
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


# TestStartSerializer remains the same
class TestStartSerializer(serializers.Serializer):
    """Validates the request to start a new test (practice, custom, simulation)."""

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

        # --- Check Question Availability using Service ---
        try:
            # Extract slugs/ids correctly
            subsection_slugs = [s.slug for s in config.get("subsections", [])]
            skill_slugs = [s.slug for s in config.get("skills", [])]

            question_pool = get_filtered_questions(
                user=user,
                limit=config["num_questions"]
                + 1,  # Check if *at least* num_questions exist
                subsections=subsection_slugs,
                skills=skill_slugs,
                starred=config.get("starred", False),
                not_mastered=config.get("not_mastered", False),
                exclude_ids=None,
            )
            pool_count = question_pool.count()

            if pool_count == 0:
                raise serializers.ValidationError(
                    _("No active questions found matching the specified criteria.")
                )

            requested_num = config["num_questions"]
            min_required = self.fields["config"].fields["num_questions"].min_value
            if pool_count < min_required:
                raise serializers.ValidationError(
                    _(
                        "Not enough questions ({count}) available for the minimum test size ({min_req})."
                    ).format(count=pool_count, min_req=min_required)
                )

            if pool_count < requested_num:
                logger.warning(
                    f"User {user.id} requested {requested_num} questions but only {pool_count} available for config {config}. Proceeding with {pool_count}."
                )
                self.context["actual_num_questions"] = pool_count
            else:
                self.context["actual_num_questions"] = requested_num

        except serializers.ValidationError:
            raise  # Re-raise validation errors
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

        # --- Select Questions using Service Function ---
        subsection_slugs = [s.slug for s in config.get("subsections", [])]
        skill_slugs = [s.slug for s in config.get("skills", [])]

        questions_queryset = get_filtered_questions(
            user=user,
            limit=actual_num_questions,
            subsections=subsection_slugs,
            skills=skill_slugs,
            starred=config.get("starred", False),
            not_mastered=config.get("not_mastered", False),
            exclude_ids=None,
        )
        question_ids = list(questions_queryset.values_list("id", flat=True))

        if not question_ids or len(question_ids) < actual_num_questions:
            # Should be caught by validation, but double check
            logger.error(
                f"Failed to select the required number of questions ({actual_num_questions}) for test start. Found {len(question_ids)}."
            )
            raise serializers.ValidationError(
                _("Failed to select sufficient questions.")
            )

        # --- Create Test Attempt ---
        # Create a snapshot, converting model instances to slugs/ids
        config_snapshot_data = {
            "name": config.get("name"),
            "subsections": subsection_slugs,
            "skills": skill_slugs,
            "num_questions": config["num_questions"],  # Store requested number
            "starred": config.get("starred", False),
            "not_mastered": config.get("not_mastered", False),
            "full_simulation": config.get("full_simulation", False),
            "actual_num_questions_selected": len(question_ids),  # Store actual number
        }
        # Include test_type in snapshot for consistency
        full_snapshot = {
            "test_type": test_type,
            "config": config_snapshot_data,
        }

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

        # --- Prepare Response Data ---
        # Reload queryset based on the final selected IDs to pass to serializer
        final_questions_queryset = test_attempt.get_questions_queryset()
        return {
            "attempt_id": test_attempt.id,
            "questions": final_questions_queryset,
        }


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
        if obj.score_verbal is not None:
            perf["verbal"] = round(obj.score_verbal, 1)  # Round for display
        if obj.score_quantitative is not None:
            perf["quantitative"] = round(obj.score_quantitative, 1)  # Round for display
        # Add overall score here as well for consistency?
        if obj.score_percentage is not None:
            perf["overall"] = round(obj.score_percentage, 1)

        return perf if perf else None


# UserTestAttemptDetailSerializer remains the same
class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.CharField(source="get_attempt_type_display", read_only=True)
    config_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)
    # Pass context to nested serializer if needed
    questions = QuestionListSerializer(
        source="get_questions_queryset",
        many=True,
        read_only=True,
        context={"is_detail_view": True},  # Add context if QLS needs it
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
        # Safely access nested dictionary
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
    answers = TestAnswerSerializer(many=True, min_length=1)

    def validate(self, data):
        user = get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = view.kwargs.get("attempt_id") if view else None

        if not attempt_id:
            raise serializers.ValidationError(
                {"non_field_errors": [_("Test attempt ID missing.")]}
            )

        # --- Fetch and Validate Test Attempt ---
        try:
            # Added select_related user__profile
            test_attempt = UserTestAttempt.objects.select_related("user__profile").get(
                pk=attempt_id,
                user=user,
                status=UserTestAttempt.Status.STARTED,  # Can only submit 'started' tests
            )
            # Ensure it's not a Level Assessment attempt submitted via this endpoint
            if (
                test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _(
                                "Use the specific level assessment submission endpoint for this type of attempt."
                            )
                        ]
                    }
                )
        except UserTestAttempt.DoesNotExist:
            # Provide more context if attempt exists but has wrong status/owner
            if UserTestAttempt.objects.filter(pk=attempt_id, user=user).exists():
                existing_attempt = UserTestAttempt.objects.get(pk=attempt_id, user=user)
                if existing_attempt.status != UserTestAttempt.Status.STARTED:
                    error_msg = _(
                        "This test attempt has already been submitted or abandoned."
                    )
                elif (
                    existing_attempt.attempt_type
                    == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
                ):
                    error_msg = _(
                        "Use the level assessment submission endpoint for this attempt."
                    )
                else:  # Should not happen
                    error_msg = _("Cannot submit this test attempt.")
                raise serializers.ValidationError({"non_field_errors": [error_msg]})
            else:
                # Attempt ID is invalid or doesn't belong to user
                raise serializers.ValidationError(
                    {
                        "non_field_errors": [
                            _("Test attempt not found or does not belong to you.")
                        ]
                    }
                )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for user {user.id} during test submission."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error during submission.")]}
            )

        # --- Validate Answers ---
        submitted_answers_data = data["answers"]
        submitted_question_ids = {
            answer["question_id"] for answer in submitted_answers_data
        }
        expected_question_ids = set(test_attempt.question_ids)

        if len(submitted_answers_data) != len(expected_question_ids):
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Incorrect number of answers submitted. Expected {expected}, got {actual}."
                        ).format(
                            expected=len(expected_question_ids),
                            actual=len(submitted_answers_data),
                        )
                    ]
                }
            )

        if submitted_question_ids != expected_question_ids:
            missing = sorted(list(expected_question_ids - submitted_question_ids))
            extra = sorted(list(submitted_question_ids - expected_question_ids))
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = missing
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = extra
            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Mismatch between submitted answers and questions in the test attempt."
                        ),
                        error_detail,
                    ]
                }
            )

        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic
    def save(self, **kwargs):
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user
        profile = user.profile  # Assumed exists

        # --- Fetch questions ---
        questions_in_attempt = test_attempt.get_questions_queryset()
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records and update proficiency ---
        attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:
                logger.error(
                    f"Question ID {question_id} from submit data not found for test attempt {test_attempt.id}"
                )
                raise serializers.ValidationError(
                    _("Internal error: Invalid question ID found during submission.")
                )

            is_correct = answer_data["selected_answer"] == question.correct_answer

            # Determine mode based on attempt type
            mode = UserQuestionAttempt.Mode.TEST  # Default for Practice/Simulation

            attempts_to_create.append(
                UserQuestionAttempt(
                    user=user,
                    question=question,
                    test_attempt=test_attempt,
                    selected_answer=answer_data["selected_answer"],
                    is_correct=is_correct,
                    time_taken_seconds=answer_data.get("time_taken_seconds"),
                    mode=mode,
                )
            )
            # Update proficiency immediately (remains synchronous)
            update_user_skill_proficiency(
                user=user, skill=question.skill, is_correct=is_correct
            )

        try:
            created_attempts = UserQuestionAttempt.objects.bulk_create(
                attempts_to_create
            )
            # Fetch attempts with related data needed for scoring
            created_attempt_ids = [attempt.id for attempt in created_attempts]
            attempts_for_scoring = list(
                UserQuestionAttempt.objects.filter(
                    id__in=created_attempt_ids
                ).select_related(
                    "question__subsection__section"  # Needed for score calculation
                )
            )
        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for test attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save test answers.")]}
            )

        # --- Calculate and Save Scores using Model Method ---
        test_attempt.calculate_and_save_scores(attempts_for_scoring)

        # --- Mark Test Complete ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        # Note: completion_points_awarded flag will be set by the signal receiver
        test_attempt.save(update_fields=["status", "end_time", "updated_at"])

        # --- Generate Smart Analysis (Example) ---
        results_summary = test_attempt.results_summary or {}
        weak_areas = [
            d["name"] for d in results_summary.values() if d.get("score", 100) < 60
        ]
        strong_areas = [
            d["name"] for d in results_summary.values() if d.get("score", 0) >= 85
        ]

        smart_analysis = _("Test completed!")
        if weak_areas:
            smart_analysis += " " + _("Consider focusing more on: {}.").format(
                ", ".join(weak_areas)
            )
        if strong_areas:
            smart_analysis += " " + _(
                "You showed strong performance in: {}. Keep it up!"
            ).format(", ".join(strong_areas))
        # Add more sophisticated analysis based on time, difficulty, specific skills etc. if needed

        # --- Return Results ---
        # Return calculated results, but not point/streak info from this sync path
        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.status,
            "score_percentage": test_attempt.score_percentage,
            "score_verbal": test_attempt.score_verbal,
            "score_quantitative": test_attempt.score_quantitative,
            "results_summary": results_summary,
            "smart_analysis": smart_analysis,
            "message": _("Test submitted successfully. Results calculated."),
        }


class TestSubmitResponseSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    smart_analysis = serializers.CharField()
    message = serializers.CharField()
    # Removed point/streak fields
