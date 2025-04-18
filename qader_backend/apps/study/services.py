# qader_backend/apps/study/services.py

from django.db.models import QuerySet, Q, Exists, OuterRef, F
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from apps.learning.models import Question, Skill, UserStarredQuestion
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


# --- Profile Update Logic ---


def record_user_study_activity(
    user,
    points_to_add: int = 0,
    reason_code: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates user's points and study streak. Creates PointLog entry if points are added.

    Args:
        user: The user instance.
        points_to_add: Number of points to add (can be 0).
        reason_code: Code for PointLog entry (e.g., 'TRADITIONAL_CORRECT').
        description: Description for PointLog entry.

    Returns:
        A dictionary containing {'streak_updated': bool, 'current_streak': int, 'current_total_points': int}.
    """
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.id} during study activity recording."
        )
        return {"streak_updated": False, "current_streak": 0, "current_total_points": 0}

    now_local = timezone.localtime(timezone.now())
    today = now_local.date()
    yesterday = today - timezone.timedelta(days=1)

    last_activity_date = None
    if profile.last_study_activity_at:
        last_activity_local_dt = timezone.localtime(profile.last_study_activity_at)
        last_activity_date = last_activity_local_dt.date()

    streak_updated = False
    streak_update_needed = False
    points_update_needed = points_to_add != 0
    profile_update_fields = ["updated_at"]  # Always update 'updated_at'

    # --- Streak Logic ---
    if last_activity_date != today:  # Only update streak if first activity today
        if last_activity_date == yesterday:
            profile.current_streak_days = F("current_streak_days") + 1
        else:  # Streak broken or first ever activity
            profile.current_streak_days = 1
        streak_updated = True
        streak_update_needed = True
        profile.last_study_activity_at = now_local
        profile_update_fields.extend(["current_streak_days", "last_study_activity_at"])

    # --- Points Logic ---
    if points_update_needed:
        profile.points = F("points") + points_to_add
        profile_update_fields.append("points")
        # TODO: Implement PointLog creation (consider signals or direct creation)
        # try:
        #     from apps.gamification.models import PointLog # Lazy import or signal preferred
        #     if reason_code:
        #         PointLog.objects.create(...)
        # except ImportError:
        #     logger.warning("Gamification app or PointLog model not found for logging points.")
        # except Exception as e:
        #      logger.error(f"Error creating PointLog for user {user.id}: {e}")

    # --- Save Profile (Atomic updates) ---
    if points_update_needed or streak_update_needed:
        # Ensure F expressions are resolved before checking longest_streak
        profile.save(update_fields=list(set(profile_update_fields)))
        profile.refresh_from_db(
            fields=["current_streak_days", "longest_streak_days", "points"]
        )

        # Update longest streak if needed *after* refresh
        if streak_updated and profile.current_streak_days > profile.longest_streak_days:
            profile.longest_streak_days = profile.current_streak_days
            profile.save(update_fields=["longest_streak_days"])
            # No need to refresh again unless immediately used elsewhere

    return {
        "streak_updated": streak_updated,
        "current_streak": profile.current_streak_days,
        "current_total_points": profile.points,
    }


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


# --- Old utils.py ---
# qader_backend/apps/study/utils.py
# (This file can now be deleted or left empty)
