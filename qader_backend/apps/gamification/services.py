import logging
from datetime import timedelta
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from apps.users.models import UserProfile  # Corrected import path
from .models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Point Management ---


class PointReason:
    # Study Related
    QUESTION_SOLVED = "QUESTION_SOLVED"
    TEST_COMPLETED = "TEST_COMPLETED"
    LEVEL_ASSESSMENT_COMPLETED = "LEVEL_ASSESSMENT_COMPLETED"  # Added specific code
    STREAK_BONUS = "STREAK_BONUS"
    FEATURE_FIRST_USE = "FEATURE_FIRST_USE"  # Needs specific codes per feature

    # Challenge Related (Placeholders)
    CHALLENGE_PARTICIPATION = "CHALLENGE_PARTICIPATION"
    CHALLENGE_WIN = "CHALLENGE_WIN"

    # Store & Admin
    REWARD_PURCHASE = "REWARD_PURCHASE"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    REFERRAL_BONUS = "REFERRAL_BONUS"

    # Badge Related
    BADGE_EARNED = "BADGE_EARNED"


def award_points(
    user: User,
    points_change: int,
    reason_code: str,
    description: str,
    related_object=None,
) -> bool:
    """
    Awards points to a user, logs the transaction, and updates the profile.
    Uses transaction and F() expression for atomic update.
    Returns True if successful, False otherwise.
    """
    if not user or not hasattr(user, "profile"):
        # Check added to ensure user/profile exist before logging username attempt
        logger.error(
            f"Attempted to award points to invalid user object or user without profile: {user}"
        )
        return False

    if points_change == 0:
        return True

    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)

            content_type = None
            object_id = None
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = related_object.pk

            PointLog.objects.create(
                user=user,
                points_change=points_change,
                reason_code=reason_code,
                description=description,
                content_type=content_type,
                object_id=object_id,
            )

            profile.points = F("points") + points_change
            profile.save(update_fields=["points", "updated_at"])

            # Refresh AFTER save to get correct value from F() expression
            profile.refresh_from_db(fields=["points"])
            # Safe logging for username
            username = getattr(user, "username", "UnknownUser")
            logger.info(
                f"Awarded {points_change} points to {username} for {reason_code}. New balance: {profile.points}"
            )
            return True

    except UserProfile.DoesNotExist:
        username = getattr(user, "username", "UnknownUser")  # Safe username access
        logger.error(
            f"UserProfile not found for user {username} during point award for {reason_code}."
        )
        return False
    except Exception as e:
        username = getattr(user, "username", "UnknownUser")  # Safe username access
        logger.error(
            f"Error awarding points to {username} for {reason_code}: {e}", exc_info=True
        )
        return False


# --- Badge Management ---


def check_and_award_badge(user: User, badge_slug: str):
    """Checks if user qualifies for a badge and awards it if not already earned."""
    if not user or not hasattr(user, "profile"):
        logger.warning(f"Badge check skipped for invalid user: {user}")
        return False

    try:
        badge = Badge.objects.get(slug=badge_slug, is_active=True)
        # Check if already earned using exists() for efficiency
        if not UserBadge.objects.filter(user=user, badge=badge).exists():

            # --- Placeholder for criteria check ---
            # This logic needs to be implemented based on the specific badge slug.
            # Example criteria checks (replace with actual logic):
            criteria_met = False
            if badge_slug == "50-questions-solved":
                # criteria_met = UserQuestionAttempt.objects.filter(user=user, is_correct=True).count() >= 50
                criteria_met = False  # Replace with real check
                pass  # Add actual check
            elif badge_slug == "first-full-test":
                # criteria_met = UserTestAttempt.objects.filter(user=user, status=UserTestAttempt.Status.COMPLETED, attempt_type=UserTestAttempt.AttemptType.SIMULATION).exists()
                criteria_met = False  # Replace with real check
                pass  # Add actual check
            elif (
                badge_slug == "10-days-studying"
            ):  # This slug needs to match your badge definition
                # Usually checked within update_streak logic, but can be checked here too
                criteria_met = user.profile.current_streak_days >= 10
            # Add more 'elif' blocks for other badges...
            else:
                logger.warning(
                    f"Criteria check logic not implemented for badge slug: {badge_slug}"
                )

            # --- Award if criteria met ---
            if criteria_met:
                UserBadge.objects.create(user=user, badge=badge)
                logger.info(
                    f"Awarded badge '{badge.name}' (slug: {badge_slug}) to user {user.username}"
                )
                # Optionally award points for earning a badge
                award_points(
                    user,
                    15,
                    PointReason.BADGE_EARNED,
                    f"Earned badge: {badge.name}",
                    badge,
                )  # Example: 15 points
                return True
            else:
                # Criteria not met, log for debugging if needed
                # logger.debug(f"Criteria not met for badge '{badge_slug}' for user {user.username}")
                pass

        return False  # Badge already earned or criteria not met

    except Badge.DoesNotExist:
        logger.warning(
            f"Badge with slug '{badge_slug}' not found or inactive during check for user {user.username}."
        )
        return False
    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.username} during badge check."
        )
        return False
    except Exception as e:
        logger.error(
            f"Error checking/awarding badge '{badge_slug}' for {user.username}: {e}",
            exc_info=True,
        )
        return False


# --- Streak Management ---


