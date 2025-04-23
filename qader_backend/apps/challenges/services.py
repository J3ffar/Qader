import random
import logging
from typing import Tuple, Optional

from django.db import transaction
from django.db.models import Q, F
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils.translation import gettext_lazy as _

from .models import Challenge, ChallengeAttempt, ChallengeType, ChallengeStatus
from apps.learning.models import Question, LearningSection, LearningSubSection
from apps.study.models import UserQuestionAttempt
from apps.gamification.services import award_points, check_and_award_badge, PointReason
from apps.users.models import UserProfile  # For level matching


User = get_user_model()
logger = logging.getLogger(__name__)

# --- Configuration ---
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

POINTS_CHALLENGE_PARTICIPATION = 5
POINTS_CHALLENGE_WIN = 10

# --- Helper Functions ---


def _get_challenge_questions(config: dict) -> list[int]:
    """Selects random questions based on the challenge configuration."""
    num_questions = config.get("num_questions", 10)
    section_slugs = config.get("sections", [])
    subsection_slugs = config.get("subsections", [])
    skill_slugs = config.get("skills", [])

    # Build filter query
    filters = Q(is_active=True)
    if skill_slugs:
        filters &= Q(skill__slug__in=skill_slugs)
    elif subsection_slugs:
        filters &= Q(subsection__slug__in=subsection_slugs)
    elif section_slugs:
        filters &= Q(subsection__section__slug__in=section_slugs)

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
        # Decide: raise error or proceed with fewer? For now, proceed.
    elif (
        len(question_ids) > num_questions
    ):  # Should not happen with [:num_questions] but safe check
        question_ids = question_ids[:num_questions]

    random.shuffle(
        question_ids
    )  # Shuffle again just in case order_by('?') isn't perfect
    return question_ids


def _find_random_opponent(challenger: User) -> Optional[User]:
    """Finds a suitable random opponent (e.g., similar level, online)."""
    # Placeholder: Implement real matchmaking logic
    # - Check for users actively seeking random challenges
    # - Filter by level proximity (using UserProfile levels)
    # - Filter out the challenger themselves
    # - Prioritize online users (requires presence tracking system)
    # For now, just pick a random *other* active user (NOT production ready)
    possible_opponents = User.objects.filter(
        is_active=True, profile__isnull=False  # Ensure profile exists
    ).exclude(pk=challenger.pk)

    if possible_opponents.exists():
        return random.choice(possible_opponents)
    return None


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

    # TODO: Add check if user already has an active challenge pending/ongoing

    try:
        config = CHALLENGE_CONFIGS[challenge_type].copy()  # Get base config
        config["name"] = config.get("name", challenge_type)  # Ensure name is set
    except KeyError:
        raise ValidationError(_("Invalid challenge type specified."))

    question_ids = _get_challenge_questions(config)
    if not question_ids:
        raise ValidationError(
            _("Could not find suitable questions for this challenge type.")
        )
    config["num_questions"] = len(question_ids)  # Store actual number used

    message = ""
    initial_status = ChallengeStatus.PENDING_INVITE

    if opponent:
        # Direct Invite
        if not hasattr(opponent, "profile"):
            raise ValidationError(_("Invalid opponent user specified."))
        # TODO: Check if opponent accepts challenges? Add notification logic here.
        message = _("Challenge issued to {username}!").format(
            username=opponent.username
        )
    else:
        # Random Matchmaking
        opponent = _find_random_opponent(challenger)
        if opponent:
            initial_status = (
                ChallengeStatus.ACCEPTED
            )  # Found opponent, assume auto-accept for random
            message = _("Random challenge started with {username}!").format(
                username=opponent.username
            )
            # TODO: Notify opponent if needed for random matches
        else:
            initial_status = ChallengeStatus.PENDING_MATCHMAKING
            message = _("Searching for a random opponent...")
            # TODO: Add logic to handle async matchmaking (e.g., Celery task, WebSockets)

    challenge = Challenge.objects.create(
        challenger=challenger,
        opponent=opponent,
        challenge_type=challenge_type,
        status=initial_status,
        challenge_config=config,
        question_ids=question_ids,
    )

    # Create initial attempt records
    ChallengeAttempt.objects.create(challenge=challenge, user=challenger)
    if opponent:
        ChallengeAttempt.objects.create(challenge=challenge, user=opponent)

    logger.info(
        f"Challenge {challenge.id} created. Status: {initial_status}. Type: {challenge_type}"
    )
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
    challenge.save(update_fields=["status", "accepted_at", "updated_at"])
    # TODO: Notify challenger
    logger.info(f"Challenge {challenge.id} accepted by {user.username}")
    return challenge


