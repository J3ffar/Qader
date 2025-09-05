import logging
import random
from typing import Optional, List, Dict, Any, Union

from django.conf import settings
from django.core.exceptions import ValidationError as CoreValidationError
from django.db import transaction
from django.db.models import Case, When, IntegerField
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError as DRFValidationError

from apps.api.exceptions import UsageLimitExceeded
from apps.gamification.services import process_test_completion_gamification
from apps.gamification.signals import (
    gamify_on_test_completed as gamify_test_completed_signal_handler,
)
from apps.learning.models import Question, LearningSection, LearningSubSection, Skill
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.users.models import UserProfile
from apps.users.services import UsageLimiter
from django.contrib.auth import get_user_model

from .questions import get_filtered_questions
from .proficiency import update_user_skill_proficiency
from .ai_analysis import _generate_ai_performance_analysis
from .constants import (
    AI_ANALYSIS_DEFAULT_FALLBACK,
    AI_ANALYSIS_HIGH_SCORE_THRESHOLD,
    AI_ANALYSIS_LOW_SCORE_THRESHOLD,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@transaction.atomic
def record_single_answer(
    test_attempt: UserTestAttempt, question: Question, answer_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Records a single answer submitted by a user during an ongoing test attempt."""
    user = test_attempt.user
    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise DRFValidationError(
            {"non_field_errors": [_("This test attempt is not currently active.")]}
        )
    if question.id not in test_attempt.question_ids:
        raise DRFValidationError(
            {
                "question_id": [
                    _("This question is not part of the current test attempt.")
                ]
            }
        )
    selected_answer = answer_data.get("selected_answer")
    if selected_answer not in UserQuestionAttempt.AnswerChoice.values:
        raise DRFValidationError(
            {"selected_answer": [_("Invalid answer choice provided.")]}
        )

    mode_map = {
        UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        UserTestAttempt.AttemptType.PRACTICE: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.SIMULATION: UserQuestionAttempt.Mode.TEST,
        UserTestAttempt.AttemptType.TRADITIONAL: UserQuestionAttempt.Mode.TRADITIONAL,
    }
    mode = mode_map.get(test_attempt.attempt_type, UserQuestionAttempt.Mode.TEST)

    attempt_defaults = {
        "selected_answer": selected_answer,
        "is_correct": selected_answer == question.correct_answer,
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

    update_user_skill_proficiency(
        user=user, skill=question.skill, is_correct=question_attempt.is_correct
    )

    feedback = {
        "question_id": question.id,
        "is_correct": question_attempt.is_correct,
        "correct_answer": None,
        "explanation": None,
        "feedback_message": _("Answer recorded."),
    }
    if test_attempt.attempt_type == UserTestAttempt.AttemptType.TRADITIONAL:
        feedback.update(
            {
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "feedback_message": _("Answer recorded. See feedback below."),
            }
        )
    return feedback


@transaction.atomic
def complete_test_attempt(test_attempt: UserTestAttempt) -> Dict[str, Any]:
    """Finalizes a test attempt, calculates scores, and triggers post-completion logic."""
    user = test_attempt.user
    if test_attempt.status != UserTestAttempt.Status.STARTED:
        raise DRFValidationError(
            {
                "non_field_errors": [
                    _("This test attempt is not active or has already been completed.")
                ]
            }
        )

    signal_disconnected = False
    try:
        if post_save.disconnect(
            gamify_test_completed_signal_handler,
            UserTestAttempt,
            "gamify_test_completed",
        ):
            signal_disconnected = True
            logger.debug(
                f"Temporarily disconnected 'gamify_on_test_completed' signal for attempt {test_attempt.id}."
            )

        test_attempt.status = UserTestAttempt.Status.COMPLETED
        test_attempt.end_time = timezone.now()

        question_attempts_qs = test_attempt.question_attempts.select_related(
            "question__subsection__section", "question__skill"
        ).all()
        correct_answers_count = question_attempts_qs.filter(is_correct=True).count()

        try:
            test_attempt.calculate_and_save_scores(
                question_attempts_qs=question_attempts_qs
            )
        except Exception as e:
            logger.exception(
                f"Error calculating scores for test attempt {test_attempt.id}: {e}"
            )
            test_attempt.status = UserTestAttempt.Status.ERROR

        test_attempt.save(update_fields=["status", "end_time", "updated_at"])

        gamification_results = {
            "total_points_earned": 0,
            "badges_won_details": [],
            "streak_info": {},
        }
        try:
            gamification_results = process_test_completion_gamification(
                user, test_attempt
            )
        except Exception as e:
            logger.exception(
                f"Error processing gamification for test_attempt {test_attempt.id}: {e}"
            )
    finally:
        if signal_disconnected:
            post_save.connect(
                gamify_test_completed_signal_handler,
                UserTestAttempt,
                dispatch_uid="gamify_test_completed",
            )
            logger.debug(
                f"Reconnected 'gamify_on_test_completed' signal for attempt {test_attempt.id}."
            )

    test_attempt.refresh_from_db()

    if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
        try:
            profile = UserProfile.objects.select_for_update().get(user=user)
            if (
                test_attempt.score_verbal is not None
                and test_attempt.score_quantitative is not None
            ):
                profile.current_level_verbal, profile.current_level_quantitative = (
                    test_attempt.score_verbal,
                    test_attempt.score_quantitative,
                )
                profile.save(
                    update_fields=[
                        "current_level_verbal",
                        "current_level_quantitative",
                        "updated_at",
                    ]
                )
        except UserProfile.DoesNotExist:
            logger.error(f"UserProfile not found for user {user.id}")

    smart_analysis = (
        _generate_ai_performance_analysis(user, test_attempt)
        if test_attempt.attempt_type != UserTestAttempt.AttemptType.TRADITIONAL
        and test_attempt.score_percentage is not None
        else _("Practice session ended.")
    )

    return {
        "attempt_id": test_attempt.id,
        "status": test_attempt.get_status_display(),
        "score": {
            "overall": test_attempt.score_percentage,
            "verbal": test_attempt.score_verbal,
            "quantitative": test_attempt.score_quantitative,
        },
        "results_summary": test_attempt.results_summary or {},
        "answered_question_count": question_attempts_qs.count(),
        "total_questions": test_attempt.num_questions,
        "correct_answers_in_test_count": correct_answers_count,
        "smart_analysis": smart_analysis,
        "points_from_test_completion_event": gamification_results.get(
            "total_points_earned", 0
        ),
        "points_from_correct_answers_this_test": correct_answers_count
        * settings.POINTS_QUESTION_SOLVED_CORRECT,
        "badges_won": [
            {"slug": b["slug"], "name": b["name"], "description": b["description"]}
            for b in gamification_results.get("badges_won_details", [])
        ],
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
    """Internal base function to start any test attempt type."""
    if UserTestAttempt.objects.filter(
        user=user, status=UserTestAttempt.Status.STARTED, attempt_type=attempt_type
    ).exists():
        raise DRFValidationError(
            {
                "non_field_errors": [
                    _("You already have an active '{type}' in progress.").format(
                        type=UserTestAttempt.AttemptType(attempt_type).label
                    )
                ]
            }
        )

    try:
        limiter = UsageLimiter(user)
        limiter.check_can_start_test_attempt(attempt_type)
        max_allowed_q = limiter.get_max_questions_per_attempt()
        actual_num_to_select = num_questions_requested
        if max_allowed_q is not None and num_questions_requested > max_allowed_q:
            actual_num_to_select = max_allowed_q
    except UsageLimitExceeded as e:
        raise e

    questions_qs = Question.objects.none()
    question_ids = []
    if actual_num_to_select > 0:
        questions_qs = get_filtered_questions(
            user=user,
            limit=actual_num_to_select,
            subsections=subsections,
            skills=skills,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=exclude_ids,
            min_required=1,
        )
        question_ids = list(questions_qs.values_list("id", flat=True))

    config_snapshot.update(
        {
            "num_questions_requested": num_questions_requested,
            "num_questions_selected": len(question_ids),
        }
    )

    test_attempt = UserTestAttempt.objects.create(
        user=user,
        attempt_type=attempt_type,
        test_configuration=config_snapshot,
        question_ids=question_ids,
        status=UserTestAttempt.Status.STARTED,
    )
    logger.info(
        f"Started {attempt_type.label} (ID: {test_attempt.id}) for user {user.id} with {len(question_ids)} questions."
    )

    return {
        "attempt_id": test_attempt.id,
        "attempt_number_for_type": UserTestAttempt.objects.filter(
            user=user, attempt_type=attempt_type
        ).count(),
        "questions": questions_qs,
    }


def start_level_assessment(
    user: User, sections: List[LearningSection], num_questions_requested: int
) -> Dict[str, Any]:
    """Starts a Level Assessment test."""
    subsection_slugs = list(
        LearningSubSection.objects.filter(section__in=sections).values_list(
            "slug", flat=True
        )
    )
    if not subsection_slugs:
        raise DRFValidationError(
            {"sections": [_("No subsections found for the selected sections.")]}
        )
    config = {
        "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value,
        "sections_requested": [s.slug for s in sections],
    }
    return _start_test_attempt_base(
        user=user,
        attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
        config_snapshot=config,
        num_questions_requested=num_questions_requested,
        subsections=subsection_slugs,
    )


def start_practice_or_simulation(
    user: User,
    attempt_type: UserTestAttempt.AttemptType,
    num_questions_requested: int,
    **kwargs,
) -> Dict[str, Any]:
    """Starts a Practice or Simulation test."""
    sub_slugs = (
        [s.slug for s in kwargs.get("subsections", [])]
        if kwargs.get("subsections")
        else None
    )
    skill_slugs = (
        [s.slug for s in kwargs.get("skills", [])] if kwargs.get("skills") else None
    )
    config = {
        "test_type": attempt_type.value,
        "name": kwargs.get("name"),
        "subsections_requested": sub_slugs or [],
        "skills_requested": skill_slugs or [],
        "starred_requested": kwargs.get("starred", False),
        "not_mastered_requested": kwargs.get("not_mastered", False),
    }
    return _start_test_attempt_base(
        user=user,
        attempt_type=attempt_type,
        config_snapshot=config,
        num_questions_requested=num_questions_requested,
        subsections=sub_slugs,
        skills=skill_slugs,
        starred=kwargs.get("starred", False),
        not_mastered=kwargs.get("not_mastered", False),
    )


def start_traditional_practice(
    user: User, num_questions_initial: int, **kwargs
) -> Dict[str, Any]:
    """Starts a Traditional practice session."""
    sub_slugs = (
        [s.slug for s in kwargs.get("subsections", [])]
        if kwargs.get("subsections")
        else None
    )
    skill_slugs = (
        [s.slug for s in kwargs.get("skills", [])] if kwargs.get("skills") else None
    )
    config = {
        "test_type": UserTestAttempt.AttemptType.TRADITIONAL.value,
        "subsections_requested": sub_slugs or [],
        "skills_requested": skill_slugs or [],
        "starred_requested": kwargs.get("starred", False),
        "not_mastered_requested": kwargs.get("not_mastered", False),
    }
    result = _start_test_attempt_base(
        user=user,
        attempt_type=UserTestAttempt.AttemptType.TRADITIONAL,
        config_snapshot=config,
        num_questions_requested=num_questions_initial,
        subsections=sub_slugs,
        skills=skill_slugs,
        starred=kwargs.get("starred", False),
        not_mastered=kwargs.get("not_mastered", False),
    )
    result["status"] = UserTestAttempt.Status.STARTED.value
    return result


@transaction.atomic
def retake_test_attempt(
    user: User, original_attempt: UserTestAttempt
) -> Dict[str, Any]:
    """Starts a new test attempt based on the configuration of a previous one."""
    original_config = original_attempt.test_configuration
    if not isinstance(original_config, dict):
        raise DRFValidationError(
            {"detail": _("Original test configuration is missing or invalid.")}
        )

    if UserTestAttempt.objects.filter(
        user=user,
        status=UserTestAttempt.Status.STARTED,
        attempt_type=original_attempt.attempt_type,
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

    num_questions = original_config.get("num_questions_selected") or 10
    if num_questions <= 0:
        raise DRFValidationError(
            {"detail": _("Cannot retake a test that had no questions selected.")}
        )

    sub_slugs = original_config.get("subsections_requested", [])
    skill_slugs = original_config.get("skills_requested", [])
    starred = original_config.get("starred_requested", False)
    not_mastered = original_config.get("not_mastered_requested", False)

    try:
        limiter = UsageLimiter(user)
        limiter.check_can_start_test_attempt(original_attempt.attempt_type)
        max_allowed = limiter.get_max_questions_per_attempt()
        if max_allowed is not None and num_questions > max_allowed:
            num_questions = max_allowed
    except UsageLimitExceeded as e:
        raise e

    try:
        new_qs = get_filtered_questions(
            user=user,
            limit=num_questions,
            subsections=sub_slugs,
            skills=skill_slugs,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=original_attempt.question_ids,
            min_required=0,
        )

        if new_qs.count() < num_questions:
            logger.warning(
                f"Could not find {num_questions} *new* questions for retake of {original_attempt.id}. Trying again including original questions."
            )
            new_qs = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=None,
                min_required=1,
            )

        if not new_qs.exists():
            raise DRFValidationError(
                {"detail": _("No suitable questions found to generate a similar test.")}
            )

        final_question_ids = list(new_qs.values_list("id", flat=True))
        actual_num_selected = len(final_question_ids)

    except DRFValidationError as e:
        raise e
    except Exception as e:
        logger.exception(
            f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
        )
        raise DRFValidationError(
            {"detail": _("Failed to select questions for the new test.")}
        )

    new_config = original_config.copy()
    new_config.update(
        {
            "retake_of_attempt_id": original_attempt.id,
            "num_questions_selected": actual_num_selected,
        }
    )

    new_attempt = UserTestAttempt.objects.create(
        user=user,
        attempt_type=original_attempt.attempt_type,
        test_configuration=new_config,
        question_ids=final_question_ids,
        status=UserTestAttempt.Status.STARTED,
    )

    return {
        "attempt_id": new_attempt.id,
        "attempt_number_for_type": UserTestAttempt.objects.filter(
            user=user, attempt_type=original_attempt.attempt_type
        ).count(),
        "questions": new_qs,
    }
