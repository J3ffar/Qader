import random
import logging
import json  # Add json import
from typing import Tuple, Optional

from django.conf import settings
from django.db import transaction
from django.db.models import Q, F
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _
from channels.layers import get_channel_layer  # Add channel layer import
from asgiref.sync import async_to_sync

from apps.gamification.models import (
    Badge,
)  # To call async group_send from sync code

from .models import Challenge, ChallengeAttempt, ChallengeType, ChallengeStatus
from apps.learning.models import (
    Question,
)  # Removed unused LearningSection, LearningSubSection
from apps.study.models import UserQuestionAttempt
from apps.gamification.services import award_points, check_and_award_badge, PointReason
from apps.users.models import UserProfile  # For level matching

# Import serializers to format broadcast data
from .api.serializers import (
    ChallengeDetailSerializer,
    ChallengeAttemptSerializer,
    ChallengeListSerializer,
    UnifiedQuestionSerializer,  # Assuming this exists and works standalone
    ChallengeResultSerializer,  # Import the result serializer
)


User = get_user_model()
logger = logging.getLogger(__name__)

# --- Configuration ---
# Using constants from settings is better if they need to be configurable
# For simplicity here, keeping them defined, but consider moving to settings
CHALLENGE_CONFIGS = {
    ChallengeType.QUICK_QUANT_10: {
        "num_questions": 10,
        "time_limit_seconds": 300,
        "allow_hints": False,
        "sections": ["quantitative"],
        "subsections": [],
        "skills": [],
        "name": _("Quick Quant Challenge"),
    },
    ChallengeType.MEDIUM_VERBAL_15: {
        "num_questions": 15,
        "time_limit_seconds": 600,
        "allow_hints": False,
        "sections": ["verbal"],
        "subsections": [],
        "skills": [],
        "name": _("Medium Verbal Challenge"),
    },
    ChallengeType.COMPREHENSIVE_20: {
        "num_questions": 20,
        "time_limit_seconds": 900,
        "allow_hints": True,
        "sections": ["quantitative", "verbal"],
        "subsections": [],
        "skills": [],
        "name": _("Comprehensive Challenge"),
    },
    # Add configs for SPEED_CHALLENGE_5MIN, ACCURACY_CHALLENGE, CUSTOM if needed
}

# Consider moving points to settings for configurability
POINTS_CHALLENGE_PARTICIPATION = 5
POINTS_CHALLENGE_WIN = 10

# --- Broadcasting Helper Functions ---


def broadcast_challenge_update(challenge: Challenge):
    """Sends the full challenge state to the challenge group."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return  # Avoid errors if channels isn't configured
    group_name = f"challenge_{challenge.id}"
    try:
        # Pass minimal context; avoid passing request if possible
        serializer = ChallengeDetailSerializer(challenge, context={"request": None})
        payload = serializer.data
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "challenge.update",  # Matches consumer method name
                "payload": payload,
            },
        )
        logger.info(
            f"Broadcasted challenge_update for Challenge {challenge.id} to group {group_name}"
        )
    except Exception as e:
        logger.error(
            f"Error broadcasting challenge update for {challenge.id}: {e}",
            exc_info=True,
        )


def broadcast_participant_update(attempt: ChallengeAttempt):
    """Sends an update about a specific participant."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    group_name = f"challenge_{attempt.challenge_id}"
    try:
        serializer = ChallengeAttemptSerializer(attempt)
        payload = serializer.data
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "participant.update",
                "payload": payload,
            },
        )
        logger.info(
            f"Broadcasted participant_update for User {attempt.user_id}, Challenge {attempt.challenge_id}"
        )
    except Exception as e:
        logger.error(
            f"Error broadcasting participant update for user {attempt.user_id}, challenge {attempt.challenge_id}: {e}",
            exc_info=True,
        )


