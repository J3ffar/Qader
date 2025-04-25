import logging
from datetime import timedelta
from typing import Optional, Any, Callable, Dict  # Added Callable, Dict
from django.db import transaction, models
from django.db.models import F

# from django.contrib.auth import get_user_model # Use settings instead
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings  # Import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.users.models import UserProfile
from .models import (
    PointLog,
    Badge,
    UserBadge,
    RewardStoreItem,
    UserRewardPurchase,
    PointReason,
)
from apps.study.models import UserQuestionAttempt, UserTestAttempt  # For badge checks

# User = get_user_model() # Use settings.AUTH_USER_MODEL
DjangoUser = settings.AUTH_USER_MODEL  # Alias for clarity if needed

logger = logging.getLogger(__name__)

# Type alias for badge checker functions
BadgeChecker = Callable[[DjangoUser, UserProfile], bool]

# --- Point Management ---


def award_points(
    user: DjangoUser,
    points_change: int,
    reason_code: PointReason,  # Use Enum
    description: str,
    related_object: Optional[models.Model] = None,  # Type hint Model
) -> bool:
    """
    Atomically awards points to a user, logs the transaction, and updates the profile.

    Args:
        user: The user receiving points.
        points_change: The number of points to add (positive) or subtract (negative).
        reason_code: The standardized reason from PointReason enum.
        description: A human-readable description for the log.
        related_object: Optional Django model instance that triggered the points.

    Returns:
        True if points were awarded successfully, False otherwise.
    """
    if not user or not hasattr(user, "pk"):  # Check for valid user object
        logger.error(f"Attempted to award points to invalid user object: {user}")
        return False

    if points_change == 0:
        return True  # No change needed

    username = getattr(user, "username", f"UserID_{user.pk}")  # Safe username access

    try:
        with transaction.atomic():
            # Lock the profile row for the duration of the transaction
            profile = UserProfile.objects.select_for_update().get(user=user)

            content_type = None
            object_id = None
            if related_object:
                content_type = ContentType.objects.get_for_model(related_object)
                object_id = related_object.pk

            PointLog.objects.create(
                user=user,
                points_change=points_change,
                reason_code=reason_code,  # Store enum value
                description=description,
                content_type=content_type,
                object_id=object_id,
            )

            # Use F() expression for atomic update, avoids race conditions
            profile.points = F("points") + points_change
            profile.save(update_fields=["points", "updated_at"])

            # Refresh is needed AFTER save to get the updated value from F()
            profile.refresh_from_db(fields=["points"])
            logger.info(
                f"Awarded {points_change} points to {username} for {reason_code.label}. "
                f"New balance: {profile.points}"
            )
            return True

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {username} during point award for {reason_code.label}."
        )
        return False
    except Exception as e:
        logger.exception(  # Use logger.exception to include traceback
            f"Error awarding points to {username} for {reason_code.label}: {e}"
        )
        return False


# --- Badge Management ---

# --- Badge Checker Functions ---
# These functions contain the *actual logic* to determine if a user qualifies for a badge.
# They MUST be implemented based on the specific requirements.


def _check_50_questions_solved(user: DjangoUser, profile: UserProfile) -> bool:
    """Checks if the user has solved at least 50 questions."""
    # !! IMPORTANT: Implement the actual logic here !!
    # This might involve querying UserQuestionAttempt or a counter on UserProfile
    # Example (potentially inefficient, consider optimization/denormalization):
    # return UserQuestionAttempt.objects.filter(user=user, is_correct=True).count() >= 50
    logger.warning(
        f"Badge check logic for '{settings.BADGE_SLUG_50_QUESTIONS}' is not implemented."
    )
    return False  # Placeholder


def _check_first_full_test(user: DjangoUser, profile: UserProfile) -> bool:
    """Checks if the user has completed their first full simulation test."""
    # !! IMPORTANT: Implement the actual logic here !!
    # return UserTestAttempt.objects.filter(
    #     user=user,
    #     status=UserTestAttempt.Status.COMPLETED,
    #     attempt_type=UserTestAttempt.AttemptType.SIMULATION # Ensure this type exists
    # ).exists()
    logger.warning(
        f"Badge check logic for '{settings.BADGE_SLUG_FIRST_FULL_TEST}' is not implemented."
    )
    return False  # Placeholder


def _check_streak_badge(
    user: DjangoUser, profile: UserProfile, required_streak: int
) -> bool:
    """Checks if the user's current streak meets the required number of days."""
    # This logic is straightforward based on the profile field
    return profile.current_streak_days >= required_streak