@transaction.atomic
def decline_challenge(challenge: Challenge, user: User) -> Challenge:
    """Declines a pending challenge invitation."""
    if challenge.opponent != user:
        raise PermissionDenied(_("You are not the invited opponent."))
    if challenge.status != ChallengeStatus.PENDING_INVITE:
        raise ValidationError(_("Challenge is not pending invitation."))

    challenge.status = ChallengeStatus.DECLINED
    challenge.save(update_fields=["status", "updated_at"])
    # TODO: Notify challenger
    logger.info(f"Challenge {challenge.id} declined by {user.username}")
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
    challenge.save(update_fields=["status", "updated_at"])
    # TODO: Notify opponent if invite was sent
    logger.info(f"Challenge {challenge.id} cancelled by {user.username}")
    return challenge


@transaction.atomic
def set_participant_ready(challenge: Challenge, user: User) -> Tuple[Challenge, bool]:
    """Marks a participant as ready and checks if the challenge can start."""
    if not challenge.is_participant(user):
        raise PermissionDenied(_("You are not a participant in this challenge."))
    if challenge.status not in [ChallengeStatus.ACCEPTED, ChallengeStatus.ONGOING]:
        raise ValidationError(_("Challenge is not in a state to be started."))

    attempt, created = ChallengeAttempt.objects.get_or_create(
        challenge=challenge, user=user
    )
    if not attempt.is_ready:
        attempt.is_ready = True
        attempt.start_time = timezone.now()  # Mark user's start time
        attempt.save(update_fields=["is_ready", "start_time", "updated_at"])
        logger.info(
            f"User {user.username} marked as ready for Challenge {challenge.id}"
        )

    # Check if both participants are ready
    all_attempts = challenge.attempts.all()
    required_participants = (
        2 if challenge.opponent else 1
    )  # Should always be 2 after matching
    if all_attempts.count() >= required_participants and all(
        a.is_ready for a in all_attempts
    ):
        if challenge.status == ChallengeStatus.ACCEPTED:
            challenge.status = ChallengeStatus.ONGOING
            challenge.started_at = timezone.now()  # Mark overall challenge start
            challenge.save(update_fields=["status", "started_at", "updated_at"])
            logger.info(f"Challenge {challenge.id} transitioned to ONGOING.")
            # TODO: Trigger WebSocket event to start challenge for clients
            return challenge, True  # Challenge started
    return challenge, False  # Challenge not started yet


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

    # Get or create the user's attempt record for this challenge
    challenge_attempt, _ = ChallengeAttempt.objects.get_or_create(
        challenge=challenge, user=user
    )

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
        # No direct link to challenge_attempt needed here if using M2M below
    )
    # Link it to the ChallengeAttempt via M2M
    challenge_attempt.question_attempts.add(user_question_attempt)

    # Update score immediately (or could do at the end)
    if is_correct:
        challenge_attempt.score = F("score") + 1
        challenge_attempt.save(update_fields=["score", "updated_at"])
        # Refresh to get updated score for potential immediate checks
        challenge_attempt.refresh_from_db(fields=["score"])

    logger.info(
        f"User {user.username} answered Q:{question_id} in Challenge {challenge.id}. Correct: {is_correct}"
    )

    # Check if challenge ended for this user
    challenge_ended = False
    num_answered = challenge_attempt.question_attempts.count()
    if num_answered >= challenge.num_questions:
        challenge_attempt.end_time = timezone.now()
        challenge_attempt.save(update_fields=["end_time", "updated_at"])
        logger.info(
            f"User {user.username} finished their part of Challenge {challenge.id}"
        )
        # Check if *both* players have finished to finalize
        if _check_and_finalize_challenge(challenge):
            challenge_ended = True

    # Check for time limit expiration (needs async task or WebSocket handling ideally)

    return user_question_attempt, challenge_ended


def _check_and_finalize_challenge(challenge: Challenge) -> bool:
    """Checks if all participants have finished and finalizes the challenge."""
    if challenge.status != ChallengeStatus.ONGOING:
        return False  # Already finalized or not started

    with transaction.atomic():
        # Lock challenge for update
        challenge = Challenge.objects.select_for_update().get(pk=challenge.id)
        attempts = challenge.attempts.all()
        required_participants = 2 if challenge.opponent else 1

        # Check if everyone required has finished (has an end_time)
        if attempts.count() >= required_participants and all(
            a.end_time is not None for a in attempts
        ):
            logger.info(
                f"All participants finished Challenge {challenge.id}. Finalizing..."
            )
            finalize_challenge(challenge)  # Call the finalization logic
            return True
    return False