def broadcast_challenge_start(challenge: Challenge):
    """Sends the start signal and potentially questions."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    group_name = f"challenge_{challenge.id}"
    try:
        questions_qs = challenge.get_questions_queryset()
        # Ensure UnifiedQuestionSerializer doesn't strictly require a request context
        question_serializer = UnifiedQuestionSerializer(
            questions_qs, many=True, context={"request": None}
        )

        payload = {
            "id": challenge.id,
            "status": challenge.status,
            "started_at": (
                challenge.started_at.isoformat() if challenge.started_at else None
            ),
            "challenge_config": challenge.challenge_config,
            "questions": question_serializer.data,  # Send questions on start
        }
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "challenge.start",
                "payload": payload,
            },
        )
        logger.info(f"Broadcasted challenge_start for Challenge {challenge.id}")
    except Exception as e:
        logger.error(
            f"Error broadcasting challenge start for {challenge.id}: {e}", exc_info=True
        )


def broadcast_answer_result(attempt: UserQuestionAttempt, challenge_id: int):
    """Broadcasts the result of a single answer submission."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    group_name = f"challenge_{challenge_id}"
    try:
        # Fetch current score *after* potential update in process_challenge_answer
        current_score = (
            ChallengeAttempt.objects.values_list("score", flat=True)
            .filter(challenge_id=challenge_id, user_id=attempt.user_id)
            .first()
        )

        payload = {
            "user_id": attempt.user_id,
            "question_id": attempt.question_id,
            "is_correct": attempt.is_correct,
            "selected_answer": attempt.selected_answer,
            "current_score": current_score if current_score is not None else 0,
        }
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "answer.result",
                "payload": payload,
            },
        )
        logger.info(
            f"Broadcasted answer_result for Q:{attempt.question_id}, User:{attempt.user_id}, Challenge:{challenge_id}"
        )
    except Exception as e:
        logger.error(
            f"Error broadcasting answer result for Q:{attempt.question_id}, User:{attempt.user_id}, Challenge:{challenge_id}: {e}",
            exc_info=True,
        )


def broadcast_challenge_end(challenge: Challenge):
    """Broadcasts the final results of the challenge."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    group_name = f"challenge_{challenge.id}"
    try:
        serializer = ChallengeResultSerializer(challenge, context={"request": None})
        payload = serializer.data
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "challenge.end",
                "payload": payload,
            },
        )
        logger.info(f"Broadcasted challenge_end for Challenge {challenge.id}")
    except Exception as e:
        logger.error(
            f"Error broadcasting challenge end for {challenge.id}: {e}", exc_info=True
        )


def notify_user(user_id: int, event_type: str, payload: dict):
    """Sends a notification to a specific user's notification channel."""
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    user_group_name = f"user_{user_id}_challenges"
    try:
        async_to_sync(channel_layer.group_send)(
            user_group_name,
            {
                "type": event_type,  # e.g., "new.challenge.invite"
                "payload": payload,
            },
        )
        logger.info(f"Sent notification {event_type} to user {user_id}")
    except Exception as e:
        logger.error(
            f"Error sending notification {event_type} to user {user_id}: {e}",
            exc_info=True,
        )


# --- Question/Opponent Selection Helper Functions ---


def _get_challenge_questions(config: dict) -> list[int]:
    """Selects random questions based on the challenge configuration."""
    num_questions = config.get("num_questions", 10)
    section_slugs = config.get("sections", [])
    subsection_slugs = config.get("subsections", [])
    skill_slugs = config.get("skills", [])

    # Build filter query
    filters = Q(is_active=True)
    # Apply filters progressively specific -> general
    if skill_slugs:
        filters &= Q(skill__slug__in=skill_slugs)
    elif subsection_slugs:
        filters &= Q(subsection__slug__in=subsection_slugs)
    elif section_slugs:
        # Assuming Question has direct FK to Subsection, and Subsection has FK to Section
        filters &= Q(subsection__section__slug__in=section_slugs)
    else:
        # No filters applied, might select from all active questions
        pass

    question_ids = list(
        Question.objects.filter(filters)
        .order_by("?")  # Random order
        .values_list("id", flat=True)[:num_questions]
    )

    # Ensure exact number requested, handle cases with fewer available questions
    if len(question_ids) < num_questions:
        logger.warning(
            f"Could only find {len(question_ids)}/{num_questions} questions for challenge config: {config}"
        )
        # Raise error if NO questions found?
        if not question_ids:
            raise ValidationError(
                _("No suitable questions found for this challenge configuration.")
            )
        # Proceed with fewer questions
    elif len(question_ids) > num_questions:  # Should not happen with slice
        question_ids = question_ids[:num_questions]

    random.shuffle(question_ids)  # Shuffle again for good measure
    return question_ids