# --- Badge Dispatcher ---
# Maps badge slugs (from settings) to their respective checker functions.
# This makes adding new badges much easier (Open/Closed Principle).
BADGE_CHECKERS: Dict[str, BadgeChecker] = {
    settings.BADGE_SLUG_50_QUESTIONS: _check_50_questions_solved,
    settings.BADGE_SLUG_FIRST_FULL_TEST: _check_first_full_test,
    settings.BADGE_SLUG_5_DAY_STREAK: lambda u, p: _check_streak_badge(u, p, 5),
    settings.BADGE_SLUG_10_DAY_STREAK: lambda u, p: _check_streak_badge(u, p, 10),
    # Add entries for ALL other badge slugs defined in settings here
    # "another-badge-slug": _check_another_badge_logic,
}


def check_and_award_badge(user: DjangoUser, badge_slug: str):
    """
    Checks if a user qualifies for a specific badge and awards it if not already earned.
    Uses the BADGE_CHECKERS dictionary to find the correct logic.

    Args:
        user: The user to check.
        badge_slug: The unique slug of the badge to check (should match settings).
    """
    if not user or not hasattr(user, "pk"):
        logger.warning(f"Badge check skipped for invalid user object: {user}")
        return

    username = getattr(user, "username", f"UserID_{user.pk}")

    # Find the checker function for this badge slug
    checker_func = BADGE_CHECKERS.get(badge_slug)
    if not checker_func:
        logger.error(f"No checker function defined for badge slug: {badge_slug}")
        return

    try:
        # Use select_related('profile') if profile is accessed frequently
        # Or get profile separately if needed for checker
        profile = UserProfile.objects.get(user=user)

        badge = Badge.objects.get(slug=badge_slug, is_active=True)

        # Check if already earned using exists() for efficiency
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            # logger.debug(f"User {username} already has badge '{badge_slug}'.")
            return  # Already earned

        # --- Execute the specific criteria check function ---
        criteria_met = checker_func(user, profile)

        if criteria_met:
            # Use transaction to ensure badge award and point award are atomic
            with transaction.atomic():
                user_badge = UserBadge.objects.create(user=user, badge=badge)
                logger.info(
                    f"Awarded badge '{badge.name}' (slug: {badge_slug}) to user {username}"
                )

                # Award points for earning the badge, using constant from settings
                if settings.POINTS_BADGE_EARNED > 0:
                    award_points(
                        user=user,
                        points_change=settings.POINTS_BADGE_EARNED,
                        reason_code=PointReason.BADGE_EARNED,
                        description=f"Earned badge: {badge.name}",
                        related_object=user_badge,  # Link points to the UserBadge record
                    )
        # else:
        # logger.debug(f"Criteria not met for badge '{badge_slug}' for user {username}")

    except Badge.DoesNotExist:
        logger.warning(
            f"Badge with slug '{badge_slug}' not found or inactive during check for user {username}."
        )
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {username} during badge check.")
    except Exception as e:
        logger.exception(
            f"Error checking/awarding badge '{badge_slug}' for {username}: {e}"
        )


# --- Streak Management ---


