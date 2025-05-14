import datetime
import logging
from datetime import timedelta
from typing import Optional, Any, Callable, Dict, List  # Added List
from django.db import transaction, models
from django.db.models import F
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from apps.users.models import UserProfile
from apps.challenges.models import Challenge, ChallengeStatus
from .models import (
    PointLog,
    Badge,
    StudyDayLog,
    UserBadge,
    RewardStoreItem,
    UserRewardPurchase,
    PointReason,
)
from apps.study.models import UserQuestionAttempt, UserTestAttempt

DjangoUser = settings.AUTH_USER_MODEL
logger = logging.getLogger(__name__)
BadgeChecker = Callable[[DjangoUser, UserProfile], bool]


# --- Point Management ---
def award_points(
    user: DjangoUser,
    points_change: int,
    reason_code: PointReason,
    description: str,
    related_object: Optional[models.Model] = None,
) -> int:  # Changed return type
    """
    Atomically awards points to a user, logs the transaction, and updates the profile.
    Returns the actual number of points changed (0 if no change or error).
    """
    if not user or not hasattr(user, "pk"):
        logger.error(f"Attempted to award points to invalid user object: {user}")
        return 0  # Return 0 for failure

    if points_change == 0:
        return 0  # No change

    username = getattr(user, "username", f"UserID_{user.pk}")

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
            profile.refresh_from_db(fields=["points"])
            logger.info(
                f"Awarded {points_change} points to {username} for {reason_code.label}. "
                f"New balance: {profile.points}"
            )
            return points_change  # Return actual points changed
    except UserProfile.DoesNotExist:
        logger.error(
            f"UserProfile not found for user {username} during point award for {reason_code.label}."
        )
        return 0
    except Exception as e:
        logger.exception(
            f"Error awarding points to {username} for {reason_code.label}: {e}"
        )
        return 0


# --- Badge Management ---
def check_and_award_badge(
    user: DjangoUser, badge_slug: str
) -> Optional[Dict[str, Any]]:  # Changed return type
    """
    Checks if a user qualifies for a specific badge and awards it.
    Returns a dict with badge details and points awarded if newly earned, else None.
    Badge details: {'slug': str, 'name': str, 'description': str, 'points_awarded': int}
    """
    if not user or not hasattr(user, "pk"):
        logger.warning(f"Badge check skipped for invalid user object: {user}")
        return None

    username = getattr(user, "username", f"UserID_{user.pk}")

    try:
        badge = Badge.objects.get(slug=badge_slug, is_active=True)
        profile = UserProfile.objects.get(user=user)

        if UserBadge.objects.filter(user=user, badge=badge).exists():
            return None

        if badge.criteria_type == Badge.BadgeCriteriaType.OTHER:
            return None

        if (
            badge.target_value is None
            and badge.criteria_type != Badge.BadgeCriteriaType.OTHER
        ):  # Ensure target_value exists where needed
            logger.error(
                f"Badge '{badge_slug}' (type: {badge.criteria_type}) is missing target_value."
            )
            return None

        current_value = None
        if badge.criteria_type == Badge.BadgeCriteriaType.STUDY_STREAK:
            current_value = profile.current_streak_days
        elif badge.criteria_type == Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY:
            current_value = UserQuestionAttempt.objects.filter(
                user=user, is_correct=True
            ).count()
        elif badge.criteria_type == Badge.BadgeCriteriaType.TESTS_COMPLETED:
            current_value = UserTestAttempt.objects.filter(
                user=user, status=UserTestAttempt.Status.COMPLETED
            ).count()
        elif badge.criteria_type == Badge.BadgeCriteriaType.CHALLENGES_WON:
            current_value = Challenge.objects.filter(
                winner=user, status=ChallengeStatus.COMPLETED
            ).count()
        else:
            logger.warning(
                f"Unhandled criteria type '{badge.criteria_type}' for badge '{badge_slug}'."
            )
            return None

        criteria_met = False
        if current_value is not None and (
            badge.target_value is None or current_value >= badge.target_value
        ):
            # Handle cases where target_value might be None for certain auto-awarded badges not requiring a specific count
            if badge.target_value is not None and current_value < badge.target_value:
                criteria_met = False
            else:
                criteria_met = True

        if criteria_met:
            with transaction.atomic():
                user_badge, created = UserBadge.objects.get_or_create(
                    user=user, badge=badge
                )
                if created:
                    logger.info(
                        f"Awarded badge '{badge.name}' (slug: {badge_slug}) to user {username}"
                    )
                    points_for_this_badge = 0
                    points_badge_earned_setting = getattr(
                        settings, "POINTS_BADGE_EARNED", 0
                    )
                    if points_badge_earned_setting > 0:
                        points_for_this_badge = award_points(
                            user=user,
                            points_change=points_badge_earned_setting,
                            reason_code=PointReason.BADGE_EARNED,
                            description=f"Earned badge: {badge.name}",
                            related_object=user_badge,
                        )
                    return {
                        "slug": badge.slug,
                        "name": badge.name,
                        "description": badge.description,  # Or criteria_description
                        "points_awarded": points_for_this_badge,
                    }
                else:
                    logger.warning(
                        f"Badge '{badge_slug}' was already present for user {username} (race condition?)."
                    )
                    return None  # Not newly awarded
        return None  # Criteria not met
    except Badge.DoesNotExist:
        logger.warning(
            f"Badge with slug '{badge_slug}' not found or inactive for user {username}."
        )
        return None
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {username} during badge check.")
        return None
    except Exception as e:
        logger.exception(
            f"Error checking/awarding badge '{badge_slug}' for {username}: {e}"
        )
        return None