@transaction.atomic
def finalize_challenge(challenge: Challenge):
    """Calculates winner, updates status, awards points/badges."""
    if challenge.status != ChallengeStatus.ONGOING:
        logger.warning(
            f"Attempted to finalize challenge {challenge.id} which is not ongoing (Status: {challenge.status})."
        )
        return

    challenger_attempt = challenge.attempts.filter(user=challenge.challenger).first()
    opponent_attempt = (
        challenge.attempts.filter(user=challenge.opponent).first()
        if challenge.opponent
        else None
    )

    # Determine winner (simple score comparison, add time tie-breaker if needed)
    winner = None
    if challenger_attempt and opponent_attempt:
        if challenger_attempt.score > opponent_attempt.score:
            winner = challenge.challenger
        elif opponent_attempt.score > challenger_attempt.score:
            winner = challenge.opponent
        # Handle ties? For now, no winner in case of tie.
    elif (
        challenger_attempt
    ):  # Only challenger participated (e.g., opponent never joined/finished?)
        # Decide if this counts as a win or just completion? For now, no winner.
        pass

    challenge.winner = winner
    challenge.status = ChallengeStatus.COMPLETED
    challenge.completed_at = timezone.now()

    # Award points
    challenger_points = POINTS_CHALLENGE_PARTICIPATION
    opponent_points = POINTS_CHALLENGE_PARTICIPATION if challenge.opponent else 0

    if winner == challenge.challenger:
        challenger_points += POINTS_CHALLENGE_WIN
    elif winner == challenge.opponent:
        opponent_points += POINTS_CHALLENGE_WIN

    challenge.challenger_points_awarded = challenger_points
    challenge.opponent_points_awarded = opponent_points if challenge.opponent else None

    challenge.save()  # Save winner, status, completion time, points

    # Actually award points using gamification service
    if challenger_attempt:
        award_points(
            user=challenge.challenger,
            points_change=challenger_points,
            reason_code=(
                PointReason.CHALLENGE_PARTICIPATION
                if winner != challenge.challenger
                else PointReason.CHALLENGE_WIN
            ),
            description=_("Challenge #{cid} vs {opp} - Result: {res}").format(
                cid=challenge.id,
                opp=challenge.opponent.username if challenge.opponent else "N/A",
                res=(
                    "Win"
                    if winner == challenge.challenger
                    else ("Loss" if winner else "Tie/Completed")
                ),
            ),
            related_object=challenge,
        )
    if opponent_attempt:
        award_points(
            user=challenge.opponent,
            points_change=opponent_points,
            reason_code=(
                PointReason.CHALLENGE_PARTICIPATION
                if winner != challenge.opponent
                else PointReason.CHALLENGE_WIN
            ),
            description=_("Challenge #{cid} vs {opp} - Result: {res}").format(
                cid=challenge.id,
                opp=challenge.challenger.username,
                res=(
                    "Win"
                    if winner == challenge.opponent
                    else ("Loss" if winner else "Tie/Completed")
                ),
            ),
            related_object=challenge,
        )

    # Check for badges
    if winner:
        # Placeholder: check win streak badges etc.
        check_and_award_badge(
            winner, "challenge-winner-badge"
        )  # e.g., "First Challenge Win"
        # check_and_award_badge(winner, '3-consecutive-wins-badge') # Needs tracking win history

    logger.info(
        f"Challenge {challenge.id} finalized. Winner: {winner.username if winner else 'Tie'}."
    )


# --- Rematch Service --- (Optional)
def create_rematch(original_challenge: Challenge, user_initiating: User) -> Challenge:
    """Creates a new challenge as a rematch of a completed one."""
    if original_challenge.status != ChallengeStatus.COMPLETED:
        raise ValidationError(_("Can only rematch completed challenges."))
    if not original_challenge.is_participant(user_initiating):
        raise PermissionDenied(
            _("You were not a participant in the original challenge.")
        )

    challenger = user_initiating
    opponent = (
        original_challenge.challenger
        if original_challenge.opponent == user_initiating
        else original_challenge.opponent
    )

    if not opponent:  # Should not happen if original challenge had 2 participants
        raise ValidationError(_("Cannot rematch this challenge (missing opponent)."))

    # Re-use the same challenge type/config from original
    new_challenge, _, _ = start_challenge(
        challenger=challenger,
        opponent=opponent,
        challenge_type=original_challenge.challenge_type,
    )
    logger.info(
        f"Rematch initiated (New Challenge {new_challenge.id}) based on original Challenge {original_challenge.id}."
    )
    return new_challenge
