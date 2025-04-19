import logging
from datetime import date, timedelta
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.users.models import UserProfile  # Assuming UserProfile is in users app
from .models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Point Management ---


class PointReason:
    QUESTION_SOLVED = "QUESTION_SOLVED"
    TEST_COMPLETED = "TEST_COMPLETED"
    STREAK_BONUS = "STREAK_BONUS"
    FEATURE_FIRST_USE = "FEATURE_FIRST_USE"  # Need specific codes per feature
    CHALLENGE_PARTICIPATION = "CHALLENGE_PARTICIPATION"
    CHALLENGE_WIN = "CHALLENGE_WIN"
    REWARD_PURCHASE = "REWARD_PURCHASE"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    REFERRAL_BONUS = "REFERRAL_BONUS"


def award_points(
    user: User,
    points_change: int,
    reason_code: str,
    description: str,
    related_object=None,
):
    """
    Awards points to a user, logs the transaction, and updates the profile.
    Uses transaction and F() expression for atomic update.
    """
    if not user or not hasattr(user, "profile"):
        logger.error(f"Attempted to award points to invalid user: {user}")
        return False

    try:
        with transaction.atomic():
            # Create the log entry
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

            # Update UserProfile atomically
            # Get profile using the correct related name
            profile = user.profile
            # Lock the profile row for update
            profile = UserProfile.objects.select_for_update().get(user=user)
            profile.points = F("points") + points_change
            profile.save(update_fields=["points"])  # Only update points field

            logger.info(
                f"Awarded {points_change} points to {user.username} for {reason_code}. New balance: {profile.points + points_change}"
            )  # Note: F() object needs calculation post-save for logging
            return True

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.username} during point award."
        )
        return False
    except Exception as e:
        logger.error(f"Error awarding points to {user.username}: {e}", exc_info=True)
        # Transaction automatically rolls back
        return False


# --- Badge Management ---


def check_and_award_badge(user: User, badge_slug: str):
    """Checks if user qualifies for a badge and awards it if not already earned."""
    if not user or not hasattr(user, "profile"):
        return False

    try:
        badge = Badge.objects.get(slug=badge_slug, is_active=True)
        # Check if already earned using exists() for efficiency
        if not UserBadge.objects.filter(user=user, badge=badge).exists():
            # **Placeholder for criteria check**
            # This logic needs to be implemented based on the specific badge.
            # For example, for '50-questions-solved', check count of UserQuestionAttempt.
            # For 'first-full-test', check if a completed UserTestAttempt with type 'simulation' exists.
            # This might involve querying other models.
            criteria_met = True  # Replace with actual check

            if criteria_met:
                UserBadge.objects.create(user=user, badge=badge)
                logger.info(f"Awarded badge '{badge.name}' to user {user.username}")
                # Optionally award points for earning a badge?
                # award_points(user, 10, PointReason.BADGE_EARNED, f"Earned badge: {badge.name}", badge)
                return True
        return False  # Already earned or criteria not met

    except Badge.DoesNotExist:
        logger.warning(f"Badge with slug '{badge_slug}' not found or inactive.")
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
    """
    if not user or not hasattr(user, "profile"):
        return

    try:
        profile = UserProfile.objects.get(user=user)
        profile = user.profile
        today = timezone.now().date()
        last_activity_date = None
        if profile.last_study_activity_at:
            last_activity_date = profile.last_study_activity_at.date()

        streak_updated = False
        if last_activity_date == today:
            # Already active today, no change to streak needed, just update timestamp
            profile.last_study_activity_at = timezone.now()
            profile.save(update_fields=["last_study_activity_at"])
            return  # No streak update logic needed

        if last_activity_date == (today - timedelta(days=1)):
            # Continued streak
            profile.current_streak_days = F("current_streak_days") + 1
            profile.longest_streak_days = F(
                "longest_streak_days"
            )  # Keep current max initially
            streak_updated = True
        elif last_activity_date is None or last_activity_date < (
            today - timedelta(days=1)
        ):
            # Started new streak or broke streak
            profile.current_streak_days = 1
            streak_updated = True  # Reset streak

        profile.last_study_activity_at = timezone.now()

        # Save profile and re-fetch for updated values
        if streak_updated:
            profile.save(
                update_fields=[
                    "current_streak_days",
                    "longest_streak_days",
                    "last_study_activity_at",
                ]
            )
            profile.refresh_from_db()  # Get actual values after F() expressions
            # Update longest streak if current exceeds it
            if profile.current_streak_days > profile.longest_streak_days:
                profile.longest_streak_days = profile.current_streak_days
                profile.save(update_fields=["longest_streak_days"])

            logger.info(
                f"Updated streak for {user.username}. Current: {profile.current_streak_days}, Longest: {profile.longest_streak_days}"
            )

            # Check for streak-based rewards/badges
            # Example:
            if profile.current_streak_days == 2:
                award_points(
                    user,
                    5,
                    PointReason.STREAK_BONUS,
                    _("Reached 2-day streak!"),
                    profile,
                )
            elif profile.current_streak_days == 5:
                check_and_award_badge(user, "5-day-streak")  # Assuming slug exists
            # Add more conditions as needed

        else:
            # Only update timestamp if streak didn't change (already active today)
            profile.save(update_fields=["last_study_activity_at"])

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


def purchase_reward(user: User, item_id: int):
    """Handles the purchase of a reward store item."""
    if not user or not hasattr(user, "profile"):
        # Use PurchaseError consistent with other checks
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
            # Pass the profile instance to avoid refetching inside award_points if possible
            # (Note: award_points current implementation refetches with select_for_update anyway)
            point_deducted = award_points(
                user=user,
                points_change=-item.cost_points,
                reason_code=PointReason.REWARD_PURCHASE,
                description=f"Purchased: {item.name}",
                related_object=item,
            )

            if not point_deducted:
                # award_points handles logging errors, raise specific error here
                raise PurchaseError(_("Failed to deduct points during purchase."))

            # Record the purchase
            UserRewardPurchase.objects.create(
                user=user, item=item, points_spent=item.cost_points
            )

            logger.info(
                f"User {user.username} purchased reward '{item.name}' (ID: {item.id})."
            )

            # Return a dictionary matching the RewardPurchaseResponseSerializer
            profile.refresh_from_db()  # Refresh to get the final point count
            return {
                "item_id": item.id,  # Add item_id
                "item_name": item.name,
                "points_spent": item.cost_points,
                "remaining_points": profile.points,
                # "message": _("Purchase successful!") # Can be added here or rely on serializer default
            }

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {user.username} during reward purchase."
        )
        # Consistent error type for the view to potentially handle (though view expects 400/404)
        raise PurchaseError(_("User profile not found."))
    except PurchaseError as pe:
        # Re-raise specific purchase errors (like insufficient points)
        raise pe
    except Exception as e:
        logger.error(
            f"Error during reward purchase by {user.username} for item {item_id}: {e}",
            exc_info=True,
        )
        # Transaction automatically rolls back
        raise PurchaseError(_("An unexpected error occurred during purchase."))