# --- Streak Management ---
def update_streak(user: DjangoUser) -> Dict[str, Any]:  # Changed return type
    """
    Updates user's study streak, logs study day, and handles streak-related points/badges.
    Returns a dict with streak update details, points, and badges awarded due to streak.
    """
    default_return = {
        "streak_was_updated": False,
        "current_streak_days": 0,
        "longest_streak_days": 0,
        "points_awarded_for_streak_bonus": 0,
        "badges_awarded_during_streak_update": [],
    }
    if not user or not hasattr(user, "pk"):
        logger.warning("Streak update skipped for invalid user object.")
        return default_return

    username = getattr(user, "username", f"UserID_{user.pk}")
    points_from_streak_bonus = 0
    badges_from_streak_update_details: List[Dict[str, Any]] = (
        []
    )  # Store full badge dicts

    try:
        now_utc = timezone.now()
        today_utc = now_utc.date()
        yesterday_utc = today_utc - timedelta(days=1)

        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)
            default_return["current_streak_days"] = profile.current_streak_days
            default_return["longest_streak_days"] = profile.longest_streak_days

            last_activity_date_utc = None
            if profile.last_study_activity_at:
                last_activity_date_utc = profile.last_study_activity_at.astimezone(
                    datetime.timezone.utc
                ).date()

            study_day_logged_this_call = False
            if last_activity_date_utc != today_utc:
                _, created = StudyDayLog.objects.get_or_create(
                    user=user, study_date=today_utc
                )
                if created:
                    study_day_logged_this_call = True
                    logger.info(
                        f"Logged new study day {today_utc.isoformat()} for user {username}"
                    )

            streak_value_changed = False
            original_streak_for_comparison = profile.current_streak_days

            if last_activity_date_utc == today_utc:
                if (
                    profile.last_study_activity_at < now_utc
                ):  # Later activity on same day
                    profile.last_study_activity_at = now_utc
                    profile.save(update_fields=["last_study_activity_at"])
                # No change to streak days itself, but day was logged if first activity
                default_return["streak_was_updated"] = (
                    study_day_logged_this_call  # True if new day log created
                )
                return default_return

            if last_activity_date_utc == yesterday_utc:
                profile.current_streak_days = F("current_streak_days") + 1
                streak_value_changed = True
                logger.info(f"User {username} continued streak.")
            elif (
                last_activity_date_utc is None or last_activity_date_utc < yesterday_utc
            ):
                profile.current_streak_days = 1
                streak_value_changed = True
                logger.info(f"User {username} started/reset streak to 1.")

            profile.last_study_activity_at = now_utc
            update_fields = ["last_study_activity_at"]
            if streak_value_changed:
                update_fields.append("current_streak_days")

            profile.save(update_fields=update_fields)
            profile.refresh_from_db(
                fields=[
                    "current_streak_days",
                    "longest_streak_days",
                    "last_study_activity_at",
                ]
            )  # Ensure all are fresh

            current_streak_after_update = profile.current_streak_days
            default_return["current_streak_days"] = current_streak_after_update
            default_return["streak_was_updated"] = (
                streak_value_changed or study_day_logged_this_call
            )

            if current_streak_after_update > profile.longest_streak_days:
                profile.longest_streak_days = current_streak_after_update
                profile.save(update_fields=["longest_streak_days"])
                logger.info(
                    f"User {username} updated longest streak to {current_streak_after_update} days."
                )
            default_return["longest_streak_days"] = profile.longest_streak_days

            # Award points and badges only if streak value actually increased
            if (
                streak_value_changed
                and current_streak_after_update > original_streak_for_comparison
            ):
                points_for_current_streak = settings.POINTS_STREAK_BONUS_MAP.get(
                    current_streak_after_update, 0
                )
                if points_for_current_streak > 0:
                    points_from_streak_bonus = award_points(
                        user=user,
                        points_change=points_for_current_streak,
                        reason_code=PointReason.STREAK_BONUS,
                        description=_("Reached {days}-day streak!").format(
                            days=current_streak_after_update
                        ),
                        related_object=profile,
                    )
                default_return["points_awarded_for_streak_bonus"] = (
                    points_from_streak_bonus
                )

                active_streak_badges_qs = Badge.objects.filter(
                    is_active=True, criteria_type=Badge.BadgeCriteriaType.STUDY_STREAK
                ).only(
                    "slug", "name", "description"
                )  # Fetch details needed

                for badge_def in active_streak_badges_qs:
                    # check_and_award_badge will compare current_streak_after_update with badge_def.target_value
                    badge_award_detail = check_and_award_badge(user, badge_def.slug)
                    if badge_award_detail:
                        badges_from_streak_update_details.append(badge_award_detail)
                        # Points for earning the badge are handled within check_and_award_badge
                        # and are already added to user's total. We collect them later if needed for summary.

            default_return["badges_awarded_during_streak_update"] = (
                badges_from_streak_update_details
            )
            return default_return

    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for user {username} during streak update.")
        # Return initial default values
        initial_default = {
            "streak_was_updated": False,
            "current_streak_days": 0,
            "longest_streak_days": 0,
            "points_awarded_for_streak_bonus": 0,
            "badges_awarded_during_streak_update": [],
        }
        try:  # Attempt to get latest profile values if possible, otherwise use 0s
            profile = UserProfile.objects.get(user=user)
            initial_default["current_streak_days"] = profile.current_streak_days
            initial_default["longest_streak_days"] = profile.longest_streak_days
        except UserProfile.DoesNotExist:
            pass  # Keep 0s
        return initial_default
    except Exception as e:
        logger.exception(f"Error updating streak/logging study day for {username}: {e}")
        # Return initial default values, potentially fetching current profile state if possible
        initial_default = {
            "streak_was_updated": False,
            "current_streak_days": 0,
            "longest_streak_days": 0,
            "points_awarded_for_streak_bonus": 0,
            "badges_awarded_during_streak_update": [],
        }
        try:
            profile = UserProfile.objects.get(user=user)
            initial_default["current_streak_days"] = profile.current_streak_days
            initial_default["longest_streak_days"] = profile.longest_streak_days
        except UserProfile.DoesNotExist:
            pass  # Keep 0s
        return initial_default


