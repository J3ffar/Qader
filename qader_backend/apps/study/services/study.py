import json
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
from django.utils.translation import (
    gettext_lazy as _,
    gettext,
)  # Import gettext as well for immediate translation
from django.conf import settings
from django.core.exceptions import ValidationError as CoreValidationError
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
)
from django.db import transaction
from django.utils import timezone
from openai import OpenAIError
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
    ConversationSession,
    UserSkillProficiency,
    UserTestAttempt,
    UserQuestionAttempt,
    EmergencyModeSession,
)
from django.contrib.auth import get_user_model

from apps.api.exceptions import UsageLimitExceeded
from apps.users.services import UsageLimiter
from apps.study.services.ai_manager import get_ai_manager
from apps.gamification import services as gamification_services
from apps.gamification.models import Badge
from django.db.models.signals import post_save
from apps.gamification.signals import (
    gamify_on_test_completed as gamify_test_completed_signal_handler,
)  # Specific import
from apps.gamification.services import (
    process_test_completion_gamification,
)  # New import

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

AI_ANALYSIS_DEFAULT_FALLBACK = _(
    "Test completed! Review your detailed results to identify areas for improvement."
)
AI_ANALYSIS_LOW_SCORE_THRESHOLD = getattr(
    settings, "AI_ANALYSIS_LOW_SCORE_THRESHOLD", 50
)
AI_ANALYSIS_HIGH_SCORE_THRESHOLD = getattr(
    settings, "AI_ANALYSIS_HIGH_SCORE_THRESHOLD", 85
)
AI_ANALYSIS_MAX_ANSWER_DETAILS = getattr(settings, "AI_ANALYSIS_MAX_ANSWER_DETAILS", 10)


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
            raise serializers.ValidationError(
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


# --- AI Performance Analysis Helper ---
def _format_results_summary_for_ai(results_summary: Optional[Dict[str, Any]]) -> str:
    """Formats the results_summary dictionary into a string for the AI prompt."""
    if not results_summary:
        return _("No detailed breakdown by topic available.")

    summary_lines = []
    for slug, data in results_summary.items():
        if isinstance(data, dict) and "name" in data and "score" in data:
            name = data.get("name", slug)
            score = data.get("score")
            if score is not None:
                # Ensure score is presented as a number for the AI
                score_str = (
                    f"{score:.1f}%" if isinstance(score, (float, int)) else str(score)
                )
                summary_lines.append(f"- {name}: {score_str}")
            else:
                summary_lines.append(f"- {name}: {_('N/A')}")  # Score not available
        # Handle cases where data might not be a dict or lack expected keys, though model validation should prevent this

    if not summary_lines:
        return _("Detailed topic scores are not available for this attempt.")
    return "\n".join(summary_lines)


def _format_user_answers_for_ai(
    user_test_attempt: UserTestAttempt,
    max_questions_to_detail: int = AI_ANALYSIS_MAX_ANSWER_DETAILS,
) -> str:
    """
    Formats user's question attempts into a string for the AI prompt.
    Focuses on incorrect answers first, then a sample of correct ones if space permits.
    """
    # Fetch question attempts with related question, skill, and subsection for context
    # This is a list comprehension that executes the query immediately.
    question_attempts = list(
        user_test_attempt.question_attempts.select_related(
            "question__subsection", "question__skill"
        ).all()
    )

    if not question_attempts:
        return _("No specific answer details available for this attempt.")

    answer_details_lines = []

    incorrect_attempts = [qa for qa in question_attempts if qa.is_correct is False]
    correct_attempts = [qa for qa in question_attempts if qa.is_correct is True]

    # Process incorrect attempts
    for qa in incorrect_attempts:
        if len(answer_details_lines) >= max_questions_to_detail:
            break
        q = qa.question  # Safe due to select_related
        subsection_name = q.subsection.name if q.subsection else _("N/A")
        skill_name = q.skill.name if q.skill else _("N/A")
        # Translators: Part of AI analysis summary showing an incorrect answer.
        # {subsection} is the topic, {skill} is the specific skill.
        # {user_ans} is user's choice, {correct_ans} is the right one.
        line = _(
            "Question in '{subsection}' (Skill: {skill}): Your answer '{user_ans}', Correct: '{correct_ans}' (Incorrect)."
        ).format(
            subsection=subsection_name,
            skill=skill_name,
            user_ans=qa.selected_answer or _("Not Answered"),
            correct_ans=q.correct_answer,  # Assuming Question model has correct_answer field
        )
        answer_details_lines.append(line)

    # If space, add some correct answers
    # Keep this part minimal to focus AI on areas of improvement from incorrect answers
    # For example, limit correct examples to a small number like 2-3 if incorrect ones are few.
    remaining_space_for_correct = max_questions_to_detail - len(answer_details_lines)
    if remaining_space_for_correct > 0:
        # Show only a few correct answers to not dilute focus on incorrect ones.
        # For instance, show at most 2-3 correct answers.
        num_correct_to_show = min(remaining_space_for_correct, 2)
        for qa in correct_attempts[:num_correct_to_show]:  # Take only the first few
            q = qa.question
            subsection_name = q.subsection.name if q.subsection else _("N/A")
            skill_name = q.skill.name if q.skill else _("N/A")
            # Translators: Part of AI analysis summary showing a correct answer.
            # {subsection} is the topic, {skill} is the specific skill.
            # {user_ans} is user's choice.
            line = _(
                "Question in '{subsection}' (Skill: {skill}): Your answer '{user_ans}' (Correct)."
            ).format(
                subsection=subsection_name,
                skill=skill_name,
                user_ans=qa.selected_answer,
            )
            answer_details_lines.append(line)

    if not answer_details_lines:
        # This might happen if all questions were skipped or if there's an issue fetching.
        return _("Could not retrieve specific answer details for analysis.")

    # Indicate if more answers were ommitted due to length constraints
    total_processed_in_detail = len(answer_details_lines)
    total_attempted_questions = len(question_attempts)
    if (
        total_attempted_questions > total_processed_in_detail
        and total_processed_in_detail >= max_questions_to_detail
    ):
        # Translators: Indicates more questions were answered than detailed in AI summary.
        answer_details_lines.append(
            _("... (and {num_more} other questions were answered).").format(
                num_more=total_attempted_questions - total_processed_in_detail
            )
        )

    return "\n".join(answer_details_lines)


def _generate_ai_performance_analysis(user: User, test_attempt: UserTestAttempt) -> str:
    """
    Generates a smart performance analysis using AI.
    Returns the AI-generated text or a fallback message.
    """
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for performance analysis (User: {user.id}, Attempt: {test_attempt.id}). Reason: {ai_manager.init_error}"
        )
        if test_attempt.score_percentage is not None:
            if test_attempt.score_percentage >= AI_ANALYSIS_HIGH_SCORE_THRESHOLD:
                return _(
                    "Excellent work! You demonstrated strong understanding in this test."
                )
            elif test_attempt.score_percentage < AI_ANALYSIS_LOW_SCORE_THRESHOLD:
                return _(
                    "Good effort! Keep practicing to improve your score. Review your answers to learn from any mistakes."
                )
        return AI_ANALYSIS_DEFAULT_FALLBACK

    overall_score_str = (
        f"{test_attempt.score_percentage:.1f}"
        if test_attempt.score_percentage is not None
        else _("N/A")
    )
    verbal_score_str = (
        f"{test_attempt.score_verbal:.1f}%"
        if test_attempt.score_verbal is not None
        else _("N/A")
    )
    quantitative_score_str = (
        f"{test_attempt.score_quantitative:.1f}%"
        if test_attempt.score_quantitative is not None
        else _("N/A")
    )

    user_answers_details_str = _format_user_answers_for_ai(test_attempt)

    context_params = {
        "overall_score": overall_score_str,
        "verbal_score_str": verbal_score_str,
        "quantitative_score_str": quantitative_score_str,
        "results_summary_str": _format_results_summary_for_ai(
            test_attempt.results_summary
        ),
        "test_type_display": test_attempt.get_attempt_type_display(),
        "user_answers_details_str": user_answers_details_str,
    }

    system_prompt = ai_manager._construct_system_prompt(
        ai_tone_value="encouraging_analytic",
        context_key="generate_test_performance_analysis",
        context_params=context_params,
    )

    trigger_message = _(
        "Please provide a performance analysis for the test I just completed based on my scores and answer summary."
    )

    ai_response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt,
        messages_for_api=[{"role": "user", "content": trigger_message}],
        temperature=0.6,
        max_tokens=450,  # Slightly increased max_tokens for potentially more detailed analysis
        response_format=None,
        user_id_for_tracking=str(user.id),
    )

    if (
        error_msg
        or not isinstance(ai_response_content, str)
        or not ai_response_content.strip()
    ):
        logger.error(
            f"AI performance analysis generation failed for User: {user.id}, Attempt: {test_attempt.id}. Error: {error_msg or 'Empty response'}. "
            f"AI Response: '{str(ai_response_content)[:200]}...'"
        )
        # More nuanced fallback based on scores if AI fails
        if test_attempt.score_percentage is not None:
            if test_attempt.score_percentage >= AI_ANALYSIS_HIGH_SCORE_THRESHOLD:
                return _("Fantastic job on this test! Your hard work is paying off.")
            elif test_attempt.score_percentage < AI_ANALYSIS_LOW_SCORE_THRESHOLD:
                weakest_area_name = None
                min_score = 101  # Initialize higher than max score
                if test_attempt.results_summary:
                    for area_slug, data in test_attempt.results_summary.items():
                        if (
                            isinstance(data, dict)
                            and isinstance(data.get("score"), (int, float))
                            and data["score"] is not None
                        ):
                            if data["score"] < min_score:
                                min_score = data["score"]
                                weakest_area_name = data.get("name") or area_slug
                if (
                    weakest_area_name and min_score < LEVEL_ASSESSMENT_SCORE_THRESHOLD
                ):  # Using a general threshold for "weak"
                    return _(
                        "Good effort! Your results suggest focusing more practice on '{area}' where your score was {score}%."
                    ).format(area=weakest_area_name, score=round(min_score, 1))
                return _(
                    "You've completed the test. Take some time to review your answers and identify areas for growth."
                )
        return AI_ANALYSIS_DEFAULT_FALLBACK  # Ultimate fallback

    logger.info(
        f"Successfully generated AI performance analysis for User: {user.id}, Attempt: {test_attempt.id}. Analysis: {ai_response_content[:200]}..."
    )
    return ai_response_content.strip()


