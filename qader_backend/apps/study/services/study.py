import random
import logging
from typing import Optional, List, Dict, Any, Set, Union

from django.db.models import (
    QuerySet,
    Q,
    Exists,
    OuterRef,
    F,
    Case,
    When,
    IntegerField,
    Count,
    Value,
    FloatField,
)
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import (
    serializers,
    status,
)  # Use DRF's validation error for API context
from rest_framework.exceptions import PermissionDenied, APIException

from apps.learning.models import (
    LearningSubSection,
    Question,
    Skill,
    UserStarredQuestion,
    LearningSection,  # Import needed for profile update check
)
from apps.users.models import UserProfile
from apps.study.models import (
    UserSkillProficiency,
    UserTestAttempt,
    UserQuestionAttempt,
)
from django.contrib.auth import get_user_model

from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_PROFICIENCY_THRESHOLD = getattr(settings, "DEFAULT_PROFICIENCY_THRESHOLD", 0.7)
EMERGENCY_MODE_DEFAULT_QUESTIONS = getattr(
    settings, "EMERGENCY_MODE_DEFAULT_QUESTIONS", 15
)
EMERGENCY_MODE_WEAK_SKILL_COUNT = getattr(
    settings, "EMERGENCY_MODE_WEAK_SKILL_COUNT", 3
)
EMERGENCY_MODE_MIN_QUESTIONS = getattr(settings, "EMERGENCY_MODE_MIN_QUESTIONS", 5)
EMERGENCY_MODE_ESTIMATED_MINS_PER_Q = getattr(
    settings, "EMERGENCY_MODE_ESTIMATED_MINS_PER_Q", 2.5
)
LEVEL_ASSESSMENT_SCORE_THRESHOLD = getattr(
    settings, "LEVEL_ASSESSMENT_SCORE_THRESHOLD", 60
)  # Example threshold for analysis


# --- Question Filtering Logic ---
def get_filtered_questions(
    user: User,
    limit: int = 10,
    subsections: Optional[List[str]] = None,  # List of subsection slugs
    skills: Optional[List[str]] = None,  # List of skill slugs
    starred: bool = False,
    not_mastered: bool = False,
    exclude_ids: Optional[List[int]] = None,
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    min_required: int = 1,
) -> QuerySet[Question]:
    """
    Retrieves a randomly ordered QuerySet of active Questions based on various filters.

    Args:
        user: The User for whom to filter (required for 'starred' and 'not_mastered').
        limit: The maximum number of questions to return.
        subsections: Optional list of subsection slugs to filter by.
        skills: Optional list of skill slugs to filter by.
        starred: If True, only return questions starred by the user.
        not_mastered: If True, prioritize questions from skills the user is below
                      the proficiency_threshold in, or skills they haven't attempted yet.
        exclude_ids: Optional list of Question IDs to exclude from the results.
        proficiency_threshold: The score threshold used for the 'not_mastered' filter.
        min_required: If > 0, checks if at least this many questions match the criteria.

    Returns:
        A QuerySet of Question objects, randomly ordered up to the specified limit.
        Returns an empty QuerySet if no matching questions are found or limit is <= 0.
    """
    if limit <= 0:
        return Question.objects.none()

    # Base queryset - only active questions, prefetch related data for efficiency
    queryset = Question.objects.filter(is_active=True).select_related(
        "subsection",
        "subsection__section",
        "skill",  # Select related for common access patterns
    )
    filters = Q()
    exclude_ids_set = (
        set(int(id) for id in exclude_ids if isinstance(id, int))
        if exclude_ids
        else set()
    )

    # Apply filters based on arguments
    if subsections:
        filters &= Q(subsection__slug__in=subsections)
    if skills:
        filters &= Q(skill__slug__in=skills)

    # Authentication-dependent filters
    if starred or not_mastered:
        if not user or not user.is_authenticated:
            logger.warning(
                f"get_filtered_questions: 'starred' or 'not_mastered' filter requested for anonymous user. Ignoring filter."
            )
        else:
            if starred:
                # Use Exists for efficient subquery checking
                starred_subquery = UserStarredQuestion.objects.filter(
                    user=user, question=OuterRef("pk")
                )
                filters &= Q(Exists(starred_subquery))

            if not_mastered:
                try:
                    # Skills user has attempted and proficiency is below threshold
                    low_prof_skill_ids = set(
                        UserSkillProficiency.objects.filter(
                            user=user, proficiency_score__lt=proficiency_threshold
                        ).values_list("skill_id", flat=True)
                    )
                    # All skills user has ever attempted (has a proficiency record for)
                    attempted_skill_ids = set(
                        UserSkillProficiency.objects.filter(user=user).values_list(
                            "skill_id", flat=True
                        )
                    )

                    # Logic: Include questions if:
                    # 1. Skill is known to be low proficiency OR
                    # 2. Question has a skill, and that skill has never been attempted by the user
                    not_mastered_filter = Q(skill_id__in=low_prof_skill_ids) | (
                        Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids)
                    )
                    filters &= not_mastered_filter
                    logger.info(
                        f"Applied 'not_mastered' filter for user {user.id}. Low prof skills: {len(low_prof_skill_ids)}, Attempted skills: {len(attempted_skill_ids)}"
                    )

                except Exception as e:
                    logger.error(
                        f"get_filtered_questions: Error applying 'not_mastered' filter for user {user.id}: {e}",
                        exc_info=True,
                    )
                    # Decide behavior: either fail safely (return none) or continue without the filter
                    # return Question.objects.none() # Safer option
                    # Continuing without filter:
                    logger.warning(
                        f"Could not apply 'not_mastered' filter for user {user.id} due to error. Proceeding without it."
                    )

    # Apply collected filters
    if filters:
        queryset = queryset.filter(filters)

    # Apply exclusions AFTER main filters
    if exclude_ids_set:
        queryset = queryset.exclude(id__in=exclude_ids_set)

    if min_required > 0:
        # Use count() which is efficient after filtering
        pool_count = queryset.count()
        if pool_count < min_required:
            logger.warning(
                f"Insufficient questions ({pool_count}) found matching criteria for user {user.id}. Minimum required: {min_required}."
            )
            # Raise validation error to be caught by caller (e.g., start service)
            raise ValidationError(
                _(
                    "Not enough questions found matching your criteria (found {count}, need at least {min}). Please broaden your filters."
                ).format(count=pool_count, min=min_required)
            )

    # --- Random Sampling Technique ---
    # 1. Get all potential IDs matching the criteria
    all_matching_ids = list(queryset.values_list("id", flat=True))
    count = len(all_matching_ids)

    if count == 0:
        logger.debug(
            f"get_filtered_questions: No questions found matching criteria for user {user.id if user else 'Anonymous'}."
        )
        return Question.objects.none()

    # 2. Determine how many to fetch and sample randomly
    num_to_fetch = min(limit, count)
    try:
        random_ids = random.sample(all_matching_ids, num_to_fetch)
    except ValueError as e:
        # Should only happen if logic above is flawed (e.g., num_to_fetch > count)
        logger.error(
            f"Error during random sampling in get_filtered_questions: {e}. IDs: {all_matching_ids}, Num: {num_to_fetch}",
            exc_info=True,
        )
        return Question.objects.none()

    # 3. Preserve the random order using Case/When
    preserved_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(random_ids)],
        output_field=IntegerField(),
    )

    # Final query retrieving only the randomly selected questions in the specific random order
    final_queryset = (
        Question.objects.filter(id__in=random_ids)
        .select_related(
            "subsection", "subsection__section", "skill"
        )  # Re-apply select_related
        .order_by(preserved_order)
    )

    logger.info(
        f"get_filtered_questions: Returning {len(random_ids)} questions for user {user.id if user else 'Anonymous'}."
    )
    return final_queryset