# --- New Consolidating Service ---
@transaction.atomic  # Ensure all gamification for a test completion is one unit
def process_test_completion_gamification(
    user: DjangoUser, test_attempt: UserTestAttempt
) -> Dict[str, Any]:
    """
    Processes all gamification aspects for a completed test attempt.
    Awards points, updates streak, checks for badges.
    Sets test_attempt.completion_points_awarded = True and saves it.
    """
    if test_attempt.completion_points_awarded:
        logger.warning(
            f"Gamification for test attempt {test_attempt.id} already processed. Skipping."
        )
        # Return what might have been if it was processed now, or simply indicate no new actions
        profile = UserProfile.objects.get(user=user)  # Get current state
        return {
            "total_points_earned": 0,
            "badges_won_details": [],
            "streak_info": {
                "was_updated": False,
                "current_days": profile.current_streak_days,  # Current streak, not necessarily updated now
            },
        }

    total_points_earned_this_event = 0
    all_newly_awarded_badges_details: List[Dict[str, Any]] = []

    # 1. Award points for the test type
    points_for_test_type = 0
    reason_for_test_points = PointReason.TEST_COMPLETED
    description_for_test_points = _("Completed Test Attempt #{att_id} ({type})").format(
        att_id=test_attempt.id, type=test_attempt.get_attempt_type_display()
    )

    if test_attempt.attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT:
        points_for_test_type = settings.POINTS_LEVEL_ASSESSMENT_COMPLETED
        reason_for_test_points = PointReason.LEVEL_ASSESSMENT_COMPLETED
        description_for_test_points = _("Completed Level Assessment #{att_id}").format(
            att_id=test_attempt.id
        )
    elif test_attempt.attempt_type in [
        UserTestAttempt.AttemptType.PRACTICE,
        UserTestAttempt.AttemptType.SIMULATION,
    ]:
        points_for_test_type = settings.POINTS_TEST_COMPLETED
    # For TRADITIONAL, points_for_test_type remains 0, which is fine.

    if points_for_test_type > 0:
        awarded_test_points = award_points(
            user=user,
            points_change=points_for_test_type,
            reason_code=reason_for_test_points,
            description=description_for_test_points,
            related_object=test_attempt,
        )
        total_points_earned_this_event += awarded_test_points

    # 2. Update streak (this also handles streak-specific points and badges)
    streak_results = update_streak(user)
    total_points_earned_this_event += streak_results.get(
        "points_awarded_for_streak_bonus", 0
    )

    # Add badges from streak update, ensuring no duplicates if a badge could be awarded by multiple paths
    for badge_detail in streak_results.get("badges_awarded_during_streak_update", []):
        if not any(
            b["slug"] == badge_detail["slug"] for b in all_newly_awarded_badges_details
        ):
            all_newly_awarded_badges_details.append(badge_detail)
            total_points_earned_this_event += badge_detail.get("points_awarded", 0)

    # 3. Check for other relevant badges (e.g., "N Tests Completed", "N Questions Solved")
    # These checks use the user's current overall stats.
    # Badges for "TESTS_COMPLETED"
    test_count_badges_qs = Badge.objects.filter(
        is_active=True, criteria_type=Badge.BadgeCriteriaType.TESTS_COMPLETED
    ).only("slug", "name", "description")
    for badge_def in test_count_badges_qs:
        badge_award_detail = check_and_award_badge(user, badge_def.slug)
        if badge_award_detail:
            if not any(
                b["slug"] == badge_award_detail["slug"]
                for b in all_newly_awarded_badges_details
            ):
                all_newly_awarded_badges_details.append(badge_award_detail)
                total_points_earned_this_event += badge_award_detail.get(
                    "points_awarded", 0
                )

    # Badges for "QUESTIONS_SOLVED_CORRECTLY"
    question_count_badges_qs = Badge.objects.filter(
        is_active=True, criteria_type=Badge.BadgeCriteriaType.QUESTIONS_SOLVED_CORRECTLY
    ).only("slug", "name", "description")
    for badge_def in question_count_badges_qs:
        badge_award_detail = check_and_award_badge(user, badge_def.slug)
        if badge_award_detail:
            if not any(
                b["slug"] == badge_award_detail["slug"]
                for b in all_newly_awarded_badges_details
            ):
                all_newly_awarded_badges_details.append(badge_award_detail)
                total_points_earned_this_event += badge_award_detail.get(
                    "points_awarded", 0
                )

    # 4. Mark test attempt as gamification processed and save
    test_attempt.completion_points_awarded = (
        True  # Using this flag universally for "gamification processed"
    )
    test_attempt.save(update_fields=["completion_points_awarded", "updated_at"])

    logger.info(
        f"Gamification processed for test attempt {test_attempt.id}. "
        f"Points: {total_points_earned_this_event}, Badges: {len(all_newly_awarded_badges_details)}, "
        f"Streak Updated: {streak_results.get('streak_was_updated', False)}, Current Streak: {streak_results.get('current_streak_days', 0)}"
    )

    return {
        "total_points_earned": total_points_earned_this_event,
        "badges_won_details": all_newly_awarded_badges_details,  # Contains full badge dicts
        "streak_info": {
            "was_updated": streak_results.get("streak_was_updated", False),
            "current_days": streak_results.get("current_streak_days", 0),
        },
    }