def _find_random_opponent(challenger: User) -> Optional[User]:
    """Finds a suitable random opponent (basic implementation)."""
    # Placeholder: Implement real matchmaking logic
    # - Consider UserProfile level for matching
    # - Check for users actively seeking random challenges (new model field?)
    # - Prioritize online users (requires presence tracking - complex)
    # Basic: Find any other active user with a profile
    possible_opponents = (
        User.objects.filter(is_active=True, profile__isnull=False)
        .exclude(pk=challenger.pk)
        .order_by("?")  # Random opponent
    )
    # Future: Filter by level difference:
    # challenger_level = challenger.profile.get_current_level() # Assumes method exists
    # possible_opponents = possible_opponents.annotate(
    #     level_diff=Abs(F('profile__level_field') - challenger_level)
    # ).filter(level_diff__lte=2).order_by('level_diff', '?') # Prioritize closer levels

    return possible_opponents.first()


# --- Core Service Functions ---


@transaction.atomic
def start_challenge(
    challenger: User, opponent: Optional[User], challenge_type: str
) -> Tuple[Challenge, str, ChallengeStatus]:
    """
    Starts a new challenge, either direct invite or random matchmaking.
    Returns (Challenge instance, user message, initial status).
    Raises ValidationError on failure.
    """
    if not challenger or not hasattr(challenger, "profile"):
        raise ValidationError(_("Invalid challenger user."))
    if opponent and not hasattr(opponent, "profile"):
        raise ValidationError(_("Invalid opponent user specified."))
    if opponent and opponent == challenger:
        raise ValidationError(_("You cannot challenge yourself."))

    # Consider adding checks for active challenges, subscription status etc. here

    try:
        config = CHALLENGE_CONFIGS[
            ChallengeType(challenge_type)
        ].copy()  # Validate choice & copy
        config["name"] = str(config.get("name", challenge_type))
    except (KeyError, ValueError):
        raise ValidationError(_("Invalid challenge type specified."))

    question_ids = _get_challenge_questions(config)
    if not question_ids:
        # _get_challenge_questions should raise if none found, but double check
        raise ValidationError(
            _("Could not find suitable questions for this challenge type.")
        )
    config["num_questions"] = len(question_ids)  # Store actual number used

    message = ""
    initial_status = ChallengeStatus.PENDING_INVITE
    found_opponent = opponent  # Track if we have a definite opponent

    if not opponent:
        # Random Matchmaking logic
        random_opponent = _find_random_opponent(challenger)
        if random_opponent:
            opponent = random_opponent  # Assign found opponent
            found_opponent = opponent
            initial_status = ChallengeStatus.ACCEPTED  # Auto-accept random matches
            message = _("Random challenge started with {username}!").format(
                username=opponent.username
            )
            # TODO: Need robust notification system if opponent isn't immediately connected via WS
        else:
            initial_status = ChallengeStatus.PENDING_MATCHMAKING
            message = _("Searching for a random opponent...")
            # TODO: Add logic for async matchmaking (e.g., Celery task + polling/WS updates)
    else:
        # Direct Invite logic
        message = _("Challenge issued to {username}!").format(
            username=opponent.username
        )

    challenge = Challenge.objects.create(
        challenger=challenger,
        opponent=opponent,  # Can be None if PENDING_MATCHMAKING
        challenge_type=challenge_type,
        status=initial_status,
        challenge_config=config,
        question_ids=question_ids,
    )

    # Create initial attempt records only if participants are known
    ChallengeAttempt.objects.create(challenge=challenge, user=challenger)
    if found_opponent:
        ChallengeAttempt.objects.create(challenge=challenge, user=found_opponent)

    logger.info(
        f"Challenge {challenge.id} created by {challenger.username} "
        f"(vs {opponent.username if opponent else 'Matchmaking'}). "
        f"Status: {initial_status}. Type: {challenge_type}"
    )

    # --- Broadcast ---
    if initial_status == ChallengeStatus.PENDING_INVITE and opponent:
        # Notify opponent via their specific notification channel
        invite_payload = ChallengeListSerializer(
            challenge, context={"request": None}
        ).data
        notify_user(
            opponent.id, "new_challenge_invite", invite_payload
        )  # Use snake_case type for consumer
    elif initial_status == ChallengeStatus.ACCEPTED:  # Random match found and accepted
        # Both participants are in, broadcast initial state to challenge group
        broadcast_challenge_update(challenge)

    return challenge, message, initial_status