# --- Skill Proficiency Update Logic ---
# @transaction.atomic # Usually not needed here, called within other atomic transactions
def update_user_skill_proficiency(user: User, skill: Optional[Skill], is_correct: bool):
    """
    Updates the UserSkillProficiency record for a given user and skill based on an attempt.
    Creates the record if it doesn't exist. Logs errors but does not raise them
    to avoid interrupting the main flow (e.g., test submission).

    Args:
        user: The user whose proficiency is being updated.
        skill: The Skill associated with the question attempted. Can be None.
        is_correct: Boolean indicating if the attempt was correct.
    """
    if not skill:
        logger.debug(
            f"Proficiency update skipped for user {user.id}: No skill associated with the question."
        )
        return
    if not user or not user.is_authenticated:
        # Should not happen if called from authenticated views/services
        logger.warning(
            "Proficiency update skipped: Invalid or anonymous user provided."
        )
        return
    # is_correct can be None if validation failed earlier, handle gracefully
    if is_correct is None:
        logger.warning(
            f"Proficiency update skipped for user {user.id}, skill {skill.id}: is_correct is None."
        )
        return

    try:
        # Use get_or_create for atomicity and simplicity
        proficiency, created = UserSkillProficiency.objects.get_or_create(
            user=user,
            skill=skill,
            defaults={
                "proficiency_score": 0.0,
                "attempts_count": 0,
                "correct_count": 0,
            },
        )
        # Call the model method to handle the update logic
        proficiency.record_attempt(
            is_correct=is_correct
        )  # Assumes this method saves itself
        if created:
            logger.info(
                f"Created skill proficiency record for user {user.id}, skill '{skill.name}' (ID: {skill.id}). Score after first attempt: {proficiency.proficiency_score:.2f}"
            )
        else:
            logger.info(
                f"Updated skill proficiency for user {user.id}, skill '{skill.name}' (ID: {skill.id}). New score: {proficiency.proficiency_score:.2f}, Attempts: {proficiency.attempts_count}"
            )

    except Exception as e:
        # Log error but don't interrupt the main process
        logger.error(
            f"Error updating proficiency for user {user.id}, skill {skill.id}: {e}",
            exc_info=True,
        )