def update_streak(user: User):
    """
    Updates the user's study streak based on their last activity.
    Should be called after any significant study activity (e.g., solving question, completing test).
    Handles awarding streak-related points and badges.
    """
    if not user:
        logger.warning("Streak update skipped for invalid user.")
        return

    try:
        profile = UserProfile.objects.select_for_update().get(
            user=user
        )  # Lock for update
        now_local = timezone.localtime(timezone.now())
        today = now_local.date()
        yesterday = today - timedelta(days=1)

        last_activity_date = None
        if profile.last_study_activity_at:
            last_activity_local_dt = timezone.localtime(profile.last_study_activity_at)
            last_activity_date = last_activity_local_dt.date()

        # Only process if the last activity wasn't today
        if last_activity_date == today:
            # logger.debug(f"User {user.username} already active today. Streak not updated.")
            # Still update the timestamp to reflect latest activity *within* today
            if profile.last_study_activity_at < now_local:  # Avoid redundant saves
                profile.last_study_activity_at = now_local
                profile.save(update_fields=["last_study_activity_at"])
            return

        with transaction.atomic():  # Wrap streak logic in transaction with profile lock
            original_streak = profile.current_streak_days
            streak_updated = False

            if last_activity_date == yesterday:
                # Continued streak
                profile.current_streak_days = F("current_streak_days") + 1
                streak_updated = True
                logger.info(f"User {user.username} continued streak.")
            elif last_activity_date is None or last_activity_date < yesterday:
                # Started new streak or broke streak
                profile.current_streak_days = 1
                streak_updated = True
                logger.info(f"User {user.username} started/reset streak.")

            profile.last_study_activity_at = now_local
            update_fields = ["last_study_activity_at"]
            if streak_updated:
                update_fields.append("current_streak_days")

            profile.save(update_fields=update_fields)

            # Refresh after potential F() expression update
            if streak_updated:
                profile.refresh_from_db(
                    fields=["current_streak_days", "longest_streak_days"]
                )

                # Check and update longest streak
                if profile.current_streak_days > profile.longest_streak_days:
                    profile.longest_streak_days = profile.current_streak_days
                    profile.save(update_fields=["longest_streak_days"])
                    logger.info(
                        f"User {user.username} updated longest streak to {profile.longest_streak_days} days."
                    )

                # --- Check for streak-based rewards/badges ---
                current_streak = profile.current_streak_days
                if (
                    current_streak == 2 and original_streak < 2
                ):  # Award only once when hitting 2
                    award_points(
                        user,
                        5,
                        PointReason.STREAK_BONUS,
                        _("Reached 2-day streak!"),
                        profile,
                    )
                elif (
                    current_streak == 5 and original_streak < 5
                ):  # Award only once when hitting 5
                    check_and_award_badge(
                        user, "5-day-streak"
                    )  # Ensure slug '5-day-streak' exists
                elif (
                    current_streak == 10 and original_streak < 10
                ):  # Award only once when hitting 10
                    # Award 'greeting card' - how? Maybe just points or another badge?
                    award_points(
                        user,
                        20,
                        PointReason.STREAK_BONUS,
                        _("Reached 10-day streak! Amazing!"),
                        profile,
                    )
                    check_and_award_badge(
                        user, "10-days-studying"
                    )  # Ensure slug '10-days-studying' exists
                # Add more streak milestones as needed...

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.username} during streak update."
        )
    except Exception as e:
        logger.error(f"Error updating streak for {user.username}: {e}", exc_info=True)


# --- Rewards Store Management ---


class PurchaseError(Exception):
    """Custom exception for reward purchase errors."""

    pass


def purchase_reward(user: User, item_id: int) -> dict:  # Specify return type hint
    """Handles the purchase of a reward store item."""
    if not user:
        raise PurchaseError(_("Invalid user."))

    try:
        # Fetch the item first - DoesNotExist will propagate if it fails here
        item = RewardStoreItem.objects.get(pk=item_id, is_active=True)
    except RewardStoreItem.DoesNotExist:
        # Re-raise explicitly for clarity, although view catches it too
        raise RewardStoreItem.DoesNotExist(_("Reward item not found or is inactive."))

    try:
        with transaction.atomic():
            # Use select_for_update to lock the profile row during the transaction
            profile = UserProfile.objects.select_for_update().get(user=user)

            if profile.points < item.cost_points:
                raise PurchaseError(_("Insufficient points to purchase this item."))

            # Deduct points using the award_points service (negative value)
            point_deducted = award_points(
                user=user,
                points_change=-item.cost_points,
                reason_code=PointReason.REWARD_PURCHASE,
                description=f"Purchased: {item.name}",
                related_object=item,
            )

            if not point_deducted:
                # award_points handles logging errors, raise specific error here
                raise PurchaseError(
                    _("Failed to update points balance during purchase.")
                )

            # Record the purchase
            UserRewardPurchase.objects.create(
                user=user, item=item, points_spent=item.cost_points
            )

            logger.info(
                f"User {user.username} purchased reward '{item.name}' (ID: {item.id})."
            )

            # Refresh the profile *after* transaction potentially commits (though F() needs refresh anyway)
            profile.refresh_from_db(
                fields=["points"]
            )  # Get the actual final point count

            # Return a dictionary matching the RewardPurchaseResponseSerializer
            return {
                "item_id": item.id,
                "item_name": item.name,
                "points_spent": item.cost_points,
                "remaining_points": profile.points,
                # Message can be added by serializer or view
            }

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.username} during reward purchase."
        )
        raise PurchaseError(
            _("User profile error during purchase.")
        )  # Use consistent exception
    except PurchaseError as pe:
        # Re-raise specific purchase errors (like insufficient points)
        logger.warning(
            f"Purchase failed for user {user.username}, item {item.id}: {pe}"
        )
        raise pe
    except Exception as e:
        logger.error(
            f"Error during reward purchase by {user.username} for item {item_id}: {e}",
            exc_info=True,
        )
        # Transaction automatically rolls back
        raise PurchaseError(_("An unexpected error occurred during purchase."))
