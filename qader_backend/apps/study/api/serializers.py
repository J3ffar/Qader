from datetime import timedelta
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.conf import settings
from django.db.models import F, Q

from ..models import UserSkillProficiency, UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import (
    LearningSection,
    LearningSubSection,
    Question,
    Skill,
    UserStarredQuestion,
)
from apps.learning.api.serializers import (
    LearningSubSectionSerializer,
    QuestionListSerializer,
    SkillSerializer,  # Reused for questions list in response
    # QuestionDetailSerializer # Not directly needed here, but maybe for review later
)
from apps.users.models import UserProfile

# Import the full UserProfileSerializer to represent the updated profile structure
from apps.users.api.serializers import UserProfileSerializer

import random
import logging

logger = logging.getLogger(__name__)

# --- Helper: Get User from Context ---


def _get_user_from_context(context):
    """Helper to safely get the authenticated user from serializer context."""
    request = context.get("request")
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    logger.error("Authenticated user could not be retrieved from serializer context.")
    # Raise PermissionDenied, as this implies an authentication issue if called within protected views.
    raise PermissionDenied(
        _("User not found or not authenticated in serializer context.")
    )


# --- Level Assessment Serializers ---


class LevelAssessmentStartSerializer(serializers.Serializer):
    """Serializer for validating the request to start a level assessment."""

    sections = serializers.ListField(
        child=serializers.SlugRelatedField(
            slug_field="slug",
            queryset=LearningSection.objects.all(),  # Validate slugs exist
        ),
        min_length=1,
        help_text=_(
            "List of section slugs (e.g., ['verbal', 'quantitative']) to include."
        ),
    )
    num_questions = serializers.IntegerField(
        # min_value=5,  # Sensible minimum
        max_value=100,  # Sensible maximum
        default=30,
        help_text=_("Desired number of questions for the assessment."),
    )

    def validate(self, data):
        """Perform cross-field validation and checks."""
        user = _get_user_from_context(self.context)

        # 1. Check if profile level is already determined - skip for now
        # try:
        #     profile = user.profile  # Access profile via related name
        #     if profile.level_determined:
        #         # Use non_field_errors for general validation errors related to state
        #         raise serializers.ValidationError(
        #             {
        #                 "non_field_errors": [_("Level assessment already completed.")]
        #                 # Add note about retake if that feature exists:
        #                 # " Feature to retake is not yet implemented or requires specific flag."
        #             }
        #         )
        # except UserProfile.DoesNotExist:
        #     logger.error(
        #         f"UserProfile missing for authenticated user ID: {user.id}. Check signals/initial setup."
        #     )
        #     raise serializers.ValidationError(
        #         {"non_field_errors": [_("User profile could not be found.")]}
        #     )
        # except AttributeError:
        #     logger.error(
        #         f"AttributeError accessing profile for user ID {user.id}. Check user model/signal."
        #     )
        #     raise serializers.ValidationError(
        #         {"non_field_errors": [_("Error accessing user profile.")]}
        #     )

        # 2. Check for existing *ongoing* Level Assessments for this user
        if UserTestAttempt.objects.filter(
            user=user,
            status=UserTestAttempt.Status.STARTED,
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Check specific type
        ).exists():
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "You already have an ongoing level assessment. Please complete or abandon it first."
                        )
                    ]
                }
            )

        # 3. Check if enough questions exist for the request
        sections = data["sections"]
        num_questions_requested = data["num_questions"]
        self.question_pool_count = Question.objects.filter(
            subsection__section__in=sections, is_active=True
        ).count()

        if self.question_pool_count < num_questions_requested:
            logger.warning(
                f"User {user.id} requested {num_questions_requested} level assessment questions for sections "
                f"{[s.slug for s in sections]}, but only {self.question_pool_count} active questions are available."
            )
            # Optionally, allow proceeding with fewer questions or raise an error
            # if (
            #     self.question_pool_count < 5
            # ):  # If fewer than minimum required, definitely raise error
            #     raise serializers.ValidationError(
            #         {
            #             "non_field_errors": [
            #                 _(
            #                     "Not enough active questions available in the selected sections to start the assessment."
            #                 )
            #             ]
            #         }
            #     )
            # If proceeding with fewer: Adjust num_questions in data? Or handle in create?
            # Let's adjust in create for now. Validation passes if minimum is met.

        return data

    def create(self, validated_data):
        """Creates the UserTestAttempt and selects questions."""
        user = _get_user_from_context(self.context)
        sections = validated_data["sections"]
        num_questions_requested = validated_data["num_questions"]

        # --- Question Selection ---
        # Use the count calculated during validation
        question_pool = Question.objects.filter(
            subsection__section__in=sections, is_active=True
        ).values_list(
            "id", flat=True
        )  # More efficient

        actual_num_questions = min(num_questions_requested, len(question_pool))

        # Sample the questions
        # Ensure random.sample gets a list or tuple
        question_ids = random.sample(list(question_pool), actual_num_questions)

        # --- Create Test Attempt ---
        config_snapshot = {
            # Removed "assessment_type": "level" - now handled by attempt_type field
            "sections_requested": [s.slug for s in sections],
            "num_questions_requested": num_questions_requested,
            "actual_num_questions_selected": actual_num_questions,
            # Add any other relevant context for this specific attempt if needed
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Set the type explicitly
                test_configuration=config_snapshot,
                question_ids=question_ids,
                status=UserTestAttempt.Status.STARTED,
                # test_definition can be null here, as it's dynamically generated
            )
        except Exception as e:
            logger.exception(f"Error creating UserTestAttempt for user {user.id}: {e}")
            # Use non_field_errors for creation failures
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the assessment.")]}
            )

        # --- Prepare Response Data ---
        # Fetch the actual Question objects ordered correctly
        questions_queryset = test_attempt.get_questions_queryset()

        # Return data structured for LevelAssessmentResponseSerializer
        return {
            "attempt_id": test_attempt.id,
            "questions": questions_queryset,  # Pass the queryset directly
        }