# --- Rewards Store Management (largely unchanged from original structure) ---
class PurchaseError(Exception):
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
        raise
    try:
        with transaction.atomic():
            profile = UserProfile.objects.select_for_update().get(user=user)
            if profile.points < item.cost_points:
                raise PurchaseError(_("Insufficient points to purchase this item."))

            point_deducted_amount = award_points(  # award_points returns amount
                user=user,
                points_change=-item.cost_points,
                reason_code=PointReason.REWARD_PURCHASE,
                description=f"Purchased: {item.name} (ID: {item.id})",
                related_object=item,
            )
            if (
                point_deducted_amount == 0 and item.cost_points > 0
            ):  # Check if deduction actually happened
                raise PurchaseError(
                    _("Failed to update points balance during purchase.")
                )

            UserRewardPurchase.objects.create(
                user=user, item=item, points_spent=item.cost_points
            )
            logger.info(
                f"User {username} purchased reward '{item.name}' (ID: {item.id})."
            )
            profile.refresh_from_db(fields=["points"])
            return {
                "item_id": item.id,
                "item_name": item.name,
                "points_spent": item.cost_points,
                "remaining_points": profile.points,
            }
    except UserProfile.DoesNotExist:
        logger.error(f"UserProfile not found for {username} during reward purchase.")
        raise PurchaseError(_("User profile error during purchase."))
    except PurchaseError as pe:
        logger.warning(f"Purchase failed for user {username}, item {item.id}: {pe}")
        raise pe
    except Exception as e:
        logger.exception(
            f"Unexpected error purchasing item {item_id} by {username}: {e}"
        )
        raise PurchaseError(_("An unexpected error occurred during purchase."))
