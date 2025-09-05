import random
import logging
from typing import Optional, List, Dict, Any, Set

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.learning.models import Skill, LearningSection
from apps.study.models import (
    UserSkillProficiency,
    EmergencyModeSession,
    UserQuestionAttempt,
)
from django.contrib.auth import get_user_model

from .ai_analysis import (
    _generate_ai_emergency_tips,
    _generate_ai_emergency_session_feedback,
    _format_results_summary_for_ai,
)
from .constants import (
    DEFAULT_PROFICIENCY_THRESHOLD,
    EMERGENCY_MODE_WEAK_SKILL_COUNT,
    EMERGENCY_MODE_DEFAULT_QUESTIONS,
    EMERGENCY_MODE_MIN_QUESTIONS,
    EMERGENCY_MODE_ESTIMATED_MINS_PER_Q,
    DEFAULT_EMERGENCY_TIPS,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def generate_emergency_plan(
    user: User,
    available_time_hours: Optional[float] = None,
    days_until_test: Optional[int] = None,
    focus_areas: Optional[List[str]] = None,
    proficiency_threshold: float = DEFAULT_PROFICIENCY_THRESHOLD,
    num_weak_skills: int = EMERGENCY_MODE_WEAK_SKILL_COUNT,
    default_question_count: int = EMERGENCY_MODE_DEFAULT_QUESTIONS,
    min_question_count: int = EMERGENCY_MODE_MIN_QUESTIONS,
    estimated_mins_per_q: float = EMERGENCY_MODE_ESTIMATED_MINS_PER_Q,
) -> Dict[str, Any]:
    """Generates a detailed study plan for Emergency Mode."""
    if not user or not user.is_authenticated:
        return {
            "focus_area_names": [],
            "estimated_duration_minutes": None,
            "target_skills": [],
            "recommended_question_count": 0,
            "quick_review_topics": [],
            "motivational_tips": [str(_("Please log in to get a personalized plan."))],
        }

    plan: Dict[str, Any] = {"recommended_question_count": default_question_count}
    if (
        available_time_hours
        and isinstance(available_time_hours, (int, float))
        and available_time_hours > 0
    ):
        try:
            plan["estimated_duration_minutes"] = int(available_time_hours * 60)
            plan["recommended_question_count"] = max(
                min_question_count,
                int(plan["estimated_duration_minutes"] / estimated_mins_per_q),
            )
        except (ZeroDivisionError, Exception) as e:
            logger.error(f"Error adjusting question count for user {user.id}: {e}")
            plan["estimated_duration_minutes"] = (
                int(default_question_count * estimated_mins_per_q)
                if estimated_mins_per_q > 0
                else None
            )
    else:
        plan["estimated_duration_minutes"] = (
            int(plan["recommended_question_count"] * estimated_mins_per_q)
            if estimated_mins_per_q > 0
            else None
        )

    # --- Determine Weak Skills & Focus Areas ---
    target_skills_data, target_skill_ids, review_topics_data = [], set(), {}
    core_plan_error_tip_added = False
    try:
        proficiency_qs = UserSkillProficiency.objects.filter(user=user).select_related(
            "skill__subsection__section", "skill__subsection", "skill"
        )
        if focus_areas:
            proficiency_qs = proficiency_qs.filter(
                skill__subsection__section__slug__in=focus_areas
            )
            plan["focus_area_names"] = list(
                LearningSection.objects.filter(slug__in=focus_areas).values_list(
                    "name", flat=True
                )
            )
        else:
            plan["focus_area_names"] = list(
                proficiency_qs.values_list(
                    "skill__subsection__section__name", flat=True
                )
                .distinct()
                .exclude(skill__subsection__section__name__isnull=True)
            ) or [_("Verbal"), _("Quantitative")]

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

        # 2. If needed, find other attempted skills to reach the target count
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

        plan["target_skills"] = target_skills_data
    except Exception as e:
        logger.error(
            f"Error determining weak skills for user {user.id} emergency plan: {e}",
            exc_info=True,
        )
        plan["motivational_tips"] = [
            str(
                _(
                    "Could not generate personalized focus areas due to an error. Focusing on general review."
                )
            )
        ]
        core_plan_error_tip_added = True

    try:
        ai_tips = _generate_ai_emergency_tips(
            user,
            plan.get("target_skills", []),
            plan.get("focus_area_names", []),
            available_time_hours,
            days_until_test,
        )
    except Exception as e:
        logger.error(
            f"Error calling _generate_ai_emergency_tips for user {user.id}: {e}",
            exc_info=True,
        )
        num_tips = min(len(DEFAULT_EMERGENCY_TIPS), 3)
        ai_tips = (
            random.sample(DEFAULT_EMERGENCY_TIPS, k=num_tips)
            if num_tips > 0
            else [str(_("Remember to stay calm and focused!"))]
        )

    final_tips = [str(tip) for tip in ai_tips]
    if core_plan_error_tip_added:
        plan["motivational_tips"].extend(final_tips)
    else:
        plan["motivational_tips"] = final_tips

    if not plan.get("motivational_tips"):
        plan["motivational_tips"] = [
            str(tip) for tip in random.sample(DEFAULT_EMERGENCY_TIPS, k=1)
        ]

    logger.info(
        f"Generated emergency plan for user {user.id}. Skills: {len(plan.get('target_skills',[]))}, Qs: {plan['recommended_question_count']}"
    )
    return plan


@transaction.atomic
def complete_emergency_session(session: EmergencyModeSession) -> Dict[str, Any]:
    """Completes an emergency session, calculates scores, and generates feedback."""
    if session.end_time:
        raise DRFValidationError(
            _("This emergency session has already been completed.")
        )

    user = session.user
    question_attempts_qs = UserQuestionAttempt.objects.filter(
        emergency_session=session
    ).select_related("question__subsection__section", "question__subsection")

    if not question_attempts_qs.exists():
        session.end_time = timezone.now()
        session.overall_score = 0.0
        session.results_summary = {}
        session.ai_feedback = _(
            "You completed the session without answering any questions."
        )
        session.save(
            update_fields=[
                "end_time",
                "overall_score",
                "results_summary",
                "ai_feedback",
                "updated_at",
            ]
        )
        return {
            "session_id": session.id,
            "overall_score": 0.0,
            "results_summary": {},
            "ai_feedback": session.ai_feedback,
        }

    results_calc: Dict[str, Dict[str, Any]] = {}
    total_q, correct_q = 0, 0
    for qa in question_attempts_qs:
        total_q += 1
        if qa.is_correct:
            correct_q += 1
        section = qa.question.subsection.section
        subsection = qa.question.subsection

        if section.slug not in results_calc:
            results_calc[section.slug] = {
                "name": section.name,
                "total": 0,
                "correct": 0,
                "subsections": {},
            }

        if subsection.slug not in results_calc[section.slug]["subsections"]:
            results_calc[section.slug]["subsections"][subsection.slug] = {
                "name": subsection.name,
                "total": 0,
                "correct": 0,
            }

        results_calc[section.slug]["total"] += 1
        results_calc[section.slug]["subsections"][subsection.slug]["total"] += 1
        if qa.is_correct:
            results_calc[section.slug]["correct"] += 1
            results_calc[section.slug]["subsections"][subsection.slug]["correct"] += 1

    results_summary_final = {}
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

    overall_score = (correct_q / total_q * 100) if total_q > 0 else 0.0
    verbal_score = results_summary_final.get("verbal", {}).get("score", 0.0)
    quantitative_score = results_summary_final.get("quantitative", {}).get("score", 0.0)

    flat_summary_for_ai = {}
    for section in results_summary_final.values():
        if "subsections" in section:
            flat_summary_for_ai.update(section["subsections"])

    ai_feedback = _generate_ai_emergency_session_feedback(
        user, session, overall_score, flat_summary_for_ai
    )

    session.end_time = timezone.now()
    session.overall_score, session.verbal_score, session.quantitative_score = (
        round(overall_score, 2),
        round(verbal_score, 2),
        round(quantitative_score, 2),
    )
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

    return {
        "session_id": session.id,
        "overall_score": session.overall_score,
        "verbal_score": session.verbal_score,
        "quantitative_score": session.quantitative_score,
        "results_summary": session.results_summary,
        "ai_feedback": session.ai_feedback,
        "answered_question_count": total_q,
        "correct_answers_count": correct_q,
    }