# --- Level Assessment Submission Serializers ---


class LevelAssessmentAnswerSerializer(serializers.Serializer):
    """Serializer for individual answers within the submission payload."""

    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )

    # Add validation if needed, e.g., check if question_id exists, but primary check is in parent


class LevelAssessmentSubmitSerializer(serializers.Serializer):
    """Serializer for validating and processing the submission of level assessment answers."""

    answers = LevelAssessmentAnswerSerializer(many=True, allow_empty=False)

    def validate(self, data):
        """Validate the submission against the specific test attempt."""
        request = self.context["request"]
        user = _get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = (
            view.kwargs.get("attempt_id") if view and hasattr(view, "kwargs") else None
        )

        if not attempt_id:
            # Should not happen with URL routing, but check defensively
            raise serializers.ValidationError(_("Assessment attempt ID missing."))

        # 1. Fetch the Test Attempt and check ownership, status, and type
        try:
            test_attempt = UserTestAttempt.objects.select_related("user").get(
                pk=attempt_id, user=user  # Ensure ownership
            )
        except UserTestAttempt.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Assessment attempt not found or does not belong to you.")
                    ]
                }
            )

        if test_attempt.status != UserTestAttempt.Status.STARTED:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "This assessment attempt is not active or has already been submitted."
                        )
                    ]
                }
            )

        if test_attempt.attempt_type != UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
            raise serializers.ValidationError(
                {"non_field_errors": [_("This is not a level assessment attempt.")]}
            )

        # 2. Validate submitted answers against expected questions
        submitted_answers_data = data["answers"]
        submitted_question_ids = {
            answer["question_id"] for answer in submitted_answers_data
        }
        expected_question_ids = set(test_attempt.question_ids)

        if submitted_question_ids != expected_question_ids:
            missing = expected_question_ids - submitted_question_ids
            extra = submitted_question_ids - expected_question_ids
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = list(missing)
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = list(extra)

            raise serializers.ValidationError(
                {
                    "answers": [
                        _(
                            "Mismatch between submitted answers and questions in the assessment attempt."
                        ),
                        error_detail,
                    ]
                }
            )

        # Make the validated test_attempt available to the save method via context
        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic  # Ensure all DB updates succeed or fail together
    def save(self, **kwargs):
        """Processes the validated answers, calculates results, updates models."""
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user  # Get user from the validated attempt

        # Fetch related questions efficiently
        questions_in_attempt = test_attempt.get_questions_queryset().select_related(
            "subsection", "subsection__section"  # Preload for scoring
        )
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records ---
        question_attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)
            if not question:
                # Should be caught by validation, but handle defensively
                logger.error(
                    f"Question ID {question_id} from submit data not found in fetched questions for test attempt {test_attempt.id}"
                )
                # Consider raising an error or logging and skipping
                raise serializers.ValidationError(
                    {
                        "answers": _(
                            f"Internal error: Question {question_id} not found during processing."
                        )
                    }
                )

            # is_correct is calculated in the model's save method now, but we can set it here too
            is_correct_flag = answer_data["selected_answer"] == question.correct_answer

            attempt = UserQuestionAttempt(
                user=user,
                question=question,
                test_attempt=test_attempt,  # Link to the parent attempt
                selected_answer=answer_data["selected_answer"],
                time_taken_seconds=answer_data.get("time_taken_seconds"),
                mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,  # Set mode explicitly
                is_correct=is_correct_flag,  # Set correctness
                # attempted_at is handled by default=timezone.now
            )
            question_attempts_to_create.append(attempt)

        try:
            # Bulk create for performance
            created_attempts = UserQuestionAttempt.objects.bulk_create(
                question_attempts_to_create
            )
        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for test attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save assessment answers.")]}
            )

        # --- Calculate Scores ---
        # Use the created attempts for calculation
        total_questions = len(created_attempts)
        correct_answers = sum(1 for attempt in created_attempts if attempt.is_correct)

        overall_score = (
            (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
        )

        # Calculate Section Scores (Verbal/Quantitative) & Detailed Summary
        verbal_correct = 0
        verbal_total = 0
        quant_correct = 0
        quant_total = 0
        results_summary = {}  # Store detailed breakdown by subsection slug

        for attempt in created_attempts:
            # Access preloaded related fields
            subsection = attempt.question.subsection
            if not subsection:
                logger.warning(
                    f"Question {attempt.question.id} in attempt {test_attempt.id} has no subsection."
                )
                continue  # Skip questions without subsection for scoring

            section = subsection.section
            if not section:
                logger.warning(
                    f"Subsection {subsection.id} for question {attempt.question.id} has no parent section."
                )
                continue  # Skip subsections without section

            section_slug = section.slug
            subsection_slug = subsection.slug

            # Initialize subsection summary if not present
            if subsection_slug not in results_summary:
                results_summary[subsection_slug] = {
                    "correct": 0,
                    "total": 0,
                    "name": subsection.name,
                }

            results_summary[subsection_slug]["total"] += 1

            if section_slug == "verbal":
                verbal_total += 1
                if attempt.is_correct:
                    verbal_correct += 1
                    results_summary[subsection_slug]["correct"] += 1
            elif section_slug == "quantitative":
                quant_total += 1
                if attempt.is_correct:
                    quant_correct += 1
                    results_summary[subsection_slug]["correct"] += 1
            # Handle other potential sections if needed

        verbal_score = (
            (verbal_correct / verbal_total * 100) if verbal_total > 0 else 0.0
        )
        quantitative_score = (
            (quant_correct / quant_total * 100) if quant_total > 0 else 0.0
        )

        # Calculate final scores within the results_summary dict
        for slug, data in results_summary.items():
            data["score"] = (
                round((data["correct"] / data["total"] * 100), 2)
                if data["total"] > 0
                else 0.0
            )

        # --- Update Test Attempt ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.score_percentage = round(overall_score, 2)
        test_attempt.score_verbal = round(verbal_score, 2)
        test_attempt.score_quantitative = round(quantitative_score, 2)
        test_attempt.results_summary = results_summary
        test_attempt.save(
            update_fields=[
                "status",
                "end_time",
                "score_percentage",
                "score_verbal",
                "score_quantitative",
                "results_summary",
                "updated_at",
            ]
        )

        # --- Update User Profile ---
        profile = user.profile  # Assumes profile exists (checked earlier)
        profile.current_level_verbal = test_attempt.score_verbal
        profile.current_level_quantitative = test_attempt.score_quantitative
        # No need to set profile.level_determined explicitly, the property handles it.
        profile.save(
            update_fields=[
                "current_level_verbal",
                "current_level_quantitative",
                "updated_at",
            ]
        )

        # --- Award Points ---
        # Placeholder for Gamification integration
        # points_earned = settings.POINTS_LEVEL_ASSESSMENT_COMPLETED # Example
        # PointLog.objects.create(...)
        logger.info(
            f"Level assessment attempt {test_attempt.id} completed for user {user.id}."
        )

        # --- Prepare and Return Result Data ---
        # Refresh profile from DB to get the latest state for the response
        profile.refresh_from_db()
        return {
            "attempt_id": test_attempt.id,
            "results": {
                "overall_score": test_attempt.score_percentage,
                "verbal_score": test_attempt.score_verbal,
                "quantitative_score": test_attempt.score_quantitative,
                "proficiency_summary": results_summary,  # Detailed breakdown
                "message": _(
                    "Your level assessment is complete. Your personalized learning path is now adjusted!"
                ),
            },
            # Return the actual UserProfile object here, not its serialized data
            "updated_profile": profile,
            # *************************
        }


# --- Level Assessment Response Serializers ---


class LevelAssessmentResponseSerializer(serializers.Serializer):
    """Response serializer for the start assessment endpoint (POST /level-assessment/start/)."""

    attempt_id = serializers.IntegerField(read_only=True)
    # Use QuestionListSerializer to format the questions (no answers/explanations)
    # Important: Pass context for `is_starred` calculation
    questions = QuestionListSerializer(many=True, read_only=True)


class LevelAssessmentResultSerializer(serializers.Serializer):
    """Response serializer for the submit assessment endpoint (POST /level-assessment/{id}/submit/)."""

    attempt_id = serializers.IntegerField(read_only=True)
    # Results dictionary as calculated in the submit serializer's save method
    results = serializers.JSONField(read_only=True)
    # Updated profile represented using the standard UserProfileSerializer
    # Ensure context is passed if UserProfileSerializer needs the request (e.g., for URLs)
    updated_profile = UserProfileSerializer(read_only=True)


class TraditionalLearningAnswerSerializer(serializers.Serializer):
    """Serializer for submitting an answer in Traditional Learning mode."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.filter(
            is_active=True
        ),  # Ensure question exists and is active
        required=True,
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )
    used_hint = serializers.BooleanField(default=False, required=False)
    used_elimination = serializers.BooleanField(default=False, required=False)
    used_solution_method = serializers.BooleanField(default=False, required=False)

    def validate_question_id(self, value):
        # Although PrimaryKeyRelatedField validates existence,
        # you might add further checks if needed (e.g., if the question
        # should belong to specific sections the user has access to, though not typical for traditional)
        return value

    @transaction.atomic
    def save(self, **kwargs):
        """Process the answer, update stats, award points/streak."""
        user = _get_user_from_context(self.context)
        question = self.validated_data["question_id"]
        selected_answer = self.validated_data["selected_answer"]

        # 1. Determine correctness
        is_correct = selected_answer == question.correct_answer

        # 2. Create UserQuestionAttempt record
        attempt = UserQuestionAttempt.objects.create(
            user=user,
            question=question,
            selected_answer=selected_answer,
            is_correct=is_correct,
            time_taken_seconds=self.validated_data.get("time_taken_seconds"),
            used_hint=self.validated_data.get("used_hint", False),
            used_elimination=self.validated_data.get("used_elimination", False),
            used_solution_method=self.validated_data.get("used_solution_method", False),
            mode=UserQuestionAttempt.Mode.TRADITIONAL,
        )

        # --- 3. Update User Profile (Points & Streak) ---
        # --- FIX: Ensure profile exists ---
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile not found for user {user.id} during answer submission."
            )
            # Decide how to handle: raise error or skip profile update?
            # For now, let's skip profile update and log, but raising might be better
            profile = None

        points_earned = 0
        streak_updated = False
        current_total_points = 0
        current_streak = 0

        if profile:  # Only proceed if profile exists
            now_local = timezone.localtime(timezone.now())
            today = now_local.date()

            last_activity_date = None
            if profile.last_study_activity_at:
                # Convert stored UTC (or naive) time to local date
                last_activity_local_dt = timezone.localtime(
                    profile.last_study_activity_at
                )
                last_activity_date = last_activity_local_dt.date()

            yesterday = today - timedelta(days=1)

            # Award points (using imported settings)
            if is_correct:
                points_earned = getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
                reason_code = "TRADITIONAL_CORRECT"
                description = (
                    f"Correct answer for Question #{question.id} (Traditional)"
                )
            else:
                points_earned = getattr(settings, "POINTS_TRADITIONAL_INCORRECT", 0)
                reason_code = "TRADITIONAL_INCORRECT"
                description = (
                    f"Incorrect answer for Question #{question.id} (Traditional)"
                )

            if points_earned != 0:
                profile.points = F("points") + points_earned  # Use F() for safety
                # Create PointLog entry
                # PointLog.objects.create(
                #     user=user,
                #     points_change=points_earned,
                #     reason_code=reason_code,
                #     description=description,
                # )

            # Update streak
            if last_activity_date == today:
                # Already studied today, no change to streak days
                pass  # streak_updated remains False
            elif last_activity_date == yesterday:
                # Continued streak
                # Check if current_streak_days is already an F() object before adding
                if isinstance(profile.current_streak_days, F):
                    # This case shouldn't happen if we save/refresh correctly, but handle defensively
                    profile.current_streak_days = profile.current_streak_days + 1
                else:
                    profile.current_streak_days = F("current_streak_days") + 1
                streak_updated = True
            else:  # Handles None or older dates (streak broken or first activity)
                profile.current_streak_days = 1
                streak_updated = True

            profile.last_study_activity_at = now_local  # Use the calculated local time

            # Prepare fields to update, excluding longest_streak for now
            update_fields = ["last_study_activity_at", "updated_at"]
            if points_earned != 0:
                update_fields.append("points")
            # Only include current_streak_days if it was potentially modified
            if streak_updated or isinstance(profile.current_streak_days, F):
                update_fields.append("current_streak_days")

            # Save the main updates (including F objects)
            if update_fields:  # Avoid empty update
                profile.save(update_fields=update_fields)

            # Refresh to resolve F() objects and get current values
            profile.refresh_from_db()

            # Now update longest streak based on the resolved current streak
            if profile.current_streak_days > profile.longest_streak_days:
                profile.longest_streak_days = profile.current_streak_days
                profile.save(update_fields=["longest_streak_days"])

            # Set values for the response *after* all updates and refreshes
            current_total_points = profile.points
            current_streak = profile.current_streak_days

        # --- 4. Update User Skill Proficiency (Basic Example/Trigger) ---
        # Check if UserSkillProficiency was imported successfully
        if (
            UserSkillProficiency and question.skill and profile
        ):  # Also check profile exists
            try:
                proficiency, created = UserSkillProficiency.objects.get_or_create(
                    user=user,
                    skill=question.skill,
                    defaults={
                        "proficiency_score": 0.5 if is_correct else 0.0,
                        "attempts_count": 1,
                        "correct_count": 1 if is_correct else 0,
                    },
                )
                if not created:
                    # Use F() objects for atomic updates
                    proficiency.attempts_count = F("attempts_count") + 1
                    if is_correct:
                        proficiency.correct_count = F("correct_count") + 1

                    # Save F() updates first
                    proficiency.save(
                        update_fields=[
                            "attempts_count",
                            "correct_count",
                            "last_calculated_at",
                        ]
                    )
                    proficiency.refresh_from_db()  # Get the actual counts

                    # Now calculate and save the score
                    if proficiency.attempts_count > 0:
                        proficiency.proficiency_score = round(
                            proficiency.correct_count / proficiency.attempts_count, 4
                        )
                    else:
                        proficiency.proficiency_score = 0.0
                    proficiency.save(update_fields=["proficiency_score"])

            except Exception as e:
                logger.error(
                    f"Error updating proficiency for user {user.id}, skill {question.skill.id}: {e}"
                )
        # --- End Proficiency Update ---

        # --- Prepare and Return Response Data ---
        current_total_points = profile.points if profile else 0
        current_streak = profile.current_streak_days if profile else 0
        if profile:
            profile.refresh_from_db()  # Refresh again if needed

        return {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points_earned": points_earned,
            "current_total_points": current_total_points,
            "streak_updated": streak_updated,
            "current_streak": current_streak,
        }


class TraditionalLearningResponseSerializer(serializers.Serializer):
    """Response serializer for the traditional learning answer submission."""

    question_id = serializers.IntegerField(read_only=True)
    is_correct = serializers.BooleanField(read_only=True)
    correct_answer = serializers.CharField(read_only=True)
    explanation = serializers.CharField(read_only=True, allow_null=True)
    points_earned = serializers.IntegerField(read_only=True)
    current_total_points = serializers.IntegerField(read_only=True)
    streak_updated = serializers.BooleanField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)


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
            slug_field="slug", queryset=Skill.objects.all()
        ),
        required=False,
        allow_empty=True,
        help_text=_("List of specific skill slugs to include"),
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
        if (
            not data.get("subsections")
            and not data.get("skills")
            and not data.get("starred")
        ):
            # Need at least one criteria for selecting questions if not purely starred
            raise serializers.ValidationError(
                _("Must specify subsections, skills, or filter by starred questions.")
            )
        # Add more complex validation if needed (e.g., check skill belongs to subsection if both provided)
        return data


class TestStartSerializer(serializers.Serializer):
    """Serializer for validating the request to start a new test (practice, custom, simulation)."""

    test_type = serializers.ChoiceField(
        choices=UserTestAttempt.AttemptType.choices, required=True
    )
    config = TestConfigSerializer(required=True)

    # Define a low proficiency threshold (adjust as needed)
    PROFICIENCY_THRESHOLD = 0.7

    def validate(self, data):
        """Perform cross-field validation and checks."""
        user = _get_user_from_context(self.context)
        config = data["config"]
        num_questions_requested = config["num_questions"]

        # --- Build base queryset based on config ---
        question_filters = Q(is_active=True)
        if config.get("subsections"):
            question_filters &= Q(
                subsection__slug__in=[s.slug for s in config["subsections"]]
            )
        if config.get("skills"):
            question_filters &= Q(skill__slug__in=[s.slug for s in config["skills"]])

        # --- Apply Starred Filter ---
        if config.get("starred"):
            # We need to filter by questions the current user has starred
            starred_ids = UserStarredQuestion.objects.filter(user=user).values_list(
                "question_id", flat=True
            )
            question_filters &= Q(id__in=list(starred_ids))

        # --- Apply Not Mastered Filter ---
        if config.get("not_mastered") and UserSkillProficiency:
            try:
                low_proficiency_skills_qs = UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=self.PROFICIENCY_THRESHOLD
                ).values_list("skill_id", flat=True)
                # FIX: Explicitly convert QuerySet to list for __in lookup
                low_proficiency_skills_ids = list(low_proficiency_skills_qs)

                attempted_skill_qs = UserSkillProficiency.objects.filter(
                    user=user
                ).values_list("skill_id", flat=True)
                # FIX: Explicitly convert QuerySet to list for __in lookup
                attempted_skill_ids = list(attempted_skill_qs)

                not_mastered_filter = Q(skill_id__in=low_proficiency_skills_ids) | (
                    Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids)
                )
                question_filters &= not_mastered_filter
            except Exception as e:
                logger.error(
                    f"Error applying 'not_mastered' filter for user {user.id}: {e}"
                )
                # Optionally raise validation error or just skip the filter

        # --- Check Question Availability ---
        question_pool_query = Question.objects.filter(question_filters)
        self.question_pool_ids = list(question_pool_query.values_list("id", flat=True))
        pool_count = len(self.question_pool_ids)

        if pool_count < num_questions_requested:
            logger.warning(
                f"User {user.id} requested {num_questions_requested} test questions with config {config}, "
                f"but only {pool_count} matching active questions are available."
            )
            # Decide: error out, or proceed with fewer? Let's proceed with fewer.
            if pool_count == 0:
                raise serializers.ValidationError(
                    _("No active questions found matching the specified criteria.")
                )
        # Store pool IDs in context for create method
        self.context["question_pool_ids"] = self.question_pool_ids
        return data

    def create(self, validated_data):
        """Creates the UserTestAttempt and selects questions based on validated config."""
        user = _get_user_from_context(self.context)
        config = validated_data["config"]
        test_type = validated_data["test_type"]
        num_questions_requested = config["num_questions"]
        question_pool_ids = self.context[
            "question_pool_ids"
        ]  # Get IDs from validation context

        actual_num_questions = min(num_questions_requested, len(question_pool_ids))

        # Sample the questions
        question_ids = random.sample(question_pool_ids, actual_num_questions)

        # --- Create Test Attempt ---
        # Create a snapshot of the config used
        config_snapshot = {
            "test_type": test_type,  # Store the requested type
            "config": {  # Store the validated config dictionary
                **config,
                # Convert related objects back to slugs/ids for JSON storage
                "subsections": [s.slug for s in config.get("subsections", [])],
                "skills": [s.slug for s in config.get("skills", [])],
                "actual_num_questions_selected": actual_num_questions,
            },
        }

        try:
            test_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=test_type,  # Store the specific attempt type
                test_configuration=config_snapshot,
                question_ids=question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating UserTestAttempt (Type: {test_type}) for user {user.id}: {e}"
            )
            raise serializers.ValidationError(_("Failed to start the test."))

        # --- Prepare Response Data ---
        questions_queryset = test_attempt.get_questions_queryset()

        return {
            "attempt_id": test_attempt.id,
            "questions": questions_queryset,
        }


class TestStartResponseSerializer(serializers.Serializer):
    """Response serializer for the start test endpoint (POST /tests/start/)."""

    attempt_id = serializers.IntegerField(read_only=True)
    questions = QuestionListSerializer(
        many=True, read_only=True, context={"show_sensitive": False}
    )  # Pass context


class UserTestAttemptListSerializer(serializers.ModelSerializer):
    """Serializer for listing user's previous test attempts."""

    # Derive fields from the model or its configuration snapshot
    test_type = serializers.SerializerMethodField()
    num_questions = serializers.IntegerField(read_only=True)  # Use property from model
    date = serializers.DateTimeField(source="start_time", read_only=True)
    performance = serializers.SerializerMethodField()
    # Rename id for clarity in API response
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
        read_only_fields = fields  # All fields derived or read-only

    def get_test_type(self, obj):
        """Derive test type display name from stored config or attempt_type."""
        # Prioritize display name from attempt_type field
        if obj.attempt_type:
            return obj.get_attempt_type_display()
        # Fallback to checking configuration if needed (legacy or specific cases)
        if isinstance(obj.test_configuration, dict):
            # Check common patterns used before attempt_type was added
            if obj.test_configuration.get("test_type") == "custom":
                return obj.test_configuration.get("config", {}).get("name") or _(
                    "Custom Test"
                )
            if obj.test_configuration.get("test_type"):
                # Try to map old values or return as is
                return obj.test_configuration["test_type"].replace("_", " ").title()
        return _("Unknown Test Type")  # Default fallback

    def get_performance(self, obj):
        """Return a summary of performance by section."""
        performance_summary = {}
        if obj.score_verbal is not None:
            performance_summary["verbal"] = obj.score_verbal
        if obj.score_quantitative is not None:
            performance_summary["quantitative"] = obj.score_quantitative
        # Add more sections if the model supports them
        return performance_summary if performance_summary else None


class UserTestAttemptDetailSerializer(serializers.ModelSerializer):
    """Serializer for retrieving details of a specific test attempt."""

    attempt_id = serializers.IntegerField(source="id", read_only=True)
    test_type = serializers.SerializerMethodField()
    config_name = serializers.SerializerMethodField()
    date = serializers.DateTimeField(source="start_time", read_only=True)
    num_questions = serializers.IntegerField(read_only=True)  # Use model property
    questions = serializers.SerializerMethodField()  # Get questions based on stored IDs

    class Meta:
        model = UserTestAttempt
        fields = [
            "attempt_id",
            "test_type",
            "config_name",  # Name from config if custom
            "date",
            "num_questions",
            "score_percentage",
            "status",
            "questions",
            "results_summary",  # Only shown if completed
        ]
        read_only_fields = fields

    def get_test_type(self, obj):
        """Get display name for the attempt type."""
        return obj.get_attempt_type_display()

    def get_config_name(self, obj):
        """Extract the name from the configuration if it exists."""
        if isinstance(obj.test_configuration, dict):
            return obj.test_configuration.get("config", {}).get("name", None)
        return None

    def get_questions(self, obj):
        """Retrieve and serialize the questions associated with this attempt."""
        request = self.context.get("request")
        queryset = obj.get_questions_queryset()
        # Use QuestionListSerializer to avoid exposing answers/explanations here
        # Pass context for 'is_starred' check
        serializer = QuestionListSerializer(
            queryset, many=True, context={"request": request}
        )
        return serializer.data


class TestAnswerSerializer(serializers.Serializer):
    """Serializer for individual answers within the test submission payload."""

    question_id = serializers.IntegerField(required=True)
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices, required=True
    )
    time_taken_seconds = serializers.IntegerField(
        required=False, min_value=0, allow_null=True
    )


