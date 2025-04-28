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
    """
    Retrieves a filtered and randomized QuerySet of active Questions.
    Handles various filtering criteria including proficiency.
    """
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
            logger.warning("Attempted to filter by starred for anonymous user.")
        else:
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            filters &= Q(Exists(starred_subquery))

    if not_mastered:
        if not user or not user.is_authenticated:
            logger.warning("Attempted to filter by not_mastered for anonymous user.")
        else:
            try:
                low_prof_skill_ids = UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=proficiency_threshold
                ).values_list("skill_id", flat=True)
                attempted_skill_ids = UserSkillProficiency.objects.filter(
                    user=user
                ).values_list("skill_id", flat=True)

                low_prof_skill_ids_list = list(low_prof_skill_ids)
                attempted_skill_ids_list = list(attempted_skill_ids)

                not_mastered_filter = Q(skill_id__in=low_prof_skill_ids_list) | (
                    Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids_list)
                )
                filters &= not_mastered_filter
            except Exception as e:
                logger.error(
                    f"Error applying 'not_mastered' filter for user {user.id}: {e}",
                    exc_info=True,
                )

    queryset = queryset.filter(filters)

    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)

    all_ids = queryset.values_list("id", flat=True)
    count = all_ids.count()

    if count == 0:
        return Question.objects.none()

    num_to_fetch = min(limit, count)
    random_ids = random.sample(list(all_ids), num_to_fetch)

    preserved_order = Case(
        *[When(pk=pk, then=pos) for pos, pk in enumerate(random_ids)],
        output_field=IntegerField(),
    )
    return (
        Question.objects.filter(id__in=random_ids)
        .select_related("subsection", "subsection__section", "skill")
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
    Records a single answer within an ongoing test attempt.
    Creates/Updates UserQuestionAttempt, updates proficiency.

    Args:
        test_attempt: The UserTestAttempt instance.
        question: The Question instance being answered.
        answer_data: Dict containing 'selected_answer', 'time_taken_seconds' etc.

    Returns:
        Dict with result: {'is_correct', 'correct_answer', 'explanation', 'feedback_message'}

    Raises:
        serializers.ValidationError: If input is invalid or attempt is not active.
    """
    user = test_attempt.user
    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise serializers.ValidationError(
            _("This test attempt is not currently active.")
        )

    if question.id not in test_attempt.question_ids:
        raise serializers.ValidationError(
            _("This question is not part of the current test attempt.")
        )

    selected_answer = answer_data.get("selected_answer")
    if selected_answer not in UserQuestionAttempt.AnswerChoice.values:
        raise serializers.ValidationError(_("Invalid answer choice provided."))

    is_correct = selected_answer == question.correct_answer

    # Determine mode based on attempt type
    mode_map = {
        UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        UserTestAttempt.AttemptType.PRACTICE: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.SIMULATION: UserQuestionAttempt.Mode.TEST,
    }
    mode = mode_map.get(test_attempt.attempt_type, UserQuestionAttempt.Mode.TEST)

    # Use update_or_create to handle potential duplicate submissions gracefully
    # or allow users to change their answer before completing the test.
    attempt_record, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        test_attempt=test_attempt,
        question=question,
        defaults={
            "selected_answer": selected_answer,
            "is_correct": is_correct,
            "time_taken_seconds": answer_data.get("time_taken_seconds"),
            "used_hint": answer_data.get("used_hint", False),  # Add these if needed
            "used_elimination": answer_data.get("used_elimination", False),
            "used_solution_method": answer_data.get("used_solution_method", False),
            "mode": mode,
            "attempted_at": timezone.now(),  # Ensure timestamp is updated
        },
    )
    logger.info(
        f"{'Created' if created else 'Updated'} UserQuestionAttempt for Q:{question.id}, TestAttempt:{test_attempt.id}, User:{user.id}"
    )

    # Update Skill Proficiency
    update_user_skill_proficiency(
        user=user, skill=question.skill, is_correct=is_correct
    )

    # --- Prepare Immediate Feedback based on Attempt Type ---
    feedback = {
        "question_id": question.id,
        "is_correct": is_correct,
        "correct_answer": None,
        "explanation": None,
        "feedback_message": _("Answer recorded."),
    }

    # Provide full feedback ONLY for Traditional mode during the attempt
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        feedback["correct_answer"] = question.correct_answer
        feedback["explanation"] = question.explanation
        feedback["feedback_message"] = _("Answer recorded. See feedback below.")

    return feedback


# --- NEW: Service for completing a test attempt ---
@transaction.atomic
def complete_test_attempt(test_attempt: UserTestAttempt) -> Dict[str, Any]:
    """
    Finalizes a test attempt, calculates scores, updates status.

    Args:
        test_attempt: The UserTestAttempt instance to complete.

    Returns:
        A dictionary containing the final results and status.

    Raises:
        serializers.ValidationError: If the attempt cannot be completed.
    """
    user = test_attempt.user
    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise serializers.ValidationError(
            _("This test attempt is not active or already completed/abandoned.")
        )

    # --- Prevent completing Traditional attempts via this flow ---
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        logger.warning(
            f"User {user.id} attempted to use 'complete' endpoint for traditional attempt {test_attempt.id}."
        )
        raise serializers.ValidationError(
            {
                "non_field_errors": [
                    _(
                        "Traditional practice sessions should be ended using the specific 'end' endpoint, not completed like a test."
                    )
                ]
            }
        )

    # Fetch all related UserQuestionAttempts efficiently
    question_attempts_qs = UserQuestionAttempt.objects.filter(
        test_attempt=test_attempt
    ).select_related(
        "question__subsection__section",  # Needed for scoring
        "question__skill",  # Potentially useful if further analysis added
    )

    answered_count = question_attempts_qs.count()
    total_questions = test_attempt.num_questions

    # Optional: Check if all questions were answered. Decide policy: allow incomplete or raise error.
    # For now, we allow completing with unanswered questions.
    if answered_count < total_questions:
        logger.warning(
            f"Test attempt {test_attempt.id} completed by user {user.id} with {answered_count}/{total_questions} questions answered."
        )
        # You could potentially add logic here to automatically mark unanswered questions as incorrect,
        # or just calculate score based on total questions as implemented in calculate_and_save_scores.

    # Calculate and Save Scores using the model method
    test_attempt.calculate_and_save_scores(question_attempts_qs)  # Pass the queryset

    # Mark Test Attempt Complete
    test_attempt.status = UserTestAttempt.Status.COMPLETED
    test_attempt.end_time = timezone.now()
    test_attempt.save(
        update_fields=[
            "status",
            "end_time",
            "updated_at",
            "score_percentage",
            "score_verbal",
            "score_quantitative",
            "results_summary",
        ]
    )  # Save all updated fields
    logger.info(f"Test attempt {test_attempt.id} completed for user {user.id}.")

    # --- Update User Profile Level Scores (if Level Assessment) ---
    updated_profile = None
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
        try:
            profile = user.profile
            profile.current_level_verbal = test_attempt.score_verbal
            profile.current_level_quantitative = test_attempt.score_quantitative
            profile.is_level_determined = True  # Mark level as determined
            profile.save(
                update_fields=[
                    "current_level_verbal",
                    "current_level_quantitative",
                    "is_level_determined",
                    "updated_at",
                ]
            )
            updated_profile = profile  # Pass updated profile in response
            logger.info(
                f"Profile level scores updated for user {user.id} after assessment {test_attempt.id}."
            )
        except UserProfile.DoesNotExist:
            logger.error(
                f"UserProfile missing for user {user.id} during level assessment score update."
            )
        except Exception as e:
            logger.exception(
                f"Error updating profile levels for user {user.id} after assessment {test_attempt.id}: {e}"
            )

    # --- Generate Smart Analysis (Example - kept same as before) ---
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

    # --- Return Results ---
    return {
        "attempt_id": test_attempt.id,
        "status": test_attempt.status,
        "score_percentage": test_attempt.score_percentage,
        "score_verbal": test_attempt.score_verbal,
        "score_quantitative": test_attempt.score_quantitative,
        "results_summary": results_summary,
        "answered_question_count": answered_count,  # Add count here
        "total_questions": total_questions,  # Add total here
        "smart_analysis": smart_analysis,
        "message": _("Test completed successfully. Results calculated."),
        "updated_profile": updated_profile,  # Include if level assessment
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