@transaction.atomic
def accept_challenge(challenge: Challenge, user: User) -> Challenge:
    """Accepts a pending challenge invitation."""
    if challenge.opponent != user:
        raise PermissionDenied(_("You are not the invited opponent."))
    if challenge.status != ChallengeStatus.PENDING_INVITE:
        raise ValidationError(_("Challenge is not pending invitation."))

    challenge.status = ChallengeStatus.ACCEPTED
    challenge.accepted_at = timezone.now()
    challenge.save(update_fields=["status", "accepted_at"])
    logger.info(f"Challenge {challenge.id} accepted by {user.username}")

    # --- Broadcast ---
    # Notify challenger via their notification channel
    accept_payload = {"challenge_id": challenge.id, "accepted_by": user.username}
    notify_user(
        challenge.challenger.id, "challenge_accepted_notification", accept_payload
    )

    # Update everyone in the challenge group with the new state
    broadcast_challenge_update(challenge)

    return challenge


@transaction.atomic
def decline_challenge(challenge: Challenge, user: User) -> Challenge:
    """Declines a pending challenge invitation."""
    if challenge.opponent != user:
        raise PermissionDenied(_("You are not the invited opponent."))
    if challenge.status != ChallengeStatus.PENDING_INVITE:
        raise ValidationError(_("Challenge is not pending invitation."))

    challenge.status = ChallengeStatus.DECLINED
    challenge.save(update_fields=["status"])
    logger.info(f"Challenge {challenge.id} declined by {user.username}")

    # --- Broadcast ---
    # Notify challenger (optional)
    decline_payload = {"challenge_id": challenge.id, "declined_by": user.username}
    notify_user(
        challenge.challenger.id, "challenge_declined_notification", decline_payload
    )

    # Update challenge group (status is now Declined)
    broadcast_challenge_update(challenge)

    return challenge


@transaction.atomic
def cancel_challenge(challenge: Challenge, user: User) -> Challenge:
    """Cancels a challenge before it's accepted (by challenger)."""
    if challenge.challenger != user:
        raise PermissionDenied(_("Only the challenger can cancel."))
    if challenge.status not in [
        ChallengeStatus.PENDING_INVITE,
        ChallengeStatus.PENDING_MATCHMAKING,
    ]:
        raise ValidationError(_("Challenge cannot be cancelled in its current state."))

    challenge.status = ChallengeStatus.CANCELLED
    challenge.save(update_fields=["status"])
    logger.info(f"Challenge {challenge.id} cancelled by {user.username}")

    # --- Broadcast ---
    # Notify opponent if they were invited (optional)
    cancel_payload = {"challenge_id": challenge.id, "cancelled_by": user.username}
    if challenge.opponent and challenge.status == ChallengeStatus.PENDING_INVITE:
        notify_user(
            challenge.opponent.id, "challenge_cancelled_notification", cancel_payload
        )

    # Update challenge group (status is now Cancelled)
    broadcast_challenge_update(challenge)

    return challenge