class TestSubmitSerializer(serializers.Serializer):
    """Serializer for validating and processing the submission of test answers."""

    answers = TestAnswerSerializer(many=True, allow_empty=False)

    def validate(self, data):
        """Validate the submission against the specific test attempt."""
        request = self.context["request"]
        user = _get_user_from_context(self.context)
        view = self.context.get("view")
        attempt_id = (
            view.kwargs.get("attempt_id") if view and hasattr(view, "kwargs") else None
        )

        if not attempt_id:
            raise serializers.ValidationError(_("Test attempt ID missing."))

        # --- Fetch the Test Attempt ---
        try:
            test_attempt = UserTestAttempt.objects.select_related(
                "user", "user__profile"
            ).get(
                pk=attempt_id, user=user  # Ensure ownership
            )
        except UserTestAttempt.DoesNotExist:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _("Test attempt not found or does not belong to you.")
                    ]
                }
            )
        except UserProfile.DoesNotExist:  # Handle case where profile might be missing
            logger.error(
                f"UserProfile missing for user ID {user.id} during test submission."
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("User profile error.")]}
            )

        # --- Check Status ---
        if test_attempt.status != UserTestAttempt.Status.STARTED:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "This test attempt is not active or has already been submitted."
                        )
                    ]
                }
            )

        # --- Validate Submitted Answers ---
        submitted_answers_data = data["answers"]
        submitted_question_ids = {
            answer["question_id"] for answer in submitted_answers_data
        }
        expected_question_ids = set(test_attempt.question_ids)

        if len(submitted_answers_data) != len(expected_question_ids):
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Incorrect number of answers submitted. Expected {}, got {}."
                        ).format(
                            len(expected_question_ids), len(submitted_answers_data)
                        )
                    ]
                }
            )

        if submitted_question_ids != expected_question_ids:
            missing = expected_question_ids - submitted_question_ids
            extra = submitted_question_ids - expected_question_ids
            error_detail = {}
            if missing:
                error_detail["missing_answers_for_question_ids"] = list(missing)
            if extra:
                error_detail["unexpected_answers_for_question_ids"] = list(extra)
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

        # Make the validated attempt available to the save method
        self.context["test_attempt"] = test_attempt
        return data

    @transaction.atomic
    def save(self, **kwargs):
        """Processes answers, calculates score, updates attempt, profile, proficiency."""
        test_attempt = self.context["test_attempt"]
        answers_data = self.validated_data["answers"]
        user = test_attempt.user
        profile = user.profile  # Assume profile exists from validation check

        # Fetch related questions efficiently
        questions_in_attempt = test_attempt.get_questions_queryset().select_related(
            "subsection",
            "subsection__section",
            "skill",  # Preload for scoring and proficiency
        )
        question_map = {q.id: q for q in questions_in_attempt}

        # --- Create UserQuestionAttempt records ---
        question_attempts_to_create = []
        for answer_data in answers_data:
            question_id = answer_data["question_id"]
            question = question_map.get(question_id)  # Get preloaded question
            if not question:
                continue  # Should not happen due to validation

            is_correct_flag = answer_data["selected_answer"] == question.correct_answer

            # Map test attempt type to question attempt mode
            mode = UserQuestionAttempt.Mode.TEST  # Default for practice/simulation
            if (
                test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                mode = UserQuestionAttempt.Mode.LEVEL_ASSESSMENT

            attempt = UserQuestionAttempt(
                user=user,
                question=question,
                test_attempt=test_attempt,
                selected_answer=answer_data["selected_answer"],
                is_correct=is_correct_flag,
                time_taken_seconds=answer_data.get("time_taken_seconds"),
                mode=mode,
                # attempted_at handled by default
            )
            question_attempts_to_create.append(attempt)

        try:
            created_attempts = UserQuestionAttempt.objects.bulk_create(
                question_attempts_to_create
            )
        except Exception as e:
            logger.exception(
                f"Error bulk creating UserQuestionAttempts for test attempt {test_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to save test answers.")]}
            )

        # --- Calculate Scores ---
        total_questions = len(created_attempts)
        correct_answers = sum(1 for attempt in created_attempts if attempt.is_correct)
        overall_score = (
            (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
        )

        verbal_correct, verbal_total, quant_correct, quant_total = 0, 0, 0, 0
        results_summary = {}  # Store detailed breakdown by subsection slug

        for attempt in created_attempts:
            question = (
                attempt.question
            )  # Already preloaded with subsection/section/skill
            subsection = question.subsection
            if not subsection:
                continue
            section = subsection.section
            if not section:
                continue

            section_slug = section.slug
            subsection_slug = subsection.slug

            if subsection_slug not in results_summary:
                results_summary[subsection_slug] = {
                    "correct": 0,
                    "total": 0,
                    "name": subsection.name,
                }
            results_summary[subsection_slug]["total"] += 1

            if section_slug == "verbal":
                verbal_total += 1
            elif section_slug == "quantitative":
                quant_total += 1

            if attempt.is_correct:
                results_summary[subsection_slug]["correct"] += 1
                if section_slug == "verbal":
                    verbal_correct += 1
                elif section_slug == "quantitative":
                    quant_correct += 1

            # --- Update User Skill Proficiency ---
            # Run this inside the loop for each question attempt
            if question.skill and UserSkillProficiency:
                try:
                    proficiency, created = UserSkillProficiency.objects.get_or_create(
                        user=user,
                        skill=question.skill,
                        defaults={
                            "proficiency_score": 1.0 if attempt.is_correct else 0.0,
                            "attempts_count": 1,
                            "correct_count": 1 if attempt.is_correct else 0,
                        },
                    )
                    if not created:
                        proficiency.attempts_count = F("attempts_count") + 1
                        if attempt.is_correct:
                            proficiency.correct_count = F("correct_count") + 1
                        proficiency.save(
                            update_fields=[
                                "attempts_count",
                                "correct_count",
                                "last_calculated_at",
                            ]
                        )
                        proficiency.refresh_from_db()
                        proficiency.proficiency_score = (
                            round(
                                proficiency.correct_count / proficiency.attempts_count,
                                4,
                            )
                            if proficiency.attempts_count > 0
                            else 0.0
                        )
                        proficiency.save(update_fields=["proficiency_score"])
                except Exception as e:
                    logger.error(
                        f"Error updating proficiency for user {user.id}, skill {question.skill.id} in test {test_attempt.id}: {e}"
                    )
            # --- End Proficiency Update ---

        verbal_score = (
            (verbal_correct / verbal_total * 100) if verbal_total > 0 else None
        )  # Null if no questions of this type
        quantitative_score = (
            (quant_correct / quant_total * 100) if quant_total > 0 else None
        )

        # Calculate final scores within the results_summary dict
        for slug, data in results_summary.items():
            data["score"] = (
                round((data["correct"] / data["total"] * 100), 1)
                if data["total"] > 0
                else 0.0
            )

        # --- Update Test Attempt ---
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.score_percentage = round(overall_score, 1)
        test_attempt.score_verbal = (
            round(verbal_score, 1) if verbal_score is not None else None
        )
        test_attempt.score_quantitative = (
            round(quantitative_score, 1) if quantitative_score is not None else None
        )
        test_attempt.results_summary = results_summary
        test_attempt.save()

        # --- Update User Profile (Points & Streak) ---
        points_earned = 0
        streak_updated = False
        if profile:
            now_local = timezone.localtime(timezone.now())
            today = now_local.date()
            last_activity_date = (
                timezone.localtime(profile.last_study_activity_at).date()
                if profile.last_study_activity_at
                else None
            )
            yesterday = today - timedelta(days=1)

            points_earned = getattr(
                settings, "POINTS_TEST_COMPLETED", 10
            )  # Get points for completing a test
            reason_code = "TEST_COMPLETED"
            description = f"Completed Test Attempt #{test_attempt.id} ({test_attempt.get_attempt_type_display()})"

            if points_earned != 0:
                profile.points = F("points") + points_earned
                # PointLog.objects.create(...) # Add log entry

            # Update streak
            if last_activity_date != today:
                if last_activity_date == yesterday:
                    profile.current_streak_days = F("current_streak_days") + 1
                else:
                    profile.current_streak_days = 1
                streak_updated = True  # Set flag even if F object used
                profile.last_study_activity_at = now_local

                update_fields = [
                    "points",
                    "current_streak_days",
                    "last_study_activity_at",
                    "updated_at",
                ]
                profile.save(update_fields=update_fields)
                profile.refresh_from_db()  # Resolve F() objects

                if profile.current_streak_days > profile.longest_streak_days:
                    profile.longest_streak_days = profile.current_streak_days
                    profile.save(update_fields=["longest_streak_days"])
            elif points_earned != 0:  # Just update points if activity was already today
                profile.save(update_fields=["points", "updated_at"])
                profile.refresh_from_db()

        # --- Generate Smart Analysis (Placeholder) ---
        smart_analysis = "Good job completing the test!"  # Basic placeholder
        # Add logic here to analyze results_summary or proficiency changes
        weak_areas = [d["name"] for d in results_summary.values() if d["score"] < 60]
        strong_areas = [d["name"] for d in results_summary.values() if d["score"] >= 85]
        if weak_areas:
            smart_analysis += f" Focus on improving in: {', '.join(weak_areas)}."
        if strong_areas:
            smart_analysis += f" Keep up the great work in: {', '.join(strong_areas)}!"

        # --- Return Results ---
        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.status,
            "score_percentage": test_attempt.score_percentage,
            "score_verbal": test_attempt.score_verbal,
            "score_quantitative": test_attempt.score_quantitative,
            "results_summary": test_attempt.results_summary,
            "smart_analysis": smart_analysis,
            "points_earned": points_earned,
            "current_total_points": profile.points if profile else 0,
        }


