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
)
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers  # Use DRF's validation error

from apps.learning.models import (
    LearningSubSection,
    Question,
    Skill,
    UserStarredQuestion,
)
from apps.users.models import UserProfile
from apps.study.models import (
    UserSkillProficiency,
    UserTestAttempt,
    UserQuestionAttempt,
)
import random
import logging
from typing import Optional, List, Dict, Any


logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_PROFICIENCY_THRESHOLD = getattr(settings, "DEFAULT_PROFICIENCY_THRESHOLD", 0.7)
EMERGENCY_MODE_DEFAULT_QUESTIONS = getattr(
    settings, "EMERGENCY_MODE_DEFAULT_QUESTIONS", 15
)
EMERGENCY_MODE_WEAK_SKILL_COUNT = getattr(
    settings, "EMERGENCY_MODE_WEAK_SKILL_COUNT", 3
)
EMERGENCY_MODE_TIPS = getattr(
    settings,
    "EMERGENCY_MODE_TIPS",
    [
        _("Take deep breaths before starting each question."),
        _("Don't get stuck on one question for too long."),
        _("Focus on understanding the concept, not just getting the answer."),
        _("Remember your preparation and trust your abilities."),
    ],
)


# --- Question Filtering Logic (Keep existing) ---
def get_filtered_questions(
    user,
    limit: int = 10,
    subsections: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    starred: bool = False,
    not_mastered: bool = False,
    exclude_ids: Optional[List[int]] = None,
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
) -> QuerySet[Question]:
    # ... (Keep existing implementation - it seems robust) ...
    # Ensure logging is adequate
    if limit <= 0:
        return Question.objects.none()

    queryset = Question.objects.filter(is_active=True).select_related(
        "subsection", "subsection__section", "skill"
    )
    filters = Q()

    if subsections:
        filters &= Q(subsection__slug__in=subsections)
    if skills:
        filters &= Q(skill__slug__in=skills)
    if starred:
        if not user or not user.is_authenticated:
            logger.warning(
                "get_filtered_questions: Attempted to filter by starred for anonymous user."
            )
        else:
            # Use Exists for efficiency
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            filters &= Q(Exists(starred_subquery))

    if not_mastered:
        if not user or not user.is_authenticated:
            logger.warning(
                "get_filtered_questions: Attempted to filter by not_mastered for anonymous user."
            )
        else:
            try:
                # Get IDs of skills user has proficiency records for AND are below threshold
                low_prof_skill_ids = UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=proficiency_threshold
                ).values_list("skill_id", flat=True)

                # Get IDs of all skills user has ANY proficiency record for
                attempted_skill_ids = UserSkillProficiency.objects.filter(
                    user=user
                ).values_list("skill_id", flat=True)

                # Convert to lists for the query
                low_prof_skill_ids_list = list(low_prof_skill_ids)
                attempted_skill_ids_list = list(attempted_skill_ids)

                # Filter logic:
                # Include questions where:
                # 1. The skill IS in the low proficiency list.
                # OR
                # 2. The question HAS a skill AND that skill ID is NOT in the list of attempted skills (meaning user never attempted it)
                not_mastered_filter = Q(skill_id__in=low_prof_skill_ids_list) | (
                    Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids_list)
                )
                filters &= not_mastered_filter
            except Exception as e:
                logger.error(
                    f"get_filtered_questions: Error applying 'not_mastered' filter for user {user.id}: {e}",
                    exc_info=True,
                )
                # Depending on desired behavior, either return empty or continue without this filter

    # Apply collected filters
    queryset = queryset.filter(filters)

    # Apply exclusions
    if exclude_ids:
        # Ensure exclude_ids are integers
        valid_exclude_ids = [id for id in exclude_ids if isinstance(id, int)]
        if valid_exclude_ids:
            queryset = queryset.exclude(id__in=valid_exclude_ids)

    # --- Random Sampling ---
    # Get all matching IDs first
    all_ids = list(
        queryset.values_list("id", flat=True)
    )  # Convert to list for sampling
    count = len(all_ids)

    if count == 0:
        return Question.objects.none()

    # Determine how many to fetch and sample randomly
    num_to_fetch = min(limit, count)
    try:
        random_ids = random.sample(all_ids, num_to_fetch)
    except ValueError as e:
        # Should not happen if count > 0 and num_to_fetch <= count
        logger.error(
            f"Error during random sampling in get_filtered_questions: {e}. IDs: {all_ids}, Num: {num_to_fetch}"
        )
        return Question.objects.none()

    # --- Preserve Random Order ---
    # Use Case/When to order by the random_ids list
    preserved_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(random_ids)],
        output_field=IntegerField(),
    )

    # Final query retrieving the selected questions in the random order
    return (
        Question.objects.filter(id__in=random_ids)
        .select_related(
            "subsection", "subsection__section", "skill"
        )  # Re-apply select_related
        .order_by(preserved_order)
    )