@transaction.atomic
def set_participant_ready(challenge: Challenge, user: User) -> Tuple[Challenge, bool]:
    """Marks a participant as ready and checks if the challenge can start."""
    if not challenge.is_participant(user):
        raise PermissionDenied(_("You are not a participant in this challenge."))
    # Allow marking ready if ACCEPTED or ONGOING (e.g., reconnect)
    if challenge.status not in [ChallengeStatus.ACCEPTED, ChallengeStatus.ONGOING]:
        raise ValidationError(_("Challenge is not in a state to mark ready."))
    if not challenge.opponent:  # Cannot start if matchmaking hasn't found opponent
        raise ValidationError(_("Cannot start challenge without an opponent."))

    attempt, created = ChallengeAttempt.objects.get_or_create(
        challenge=challenge, user=user
    )

    if not attempt.is_ready:
        attempt.is_ready = True
        # Only set start_time if challenge hasn't officially started
        if not challenge.started_at:
            attempt.start_time = timezone.now()  # Mark user's *personal* start time
        attempt.save(update_fields=["is_ready", "start_time"])
        logger.info(
            f"User {user.username} marked as ready for Challenge {challenge.id}"
        )
        # --- Broadcast Participant Update ---
        broadcast_participant_update(attempt)

    challenge_started = False
    # Check if both participants are ready AND challenge is ACCEPTED
    # Use select_related for efficiency if accessing user attributes often
    all_attempts = challenge.attempts.all()
    required_participants = 2  # Assume 2 participants for standard challenges

    # Check > instead of == to handle potential race conditions/duplicates (though unique_together helps)
    if all_attempts.count() >= required_participants and all(
        a.is_ready for a in all_attempts
    ):
        # Ensure we only transition from ACCEPTED to ONGOING once
        challenge.refresh_from_db()  # Get latest status before check
        if challenge.status == ChallengeStatus.ACCEPTED:
            challenge.status = ChallengeStatus.ONGOING
            challenge.started_at = timezone.now()  # Mark overall challenge start
            challenge.save(update_fields=["status", "started_at"])
            logger.info(f"Challenge {challenge.id} transitioned to ONGOING.")

            # --- Broadcast Challenge Start ---
            broadcast_challenge_start(challenge)
            challenge_started = True
        elif challenge.status == ChallengeStatus.ONGOING:
            # Already started, maybe user reconnected and marked ready again
            challenge_started = True  # Indicate it's already running

    # Refresh challenge state before returning
    challenge.refresh_from_db()
    return challenge, challenge_started


