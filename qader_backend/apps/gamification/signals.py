from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from django.db import (
    transaction,
)  # Not strictly needed here anymore but good to keep if other signals use it
import logging

from apps.study.models import UserQuestionAttempt, UserTestAttempt
from .models import Badge, PointReason
from .services import (
    award_points,
    process_test_completion_gamification,
)  # updated import

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserQuestionAttempt, dispatch_uid="gamify_question_solved")
def gamify_on_question_solved(sender, instance: UserQuestionAttempt, created, **kwargs):
    if created and instance.is_correct:
        user = instance.user
        question = instance.question
        if settings.POINTS_QUESTION_SOLVED_CORRECT > 0:
            award_points(
                user=user,
                points_change=settings.POINTS_QUESTION_SOLVED_CORRECT,
                reason_code=PointReason.QUESTION_SOLVED,
                description=_("Solved Question #{qid} ({mode})").format(
                    qid=question.id, mode=instance.get_mode_display()
                ),
                related_object=question,
            )


@receiver(post_save, sender=UserTestAttempt, dispatch_uid="gamify_test_completed")
def gamify_on_test_completed(sender, instance: UserTestAttempt, created, **kwargs):
    if (
        instance.status == UserTestAttempt.Status.COMPLETED
        and not instance.completion_points_awarded
    ):
        # ADD A CHECK: Only process via signal if it seems like a legitimate completion
        # This is a heuristic. For example, if the test has an end_time set by the main service.
        # The main `complete_test_attempt` service *does* set `end_time`.
        # If `end_time` is None here, it might be a premature completion.
        if instance.end_time is None:
            logger.warning(
                f"Signal gamify_on_test_completed triggered for attempt {instance.id} "
                f"with status COMPLETED but no end_time. Suspecting premature completion. Skipping gamification via signal."
            )
            return  # Avoid processing if it looks premature

        logger.info(
            f"Signal gamify_on_test_completed triggered for attempt {instance.id}. "
            f"Calling gamification service."
        )
        try:
            process_test_completion_gamification(
                user=instance.user, test_attempt=instance
            )
        except Exception as e:
            logger.exception(
                f"Error in signal calling process_test_completion_gamification for attempt {instance.id}: {e}"
            )
            # Depending on requirements, you might want to retry or log for manual intervention.
