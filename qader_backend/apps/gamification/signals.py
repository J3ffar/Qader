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


@receiver(
    post_save, sender=UserQuestionAttempt, dispatch_uid="gamify_question_solved_v2"
)
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


@receiver(post_save, sender=UserTestAttempt, dispatch_uid="gamify_test_completed_v2")
def gamify_on_test_completed(sender, instance: UserTestAttempt, created, **kwargs):
    """
    Fallback handler for test completion gamification.
    The primary path is through study.services.complete_test_attempt, which
    calls process_test_completion_gamification directly after disconnecting this signal.
    This signal acts if a test is marked COMPLETED by other means and gamification
    hasn't been processed yet.
    """
    if (
        instance.status == UserTestAttempt.Status.COMPLETED
        and not instance.completion_points_awarded  # This flag indicates if gamification was done
    ):
        logger.info(
            f"Signal gamify_on_test_completed triggered for attempt {instance.id} "
            f"(likely a non-service completion path). Calling gamification service."
        )
        try:
            # process_test_completion_gamification handles setting completion_points_awarded
            # and saving the instance.
            process_test_completion_gamification(
                user=instance.user, test_attempt=instance
            )
        except Exception as e:
            logger.exception(
                f"Error in signal calling process_test_completion_gamification for attempt {instance.id}: {e}"
            )
            # Depending on requirements, you might want to retry or log for manual intervention.