# --- Skill Proficiency Update Logic (Keep existing) ---
def update_user_skill_proficiency(user, skill: Optional[Skill], is_correct: bool):
    """
    Finds or creates a UserSkillProficiency record and updates it based on an attempt.
    Handles cases where the skill might be None.
    """
    if not skill:
        logger.debug(
            f"Proficiency update skipped for user {user.id}: No skill provided."
        )
        return
    if not user or not user.is_authenticated:
        logger.warning(f"Proficiency update skipped: Invalid user provided.")
        return

    try:
        proficiency, created = UserSkillProficiency.objects.get_or_create(
            user=user,
            skill=skill,
            defaults={
                "proficiency_score": 0.0,
                "attempts_count": 0,
                "correct_count": 0,
            },
        )
        proficiency.record_attempt(is_correct)
    except Exception as e:
        logger.error(
            f"Error updating proficiency for user {user.id}, skill {skill.id}: {e}",
            exc_info=True,
        )


# --- NEW: Service for handling a single answer submission ---
@transaction.atomic
def record_single_answer(
    test_attempt: UserTestAttempt, question: Question, answer_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Records a single answer for ANY ongoing UserTestAttempt.
    Creates/Updates UserQuestionAttempt, updates proficiency, returns feedback.

    Args:
        test_attempt: The UserTestAttempt instance.
        question: The Question instance being answered.
        answer_data: Dict containing 'selected_answer', 'time_taken_seconds' etc.

    Returns:
        Dict with result: {'question_id', 'is_correct', 'correct_answer', 'explanation', 'feedback_message'}

    Raises:
        serializers.ValidationError: If input is invalid or attempt not active/valid.
    """
    user = test_attempt.user
    if not user or not user.is_authenticated:
        # Should be caught by view permissions, but double-check
        raise serializers.ValidationError(_("Authentication required."))

    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise serializers.ValidationError(
            {"non_field_errors": [_("This test attempt is not currently active.")]}
        )

    # Ensure question is part of the attempt's defined list
    if question.id not in test_attempt.question_ids:
        logger.warning(
            f"User {user.id} attempted to answer Q:{question.id} which is not in Attempt:{test_attempt.id} question list."
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
            {"selected_answer": [_("Invalid answer choice provided.")]}
        )

    is_correct = selected_answer == question.correct_answer

    # Determine UserQuestionAttempt.Mode based on UserTestAttempt.AttemptType
    mode_map = {
        UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        UserTestAttempt.AttemptType.PRACTICE: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.SIMULATION: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.TRADITIONAL: UserQuestionAttempt.Mode.TRADITIONAL,
    }
    mode = mode_map.get(test_attempt.attempt_type)
    if not mode:
        logger.error(
            f"Could not map UserTestAttempt type '{test_attempt.attempt_type}' to UserQuestionAttempt mode for attempt {test_attempt.id}"
        )
        # Fallback or raise internal error? Let's fallback for now.
        mode = UserQuestionAttempt.Mode.TEST

    # Use update_or_create: allows changing answer in ongoing tests, creates if first time
    attempt_record, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        test_attempt=test_attempt,
        question=question,
        # Defaults are applied only if 'created' is True
        defaults={
            "selected_answer": selected_answer,
            "is_correct": is_correct,  # This will be calculated/set by model's save() if None
            "time_taken_seconds": answer_data.get("time_taken_seconds"),
            "used_hint": answer_data.get("used_hint", False),
            "used_elimination": answer_data.get("used_elimination", False),
            "used_solution_method": False,  # Revealing answer sets this flag separately
            "mode": mode,  # Set the determined mode
            "attempted_at": timezone.now(),  # Record interaction time
        },
    )
    # Re-fetch is_correct in case model's save calculated it
    is_correct = attempt_record.is_correct

    logger.info(
        f"{'Recorded' if created else 'Updated'} answer for Q:{question.id}, TestAttempt:{test_attempt.id}, User:{user.id}. Correct: {is_correct}"
    )

    # --- Update Skill Proficiency ---
    update_user_skill_proficiency(
        user=user, skill=question.skill, is_correct=is_correct
    )

    # --- Prepare Immediate Feedback ---
    # By default, don't reveal answer/explanation during tests
    feedback = {
        "question_id": question.id,
        "is_correct": is_correct,
        "correct_answer": None,
        "explanation": None,
        "feedback_message": _("Answer recorded."),
    }

    # Reveal answer/explanation ONLY for Traditional mode via this flow
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        feedback["correct_answer"] = question.correct_answer
        feedback["explanation"] = question.explanation
        feedback["feedback_message"] = _("Answer recorded. Feedback provided.")
        # Mark solution method used implicitly? Or require separate reveal endpoint?
        # Let's keep reveal separate for clarity.

    return feedback


# --- NEW: Service for completing a test attempt ---
@transaction.atomic
def complete_test_attempt(test_attempt: UserTestAttempt) -> Dict[str, Any]:
    """
    Finalizes a test attempt (Level Assessment, Practice, Simulation).
    Calculates scores, updates status, updates profile (if applicable).

    Args:
        test_attempt: The UserTestAttempt instance to complete.

    Returns:
        A dictionary containing the final results and status for the response serializer.

    Raises:
        serializers.ValidationError: If the attempt cannot be completed.
    """
    user = test_attempt.user
    if not user or not user.is_authenticated:
        raise serializers.ValidationError(_("Authentication required."))

    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise serializers.ValidationError(
            {
                "non_field_errors": [
                    _("This test attempt is not active or already completed/abandoned.")
                ]
            }
        )

    # Explicitly prevent completing Traditional attempts via this endpoint
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        logger.warning(
            f"User {user.id} attempted to use 'complete' endpoint for traditional attempt {test_attempt.id}."
        )
        raise serializers.ValidationError(
            {
                "non_field_errors": [
                    _(
                        "Traditional practice sessions must be ended using the 'end' endpoint."
                    )
                ]
            }
        )

    # --- Calculate Scores ---
    # Fetch all related UserQuestionAttempts efficiently for scoring
    question_attempts_qs = test_attempt.question_attempts.select_related(
        "question__subsection__section",  # Needed for score breakdown
        "question__skill",
    ).all()

    answered_count = question_attempts_qs.count()
    total_questions = test_attempt.num_questions

    if answered_count < total_questions:
        logger.warning(
            f"Test attempt {test_attempt.id} completed by user {user.id} with {answered_count}/{total_questions} questions answered."
        )
        # Score calculation should handle this based on total_questions

    # Call the model method to calculate and save scores
    test_attempt.calculate_and_save_scores(question_attempts_qs)  # Pass the queryset
    # Reload attempt from DB to get updated scores (calculate_and_save_scores saves them)
    test_attempt.refresh_from_db()

    # --- Mark Test Attempt Complete ---
    test_attempt.status = UserTestAttempt.Status.COMPLETED
    test_attempt.end_time = timezone.now()
    # Scores are already saved by calculate_and_save_scores, just save status/time
    test_attempt.save(update_fields=["status", "end_time", "updated_at"])
    logger.info(
        f"Test attempt {test_attempt.id} completed for user {user.id}. Final Score: {test_attempt.score_percentage}%"
    )

    # --- Update User Profile (If Level Assessment) ---
    updated_profile_data = None
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
        try:
            # Use select_for_update to lock the profile row during update
            profile = UserProfile.objects.select_for_update().get(user=user)
            profile.current_level_verbal = test_attempt.score_verbal
            profile.current_level_quantitative = test_attempt.score_quantitative
            profile.is_level_determined = True
            profile.save(
                update_fields=[
                    "current_level_verbal",
                    "current_level_quantitative",
                    "is_level_determined",
                    "updated_at",
                ]
            )
            # Use UserProfileSerializer to structure profile data for response
            from apps.users.api.serializers import UserProfileSerializer  # Local import

            updated_profile_data = UserProfileSerializer(profile).data
            logger.info(
                f"Profile level scores updated for user {user.id} after assessment {test_attempt.id}."
            )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for user {user.id} during level assessment score update for attempt {test_attempt.id}."
            )
            # Decide policy: fail completion or just log? Log for now.
        except Exception as e:
            logger.exception(
                f"Error updating profile levels for user {user.id} after assessment {test_attempt.id}: {e}"
            )
            # Log error, but completion likely succeeded otherwise

    # --- Trigger Gamification (Points/Badges) ---
    # This should be handled by signals listening to UserTestAttempt save where status becomes COMPLETED
    # from apps.gamification.services import award_test_completion_rewards # Example direct call (signals preferred)
    # award_test_completion_rewards(test_attempt)

    # --- Generate Smart Analysis ---
    results_summary = test_attempt.results_summary or {}
    smart_analysis = ""
    try:
        # Example: Identify weakest subsection based on score
        weakest_subsection = None
        min_score = 101  # Initialize higher than max possible score
        for slug, data in results_summary.items():
            if isinstance(data, dict) and "score" in data and data["score"] is not None:
                if data["score"] < min_score:
                    min_score = data["score"]
                    weakest_subsection = data.get("name")

        if weakest_subsection and min_score < 60:  # Define threshold for 'weak'
            smart_analysis = _(
                "Test completed! Good effort. Consider focusing more practice on {subsection} where your score was {score}%."
            ).format(subsection=weakest_subsection, score=round(min_score, 1))
        else:
            smart_analysis = _("Test completed successfully! Keep up the great work.")

    except Exception as e:
        logger.error(
            f"Error generating smart analysis for attempt {test_attempt.id}: {e}"
        )
        smart_analysis = _("Test completed successfully.")  # Fallback message

    # --- Prepare Response Data ---
    return {
        "attempt_id": test_attempt.id,
        "status": test_attempt.get_status_display(),  # Use display value for response
        "score_percentage": test_attempt.score_percentage,
        "score_verbal": test_attempt.score_verbal,
        "score_quantitative": test_attempt.score_quantitative,
        "results_summary": results_summary,
        "answered_question_count": answered_count,
        "total_questions": total_questions,
        "smart_analysis": smart_analysis,
        "message": _("Test completed successfully. Results calculated."),
        "updated_profile": updated_profile_data,  # Include serialized profile data if updated
    }


# --- Emergency Mode Plan Generation ---
def generate_emergency_plan(
    user,
    available_time_hours: Optional[int] = None,
    focus_areas: Optional[List[str]] = None,  # Section slugs
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    num_weak_skills: int = EMERGENCY_MODE_WEAK_SKILL_COUNT,
    default_question_count: int = EMERGENCY_MODE_DEFAULT_QUESTIONS,
) -> Dict[str, Any]:
    """
    Generates a study plan for Emergency Mode based on user's weak areas.
    """
    plan = {
        "focus_skills": [],  # List of skill slugs
        "recommended_questions": default_question_count,
        "quick_review_topics": [],  # List of strings
    }
    if not user or not user.is_authenticated:
        logger.warning("Cannot generate emergency plan for unauthenticated user.")
        return plan  # Return default empty plan

    # --- Determine Weak Skills ---
    try:
        proficiency_qs = UserSkillProficiency.objects.filter(
            user=user, proficiency_score__lt=proficiency_threshold
        ).select_related("skill", "skill__subsection", "skill__subsection__section")

        if focus_areas:
            proficiency_qs = proficiency_qs.filter(
                skill__subsection__section__slug__in=focus_areas
            )

        # Weakest skills first
        weak_proficiencies = list(
            proficiency_qs.order_by("proficiency_score")[:num_weak_skills]
        )

        if not weak_proficiencies:
            # Fallback: Find skills with lowest score even if above threshold, or least attempted
            logger.info(
                f"No skills below threshold {proficiency_threshold} found for user {user.id} in Emergency Mode. Selecting least proficient overall."
            )
            least_proficient = list(
                UserSkillProficiency.objects.filter(user=user)
                .select_related("skill")
                .order_by("proficiency_score")[:num_weak_skills]
            )
            if least_proficient:
                plan["focus_skills"] = [
                    p.skill.slug for p in least_proficient if p.skill
                ]
            else:
                # Ultimate fallback: random skills if user has no proficiency data at all
                random_skill_slugs = list(
                    Skill.objects.filter(is_active=True)
                    .order_by("?")
                    .values_list("slug", flat=True)[:num_weak_skills]
                )
                plan["focus_skills"] = random_skill_slugs
        else:
            plan["focus_skills"] = [p.skill.slug for p in weak_proficiencies if p.skill]

            # --- Determine Quick Review Topics (Example: Use subsection description) ---
            subsection_ids = {
                p.skill.subsection_id
                for p in weak_proficiencies
                if p.skill and p.skill.subsection_id
            }
            review_topics = (
                LearningSubSection.objects.filter(id__in=subsection_ids)
                .exclude(description__isnull=True)
                .exclude(description__exact="")
            )
            plan["quick_review_topics"] = list(
                review_topics.values_list("name", "description")
            )  # List of tuples (name, description)

    except Exception as e:
        logger.error(
            f"Error determining weak skills/topics for user {user.id} emergency plan: {e}",
            exc_info=True,
        )
        # Return default plan or re-raise depending on desired behavior

    # --- Adjust Question Count based on time ---
    if available_time_hours and available_time_hours > 0:
        # Estimate: ~2.5 mins per question
        estimated_questions = int(available_time_hours * 60 / 2.5)
        plan["recommended_questions"] = max(5, estimated_questions)  # Min 5 questions

    logger.info(f"Generated emergency plan for user {user.id}: {plan}")
    return plan