class TestSubmitResponseSerializer(serializers.Serializer):
    """Response serializer for the test submission endpoint."""

    attempt_id = serializers.IntegerField()
    status = serializers.CharField()
    score_percentage = serializers.FloatField(allow_null=True)
    score_verbal = serializers.FloatField(allow_null=True)
    score_quantitative = serializers.FloatField(allow_null=True)
    results_summary = serializers.JSONField()
    smart_analysis = serializers.CharField()
    points_earned = serializers.IntegerField()
    current_total_points = serializers.IntegerField()


class TestReviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions within the test review response."""

    # Get related fields using nested serializers or source
    subsection = LearningSubSectionSerializer(read_only=True)  # Assuming this exists
    skill = SkillSerializer(read_only=True)  # Assuming this exists
    # Include fields from UserQuestionAttempt for this specific attempt
    user_selected_answer = serializers.SerializerMethodField()
    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",  # Options
            "correct_answer",  # Show correct answer in review
            "explanation",  # Show explanation
            "user_selected_answer",  # User's choice for this attempt
            "is_correct",  # Whether the user was correct
            "subsection",
            "skill",
            # Add difficulty or other relevant fields if needed
        ]

    def get_user_selected_answer(self, obj):
        # Retrieve from context passed by the view
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.selected_answer if user_attempt else None

    def get_is_correct(self, obj):
        user_attempt = self.context.get("user_attempts_map", {}).get(obj.id)
        return user_attempt.is_correct if user_attempt else None


class TestReviewSerializer(serializers.Serializer):
    """Response serializer for the test review endpoint."""

    attempt_id = serializers.IntegerField()
    review_questions = TestReviewQuestionSerializer(many=True)


# --- Serializers for Emergency Mode, etc. will go here ---