@transaction.atomic
def complete_test_attempt(test_attempt: UserTestAttempt) -> Dict[str, Any]:
    user = test_attempt.user
    if not user or not user.is_authenticated:
        raise DRFValidationError(
            _("Authentication required to complete a test attempt.")
        )

    if test_attempt.status != UserTestAttempt.Status.STARTED:
        logger.warning(
            f"Attempt to complete non-active or already finished test attempt {test_attempt.id} (Status: {test_attempt.status}) by user {user.id}."
        )
        raise DRFValidationError(
            {
                "non_field_errors": [
                    _("This test attempt is not active or has already been completed.")
                ]
            }
        )

    signal_disconnected_successfully = False
    try:
        # Temporarily disconnect signal to prevent double processing if calculate_and_save_scores also saves
        disconnected = post_save.disconnect(
            receiver=gamify_test_completed_signal_handler,
            sender=UserTestAttempt,
            dispatch_uid="gamify_test_completed",
        )

        if disconnected:
            signal_disconnected_successfully = True
            logger.debug(
                f"Temporarily disconnected 'gamify_on_test_completed' signal (UID: gamify_test_completed) for attempt {test_attempt.id}."
            )
        else:
            logger.warning(
                f"Failed to disconnect 'gamify_on_test_completed' signal (UID: gamify_test_completed) for attempt {test_attempt.id}. Gamification might run twice if calculate_scores saves."
            )

        # --- REFACTORED LOGIC STARTS HERE ---

        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()

        total_questions = test_attempt.num_questions

        # This block is now unified for ALL attempt types, including Traditional.
        question_attempts_qs = test_attempt.question_attempts.select_related(
            "question__subsection__section", "question__skill"
        ).all()
        answered_count = question_attempts_qs.count()
        correct_answers_in_test_count = question_attempts_qs.filter(
            is_correct=True
        ).count()

        if total_questions > 0 and answered_count < total_questions:
            logger.warning(
                f"Test attempt {test_attempt.id} (Type: {test_attempt.get_attempt_type_display()}) completed by user {user.id} with only {answered_count}/{total_questions} questions answered."
            )
        elif (
            total_questions > 0 and answered_count > total_questions
        ):  # Should not happen
            logger.error(
                f"Data inconsistency: Test attempt {test_attempt.id} has {answered_count} answers recorded but expected {total_questions}. Scoring based on recorded answers."
            )

        # Calculate scores and save them (this will update score_percentage, etc. for all types)
        try:
            test_attempt.calculate_and_save_scores(
                question_attempts_qs=question_attempts_qs
            )  # This method saves score fields itself
            logger.info(
                f"Test attempt {test_attempt.id} (Type: {test_attempt.get_attempt_type_display()}) scores calculated for user {user.id}. Score: {test_attempt.score_percentage}%"
            )
        except Exception as e:
            # Log and set status to ERROR if score calculation is critical
            logger.exception(
                f"Error calculating or saving scores for test attempt {test_attempt.id}, user {user.id}: {e}"
            )
            test_attempt.status = UserTestAttempt.Status.ERROR

        # Save status and end_time. Score fields were saved by calculate_and_save_scores.
        # This needs to run AFTER score calculation in case of errors.
        service_controlled_update_fields = ["status", "end_time", "updated_at"]
        test_attempt.save(update_fields=service_controlled_update_fields)
        logger.info(
            f"Status and end_time saved for test_attempt {test_attempt.id}. Status is now {test_attempt.status.label}."
        )

        # --- REFACTORED LOGIC ENDS HERE ---

        # Initialize gamification_results before the try block
        gamification_results = {
            "total_points_earned": 0,
            "badges_won_details": [],
            "streak_info": {"was_updated": False, "current_days": 0},
        }

        logger.info(
            f"Before calling gamification service directly for test {test_attempt.id}, completion_points_awarded is: {test_attempt.completion_points_awarded}"
        )

        # Perform gamification processing *after* scores are saved and status is COMPLETED.
        try:
            gamification_results = process_test_completion_gamification(
                user, test_attempt
            )
        except Exception as e:
            logger.exception(
                f"Error processing gamification for test_attempt {test_attempt.id}: {e}"
            )

    finally:
        # Reconnect the signal regardless of success/failure within the try block
        if signal_disconnected_successfully:
            post_save.connect(
                gamify_test_completed_signal_handler,
                sender=UserTestAttempt,
                dispatch_uid="gamify_test_completed",
            )
            logger.debug(
                f"Reconnected 'gamify_on_test_completed' signal (UID: gamify_test_completed) for attempt {test_attempt.id}."
            )

    # Refresh the instance from DB to get any updates from signals or direct saves
    test_attempt.refresh_from_db()  # Important if gamification service modifies test_attempt

    # Update user profile for level assessments
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
        try:
            profile = UserProfile.objects.select_for_update().get(user=user)
            if (
                test_attempt.score_verbal is not None
                and test_attempt.score_quantitative is not None
            ):  # Ensure scores are valid before updating
                profile.current_level_verbal = test_attempt.score_verbal
                profile.current_level_quantitative = test_attempt.score_quantitative
                profile.save(
                    update_fields=[
                        "current_level_verbal",
                        "current_level_quantitative",
                        "updated_at",
                    ]
                )
                logger.info(
                    f"User profile levels updated for user {user.id} after Level Assessment {test_attempt.id}."
                )
            else:
                logger.error(
                    f"Skipping profile update for user {user.id} (Assessment {test_attempt.id}) due to invalid scores (verbal or quantitative is None)."
                )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile not found for user {user.id} during assessment completion."
            )
        except Exception as e:
            logger.exception(f"Error updating profile levels for user {user.id}: {e}")

    # --- Generate Smart Analysis (AI or Fallback) ---
    smart_analysis = AI_ANALYSIS_DEFAULT_FALLBACK  # Default fallback
    # The `smart_analysis` logic can remain different for traditional vs. other types.
    # Our goal was to fix the score, not the analysis text.
    if test_attempt.attempt_type != UserTestAttempt.AttemptType.TRADITIONAL:
        # Only generate AI analysis for non-traditional tests that have scores
        if (
            test_attempt.score_percentage is not None
        ):  # Ensure there's a score to analyze
            try:
                smart_analysis = _generate_ai_performance_analysis(user, test_attempt)
            except Exception as e:  # Catch any unexpected error during AI call
                logger.error(
                    f"Unexpected error generating AI smart analysis for attempt {test_attempt.id}: {e}",
                    exc_info=True,
                )
                # Fallback to simpler rule-based analysis if AI fails catastrophically
                if test_attempt.score_percentage >= AI_ANALYSIS_HIGH_SCORE_THRESHOLD:
                    smart_analysis = _(
                        "Excellent work! You demonstrated strong understanding in this test."
                    )
                elif test_attempt.score_percentage < AI_ANALYSIS_LOW_SCORE_THRESHOLD:
                    smart_analysis = _(
                        "Good effort! Review your results to identify areas for improvement and keep practicing."
                    )
                else:
                    smart_analysis = _(
                        "Well done on completing the test! Check your detailed results for insights."
                    )
        else:
            smart_analysis = _(
                "Test completed. Scores are not available for detailed analysis at this time."
            )
    else:
        # This simple analysis for Traditional is fine to keep.
        smart_analysis = _("Practice session ended.")
        if answered_count > 0:
            smart_analysis = _(
                "Practice session ended. You answered {count} questions."
            ).format(count=answered_count)

    score_data = {
        "overall": test_attempt.score_percentage,
        "verbal": test_attempt.score_verbal,
        "quantitative": test_attempt.score_quantitative,
    }

    badges_won_for_response = [
        {"slug": b["slug"], "name": b["name"], "description": b["description"]}
        for b in gamification_results.get("badges_won_details", [])
    ]

    points_from_correct_answers_this_test = (
        correct_answers_in_test_count * settings.POINTS_QUESTION_SOLVED_CORRECT
    )
    points_from_test_completion_event = gamification_results.get(
        "total_points_earned", 0
    )

    return {
        "attempt_id": test_attempt.id,
        "status": test_attempt.get_status_display(),
        "score": score_data,
        "results_summary": test_attempt.results_summary
        or {},  # Ensure it's at least an empty dict
        "answered_question_count": answered_count,
        "total_questions": total_questions,
        "correct_answers_in_test_count": correct_answers_in_test_count,
        "smart_analysis": smart_analysis,
        "points_from_test_completion_event": points_from_test_completion_event,
        "points_from_correct_answers_this_test": points_from_correct_answers_this_test,
        "badges_won": badges_won_for_response,
        "streak_info": {
            "updated": gamification_results.get("streak_info", {}).get(
                "was_updated", False
            ),
            "current_days": gamification_results.get("streak_info", {}).get(
                "current_days", 0
            ),
        },
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
        user=user,
        status=UserTestAttempt.Status.STARTED,
        attempt_type=attempt_type,
    ).exists():
        attempt_type_display = UserTestAttempt.AttemptType(attempt_type).label
        raise DRFValidationError(
            {
                "non_field_errors": [
                    _(
                        "You already have an active '{attempt_type}' in progress. Please complete or cancel it before starting another of the same type."
                    ).format(attempt_type=attempt_type_display)
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
        raise DRFValidationError(
            {"non_field_errors": [_("Could not verify account limits.")]}
        )

    # 3. Select Questions
    selected_questions_queryset = Question.objects.none()
    selected_question_ids = []
    actual_num_selected = 0

    if actual_num_questions_to_select > 0:
        try:
            # Use get_filtered_questions, it raises DRFValidationError if min_required not met
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

        except DRFValidationError as e:
            # Catch validation error from get_filtered_questions (insufficient questions)
            logger.warning(
                f"Insufficient questions validation error for user {user.id} starting {attempt_type.label}: {e.detail}"
            )
            raise e  # Re-raise for the view
        except Exception as e:
            logger.exception(
                f"Error selecting questions for {attempt_type.label} start for user {user.id}: {e}"
            )
            raise DRFValidationError(
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
        raise DRFValidationError(
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
        raise DRFValidationError(
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
        raise DRFValidationError(
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
        raise DRFValidationError(
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
        raise DRFValidationError(
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
    except (
        CoreValidationError
    ) as e:  # Or catch Core VE if get_filtered_questions uses it
        # --- FIXED: Convert Core VE to DRF VE ---
        raise DRFValidationError(e.message_dict or {"detail": e.messages})
    except ValueError as e:
        logger.error(f"Error initializing UsageLimiter for user {user.id}: {e}")
        raise DRFValidationError(
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
            raise DRFValidationError(
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

    except (
        DRFValidationError
    ) as e:  # Catch validation errors from get_filtered_questions
        raise e
    except Exception as e:
        logger.exception(
            f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
        )
        raise DRFValidationError(
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
        raise DRFValidationError(
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


DEFAULT_EMERGENCY_TIPS = [  # Ensure this is defined
    _("Take deep breaths before starting."),
    _("Focus on one question at a time."),
    _("Read questions carefully."),
    _("Manage your time effectively, but don't rush needlessly."),
    _("Trust your preparation and stay positive!"),
]


def _generate_ai_emergency_tips(
    user: User,
    target_skills_data: List[Dict[str, Any]],
    focus_area_names: List[str],
    available_time_hours: Optional[float] = None,
) -> List[str]:
    ai_manager = get_ai_manager()
    # Define fallback tips here, ensuring it's always a list of 2-3 strings
    num_fallback_tips = min(
        len(DEFAULT_EMERGENCY_TIPS),
        (
            random.randint(2, 3)
            if len(DEFAULT_EMERGENCY_TIPS) >= 2
            else len(DEFAULT_EMERGENCY_TIPS)
        ),
    )
    fallback_tips = (
        random.sample(DEFAULT_EMERGENCY_TIPS, k=num_fallback_tips)
        if DEFAULT_EMERGENCY_TIPS
        else ["Stay calm and focus!"]
    )

    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for emergency tips (User {user.id}). Reason: {ai_manager.init_error}. Using default tips."
        )
        return fallback_tips

    weak_skills_summary_list = [
        f"- {s['name']} ({s.get('reason', 'Needs practice')})"
        for s in target_skills_data[:3]  # Take top 3
    ]
    weak_skills_summary_str = (
        "\n".join(weak_skills_summary_list)
        if weak_skills_summary_list
        else _("  (General review recommended or user is new)")
    )

    focus_areas_str = (
        ", ".join(focus_area_names)
        if focus_area_names
        else _("Verbal and Quantitative sections")
    )

    time_context = (
        f"The user has approximately {available_time_hours:.1f} hours available."
        if available_time_hours and available_time_hours > 0
        else "Time is limited."
    )

    context_params_for_tips = {
        "focus_areas_str": focus_areas_str,
        "weak_skills_summary_str": weak_skills_summary_str,
        "time_context": time_context,
        # "weak_skill_example" is used in the template's example, not a direct param here
    }

    # Emergency tips usually have a specific, direct tone.
    # The `CONTEXTUAL_INSTRUCTIONS` for `generate_emergency_tips` already sets this context.
    # The `ai_tone_value` for `_construct_system_prompt` can be a default or specific for emergency.
    system_prompt_for_tips = ai_manager._construct_system_prompt(
        ai_tone_value=ConversationSession.AiTone.SERIOUS,  # e.g., emergency mode uses a serious, direct tone
        context_key="generate_emergency_tips",
        context_params=context_params_for_tips,
    )

    parsed_json_response, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt_for_tips,
        messages_for_api=[
            {"role": "user", "content": "Please generate the emergency study tips now."}
        ],  # Trigger
        temperature=0.8,
        max_tokens=1000,
        response_format={"type": "json_object"},
        user_id_for_tracking=str(user.id),
    )

    if error_msg:  # Includes JSON parsing errors
        logger.error(
            f"AI Manager error generating emergency tips for user {user.id}: {error_msg}. Using default tips."
        )
        return fallback_tips

    if isinstance(parsed_json_response, dict) and "tips" in parsed_json_response:
        generated_tips = parsed_json_response["tips"]
        if (
            isinstance(generated_tips, list)
            and all(isinstance(tip, str) for tip in generated_tips)
            and 1 < len(generated_tips) <= 10
        ):  # Expect 2 or 10 tips
            logger.info(
                f"Successfully generated {len(generated_tips)} AI emergency tips for user {user.id}."
            )
            return generated_tips
        else:
            logger.warning(
                f"AI returned invalid 'tips' structure or count for user {user.id}. JSON: {parsed_json_response}. Using default tips."
            )
    else:
        logger.warning(
            f"AI returned non-dict or 'tips' key missing for user {user.id} emergency tips. Response: {parsed_json_response}. Using default tips."
        )

    return fallback_tips  # Ultimate fallback


# --- Emergency Mode Plan Generation ---
def generate_emergency_plan(
    user: User,
    available_time_hours: Optional[float] = None,
    focus_areas: Optional[List[str]] = None,  # List of section slugs
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    num_weak_skills: int = EMERGENCY_MODE_WEAK_SKILL_COUNT,
    default_question_count: int = EMERGENCY_MODE_DEFAULT_QUESTIONS,
    min_question_count: int = EMERGENCY_MODE_MIN_QUESTIONS,
    estimated_mins_per_q: float = EMERGENCY_MODE_ESTIMATED_MINS_PER_Q,
) -> Dict[str, Any]:
    """
    Generates a more detailed study plan for Emergency Mode.

    Args:
        user: The user requesting the plan.
        available_time_hours: Optional estimated time available for study.
        focus_areas: Optional list of section slugs ('verbal', 'quantitative') to focus on.
        proficiency_threshold: Score below which a skill is considered weak.
        num_weak_skills: The number of weakest skills to target.
        default_question_count: Default number of questions if time is not specified.
        min_question_count: Minimum questions to recommend, regardless of time.
        estimated_mins_per_q: Estimated minutes per question for time calculation.

    Returns:
        A dictionary representing the plan with enhanced details:
        {
            "focus_area_names": List[str], # e.g., ["Verbal", "Quantitative"]
            "estimated_duration_minutes": Optional[int], # Based on time or question count
            "target_skills": [
                {
                    "slug": str, "name": str, "reason": str, # e.g., "Low score (0.3)", "Not attempted"
                    "current_proficiency": Optional[float], # Actual score if available
                    "subsection_name": str,
                }
            ],
            "recommended_question_count": int,
            "quick_review_topics": [
                {"slug": str, "name": str, "description": Optional[str]}
            ],
            "motivational_tips": List[str]
        }
    """
    if not user or not user.is_authenticated:
        logger.warning("Cannot generate emergency plan for unauthenticated user.")
        return {
            "focus_area_names": [],
            "estimated_duration_minutes": None,
            "target_skills": [],
            "recommended_question_count": 0,
            "quick_review_topics": [],
            "motivational_tips": [str(_("Please log in to get a personalized plan."))],
        }

    plan: Dict[str, Any] = {  # Type hint for plan
        "focus_area_names": [],
        "estimated_duration_minutes": None,
        "target_skills": [],
        "recommended_question_count": default_question_count,
        "quick_review_topics": [],
        "motivational_tips": [],
    }

    # --- Determine Recommended Question Count & Duration ---
    if (
        available_time_hours
        and isinstance(available_time_hours, (int, float))
        and available_time_hours > 0
    ):
        try:
            plan["estimated_duration_minutes"] = int(available_time_hours * 60)
            estimated_questions = int(
                plan["estimated_duration_minutes"] / estimated_mins_per_q
            )
            plan["recommended_question_count"] = max(
                min_question_count, estimated_questions
            )
        except ZeroDivisionError:  # Should not happen if estimated_mins_per_q is > 0
            logger.error(
                f"estimated_mins_per_q is zero, cannot calculate questions based on time."
            )
            plan["recommended_question_count"] = default_question_count
            plan["estimated_duration_minutes"] = (
                int(default_question_count * estimated_mins_per_q)
                if estimated_mins_per_q > 0
                else None
            )
        except Exception as e:
            logger.error(
                f"Error adjusting question count based on time for user {user.id}: {e}"
            )
            plan["recommended_question_count"] = default_question_count
            plan["estimated_duration_minutes"] = (
                int(default_question_count * estimated_mins_per_q)
                if estimated_mins_per_q > 0
                else None
            )
    else:
        plan["recommended_question_count"] = default_question_count
        plan["estimated_duration_minutes"] = (
            int(plan["recommended_question_count"] * estimated_mins_per_q)
            if estimated_mins_per_q > 0
            else None
        )

    # --- Determine Weak Skills & Focus Areas ---
    target_skills_data: List[Dict[str, Any]] = []
    target_skill_ids: Set[int] = set()
    subsection_ids_for_review: Set[int] = set()
    core_plan_error_tip_added = False

    try:
        proficiency_qs = UserSkillProficiency.objects.filter(user=user).select_related(
            "skill__subsection__section",
            "skill__subsection",
            "skill",  # Ensure all are selected
        )

        if (
            focus_areas
        ):  # focus_areas is list of section slugs like ["verbal", "quantitative"]
            focus_sections_qs = LearningSection.objects.filter(slug__in=focus_areas)
            proficiency_qs = proficiency_qs.filter(
                skill__subsection__section__slug__in=focus_areas
            )
            plan["focus_area_names"] = list(
                focus_sections_qs.values_list("name", flat=True)
            )
        else:
            all_user_section_names = list(
                proficiency_qs.values_list(
                    "skill__subsection__section__name", flat=True
                )
                .distinct()
                .exclude(skill__subsection__section__name__isnull=True)
            )
            plan["focus_area_names"] = (
                all_user_section_names
                if all_user_section_names
                else [_("Verbal"), _("Quantitative")]
            )

        # 1. Skills strictly below the threshold
        weakest_proficiencies = list(
            proficiency_qs.filter(proficiency_score__lt=proficiency_threshold).order_by(
                "proficiency_score"
            )[:num_weak_skills]
        )
        for p in weakest_proficiencies:
            if p.skill and p.skill_id not in target_skill_ids:
                target_skills_data.append(
                    {
                        "slug": p.skill.slug,
                        "name": p.skill.name,
                        "reason": str(
                            _("Low score ({score}%)").format(
                                score=round(p.proficiency_score * 100)
                            )
                        ),
                        "current_proficiency": round(p.proficiency_score, 2),
                        "subsection_name": (
                            p.skill.subsection.name
                            if p.skill.subsection
                            else str(_("N/A"))
                        ),
                    }
                )
                target_skill_ids.add(p.skill_id)
                if p.skill.subsection_id:
                    subsection_ids_for_review.add(p.skill.subsection_id)

        # 2. If needed, find other attempted skills
        needed = num_weak_skills - len(target_skills_data)
        if needed > 0:
            additional_candidates = list(
                proficiency_qs.exclude(skill_id__in=target_skill_ids).order_by(
                    "proficiency_score", "attempts_count"
                )[:needed]
            )
            for p in additional_candidates:
                if p.skill and p.skill_id not in target_skill_ids:
                    target_skills_data.append(
                        {
                            "slug": p.skill.slug,
                            "name": p.skill.name,
                            "reason": str(
                                _("Area for improvement ({score}%)").format(
                                    score=round(p.proficiency_score * 100)
                                )
                            ),
                            "current_proficiency": round(p.proficiency_score, 2),
                            "subsection_name": (
                                p.skill.subsection.name
                                if p.skill.subsection
                                else str(_("N/A"))
                            ),
                        }
                    )
                    target_skill_ids.add(p.skill_id)
                    if p.skill.subsection_id:
                        subsection_ids_for_review.add(p.skill.subsection_id)

        # 3. If still needed, find unattempted skills
        needed = num_weak_skills - len(target_skills_data)
        if needed > 0:
            unattempted_skills_qs = (
                Skill.objects.filter(is_active=True)
                .exclude(id__in=target_skill_ids)
                .select_related("subsection__section", "subsection")
            )
            if focus_areas:
                unattempted_skills_qs = unattempted_skills_qs.filter(
                    subsection__section__slug__in=focus_areas
                )
            unattempted_skills = list(unattempted_skills_qs.order_by("?")[:needed])

            for s in unattempted_skills:
                if s and s.id not in target_skill_ids:
                    target_skills_data.append(
                        {
                            "slug": s.slug,
                            "name": s.name,
                            "reason": str(_("Not attempted yet")),
                            "current_proficiency": None,
                            "subsection_name": (
                                s.subsection.name if s.subsection else str(_("N/A"))
                            ),
                        }
                    )
                    target_skill_ids.add(s.id)
                    if s.subsection_id:
                        subsection_ids_for_review.add(s.subsection_id)

        plan["target_skills"] = target_skills_data

        if subsection_ids_for_review:
            review_topics_qs = LearningSubSection.objects.filter(
                id__in=list(subsection_ids_for_review), is_active=True
            ).exclude(Q(description__isnull=True) | Q(description__exact=""))[
                :num_weak_skills
            ]
            plan["quick_review_topics"] = [
                {
                    "slug": topic.slug,
                    "name": topic.name,
                    "description": topic.description,
                }
                for topic in review_topics_qs
            ]

    except Exception as e:
        logger.error(
            f"Error determining weak skills/topics for user {user.id} emergency plan: {e}",
            exc_info=True,
        )
        plan["motivational_tips"].append(
            str(
                _(
                    "Could not generate personalized focus areas due to an error. Focusing on general review."
                )
            )
        )
        core_plan_error_tip_added = True

    # --- Generate Motivational Tips (AI or Fallback) ---
    try:
        ai_or_default_tips = _generate_ai_emergency_tips(
            user=user,
            target_skills_data=plan.get("target_skills", []),
            focus_area_names=plan.get("focus_area_names", []),
            available_time_hours=available_time_hours,
        )
    except Exception as ai_tip_error_call:
        logger.error(
            f"Error calling _generate_ai_emergency_tips for user {user.id}: {ai_tip_error_call}",
            exc_info=True,
        )
        # Fallback if the call to _generate_ai_emergency_tips itself fails
        num_tips_to_sample = min(len(DEFAULT_EMERGENCY_TIPS), 3)
        if not DEFAULT_EMERGENCY_TIPS or num_tips_to_sample == 0:
            ai_or_default_tips = [str(_("Remember to stay calm and focused!"))]
        else:
            ai_or_default_tips = random.sample(
                DEFAULT_EMERGENCY_TIPS, k=num_tips_to_sample
            )

    # <<< FIX: Convert all tips (whether from AI or defaults) to strings.
    # The AI returns strings, but the default list contains proxy objects.
    # This ensures the final list is always JSON serializable.
    final_tips = [str(tip) for tip in ai_or_default_tips]

    if core_plan_error_tip_added:
        plan["motivational_tips"].extend(final_tips)
    else:
        plan["motivational_tips"] = final_tips

    # Final safety check
    if not plan.get("motivational_tips"):
        plan["motivational_tips"] = [
            str(tip) for tip in random.sample(DEFAULT_EMERGENCY_TIPS, k=1)
        ]

    logger.info(
        f"Generated emergency plan for user {user.id}. Focus Areas: {plan['focus_area_names']}, "
        f"Skills: {len(plan['target_skills'])}, Rec Qs: {plan['recommended_question_count']}, "
        f"Review Topics: {len(plan['quick_review_topics'])}, Tips: {len(plan['motivational_tips'])}"
    )
    return plan


def _generate_ai_emergency_session_feedback(
    user: User,
    session: EmergencyModeSession,
    overall_score: float,
    results_summary: Dict[str, Any],
) -> str:
    """
    Generates tailored AI feedback for a completed Emergency Mode session.
    """
    ai_manager = get_ai_manager()
    fallback_message = _(
        "Great job completing your emergency session! Review your results to see where you excelled and what you can focus on next."
    )
    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for emergency session feedback (User: {user.id}, Session: {session.id}). Reason: {ai_manager.init_error}"
        )
        return fallback_message

    # Format data for the AI prompt
    overall_score_str = f"{overall_score:.1f}%"
    results_summary_str = _format_results_summary_for_ai(results_summary)

    context_params = {
        "overall_score_str": overall_score_str,
        "results_summary_str": results_summary_str,
        "focus_areas_str": ", ".join(
            session.suggested_plan.get("focus_area_names", [])
        ),
    }

    system_prompt = ai_manager._construct_system_prompt(
        ai_tone_value="encouraging_analytic",
        context_key="generate_emergency_session_feedback",
        context_params=context_params,
    )

    trigger_message = _(
        "Please provide a performance analysis for the emergency study session I just completed."
    )

    ai_response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt,
        messages_for_api=[{"role": "user", "content": trigger_message}],
        temperature=0.6,
        max_tokens=300,
        response_format=None,
        user_id_for_tracking=str(user.id),
    )

    if (
        error_msg
        or not isinstance(ai_response_content, str)
        or not ai_response_content.strip()
    ):
        logger.error(
            f"AI emergency session feedback generation failed for User: {user.id}, Session: {session.id}. Error: {error_msg or 'Empty response'}."
        )
        return fallback_message

    logger.info(
        f"Successfully generated AI feedback for emergency session {session.id} for user {user.id}."
    )
    return ai_response_content.strip()


@transaction.atomic
def complete_emergency_session(session: EmergencyModeSession) -> Dict[str, Any]:
    """
    Completes an emergency session, calculates scores, generates AI feedback,
    and saves the results with a structured, nested summary.

    Args:
        session: The EmergencyModeSession instance to complete.

    Returns:
        A dictionary containing the final results and feedback.

    Raises:
        DRFValidationError: If the session is already completed.
    """
    if session.end_time:
        raise DRFValidationError(
            _("This emergency session has already been completed.")
        )

    user = session.user
    question_attempts_qs = UserQuestionAttempt.objects.filter(
        emergency_session=session
    ).select_related(
        "question__subsection__section",
        "question__subsection",
    )  # Ensure related models are fetched efficiently

    if not question_attempts_qs.exists():
        # Handle case with no answers submitted
        session.end_time = timezone.now()
        session.overall_score = 0.0
        session.verbal_score = 0.0
        session.quantitative_score = 0.0
        session.results_summary = {"verbal": {}, "quantitative": {}}
        session.ai_feedback = _(
            "You completed the session without answering any questions. Try a few next time!"
        )
        session.save(
            update_fields=[
                "end_time",
                "overall_score",
                "verbal_score",
                "quantitative_score",
                "results_summary",
                "ai_feedback",
                "updated_at",
            ]
        )

        return {
            "session_id": session.id,
            "overall_score": 0.0,
            "verbal_score": 0.0,
            "quantitative_score": 0.0,
            "results_summary": session.results_summary,
            "ai_feedback": session.ai_feedback,
            "answered_question_count": 0,
            "correct_answers_count": 0,
        }

    # --- 1. Calculate Scores with Nested Structure ---
    # Structure for calculation: { 'section_slug': { 'name': str, 'total': int, 'correct': int, 'subsections': { 'sub_slug': ... } } }
    results_calc: Dict[str, Dict[str, Any]] = {}
    total_questions = 0
    correct_questions = 0

    for qa in question_attempts_qs:
        total_questions += 1
        if qa.is_correct:
            correct_questions += 1

        section = qa.question.subsection.section
        subsection = qa.question.subsection

        # Initialize section if not present
        if section.slug not in results_calc:
            results_calc[section.slug] = {
                "name": section.name,
                "total": 0,
                "correct": 0,
                "subsections": {},
            }

        # Initialize subsection if not present
        if subsection.slug not in results_calc[section.slug]["subsections"]:
            results_calc[section.slug]["subsections"][subsection.slug] = {
                "name": subsection.name,
                "total": 0,
                "correct": 0,
            }

        # Increment counts
        results_calc[section.slug]["total"] += 1
        results_calc[section.slug]["subsections"][subsection.slug]["total"] += 1
        if qa.is_correct:
            results_calc[section.slug]["correct"] += 1
            results_calc[section.slug]["subsections"][subsection.slug]["correct"] += 1

    # --- 2. Format Final Results JSON and Calculate Scores ---
    results_summary_final: Dict[str, Dict[str, Any]] = {}

    # Ensure both 'verbal' and 'quantitative' keys exist even if no questions were from that section
    for slug in ["verbal", "quantitative"]:
        if slug in results_calc:
            section_data = results_calc[slug]
            section_total = section_data["total"]
            section_correct = section_data["correct"]

            subsections_final = {}
            for sub_slug, sub_data in section_data["subsections"].items():
                sub_total = sub_data["total"]
                sub_correct = sub_data["correct"]
                subsections_final[sub_slug] = {
                    "name": sub_data["name"],
                    "score": (sub_correct / sub_total * 100) if sub_total > 0 else 0.0,
                }

            results_summary_final[slug] = {
                "name": section_data["name"],
                "score": (
                    (section_correct / section_total * 100)
                    if section_total > 0
                    else 0.0
                ),
                "subsections": subsections_final,
            }
        else:
            # Get section name from DB if no questions were attempted in it
            try:
                section_obj = LearningSection.objects.get(slug=slug)
                results_summary_final[slug] = {
                    "name": section_obj.name,
                    "score": 0.0,
                    "subsections": {},
                }
            except LearningSection.DoesNotExist:
                results_summary_final[slug] = {
                    "name": slug.capitalize(),
                    "score": 0.0,
                    "subsections": {},
                }

    overall_score = (
        (correct_questions / total_questions * 100) if total_questions > 0 else 0.0
    )
    verbal_score = results_summary_final.get("verbal", {}).get("score", 0.0)
    quantitative_score = results_summary_final.get("quantitative", {}).get("score", 0.0)

    # --- 3. Generate AI Feedback ---
    # We pass the flattened summary to the existing AI helper for simplicity
    flat_summary_for_ai = {}
    for section in results_summary_final.values():
        if "subsections" in section:
            flat_summary_for_ai.update(section["subsections"])

    ai_feedback = _generate_ai_emergency_session_feedback(
        user=user,
        session=session,
        overall_score=overall_score,
        results_summary=flat_summary_for_ai,
    )

    # --- 4. Save Results to Session Model ---
    session.end_time = timezone.now()
    session.overall_score = round(overall_score, 2)
    session.verbal_score = round(verbal_score, 2)
    session.quantitative_score = round(quantitative_score, 2)
    session.results_summary = results_summary_final
    session.ai_feedback = ai_feedback
    session.save(
        update_fields=[
            "end_time",
            "overall_score",
            "verbal_score",
            "quantitative_score",
            "results_summary",
            "ai_feedback",
            "updated_at",
        ]
    )
    logger.info(
        f"Completed emergency session {session.id} for user {user.id}. Score: {session.overall_score}%"
    )

    # --- 5. Prepare Response Data ---
    return {
        "session_id": session.id,
        "overall_score": session.overall_score,
        "verbal_score": session.verbal_score,
        "quantitative_score": session.quantitative_score,
        "results_summary": session.results_summary,
        "ai_feedback": session.ai_feedback,
        "answered_question_count": total_questions,
        "correct_answers_count": correct_questions,
    }