# --- Test Attempt Answer Handling ---
@transaction.atomic
def record_single_answer(
    test_attempt: UserTestAttempt, question: Question, answer_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Records a single answer submitted by a user during an ongoing test attempt.

    Validates input, creates or updates the UserQuestionAttempt record, updates
    skill proficiency, and returns immediate feedback (hiding correct answer/explanation
    except in 'Traditional' mode).

    Args:
        test_attempt: The active UserTestAttempt instance.
        question: The Question instance being answered.
        answer_data: Dict containing 'selected_answer' (A, B, C, or D) and
                     optionally 'time_taken_seconds'.

    Returns:
        A dictionary containing feedback:
            {
                'question_id': int,
                'is_correct': bool,
                'correct_answer': Optional[str], # Only populated for Traditional mode
                'explanation': Optional[str],    # Only populated for Traditional mode
                'feedback_message': str          # User-facing message
            }

    Raises:
        serializers.ValidationError: If the input is invalid, the test attempt is not
                                     active, or the question is not part of the attempt.
    """
    user = test_attempt.user
    # Basic validation checks
    if not user or not user.is_authenticated:
        # Should be caught by permissions, but good practice
        raise serializers.ValidationError(
            _("Authentication required to record an answer.")
        )

    if test_attempt.status != UserTestAttempt.Status.STARTED:
        logger.warning(
            f"Attempt to record answer for non-active test attempt {test_attempt.id} (Status: {test_attempt.status}) by user {user.id}."
        )
        raise serializers.ValidationError(
            {"non_field_errors": [_("This test attempt is not currently active.")]}
        )

    # Ensure the question being answered belongs to this test attempt
    # Assumes test_attempt.question_ids stores the list/queryset of intended IDs
    if question.id not in test_attempt.question_ids:
        logger.error(
            f"User {user.id} attempted to answer Q:{question.id} which is NOT in the question list for TestAttempt:{test_attempt.id}."
        )
        raise serializers.ValidationError(
            {
                "question_id": [
                    _("This question is not part of the current test attempt.")
                ]
            }
        )

    selected_answer = answer_data.get("selected_answer")
    if selected_answer not in UserQuestionAttempt.AnswerChoice.values:
        raise serializers.ValidationError(
            {
                "selected_answer": [
                    _("Invalid answer choice provided. Please select A, B, C, or D.")
                ]
            }
        )

    # Determine UserQuestionAttempt.Mode based on the type of test attempt
    mode_map = {
        UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        UserTestAttempt.AttemptType.PRACTICE: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.SIMULATION: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.TRADITIONAL: UserQuestionAttempt.Mode.TRADITIONAL,
        # Add mappings for any future test types
    }
    mode = mode_map.get(test_attempt.attempt_type)
    if not mode:
        # This indicates a configuration mismatch
        logger.error(
            f"Cannot map UserTestAttempt type '{test_attempt.attempt_type}' to UserQuestionAttempt.Mode for TestAttempt:{test_attempt.id}. Falling back to 'TEST'."
        )
        mode = UserQuestionAttempt.Mode.TEST  # Fallback to a sensible default

    # Create or update the specific question attempt record within this test attempt
    # update_or_create handles cases where a user might change their answer before submitting the test
    attempt_defaults = {
        "selected_answer": selected_answer,
        "is_correct": selected_answer
        == question.correct_answer,  # Calculate correctness directly
        "time_taken_seconds": answer_data.get("time_taken_seconds"),
        "mode": mode,
        "attempted_at": timezone.now(),
    }
    question_attempt, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        test_attempt=test_attempt,
        question=question,
        defaults=attempt_defaults,
    )
    is_correct = question_attempt.is_correct  # Use the value from the saved record

    log_prefix = "Recorded" if created else "Updated"
    logger.info(
        f"{log_prefix} answer for Q:{question.id} in TestAttempt:{test_attempt.id} by User:{user.id}. Choice: {selected_answer}, Correct: {is_correct}, Mode: {mode}"
    )

    # Update user's proficiency for the skill related to this question
    update_user_skill_proficiency(
        user=user, skill=question.skill, is_correct=is_correct
    )

    # --- Prepare Immediate Feedback ---
    # Default feedback hides sensitive info during tests
    feedback = {
        "question_id": question.id,
        "is_correct": is_correct,
        "correct_answer": None,
        "explanation": None,
        "feedback_message": _("Answer recorded."),
    }

    # Reveal answer/explanation immediately ONLY for 'Traditional' practice mode
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        feedback["correct_answer"] = question.correct_answer
        feedback["explanation"] = question.explanation  # Provide full explanation
        feedback["feedback_message"] = (
            _("Answer recorded. See feedback below.")
            if is_correct
            else _("Answer recorded. The correct answer is shown below.")
        )

    return feedback


# --- Test Attempt Completion Logic ---
@transaction.atomic
def complete_test_attempt(test_attempt: UserTestAttempt) -> Dict[str, Any]:
    """
    Finalizes a test attempt, calculates scores (except for Traditional mode),
    updates user profile for Level Assessments, updates status, and returns results.

    Args:
        test_attempt: The UserTestAttempt instance to complete.

    Returns:
        A dictionary containing the final results and status. Structure varies slightly
        for Traditional mode vs. others.
        Example (Non-Traditional):
            {
                "attempt_id": int, "status": str, "score_percentage": float, ...,
                "smart_analysis": str, "message": str, "updated_profile": Optional[dict]
            }
        Example (Traditional):
            {'detail': str}

    Raises:
        serializers.ValidationError: If the attempt is not active or cannot be completed.
    """
    user = test_attempt.user
    if not user or not user.is_authenticated:
        raise serializers.ValidationError(
            _("Authentication required to complete a test attempt.")
        )

    if test_attempt.status != UserTestAttempt.Status.STARTED:
        logger.warning(
            f"Attempt to complete non-active or already finished test attempt {test_attempt.id} (Status: {test_attempt.status}) by user {user.id}."
        )
        raise serializers.ValidationError(
            {
                "non_field_errors": [
                    _("This test attempt is not active or has already been completed.")
                ]
            }
        )

    # --- Handle Traditional Attempt Completion (Simpler) ---
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.save(update_fields=["status", "end_time", "updated_at"])
        logger.info(
            f"Traditional practice session {test_attempt.id} marked as completed for user {user.id}."
        )
        # Return a simple confirmation message
        return {"detail": _("Traditional practice session ended successfully.")}

    # --- Handle Non-Traditional Attempt Completion (Requires Scoring, etc.) ---
    else:
        # Efficiently fetch related question attempts needed for scoring
        question_attempts_qs = test_attempt.question_attempts.select_related(
            "question__subsection__section",  # For score breakdown by section
            "question__skill",  # Potentially useful for analysis
        ).all()

        answered_count = question_attempts_qs.count()
        total_questions = (
            test_attempt.num_questions
        )  # Assumes this was set correctly on creation

        if answered_count < total_questions:
            logger.warning(
                f"Test attempt {test_attempt.id} (Type: {test_attempt.attempt_type}) completed by user {user.id} with only {answered_count}/{total_questions} questions answered."
            )
        elif answered_count > total_questions:
            logger.error(
                f"Data inconsistency: Test attempt {test_attempt.id} has {answered_count} answers recorded but expected {total_questions}. Scoring based on recorded answers."
            )

        # Calculate and save scores using the model method (encapsulation)
        try:
            test_attempt.calculate_and_save_scores(
                question_attempts_qs=question_attempts_qs
            )
            test_attempt.refresh_from_db()  # Ensure we have the latest scores stored in the instance
        except Exception as e:
            logger.exception(
                f"Error calculating or saving scores for test attempt {test_attempt.id}, user {user.id}: {e}"
            )
            # Decide how to proceed: raise error, or mark complete without score?
            # Let's mark complete but log the failure prominently. Score fields might remain null.
            test_attempt.status = UserTestAttempt.Status.ERROR  # Or a custom status?
            test_attempt.end_time = timezone.now()
            test_attempt.save(update_fields=["status", "end_time", "updated_at"])
            raise serializers.ValidationError(
                _("An error occurred while calculating scores. Please contact support.")
            ) from e

        # Mark Test Attempt as Completed
        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()
        test_attempt.save(
            update_fields=["status", "end_time", "updated_at"]
        )  # Save status/time after scores
        logger.info(
            f"Test attempt {test_attempt.id} (Type: {test_attempt.attempt_type}) completed for user {user.id}. Final Score: {test_attempt.score_percentage}%"
        )

        # --- Update User Profile (Only for Level Assessment) ---
        updated_profile_data = None
        if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
            try:
                # Use select_for_update for pessimistic locking to prevent race conditions
                profile = UserProfile.objects.select_for_update().get(user=user)

                # Only update if scores are valid
                if (
                    test_attempt.score_verbal is not None
                    and test_attempt.score_quantitative is not None
                ):
                    profile.current_level_verbal = test_attempt.score_verbal
                    profile.current_level_quantitative = test_attempt.score_quantitative
                    profile.is_level_determined = True  # Mark assessment as completed
                    profile.save(
                        update_fields=[
                            "current_level_verbal",
                            "current_level_quantitative",
                            "is_level_determined",
                            "updated_at",
                        ]
                    )
                    # Import serializer locally to avoid circular dependency issues
                    from apps.users.api.serializers import UserProfileSerializer

                    updated_profile_data = UserProfileSerializer(profile).data
                    logger.info(
                        f"User profile levels updated for user {user.id} after Level Assessment {test_attempt.id}. Verbal: {profile.current_level_verbal}, Quant: {profile.current_level_quantitative}"
                    )
                else:
                    logger.error(
                        f"Skipping profile update for user {user.id} after assessment {test_attempt.id} because scores were invalid/null."
                    )

            except UserProfile.DoesNotExist:
                logger.error(
                    f"UserProfile not found for user {user.id} when trying to update levels after assessment {test_attempt.id}."
                )
                # Should not happen for logged-in users, indicates data integrity issue
            except Exception as e:
                logger.exception(
                    f"Error updating profile levels for user {user.id} after assessment {test_attempt.id}: {e}"
                )
                # Log error but don't fail the entire completion process

        # --- Placeholder: Trigger Gamification (e.g., via signals) ---
        # Signals connected to UserTestAttempt post_save (when status becomes COMPLETED)
        # could handle awarding points, badges, etc.

        # --- Generate Simple Smart Analysis ---
        # This could be expanded significantly or moved to a dedicated analysis service
        smart_analysis = _("Test completed successfully!")  # Default message
        results_summary = test_attempt.results_summary or {}
        try:
            # Example: Find weakest section/subsection based on summary
            weakest_area_name = None
            min_score = 101  # Start above max percentage
            for area_slug, data in results_summary.items():
                # Check if data is a dict and contains a valid score
                if (
                    isinstance(data, dict)
                    and isinstance(data.get("score"), (int, float))
                    and data["score"] is not None
                ):
                    if data["score"] < min_score:
                        min_score = data["score"]
                        # Prefer subsection name if available, else use section name
                        weakest_area_name = data.get("name") or area_slug

            # Provide advice if a weak area below a threshold is found
            if weakest_area_name and min_score < LEVEL_ASSESSMENT_SCORE_THRESHOLD:
                smart_analysis = _(
                    "Good effort! Your results suggest focusing more practice on '{area}' where your score was {score}%."
                ).format(area=weakest_area_name, score=round(min_score, 1))
            elif (
                test_attempt.score_percentage is not None
                and test_attempt.score_percentage >= 85
            ):
                smart_analysis = _(
                    "Excellent work! You demonstrated strong understanding in this test."
                )
            else:
                smart_analysis = _(
                    "Test completed! Keep practicing to improve further."
                )

        except Exception as e:
            logger.error(
                f"Error generating smart analysis for attempt {test_attempt.id}: {e}",
                exc_info=True,
            )
            # Use default message in case of error

        # --- Prepare Response Data for Serializer ---
        return {
            "attempt_id": test_attempt.id,
            "status": test_attempt.get_status_display(),
            "score_percentage": test_attempt.score_percentage,
            "score_verbal": test_attempt.score_verbal,
            "score_quantitative": test_attempt.score_quantitative,
            "results_summary": results_summary,  # Include detailed breakdown
            "answered_question_count": answered_count,
            "total_questions": total_questions,
            "smart_analysis": smart_analysis,
            "message": _("Test completed successfully. Results calculated."),
            "updated_profile": updated_profile_data,  # Include updated profile if applicable
        }


# --- Start Test Attempt Services ---


@transaction.atomic
def _start_test_attempt_base(
    user: User,
    attempt_type: UserTestAttempt.AttemptType,
    config_snapshot: Dict[str, Any],
    num_questions_requested: int,
    subsections: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    starred: bool = False,
    not_mastered: bool = False,
    exclude_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Internal base function to start any test attempt type.
    Handles limits, question selection, and object creation.
    """
    # 1. Check for existing active attempt
    if UserTestAttempt.objects.filter(
        user=user, status=UserTestAttempt.Status.STARTED
    ).exists():
        raise ValidationError(
            {
                "non_field_errors": [
                    _(
                        "Please complete or cancel your ongoing test before starting a new one."
                    )
                ]
            }
        )

    # 2. Check Usage Limits (Type Limit and Question Limit)
    try:
        limiter = UsageLimiter(user)
        limiter.check_can_start_test_attempt(attempt_type)  # Checks attempt type limit

        # Cap the number of questions based on plan limits
        max_allowed_questions = limiter.get_max_questions_per_attempt()
        actual_num_questions_to_select = num_questions_requested
        if (
            max_allowed_questions is not None
            and num_questions_requested > max_allowed_questions
        ):
            logger.info(
                f"User {user.id} requested {num_questions_requested} questions for {attempt_type.label}, capped at {max_allowed_questions}."
            )
            actual_num_questions_to_select = max_allowed_questions
        elif num_questions_requested <= 0:
            # Handle cases where 0 questions are requested (e.g., traditional start)
            actual_num_questions_to_select = 0

    except UsageLimitExceeded as e:
        logger.warning(
            f"Usage limit exceeded for user {user.id} trying to start {attempt_type.label}: {e}"
        )
        raise e  # Re-raise for the view to handle
    except ValueError as e:  # UsageLimiter init error
        logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
        raise ValidationError(
            {"non_field_errors": [_("Could not verify account limits.")]}
        )

    # 3. Select Questions
    selected_questions_queryset = Question.objects.none()
    selected_question_ids = []
    actual_num_selected = 0

    if actual_num_questions_to_select > 0:
        try:
            # Use get_filtered_questions, it raises ValidationError if min_required not met
            # Set min_required=1 to ensure at least one question if > 0 requested
            selected_questions_queryset = get_filtered_questions(
                user=user,
                limit=actual_num_questions_to_select,
                subsections=subsections,
                skills=skills,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=exclude_ids,
                min_required=1,  # Ensure at least 1 is found if requested > 0
            )
            selected_question_ids = list(
                selected_questions_queryset.values_list("id", flat=True)
            )
            actual_num_selected = len(selected_question_ids)

            # Log if fewer questions were found than requested/capped
            if actual_num_selected < actual_num_questions_to_select:
                logger.warning(
                    f"Found only {actual_num_selected} questions matching criteria for {attempt_type.label} start for user {user.id} (requested/capped: {actual_num_questions_to_select})."
                )

        except ValidationError as e:
            # Catch validation error from get_filtered_questions (insufficient questions)
            logger.warning(
                f"Insufficient questions validation error for user {user.id} starting {attempt_type.label}: {e.detail}"
            )
            raise e  # Re-raise for the view
        except Exception as e:
            logger.exception(
                f"Error selecting questions for {attempt_type.label} start for user {user.id}: {e}"
            )
            raise ValidationError(
                {
                    "non_field_errors": [
                        _(
                            "Failed to select questions for the test. Please try again later."
                        )
                    ]
                }
            )

    # 4. Update Config Snapshot with actual numbers
    config_snapshot["num_questions_requested"] = (
        num_questions_requested  # Original request
    )
    config_snapshot["num_questions_selected"] = (
        actual_num_selected  # Actual number included
    )
    config_snapshot["limit_applied"] = (
        max_allowed_questions is not None
        and num_questions_requested > max_allowed_questions
    )

    # 5. Create UserTestAttempt
    try:
        test_attempt = UserTestAttempt.objects.create(
            user=user,
            attempt_type=attempt_type,
            test_configuration=config_snapshot,
            question_ids=selected_question_ids,  # Store the ordered list of selected IDs
            status=UserTestAttempt.Status.STARTED,
        )
        logger.info(
            f"Started {attempt_type.label} (Attempt ID: {test_attempt.id}) for user {user.id} with {actual_num_selected} questions."
        )
    except Exception as e:
        logger.exception(
            f"Error creating {attempt_type.label} UserTestAttempt for user {user.id}: {e}"
        )
        raise ValidationError(
            {"non_field_errors": [_("Failed to start the test session.")]}
        )

    # 6. Calculate attempt number for this type
    attempt_number = UserTestAttempt.objects.filter(
        user=user, attempt_type=attempt_type
    ).count()  # New attempt is now included

    # 7. Prepare response data
    return {
        "attempt_id": test_attempt.id,
        "attempt_number_for_type": attempt_number,
        # Use the queryset obtained from get_filtered_questions which has the correct order
        "questions": selected_questions_queryset,
    }


# --- Public Service Functions for Starting Attempts ---


def start_level_assessment(
    user: User, sections: List[LearningSection], num_questions_requested: int
) -> Dict[str, Any]:
    """Starts a Level Assessment test."""
    section_slugs = [s.slug for s in sections]
    attempt_type = UserTestAttempt.AttemptType.LEVEL_ASSESSMENT

    # Determine relevant subsection slugs for question filtering
    subsection_slugs = list(
        LearningSubSection.objects.filter(section__slug__in=section_slugs).values_list(
            "slug", flat=True
        )
    )
    if not subsection_slugs:
        raise ValidationError(
            {"sections": [_("No subsections found for the selected sections.")]}
        )

    config_snapshot = {
        "test_type": attempt_type.value,
        "sections_requested": section_slugs,
        # num_questions will be added by base function
    }

    return _start_test_attempt_base(
        user=user,
        attempt_type=attempt_type,
        config_snapshot=config_snapshot,
        num_questions_requested=num_questions_requested,
        subsections=subsection_slugs,  # Filter by subsections within selected sections
        skills=None,
        starred=False,
        not_mastered=False,
        exclude_ids=None,
    )


def start_practice_or_simulation(
    user: User,
    attempt_type: UserTestAttempt.AttemptType,  # PRACTICE or SIMULATION
    num_questions_requested: int,
    name: Optional[str] = None,
    subsections: Optional[List[LearningSubSection]] = None,
    skills: Optional[List[Skill]] = None,
    starred: bool = False,
    not_mastered: bool = False,
) -> Dict[str, Any]:
    """Starts a Practice or Simulation test."""
    subsection_slugs = [s.slug for s in subsections] if subsections else None
    skill_slugs = [s.slug for s in skills] if skills else None

    config_snapshot = {
        "test_type": attempt_type.value,
        "name": name,
        "subsections_requested": subsection_slugs or [],
        "skills_requested": skill_slugs or [],
        "starred_requested": starred,
        "not_mastered_requested": not_mastered,
        # num_questions will be added by base function
    }

    return _start_test_attempt_base(
        user=user,
        attempt_type=attempt_type,
        config_snapshot=config_snapshot,
        num_questions_requested=num_questions_requested,
        subsections=subsection_slugs,
        skills=skill_slugs,
        starred=starred,
        not_mastered=not_mastered,
        exclude_ids=None,
    )


def start_traditional_practice(
    user: User,
    num_questions_initial: int,  # Can be 0
    subsections: Optional[List[LearningSubSection]] = None,
    skills: Optional[List[Skill]] = None,
    starred: bool = False,
    not_mastered: bool = False,
) -> Dict[str, Any]:
    """Starts a Traditional practice session."""
    attempt_type = UserTestAttempt.AttemptType.TRADITIONAL
    subsection_slugs = [s.slug for s in subsections] if subsections else None
    skill_slugs = [s.slug for s in skills] if skills else None

    config_snapshot = {
        "test_type": attempt_type.value,
        "subsections_requested": subsection_slugs or [],
        "skills_requested": skill_slugs or [],
        "starred_requested": starred,
        "not_mastered_requested": not_mastered,
        # num_questions (initial) will be added by base function
    }

    # Call base function, allowing 0 questions initially
    result = _start_test_attempt_base(
        user=user,
        attempt_type=attempt_type,
        config_snapshot=config_snapshot,
        num_questions_requested=num_questions_initial,
        subsections=subsection_slugs,
        skills=skill_slugs,
        starred=starred,
        not_mastered=not_mastered,
        exclude_ids=None,
    )

    # Add 'status' key needed by TraditionalPracticeStartResponseSerializer
    result["status"] = UserTestAttempt.Status.STARTED.value
    return result


# --- Retake Test Attempt Service ---
@transaction.atomic
def retake_test_attempt(
    user: User, original_attempt: UserTestAttempt
) -> Dict[str, Any]:
    """
    Starts a new test attempt based on the configuration of a previous one.
    Handles limits, finding new questions, and creating the new attempt.
    """
    # 1. Check for Existing Active Test
    if UserTestAttempt.objects.filter(
        user=user, status=UserTestAttempt.Status.STARTED
    ).exists():
        raise ValidationError(
            {
                "non_field_errors": [
                    _(
                        "Please complete or cancel your ongoing test before starting a new one."
                    )
                ]
            }
        )

    # 2. Extract and Validate Original Config
    original_config_snapshot = original_attempt.test_configuration
    if not isinstance(original_config_snapshot, dict):
        logger.error(
            f"Invalid config snapshot for original attempt {original_attempt.id} during retake."
        )
        raise ValidationError(
            {"detail": _("Original test configuration is missing or invalid.")}
        )

    # Determine original type and parameters needed for filtering
    original_attempt_type = (
        original_attempt.attempt_type
    )  # Use the reliable field from the model
    num_questions = original_config_snapshot.get(
        "num_questions_selected"
    )  # Use actual selected number from original
    if num_questions is None:  # Fallback for older snapshots?
        num_questions = original_config_snapshot.get(
            "num_questions_used"
        ) or original_config_snapshot.get("num_questions")
    if not isinstance(num_questions, int) or num_questions <= 0:
        # If original had 0 questions, retake doesn't make sense? Or should allow starting with 0?
        # Let's require original to have had questions.
        raise ValidationError(
            {"detail": _("Cannot retake a test that had no questions selected.")}
        )

    # Extract filters (handle different snapshot structures)
    sub_slugs = original_config_snapshot.get("subsections_requested", [])
    skill_slugs = original_config_snapshot.get("skills_requested", [])
    starred = original_config_snapshot.get("starred_requested", False)
    not_mastered = original_config_snapshot.get("not_mastered_requested", False)
    # Handle nested 'config' dict if present
    if isinstance(original_config_snapshot.get("config"), dict):
        nested_config = original_config_snapshot["config"]
        sub_slugs = nested_config.get("subsections", sub_slugs)
        skill_slugs = nested_config.get("skills", skill_slugs)
        starred = nested_config.get("starred", starred)
        not_mastered = nested_config.get("not_mastered", not_mastered)

    # 3. Check Usage Limits for the *new* attempt
    try:
        limiter = UsageLimiter(user)
        limiter.check_can_start_test_attempt(original_attempt_type)
        max_allowed_questions = limiter.get_max_questions_per_attempt()
        if max_allowed_questions is not None and num_questions > max_allowed_questions:
            logger.info(
                f"Retake attempt for user {user.id} (original: {original_attempt.id}) capped from {num_questions} to {max_allowed_questions} questions."
            )
            num_questions = max_allowed_questions  # Cap the number for the new attempt
    except UsageLimitExceeded as e:
        raise e
    except ValueError as e:
        logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
        raise ValidationError(
            {"non_field_errors": [_("Could not verify account limits.")]}
        )

    # 4. Select New Questions
    new_questions_queryset = Question.objects.none()
    try:
        # First, try excluding questions from the original attempt
        new_questions_queryset = get_filtered_questions(
            user=user,
            limit=num_questions,
            subsections=sub_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=original_attempt.question_ids,  # Exclude original Qs
            min_required=0,  # Don't fail if fewer than num_questions are found *without* originals
        )
        new_question_ids = list(new_questions_queryset.values_list("id", flat=True))
        ids_count = len(new_question_ids)

        # Fallback: If not enough *new* questions, try again *including* originals
        if ids_count < num_questions:
            logger.warning(
                f"Could not find {num_questions} *new* questions for retake of {original_attempt.id} (found {ids_count}). Trying again including original questions."
            )
            new_questions_queryset_fallback = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=None,  # No exclusion
                min_required=1,  # Must find at least 1 question overall
            )
            # Use the fallback queryset for selection
            new_questions_queryset = new_questions_queryset_fallback
            new_question_ids = list(new_questions_queryset.values_list("id", flat=True))
            ids_count = len(new_question_ids)

        if ids_count == 0:
            raise ValidationError(
                {
                    "detail": _(
                        "No suitable questions found to generate a similar test based on the original criteria."
                    )
                }
            )

        # Randomly sample if more questions were found than needed
        final_num_to_select = min(num_questions, ids_count)
        if ids_count > final_num_to_select:
            final_question_ids = random.sample(new_question_ids, final_num_to_select)
            # Re-fetch queryset with correct order
            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(final_question_ids)],
                output_field=IntegerField(),
            )
            new_questions_queryset = (
                Question.objects.filter(id__in=final_question_ids)
                .select_related("subsection", "subsection__section", "skill")
                .order_by(preserved_order)
            )
        else:
            # Use all found questions, queryset already has random order from get_filtered_questions
            final_question_ids = new_question_ids
            # Queryset is already new_questions_queryset

        actual_num_selected = len(final_question_ids)
        if actual_num_selected < num_questions:
            logger.warning(
                f"Only selecting {actual_num_selected} questions for retake of {original_attempt.id} (target was {num_questions}) due to availability."
            )

    except ValidationError as e:  # Catch validation errors from get_filtered_questions
        raise e
    except Exception as e:
        logger.exception(
            f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
        )
        raise ValidationError(
            {"detail": _("Failed to select questions for the new test.")}
        )

    # 5. Create New Test Attempt
    # Create a new snapshot, marking it as a retake and updating selected count
    new_config_snapshot = original_config_snapshot.copy()
    new_config_snapshot["retake_of_attempt_id"] = original_attempt.id
    new_config_snapshot["num_questions_selected"] = (
        actual_num_selected  # Update actual count
    )
    # Ensure nested config dict also has updated count if it exists
    if isinstance(new_config_snapshot.get("config"), dict):
        new_config_snapshot["config"]["num_questions_selected"] = actual_num_selected

    try:
        new_attempt = UserTestAttempt.objects.create(
            user=user,
            attempt_type=original_attempt_type,
            test_configuration=new_config_snapshot,
            question_ids=final_question_ids,
            status=UserTestAttempt.Status.STARTED,
        )
        logger.info(
            f"Started retake (New Attempt: {new_attempt.id}) of original attempt {original_attempt.id} for user {user.id}."
        )
    except Exception as e:
        logger.exception(
            f"Error creating retake UserTestAttempt for user {user.id} (original: {original_attempt.id}): {e}"
        )
        raise ValidationError(
            {"non_field_errors": [_("Failed to start the new similar test.")]}
        )

    # 6. Calculate attempt number
    attempt_number = UserTestAttempt.objects.filter(
        user=user, attempt_type=original_attempt_type
    ).count()

    # 7. Prepare response data
    return {
        "attempt_id": new_attempt.id,
        "attempt_number_for_type": attempt_number,
        "questions": new_questions_queryset,  # Use the final queryset with correct order/selection
    }


