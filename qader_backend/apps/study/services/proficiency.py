import logging
from typing import Optional

from apps.learning.models import Skill
from apps.study.models import UserSkillProficiency
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


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
        logger.warning(
            "Proficiency update skipped: Invalid or anonymous user provided."
        )
        return
    if is_correct is None:
        logger.warning(
            f"Proficiency update skipped for user {user.id}, skill {skill.id}: is_correct is None."
        )
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
        proficiency.record_attempt(is_correct=is_correct)
        if created:
            logger.info(
                f"Created skill proficiency record for user {user.id}, skill '{skill.name}'. Score after first attempt: {proficiency.proficiency_score:.2f}"
            )
        else:
            logger.info(
                f"Updated skill proficiency for user {user.id}, skill '{skill.name}'. New score: {proficiency.proficiency_score:.2f}, Attempts: {proficiency.attempts_count}"
            )
    except Exception as e:
        logger.error(
            f"Error updating proficiency for user {user.id}, skill {skill.id}: {e}",
            exc_info=True,
        )