@transaction.atomic
def process_challenge_answer(
    challenge: Challenge,
    user: User,
    question_id: int,
    selected_answer: str,
    time_taken: Optional[int],
) -> Tuple[UserQuestionAttempt, bool]:
    """Processes a user's answer during a challenge."""
    if not challenge.is_participant(user):
        raise PermissionDenied(_("You are not a participant in this challenge."))
    if challenge.status != ChallengeStatus.ONGOING:
        raise ValidationError(_("Challenge is not ongoing."))
    if question_id not in challenge.question_ids:
        raise ValidationError(_("Invalid question for this challenge."))

    try:
        question = Question.objects.get(pk=question_id)
    except Question.DoesNotExist:
        raise ValidationError(_("Question not found."))

    challenge_attempt = ChallengeAttempt.objects.filter(
        challenge=challenge, user=user
    ).first()
    if not challenge_attempt:
        # Should not happen if attempts are created on start/accept
        logger.error(
            f"Missing ChallengeAttempt for user {user.id} in challenge {challenge.id}"
        )
        raise ValidationError(_("Challenge participation record not found."))

    # Check if already answered this question in this challenge
    if challenge_attempt.question_attempts.filter(question=question).exists():
        raise ValidationError(
            _("You have already answered this question in this challenge.")
        )

    is_correct = question.correct_answer == selected_answer

    # Create the specific question attempt record
    user_question_attempt = UserQuestionAttempt.objects.create(
        user=user,
        question=question,
        selected_answer=selected_answer,
        is_correct=is_correct,
        time_taken_seconds=time_taken,
        mode=UserQuestionAttempt.Mode.CHALLENGE,
    )
    # Link it to the ChallengeAttempt via M2M
    challenge_attempt.question_attempts.add(user_question_attempt)

    # Update score immediately
    if is_correct:
        # Use F expression for atomic increment
        ChallengeAttempt.objects.filter(pk=challenge_attempt.pk).update(
            score=F("score") + 1
        )
        # Refresh the instance variable if needed later in this function
        challenge_attempt.refresh_from_db(fields=["score"])

    logger.info(
        f"User {user.username} answered Q:{question_id} in Challenge {challenge.id}. Correct: {is_correct}. Score: {challenge_attempt.score}"
    )

    # --- Broadcast Answer Result ---
    broadcast_answer_result(user_question_attempt, challenge.id)

    # --- Broadcast Participant Score Update --- (Send full attempt state for simplicity)
    # Refresh attempt again *after* score update and before broadcasting
    challenge_attempt.refresh_from_db()
    broadcast_participant_update(challenge_attempt)

    challenge_ended = False
    # Check if challenge ended for THIS user
    num_answered = challenge_attempt.question_attempts.count()
    num_total_questions = challenge.num_questions  # Use property

    if num_answered >= num_total_questions:
        if not challenge_attempt.end_time:  # Set end time only once
            challenge_attempt.end_time = timezone.now()
            challenge_attempt.save(update_fields=["end_time"])
            logger.info(
                f"User {user.username} finished their part of Challenge {challenge.id}"
            )
        # Now check if *both* players have finished to finalize
        if _check_and_finalize_challenge(challenge):
            challenge_ended = True  # finalize_challenge handles end broadcast

    # TODO: Add check for time limit expiration (better handled by scheduled task or consumer logic)

    return user_question_attempt, challenge_ended


def _check_and_finalize_challenge(challenge: Challenge) -> bool:
    """
    Checks if all participants have finished and finalizes the challenge.
    Returns True if finalized, False otherwise.
    """
    # Ensure we read the latest state, especially status
    challenge.refresh_from_db()
    if challenge.status != ChallengeStatus.ONGOING:
        logger.debug(
            f"Challenge {challenge.id} is not ONGOING, skipping finalization check."
        )
        return False

    with transaction.atomic():
        # Lock challenge and attempts for update to prevent race conditions
        challenge_locked = Challenge.objects.select_for_update().get(pk=challenge.id)
        # Re-check status after locking
        if challenge_locked.status != ChallengeStatus.ONGOING:
            logger.debug(
                f"Challenge {challenge.id} status changed before finalization could occur."
            )
            return False  # Status changed while waiting for lock

        attempts = ChallengeAttempt.objects.select_for_update().filter(
            challenge=challenge_locked
        )
        required_participants = (
            2 if challenge_locked.opponent else 1
        )  # Should have opponent if ongoing

        # Check if everyone required has finished (has an end_time)
        # Need to ensure the correct number of attempts exist first
        if attempts.count() >= required_participants and all(
            a.end_time is not None for a in attempts
        ):
            logger.info(
                f"All participants finished Challenge {challenge_locked.id}. Finalizing..."
            )
            # finalize_challenge now handles the broadcast internally
            finalize_challenge(challenge_locked)  # Pass the locked instance
            return True
        else:
            logger.debug(
                f"Challenge {challenge.id} not ready for finalization. Attempts count: {attempts.count()}, Finished: {[a.end_time is not None for a in attempts]}"
            )

    return False