def update_streak(user: DjangoUser):
    """
    Updates the user's study streak based on their last activity.

    Should be called after any significant study activity. Handles awarding
    streak-related points and badges internally by calling check_and_award_badge.
    """
    if not user or not hasattr(user, "pk"):
        logger.warning("Streak update skipped for invalid user object.")
        return

    username = getattr(user, "username", f"UserID_{user.pk}")

    try:
        now_utc = timezone.now()  # Use UTC for comparison consistency
        today_utc = now_utc.date()
        yesterday_utc = today_utc - timedelta(days=1)

        with transaction.atomic():  # Ensure profile lock and updates are atomic
            profile = UserProfile.objects.select_for_update().get(user=user)

            last_activity_date_utc = None
            if profile.last_study_activity_at:
                # Ensure comparison is done in UTC
                last_activity_date_utc = profile.last_study_activity_at.astimezone(
                    timezone.utc
                ).date()

            # If last activity was today (UTC), only update timestamp if necessary
            if last_activity_date_utc == today_utc:
                if profile.last_study_activity_at < now_utc:
                    profile.last_study_activity_at = now_utc
                    profile.save(update_fields=["last_study_activity_at"])
                return  # No streak logic needed

            # --- Streak Logic ---
            original_streak = profile.current_streak_days
            streak_updated = False
            new_streak_value = 1  # Default for new/reset streak

            if last_activity_date_utc == yesterday_utc:
                # Continued streak: Increment using F()
                profile.current_streak_days = F("current_streak_days") + 1
                streak_updated = True
                # We don't know the exact value yet because of F(), will refresh later
                logger.info(f"User {username} continued streak.")
            elif (
                last_activity_date_utc is None or last_activity_date_utc < yesterday_utc
            ):
                # Started new streak or broke streak: Reset to 1
                profile.current_streak_days = 1
                streak_updated = True
                logger.info(f"User {username} started/reset streak to 1.")

            # Always update the last activity timestamp
            profile.last_study_activity_at = now_utc
            update_fields = ["last_study_activity_at"]
            if streak_updated:
                update_fields.append("current_streak_days")

            profile.save(update_fields=update_fields)

            # --- Post-Streak Update Actions ---
            if streak_updated:
                # Refresh to get the actual value after F() expression if used
                profile.refresh_from_db(
                    fields=["current_streak_days", "longest_streak_days"]
                )
                current_streak = profile.current_streak_days

                # Check and update longest streak
                if current_streak > profile.longest_streak_days:
                    profile.longest_streak_days = current_streak
                    profile.save(update_fields=["longest_streak_days"])
                    logger.info(
                        f"User {username} updated longest streak to {current_streak} days."
                    )

                # Award points based on streak milestones (only when milestone is hit)
                points_to_award = settings.POINTS_STREAK_BONUS_MAP.get(current_streak)
                if (
                    points_to_award
                    and points_to_award > 0
                    and current_streak > original_streak
                ):
                    award_points(
                        user=user,
                        points_change=points_to_award,
                        reason_code=PointReason.STREAK_BONUS,
                        description=_("Reached {days}-day streak!").format(
                            days=current_streak
                        ),
                        related_object=profile,
                    )

                # Check for streak-based badges (using slugs from settings)
                if (
                    current_streak >= 5 and original_streak < 5
                ):  # Check only when crossing threshold
                    check_and_award_badge(user, settings.BADGE_SLUG_5_DAY_STREAK)
                if current_streak >= 10 and original_streak < 10:
                    check_and_award_badge(user, settings.BADGE_SLUG_10_DAY_STREAK)
                # Add more badge checks here for other streak milestones

    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {username} during streak update.")
    except Exception as e:
        logger.exception(f"Error updating streak for {username}: {e}")


# --- Rewards Store Management ---


class PurchaseError(Exception):
    """Custom exception for reward purchase errors."""

    pass


def purchase_reward(user: DjangoUser, item_id: int) -> Dict[str, Any]:
    """
    Handles the purchase of a reward store item atomically.

    Args:
        user: The user making the purchase.
        item_id: The ID of the RewardStoreItem to purchase.

    Returns:
        A dictionary containing purchase details upon success.

    Raises:
        RewardStoreItem.DoesNotExist: If the item is not found or inactive.
        PurchaseError: For specific errors like insufficient points or profile issues.
    """
    if not user or not hasattr(user, "pk"):
        raise PurchaseError(_("Invalid user for reward purchase."))

    username = getattr(user, "username", f"UserID_{user.pk}")

    try:
        item = RewardStoreItem.objects.get(pk=item_id, is_active=True)
    except RewardStoreItem.DoesNotExist:
        logger.warning(
            f"Attempt to purchase non-existent/inactive reward item {item_id} by {username}"
        )
        raise  # Re-raise for the view to handle

    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)

            if profile.points < item.cost_points:
                raise PurchaseError(_("Insufficient points to purchase this item."))

            # Deduct points using the central service (negative value)
            point_deducted = award_points(
                user=user,
                points_change=-item.cost_points,
                reason_code=PointReason.REWARD_PURCHASE,
                description=f"Purchased: {item.name} (ID: {item.id})",
                related_object=item,
            )

            if not point_deducted:
                # award_points handles logging, raise specific error here
                raise PurchaseError(
                    _("Failed to update points balance during purchase.")
                )

            # Record the purchase AFTER points are successfully deducted
            UserRewardPurchase.objects.create(
                user=user, item=item, points_spent=item.cost_points
            )

            logger.info(
                f"User {username} purchased reward '{item.name}' (ID: {item.id})."
            )

            # Refresh profile to get the final point count after deduction
            profile.refresh_from_db(fields=["points"])

            return {
                "item_id": item.id,
                "item_name": item.name,
                "points_spent": item.cost_points,
                "remaining_points": profile.points,
            }

    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {username} during reward purchase."
        )
        raise PurchaseError(_("User profile error during purchase."))
    except PurchaseError as pe:
        # Re-raise specific purchase errors (like insufficient points)
        logger.warning(f"Purchase failed for user {username}, item {item.id}: {pe}")
        raise pe
    except Exception as e:
        logger.exception(
            f"Unexpected error during reward purchase by {username} for item {item_id}: {e}"
        )
        # Transaction automatically rolls back
        raise PurchaseError(_("An unexpected error occurred during purchase."))