# --- Traditional Mode Action Service ---
@transaction.atomic
def record_traditional_action_and_get_data(
    user: User,
    test_attempt: UserTestAttempt,
    question: Question,
    action_type: str,  # e.g., 'hint', 'eliminate', 'reveal_answer', 'reveal_explanation'
) -> Optional[Union[str, bool]]:
    """
    Records a specific action (hint, eliminate, reveal) in UserQuestionAttempt
    for a traditional session and returns the relevant data (hint text, answer, explanation).
    """
    # Basic validation (already done in view, but good practice)
    if (
        test_attempt.attempt_type != UserTestAttempt.AttemptType.TRADITIONAL
        or test_attempt.status != UserTestAttempt.Status.STARTED
        or test_attempt.user != user
    ):
        raise PermissionDenied(_("Action not valid for this session."))

    update_fields = {}
    return_data = None

    if action_type == "hint":
        update_fields = {"used_hint": True}
        return_data = question.hint
    elif action_type == "eliminate":
        update_fields = {"used_elimination": True}
        return_data = True  # Indicate success
    elif action_type == "reveal_answer":
        update_fields = {"revealed_answer": True}
        return_data = question.correct_answer
    elif action_type == "reveal_explanation":
        update_fields = {"revealed_explanation": True}
        return_data = question.explanation
    else:
        logger.error(f"Unknown traditional action type '{action_type}' requested.")
        raise ValueError("Invalid action type specified.")

    try:
        # Use update_or_create to record the action. Handles first interaction or subsequent ones.
        attempt_record, created = UserQuestionAttempt.objects.update_or_create(
            user=user,
            test_attempt=test_attempt,
            question=question,
            defaults={
                **update_fields,
                "mode": UserQuestionAttempt.Mode.TRADITIONAL,  # Ensure mode is set
                "attempted_at": timezone.now(),  # Update interaction time
            },
        )
        action_keys = ", ".join(update_fields.keys())
        logger.info(
            f"Recorded action ({action_keys}) for Q:{question.id}, Trad. Attempt:{test_attempt.id}, User:{user.id} (Created: {created})"
        )

        # Optionally update proficiency if revealing answer counts as an attempt?
        # if action_type == 'reveal_answer':
        #     update_user_skill_proficiency(user=user, skill=question.skill, is_correct=False) # Assume incorrect if revealed

        return return_data

    except Exception as e:
        action_keys = ", ".join(update_fields.keys())
        logger.exception(
            f"Error recording action ({action_keys}) for Q:{question.id}, Attempt:{test_attempt.id}, User:{user.id}: {e}"
        )
        raise APIException(
            _("Failed to record action."), status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# --- Emergency Mode Plan Generation ---
def generate_emergency_plan(
    user: User,
    available_time_hours: Optional[int] = None,
    focus_areas: Optional[
        List[str]
    ] = None,  # List of SECTION slugs (e.g., 'verbal', 'quantitative')
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    num_weak_skills: int = EMERGENCY_MODE_WEAK_SKILL_COUNT,
    default_question_count: int = EMERGENCY_MODE_DEFAULT_QUESTIONS,
) -> Dict[str, Any]:
    """
    Generates a quick study plan for Emergency Mode based on the user's weakest skills.

    Args:
        user: The user requesting the plan.
        available_time_hours: Optional estimated time available for study.
        focus_areas: Optional list of section slugs ('verbal', 'quantitative') to focus on.
        proficiency_threshold: Score below which a skill is considered weak.
        num_weak_skills: The number of weakest skills to target.
        default_question_count: Default number of questions if time is not specified.

    Returns:
        A dictionary representing the plan:
        {
            "focus_skills": List[Dict[str, str]], # [{'slug': 'skill-slug', 'name': 'Skill Name'}]
            "recommended_questions": int,
            "quick_review_topics": List[Dict[str, str]], # [{'name': 'SubSection Name', 'description': '...'}]
            "motivational_tips": List[str] # General tips
        }
    """
    plan = {
        "focus_skills": [],
        "recommended_questions": default_question_count,
        "quick_review_topics": [],
        "motivational_tips": random.sample(
            getattr(settings, "EMERGENCY_MODE_TIPS", [_("Focus and do your best!")]),
            k=min(
                len(getattr(settings, "EMERGENCY_MODE_TIPS", [])), 2
            ),  # Show 1 or 2 random tips
        ),
    }

    if not user or not user.is_authenticated:
        logger.warning("Cannot generate emergency plan for unauthenticated user.")
        plan["motivational_tips"].append(_("Log in to get a personalized plan!"))
        return plan

    # --- Determine Weak Skills ---
    try:
        # Base query for user's skill proficiencies
        proficiency_qs = UserSkillProficiency.objects.filter(user=user).select_related(
            "skill", "skill__subsection", "skill__subsection__section"
        )

        # Apply section focus if provided
        if focus_areas:
            proficiency_qs = proficiency_qs.filter(
                skill__subsection__section__slug__in=focus_areas
            )

        # Annotate with a score, defaulting to 0 if no record exists (less likely needed here)
        # Order by proficiency score ascending (weakest first)
        weakest_proficiencies = list(
            proficiency_qs.filter(proficiency_score__lt=proficiency_threshold).order_by(
                "proficiency_score"
            )[:num_weak_skills]
        )

        target_skill_ids = {p.skill_id for p in weakest_proficiencies if p.skill_id}

        if len(weakest_proficiencies) < num_weak_skills:
            # Need more skills - find skills user has attempted but are still weak-ish or least attempted
            logger.info(
                f"Found only {len(weakest_proficiencies)} skills below threshold {proficiency_threshold} for user {user.id} (Emergency Mode). Looking for other candidates."
            )
            needed = num_weak_skills - len(weakest_proficiencies)

            # Option 1: Skills attempted but still below a slightly higher threshold or just the next lowest
            additional_candidates = list(
                proficiency_qs.exclude(
                    skill_id__in=target_skill_ids
                ).order_by(  # Exclude already selected
                    "proficiency_score", "attempts_count"
                )[
                    :needed
                ]  # Lowest score, then fewest attempts
            )
            weakest_proficiencies.extend(additional_candidates)
            target_skill_ids.update(
                p.skill_id for p in additional_candidates if p.skill_id
            )

        if len(weakest_proficiencies) < num_weak_skills:
            # Still need more - find skills they *haven't* attempted yet in focused sections
            logger.info(
                f"Still need {num_weak_skills - len(weakest_proficiencies)} skills. Looking for unattempted skills for user {user.id}."
            )
            needed = num_weak_skills - len(weakest_proficiencies)
            unattempted_skills_qs = Skill.objects.filter(is_active=True).exclude(
                id__in=target_skill_ids
            )
            if focus_areas:
                unattempted_skills_qs = unattempted_skills_qs.filter(
                    subsection__section__slug__in=focus_areas
                )

            # Select randomly from unattempted skills
            unattempted_skills = list(
                unattempted_skills_qs.order_by("?")[:needed]
            )  # Random sample

            # Create mock proficiency objects for consistent structure (or just store slugs/names)
            # For simplicity, let's just store slugs/names directly for these
            plan["focus_skills"].extend(
                [{"slug": s.slug, "name": s.name} for s in unattempted_skills if s]
            )

        # Add the skills identified from proficiency records
        plan["focus_skills"].extend(
            [
                {"slug": p.skill.slug, "name": p.skill.name}
                for p in weakest_proficiencies
                if p.skill
            ]
        )
        # Ensure uniqueness if a skill was somehow added twice
        plan["focus_skills"] = list(
            {frozenset(item.items()): item for item in plan["focus_skills"]}.values()
        )

        # --- Determine Quick Review Topics (Subsections of weak skills) ---
        subsection_ids = {
            p.skill.subsection_id
            for p in weakest_proficiencies
            if p.skill and p.skill.subsection_id
        }
        if subsection_ids:
            review_topics = LearningSubSection.objects.filter(
                id__in=subsection_ids, is_active=True
            ).exclude(Q(description__isnull=True) | Q(description__exact=""))[
                :num_weak_skills
            ]  # Limit review topics

            plan["quick_review_topics"] = [
                {"name": topic.name, "description": topic.description}
                for topic in review_topics
            ]

    except Exception as e:
        logger.error(
            f"Error determining weak skills/topics for user {user.id} emergency plan: {e}",
            exc_info=True,
        )
        # Return default plan structure in case of error, maybe add a generic tip
        plan["motivational_tips"].append(
            _("Could not generate personalized focus areas due to an error.")
        )

    # --- Adjust Recommended Question Count based on available time ---
    if (
        available_time_hours
        and isinstance(available_time_hours, (int, float))
        and available_time_hours > 0
    ):
        try:
            estimated_questions = int(
                available_time_hours * 60 / EMERGENCY_MODE_ESTIMATED_MINS_PER_Q
            )
            plan["recommended_questions"] = max(
                EMERGENCY_MODE_MIN_QUESTIONS, estimated_questions
            )
            logger.info(
                f"Adjusted emergency plan question count to {plan['recommended_questions']} based on {available_time_hours} hours for user {user.id}."
            )
        except Exception as e:
            logger.error(
                f"Error adjusting question count based on time for user {user.id}: {e}"
            )
            # Keep default count

    logger.info(
        f"Generated emergency plan for user {user.id}. Focus Skills: {len(plan['focus_skills'])}, Rec Qs: {plan['recommended_questions']}, Review Topics: {len(plan['quick_review_topics'])}"
    )
    return plan