@transaction.atomic
def finalize_challenge(challenge: Challenge):
    """Calculates winner, updates status, awards points/badges, broadcasts end."""
    # Double check status inside transaction
    challenge.refresh_from_db()  # Get latest status first
    if challenge.status != ChallengeStatus.ONGOING:
        logger.warning(
            f"Attempted to finalize challenge {challenge.id} which is not ONGOING (Status: {challenge.status}). Aborting finalization."
        )
        return  # Do not proceed if not ONGOING

    # Ensure attempts are loaded for calculation
    challenger_attempt = challenge.attempts.filter(user=challenge.challenger).first()
    opponent_attempt = (
        challenge.attempts.filter(user=challenge.opponent).first()
        if challenge.opponent
        else None
    )

    # --- Determine Winner ---
    winner = None
    # Ensure both attempts exist and have end_times before comparing scores
    # (Or adjust logic if finishing first matters even if opponent disconnects)
    if (
        challenger_attempt
        and challenger_attempt.end_time
        and opponent_attempt
        and opponent_attempt.end_time
    ):
        if challenger_attempt.score > opponent_attempt.score:
            winner = challenge.challenger
        elif opponent_attempt.score > challenger_attempt.score:
            winner = challenge.opponent
        # Handle ties: winner remains None.
        # TODO: Add time tie-breaker logic if required using attempt.start_time/end_time

    # Handle cases where one participant didn't finish (optional, based on rules)
    # Example: If opponent didn't finish, challenger wins by default?
    # elif challenger_attempt and challenger_attempt.end_time and \
    #      (not opponent_attempt or not opponent_attempt.end_time):
    #     winner = challenge.challenger # Challenger wins by forfeit/timeout
    #     logger.info(f"Challenge {challenge.id}: Opponent did not complete, challenger wins.")
    # elif opponent_attempt and opponent_attempt.end_time and \
    #      (not challenger_attempt or not challenger_attempt.end_time):
    #     winner = challenge.opponent # Opponent wins by forfeit/timeout
    #     logger.info(f"Challenge {challenge.id}: Challenger did not complete, opponent wins.")
    else:
        logger.info(
            f"Challenge {challenge.id}: Finalizing without a clear winner (tie or incomplete participation)."
        )

    # --- Calculate Points ---
    # Use constants from settings directly
    challenger_points = settings.POINTS_CHALLENGE_PARTICIPATION
    opponent_points = (
        settings.POINTS_CHALLENGE_PARTICIPATION if challenge.opponent else 0
    )

    if winner == challenge.challenger:
        challenger_points += settings.POINTS_CHALLENGE_WIN
    elif winner == challenge.opponent:
        opponent_points += settings.POINTS_CHALLENGE_WIN

    # --- Update Challenge State ---
    challenge.winner = winner
    challenge.status = ChallengeStatus.COMPLETED
    challenge.completed_at = timezone.now()
    challenge.challenger_points_awarded = challenger_points
    # Store 0 or None if opponent didn't exist/participate meaningfully
    challenge.opponent_points_awarded = opponent_points if opponent_attempt else None

    challenge.save(
        update_fields=[
            "winner",
            "status",
            "completed_at",
            "challenger_points_awarded",
            "opponent_points_awarded",
        ]
    )
    logger.info(
        f"Challenge {challenge.id} status set to COMPLETED. Winner: {winner.username if winner else 'Tie/Incomplete'}. "
        f"Points: C={challenger_points}, O={opponent_points if opponent_attempt else 'N/A'}."
    )

    # --- Award Points using Gamification Service ---
    # Only award points if the attempt record exists (meaning they participated)
    if challenger_attempt:
        challenger_reason = PointReason.CHALLENGE_PARTICIPATION
        challenger_result_desc = _("Tie/Completed")
        if winner == challenge.challenger:
            challenger_reason = PointReason.CHALLENGE_WIN
            challenger_result_desc = _("Win")
        elif winner == challenge.opponent:
            challenger_result_desc = _("Loss")

        award_points(
            user=challenge.challenger,
            points_change=challenger_points,
            reason_code=challenger_reason,
            description=_("Challenge #{cid} vs {opp} - Result: {res}").format(
                cid=challenge.id,
                opp=challenge.opponent.username if challenge.opponent else "N/A",
                res=challenger_result_desc,
            ),
            related_object=challenge,
        )

    if opponent_attempt:  # Check if opponent actually participated
        opponent_reason = PointReason.CHALLENGE_PARTICIPATION
        opponent_result_desc = _("Tie/Completed")
        if winner == challenge.opponent:
            opponent_reason = PointReason.CHALLENGE_WIN
            opponent_result_desc = _("Win")
        elif winner == challenge.challenger:
            opponent_result_desc = _("Loss")

        award_points(
            user=challenge.opponent,
            points_change=opponent_points,
            reason_code=opponent_reason,
            description=_("Challenge #{cid} vs {opp} - Result: {res}").format(
                cid=challenge.id,
                opp=challenge.challenger.username,
                res=opponent_result_desc,
            ),
            related_object=challenge,
        )

    # --- Check for and Award Badges ---
    # Fetch relevant active badge slugs once
    challenge_badge_slugs = list(
        Badge.objects.filter(
            is_active=True,
            criteria_type=Badge.BadgeCriteriaType.CHALLENGES_WON,  # Use the new type
        ).values_list("slug", flat=True)
    )

    if winner:
        logger.info(
            f"Checking CHALLENGES_WON badges for winner {winner.username} on Challenge {challenge.id}"
        )
        # Call check_and_award_badge for each relevant badge slug
        # The service function will handle the logic of counting wins and comparing to target_value
        for slug in challenge_badge_slugs:
            check_and_award_badge(winner, slug)  # Pass the winner user and badge slug

    # --- Broadcast Challenge End ---
    # Broadcast AFTER all updates and point/badge awards are done
    broadcast_challenge_end(challenge)

    logger.info(f"Challenge {challenge.id} finalized completely.")


