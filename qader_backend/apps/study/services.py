from django.db.models import QuerySet, Q, Exists, OuterRef, F
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from apps.learning.models import (
    LearningSubSection,
    Question,
    Skill,
    UserStarredQuestion,
)
from apps.users.models import UserProfile
from apps.study.models import (
    UserSkillProficiency,
)
import random
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_PROFICIENCY_THRESHOLD = 0.7  # Default threshold for 'not_mastered' filter
EMERGENCY_MODE_DEFAULT_QUESTIONS = 15
EMERGENCY_MODE_WEAK_SKILL_COUNT = 3  # Number of weakest skills to focus on
EMERGENCY_MODE_TIPS = [  # Example Static Tips
    _("Take deep breaths before starting each question."),
    _("Don't get stuck on one question for too long."),
    _("Focus on understanding the concept, not just getting the answer."),
    _("Remember your preparation and trust your abilities."),
]

# --- Question Filtering Logic ---


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

    Args:
        user: The authenticated user instance.
        limit: Maximum number of questions to return.
        subsections: List of subsection slugs to filter by.
        skills: List of skill slugs to filter by.
        starred: If True, filter for questions starred by the user.
        not_mastered: If True, filter for skills user hasn't mastered.
        exclude_ids: List of question IDs to exclude.
        proficiency_threshold: The score below which a skill is considered not mastered.

    Returns:
        A QuerySet of Question objects.
    """
    queryset = Question.objects.filter(is_active=True).select_related(
        "subsection", "skill"
    )
    filters = Q()

    if subsections:
        filters &= Q(subsection__slug__in=subsections)
    if skills:
        filters &= Q(skill__slug__in=skills)
    if starred:
        starred_subquery = UserStarredQuestion.objects.filter(
            user=user, question=OuterRef("pk")
        )
        filters &= Q(Exists(starred_subquery))
    if not_mastered:
        try:
            # Skills with low proficiency
            low_prof_skill_ids = list(
                UserSkillProficiency.objects.filter(
                    user=user, proficiency_score__lt=proficiency_threshold
                ).values_list("skill_id", flat=True)
            )

            # Skills the user has *any* proficiency record for (attempted)
            attempted_skill_ids = list(
                UserSkillProficiency.objects.filter(user=user).values_list(
                    "skill_id", flat=True
                )
            )

            # Filter combines:
            # 1. Skills with low proficiency.
            # 2. Skills that exist but have *never* been attempted by the user.
            not_mastered_filter = Q(skill_id__in=low_prof_skill_ids) | (
                Q(skill__isnull=False) & ~Q(skill_id__in=attempted_skill_ids)
            )
            filters &= not_mastered_filter
        except Exception as e:
            logger.error(
                f"Error applying 'not_mastered' filter for user {user.id}: {e}"
            )
            # Decide: fail silently or raise? For now, fail silently.

    queryset = queryset.filter(filters)

    if exclude_ids:
        queryset = queryset.exclude(id__in=exclude_ids)

    # --- Efficient Random Sampling ---
    all_ids = list(queryset.values_list("id", flat=True))
    count = len(all_ids)

    if count == 0:
        return Question.objects.none()

    num_to_fetch = min(limit, count)
    random_ids = random.sample(all_ids, num_to_fetch)

    # Return the final queryset filtered by the random IDs
    # Re-apply select_related for clarity and safety after ID filtering
    return Question.objects.filter(id__in=random_ids).select_related(
        "subsection", "skill"
    )


# --- Skill Proficiency Update Logic ---


def update_user_skill_proficiency(user, skill: Skill, is_correct: bool):
    """
    Finds or creates a UserSkillProficiency record and updates it based on an attempt.
    """
    if not skill:
        logger.warning(
            f"Attempted to update proficiency for user {user.id} with no skill provided."
        )
        return

    try:
        proficiency, created = UserSkillProficiency.objects.get_or_create(
            user=user,
            skill=skill,
            defaults={  # Set initial values if created
                "proficiency_score": 1.0 if is_correct else 0.0,
                "attempts_count": 1,
                "correct_count": 1 if is_correct else 0,
            },
        )
        if not created:
            # Use the model method for updates (handles atomic increments and score recalc)
            proficiency.record_attempt(is_correct)

    except Exception as e:
        logger.error(
            f"Error updating proficiency for user {user.id}, skill {skill.id}: {e}"
        )


def generate_emergency_plan(
    user,
    available_time_hours: Optional[int] = None,
    focus_areas: Optional[List[str]] = None,
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    num_weak_skills: int = EMERGENCY_MODE_WEAK_SKILL_COUNT,
    default_question_count: int = EMERGENCY_MODE_DEFAULT_QUESTIONS,
) -> Dict[str, Any]:
    """
    Generates a study plan for Emergency Mode based on user's weak areas.

    Args:
        user: The user instance.
        available_time_hours: Optional user-provided time constraint.
        focus_areas: Optional list of section slugs ('verbal', 'quantitative') to prioritize.
        proficiency_threshold: Score below which a skill is considered weak.
        num_weak_skills: Number of weakest skills to target.
        default_question_count: Default number of questions if not time-constrained.

    Returns:
        A dictionary containing the plan:
        {
            "focus_skills": List[str], # List of skill slugs
            "recommended_questions": int,
            "quick_review_topics": List[str]
        }
    """
    plan = {
        "focus_skills": [],
        "recommended_questions": default_question_count,
        "quick_review_topics": [],
    }

    # --- Determine Weak Skills ---
    proficiency_qs = UserSkillProficiency.objects.filter(
        user=user, proficiency_score__lt=proficiency_threshold
    ).select_related(
        "skill", "skill__subsection"
    )  # Eager load related data

    if focus_areas:
        proficiency_qs = proficiency_qs.filter(
            skill__subsection__section__slug__in=focus_areas
        )

    # Order by proficiency ascending (weakest first)
    weak_proficiencies = list(
        proficiency_qs.order_by("proficiency_score")[:num_weak_skills]
    )

    if not weak_proficiencies:
        # If no weak skills found below threshold, maybe pick least proficient skills overall?
        # Or default to general practice? For now, return empty focus.
        logger.info(
            f"No weak skills found below threshold {proficiency_threshold} for user {user.id} in Emergency Mode."
        )
        # Could potentially select skills with the lowest scores even if above threshold,
        # or skills never attempted. Logic can be refined based on requirements.
        # For simplicity, let's pick *any* skills if none are weak.
        all_skills = list(
            Skill.objects.filter().values_list("slug", flat=True)[:num_weak_skills]
        )
        plan["focus_skills"] = random.sample(
            all_skills, min(len(all_skills), num_weak_skills)
        )

    else:
        plan["focus_skills"] = [p.skill.slug for p in weak_proficiencies]
        # --- Determine Quick Review Topics (Example logic) ---
        # Assumes subsections might store basic formulas/concepts
        subsection_ids = {
            p.skill.subsection_id for p in weak_proficiencies if p.skill.subsection_id
        }
        review_topics = (
            LearningSubSection.objects.filter(id__in=subsection_ids)
            .exclude(quick_review_info__isnull=True)
            .exclude(quick_review_info__exact="")
        )
        plan["quick_review_topics"] = list(
            review_topics.values_list("quick_review_info", flat=True)
        )

    # --- Adjust Question Count (Example logic based on time) ---
    if available_time_hours and available_time_hours > 0:
        # Rough estimate: ~2-3 mins per question on average in emergency?
        estimated_questions = int(available_time_hours * 60 / 2.5)
        plan["recommended_questions"] = max(
            5, estimated_questions
        )  # Ensure at least a few questions

    logger.info(f"Generated emergency plan for user {user.id}: {plan}")
    return plan
