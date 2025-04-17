from datetime import timedelta
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.conf import settings
from django.db.models import F

from ..models import UserSkillProficiency, UserTestAttempt, UserQuestionAttempt, Test
from apps.learning.models import LearningSection, Question
from apps.learning.api.serializers import (
    QuestionListSerializer,  # Reused for questions list in response
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


# --- Serializers for Tests, Emergency Mode, etc. will go here ---
