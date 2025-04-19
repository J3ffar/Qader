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


@receiver(
    post_save, sender=UserQuestionAttempt, dispatch_uid="award_point_question_solved"
)
def award_point_on_question_solved(
    sender, instance: UserQuestionAttempt, created, **kwargs
):
    """Award 1 point for each correctly solved question."""
    if created and instance.is_correct:
        # Award points only if the attempt is correct and newly created
        # Prevent awarding points if an existing attempt is somehow saved again
        award_points(
            user=instance.user,
            points_change=1,  # Configurable? Maybe based on difficulty?
            reason_code=PointReason.QUESTION_SOLVED,
            description=_("Solved Question #{instance_id}").format(
                instance_id=instance.question.id
            ),
            related_object=instance.question,  # Link to the question itself
        )
        # Update streak after successful question solve
        update_streak(instance.user)


@receiver(post_save, sender=UserTestAttempt, dispatch_uid="award_point_test_completed")
def award_point_on_test_completed(sender, instance: UserTestAttempt, created, **kwargs):
    """Award 10 points upon completing a test, only once."""
    # Check if completed AND points not already awarded for this instance
    if (
        instance.status == UserTestAttempt.Status.COMPLETED
        and not instance.completion_points_awarded
    ):
        points_awarded = False
        try:
            # Use a transaction to ensure point award and flag update are atomic
            with transaction.atomic():
                points_awarded = award_points(
                    user=instance.user,
                    points_change=10,  # Configurable?
                    reason_code=PointReason.TEST_COMPLETED,
                    description=_("Completed Test Attempt #{instance_id}").format(
                        instance_id=instance.id
                    ),
                    related_object=instance,
                )
                if points_awarded:
                    # Mark points as awarded ONLY if award_points succeeded
                    instance.completion_points_awarded = True
                    # Save the flag directly to avoid recursion and ensure it's part of the transaction
                    UserTestAttempt.objects.filter(pk=instance.pk).update(
                        completion_points_awarded=True
                    )
                    logger.info(
                        f"Marked completion points awarded for UserTestAttempt {instance.id}"
                    )

                    # Update streak only if points were successfully awarded
                    update_streak(instance.user)

                    # Check for 'first full test' badge (Example)
                    # config = instance.test_configuration or {}
                    # is_simulation = config.get('config', {}).get('full_simulation', False) \
                    #                 or instance.attempt_type == UserTestAttempt.AttemptType.SIMULATION
                    # if is_simulation:
                    #      check_and_award_badge(instance.user, 'first-full-test') # Assuming slug exists

        except Exception as e:
            logger.error(
                f"Error processing test completion points/streak for attempt {instance.id}: {e}",
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
