from django.conf import settings  # Import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

# from django.contrib.auth import get_user_model # Use settings
from django.utils.translation import gettext as _  # Keep using _ for descriptions
from django.db import transaction
import logging

from apps.study.models import UserQuestionAttempt, UserTestAttempt

# from apps.challenges.models import Challenge # Import when ready
from .models import Badge, PointReason  # Import Enum

# PointLog model not needed directly here if using award_points service
from .services import award_points, update_streak, check_and_award_badge

logger = logging.getLogger(__name__)
# User = get_user_model() # Use settings.AUTH_USER_MODEL

# --- Signal Handlers ---


@receiver(
    post_save, sender=UserQuestionAttempt, dispatch_uid="gamify_question_solved_v2"
)
def gamify_on_question_solved(sender, instance: UserQuestionAttempt, created, **kwargs):
    """Handle gamification when a question is correctly solved in any mode."""
    # Only act on newly created, correct attempts
    if created and instance.is_correct:
        user = instance.user
        question = instance.question

        # Award points using constant from settings
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
    """Handle gamification upon completing any test (Practice, Simulation, Level Assessment)."""

    # Check if the status is COMPLETED and points haven't been awarded yet
    if (
        instance.status == UserTestAttempt.Status.COMPLETED
        and not instance.completion_points_awarded  # Check the flag
    ):
        user = instance.user
        points_to_award = 0
        reason = PointReason.TEST_COMPLETED  # Default reason
        description = _("Completed Test Attempt #{att_id} ({type})").format(
            att_id=instance.id, type=instance.get_attempt_type_display()
        )

        # Determine points based on attempt type using settings constants
        if instance.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
            points_to_award = settings.POINTS_LEVEL_ASSESSMENT_COMPLETED
            reason = PointReason.LEVEL_ASSESSMENT_COMPLETED
            description = _("Completed Level Assessment #{att_id}").format(
                att_id=instance.id
            )
        elif instance.attempt_type in [
            UserTestAttempt.AttemptType.PRACTICE,
            UserTestAttempt.AttemptType.SIMULATION,
        ]:
            points_to_award = settings.POINTS_TEST_COMPLETED
            # Keep default reason/description

        if points_to_award > 0:
            try:
                # Use a transaction to ensure point award and flag update are atomic
                with transaction.atomic():
                    points_awarded_successfully = award_points(
                        user=user,
                        points_change=points_to_award,
                        reason_code=reason,
                        description=description,
                        related_object=instance,
                    )

                    if points_awarded_successfully:
                        # Mark points as awarded ONLY if award_points succeeded
                        # Use direct update to avoid recursion and stay in transaction
                        rows_updated = UserTestAttempt.objects.filter(
                            pk=instance.pk, completion_points_awarded=False
                        ).update(completion_points_awarded=True)

                        if rows_updated > 0:
                            logger.info(
                                f"Successfully awarded {points_to_award} points and marked "
                                f"completion points awarded for UserTestAttempt {instance.id}"
                            )
                            # Update streak after successfully awarding points/setting flag
                            update_streak(user)

                            # Check for relevant badges AFTER points/streak update
                            test_badges = Badge.objects.filter(
                                is_active=True,
                                criteria_type=Badge.BadgeCriteriaType.TESTS_COMPLETED,
                            ).only("slug")
                            for badge in test_badges:
                                check_and_award_badge(user, badge.slug)

                            # Check for badges related to solving questions (e.g., 50 questions)
                            # This check might be better placed within update_streak or triggered differently
                            # if performance is a concern, but check_and_award_badge handles duplicates.
                            question_badges = Badge.objects.filter(
                                is_active=True,
                                criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY,
                            ).only("slug")

                            for badge in question_badges:
                                # Let the service do the heavy lifting of counting and comparing
                                check_and_award_badge(user, badge.slug)

                        else:
                            logger.warning(
                                f"Attempted to mark completion points awarded for "
                                f"UserTestAttempt {instance.id}, but flag was already true "
                                f"or row not found (potential race condition?)."
                            )
                    else:
                        logger.error(
                            f"Failed to award points for test completion for attempt {instance.id}. "
                            f"Flag not updated."
                        )
            except Exception as e:
                logger.exception(
                    f"Error processing gamification for completed test attempt {instance.id}: {e}"
                )