# --- Rematch Service ---
@transaction.atomic  # Rematch involves creating a new challenge
def create_rematch(original_challenge: Challenge, user_initiating: User) -> Challenge:
    """Creates a new challenge as a rematch of a completed one."""
    if original_challenge.status != ChallengeStatus.COMPLETED:
        raise ValidationError(_("Can only rematch completed challenges."))
    if not original_challenge.is_participant(user_initiating):
        raise PermissionDenied(
            _("You were not a participant in the original challenge.")
        )
    if (
        not original_challenge.opponent
    ):  # Cannot rematch if original was matchmaking that failed or single player
        raise ValidationError(
            _("Cannot rematch a challenge that didn't have two participants.")
        )

    # Determine new challenger/opponent based on who initiated rematch
    challenger = user_initiating
    opponent = (
        original_challenge.challenger
        if original_challenge.opponent == user_initiating
        else original_challenge.opponent
    )

    if not opponent:  # Should not happen if original challenge had 2 participants
        raise ValidationError(_("Cannot rematch this challenge (missing opponent)."))

    # Re-use the same challenge type/config from original
    try:
        # Calls start_challenge, which handles creation and initial broadcast/notification
        new_challenge, message, initial_status = start_challenge(
            challenger=challenger,
            opponent=opponent,
            challenge_type=original_challenge.challenge_type,
        )
        # The initial status will be PENDING_INVITE

        logger.info(
            f"Rematch initiated by {user_initiating.username} "
            f"(New Challenge {new_challenge.id}) based on original Challenge {original_challenge.id}."
        )
        return new_challenge
    except ValidationError as e:  # Catch potential ValidationError from start_challenge
        # Re-raise as DRFValidationError if needed, or handle appropriately
        raise ValidationError(e.message_dict if hasattr(e, "message_dict") else str(e))
