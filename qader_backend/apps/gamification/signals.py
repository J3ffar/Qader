from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from django.db import transaction

from apps.study.models import UserQuestionAttempt, UserTestAttempt
from .models import PointLog  # Assuming models are here

import logging

logger = logging.getLogger(__name__)

# from apps.challenges.models import Challenge # Assuming model is here
from .services import award_points, update_streak, check_and_award_badge, PointReason

User = get_user_model()

# --- Point Awards ---

# Define point constants (get from settings or use defaults)
POINTS_QUESTION_SOLVED = getattr(settings, "POINTS_TRADITIONAL_CORRECT", 1)
POINTS_TEST_COMPLETED = getattr(settings, "POINTS_TEST_COMPLETED", 10)
POINTS_LEVEL_ASSESSMENT_COMPLETED = getattr(
    settings, "POINTS_LEVEL_ASSESSMENT_COMPLETED", 25
)


@receiver(post_save, sender=UserQuestionAttempt, dispatch_uid="gamify_question_solved")
def gamify_on_question_solved(sender, instance: UserQuestionAttempt, created, **kwargs):
    """Handle gamification when a question is correctly solved."""
    # Only act on newly created, correct attempts
    if created and instance.is_correct:
        user = instance.user
        question = instance.question

        # Award points
        if POINTS_QUESTION_SOLVED > 0:
            award_points(
                user=user,
                points_change=POINTS_QUESTION_SOLVED,
                reason_code=PointReason.QUESTION_SOLVED,
                description=_("Solved Question #{qid} ({mode})").format(
                    qid=question.id, mode=instance.get_mode_display()
                ),
                related_object=question,
            )

        # Update streak (this handles streak points/badges internally)
        update_streak(user)


@receiver(post_save, sender=UserTestAttempt, dispatch_uid="gamify_test_completed")
def gamify_on_test_completed(sender, instance: UserTestAttempt, created, **kwargs):
    """Handle gamification upon completing any test (Practice, Simulation, Level Assessment)."""

    # Check if the status is COMPLETED and points haven't been awarded yet
    if (
        instance.status == UserTestAttempt.Status.COMPLETED
        and not instance.completion_points_awarded
    ):
        user = instance.user
        points_to_award = 0
        reason = PointReason.TEST_COMPLETED
        description = _("Completed Test Attempt #{att_id} ({type})").format(
            att_id=instance.id, type=instance.get_attempt_type_display()
        )

        # Determine points based on attempt type
        if instance.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
            points_to_award = POINTS_LEVEL_ASSESSMENT_COMPLETED
            reason = PointReason.LEVEL_ASSESSMENT_COMPLETED
            description = _("Completed Level Assessment #{att_id}").format(
                att_id=instance.id
            )
        elif instance.attempt_type in [
            UserTestAttempt.AttemptType.PRACTICE,
            UserTestAttempt.AttemptType.SIMULATION,
        ]:
            points_to_award = POINTS_TEST_COMPLETED
            # Keep default reason/description

        if points_to_award > 0:
            points_awarded_successfully = False
            try:
                # Use a transaction to ensure point award and flag update are atomic
                with transaction.atomic():
                    # Award points via the service
                    points_awarded_successfully = award_points(
                        user=user,
                        points_change=points_to_award,
                        reason_code=reason,
                        description=description,
                        related_object=instance,
                    )

                    if points_awarded_successfully:
                        # Mark points as awarded ONLY if award_points succeeded
                        # Use direct update to avoid recursion and keep it in the transaction
                        rows_updated = UserTestAttempt.objects.filter(
                            pk=instance.pk,
                            completion_points_awarded=False,  # Ensure we only update if still false
                        ).update(completion_points_awarded=True)

                        if rows_updated > 0:
                            logger.info(
                                f"Successfully awarded {points_to_award} points and marked completion points awarded for UserTestAttempt {instance.id}"
                            )
                            # Update streak only after successfully awarding points and setting flag
                            update_streak(user)

                            # Check for relevant badges AFTER points/streak update
                            if (
                                instance.attempt_type
                                == UserTestAttempt.AttemptType.SIMULATION
                            ):
                                check_and_award_badge(
                                    user, "first-full-test"
                                )  # Ensure slug 'first-full-test' exists
                        else:
                            # This case might happen in race conditions if the signal fires twice rapidly
                            # or if the flag was already true. Log it.
                            logger.warning(
                                f"Attempted to mark completion points awarded for UserTestAttempt {instance.id}, but flag was already true or row not found."
                            )
                            points_awarded_successfully = (
                                False  # Ensure streak doesn't update if flag wasn't set
                            )

                    else:
                        # award_points failed (logged internally by the service)
                        # Transaction will roll back, flag remains false.
                        logger.error(
                            f"Failed to award points for test completion for attempt {instance.id}. Flag not updated."
                        )

            except Exception as e:
                logger.error(
                    f"Error processing gamification for completed test attempt {instance.id}: {e}",
                    exc_info=True,
                )


# Add signal for Challenge win points when Challenge model is available
# @receiver(post_save, sender=Challenge)
# def award_points_on_challenge_win(sender, instance: Challenge, **kwargs):
#     if instance.winner and instance.status == Challenge.StatusChoices.COMPLETED:
#          # Award points for winning (e.g., 10)
#          award_points(instance.winner, 10, PointReason.CHALLENGE_WIN, ...)
#          # Award points for participation to both (e.g., 5)
#          award_points(instance.challenger, 5, PointReason.CHALLENGE_PARTICIPATION, ...)
#          if instance.opponent:
#              award_points(instance.opponent, 5, PointReason.CHALLENGE_PARTICIPATION, ...)
#          # Check for challenge-related badges
#          check_and_award_badge(instance.winner, 'challenge-winner-badge')


# --- Badge Awards (Examples - Need specific badge criteria logic) ---

# @receiver(post_save, sender=UserQuestionAttempt)
# def check_questions_solved_badges(sender, instance: UserQuestionAttempt, created, **kwargs):
#     if created and instance.is_correct:
#         user = instance.user
#         # This count could be expensive, consider caching or approximate counts
#         solved_count = UserQuestionAttempt.objects.filter(user=user, is_correct=True).count()
#         if solved_count == 50:
#              check_and_award_badge(user, '50-questions-solved')
#         elif solved_count == 100:
#              check_and_award_badge(user, '100-questions-solved')
#         # ... more milestones


# Note: Streak badges are handled within the update_streak service itself.
