import logging
from enum import Enum

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.study.models import UserQuestionAttempt, Question
from apps.users.models import UserProfile  # To access levels if needed for matching

logger = logging.getLogger(__name__)


class ChallengeType(models.TextChoices):
    # Add more specific types based on description page 10, section 10.b
    QUICK_QUANT_10 = "quick_quant_10", _("Quick Quant (10 Q)")
    MEDIUM_VERBAL_15 = "medium_verbal_15", _("Medium Verbal (15 Q, No Hints)")
    COMPREHENSIVE_20 = "comprehensive_20", _("Comprehensive (20 Q)")
    SPEED_CHALLENGE_5MIN = "speed_challenge_5min", _("Speed Challenge (5 Min)")
    ACCURACY_CHALLENGE = "accuracy_challenge", _("Accuracy Challenge")
    CUSTOM = "custom", _("Custom")  # If allowing user-defined challenges


class ChallengeStatus(models.TextChoices):
    PENDING_INVITE = "pending_invite", _(
        "Pending Invite"
    )  # Waiting for opponent acceptance
    PENDING_MATCHMAKING = "pending_matchmaking", _(
        "Pending Matchmaking"
    )  # Random opponent search
    ACCEPTED = "accepted", _(
        "Accepted / Waiting Start"
    )  # Invite accepted, not yet started by both
    ONGOING = "ongoing", _("Ongoing")  # Both participants are active
    COMPLETED = "completed", _("Completed")
    DECLINED = "declined", _("Declined")
    CANCELLED = "cancelled", _("Cancelled")  # e.g., by initiator before acceptance
    EXPIRED = "expired", _("Expired")  # e.g., invite not accepted in time


class Challenge(models.Model):
    """Represents a challenge initiated between users."""

    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # If challenger deleted, challenge is gone
        related_name="initiated_challenges",
        verbose_name=_("Challenger"),
        db_index=True,
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Keep challenge record if opponent deleted
        related_name="received_challenges",
        verbose_name=_("Opponent"),
        null=True,
        blank=True,  # Null for random matchmaking until found
        db_index=True,
    )
    challenge_type = models.CharField(
        _("challenge type"),
        max_length=30,
        choices=ChallengeType.choices,
        help_text=_("Identifier for the predefined type of challenge."),
    )
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=ChallengeStatus.choices,
        default=ChallengeStatus.PENDING_INVITE,  # Or PENDING_MATCHMAKING if random
        db_index=True,
    )
    # Stores details like sections, question count, time limit, hint rules, etc.
    challenge_config = models.JSONField(
        _("challenge configuration"),
        help_text=_("Specific parameters for this challenge instance."),
    )
    # List of question IDs included in *this specific* challenge instance
    question_ids = models.JSONField(
        _("question IDs"),
        default=list,
        help_text=_("Ordered list of question IDs included in this challenge."),
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Keep challenge record if winner deleted
        related_name="won_challenges",
        verbose_name=_("Winner"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True, db_index=True)
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)
    started_at = models.DateTimeField(
        _("started at"), null=True, blank=True
    )  # When both players are ready/active
    completed_at = models.DateTimeField(_("completed at"), null=True, blank=True)

    # Gamification related (denormalized for easier access in results)
    challenger_points_awarded = models.IntegerField(
        _("Challenger Points Awarded"), null=True, blank=True
    )
    opponent_points_awarded = models.IntegerField(
        _("Opponent Points Awarded"), null=True, blank=True
    )

    class Meta:
        verbose_name = _("Challenge")
        verbose_name_plural = _("Challenges")
        ordering = ["-created_at"]

    def __str__(self):
        opponent_username = (
            self.opponent.username if self.opponent else _("Random/Pending")
        )
        return f"Challenge {self.id}: {self.challenger.username} vs {opponent_username} ({self.get_status_display()})"

    @property
    def participants(self):
        """Returns a list of participant users."""
        parts = [self.challenger]
        if self.opponent:
            parts.append(self.opponent)
        return parts

    def is_participant(self, user: settings.AUTH_USER_MODEL) -> bool:
        """Checks if a given user is a participant in this challenge."""
        return user == self.challenger or user == self.opponent

    @property
    def num_questions(self) -> int:
        """Returns the number of questions included in this challenge."""
        return len(self.question_ids) if isinstance(self.question_ids, list) else 0

    def get_questions_queryset(self) -> models.QuerySet[Question]:
        """Returns an ordered queryset for the questions associated with this challenge."""
        if not self.question_ids or not isinstance(self.question_ids, list):
            return Question.objects.none()
        # Preserve order using CASE WHEN
        preserved_order = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(self.question_ids)],
            output_field=models.IntegerField(),
        )
        return Question.objects.filter(pk__in=self.question_ids).order_by(
            preserved_order
        )


class ChallengeAttempt(models.Model):
    """
    Links a specific user's participation and score within a single challenge instance.
    """

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,  # If Challenge deleted, attempt is irrelevant
        related_name="attempts",
        verbose_name=_("Challenge"),
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # If user deleted, their attempt is gone
        related_name="challenge_attempts",
        verbose_name=_("User"),
        db_index=True,
    )
    score = models.IntegerField(_("score"), default=0)  # Number of correct answers
    # Denormalize time for potential tie-breaking? Or calculate from UserQuestionAttempt?
    # total_time_seconds = models.PositiveIntegerField(_("Total Time (seconds)"), null=True, blank=True)
    is_ready = models.BooleanField(
        _("is ready"),
        default=False,
        help_text=_(
            "Indicates if the user has joined the challenge screen and is ready to start."
        ),
    )
    start_time = models.DateTimeField(
        _("user start time"), null=True, blank=True
    )  # When user started their part
    end_time = models.DateTimeField(
        _("user end time"), null=True, blank=True
    )  # When user finished their part
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    # Link UserQuestionAttempt back here
    question_attempts = models.ManyToManyField(
        UserQuestionAttempt,
        related_name="challenge_context",  # Avoid clash with UserQuestionAttempt.challenge_attempt FK
        blank=True,
        verbose_name=_("Question Attempts in this Challenge"),
    )

    class Meta:
        verbose_name = _("Challenge Attempt")
        verbose_name_plural = _("Challenge Attempts")
        ordering = ["challenge", "user"]
        unique_together = (
            "challenge",
            "user",
        )  # User can only have one attempt per challenge

    def __str__(self):
        return f"Attempt by {self.user.username} for Challenge {self.challenge_id} (Score: {self.score})"

    def calculate_score(self):
        """Recalculates the score based on linked correct question attempts."""
        correct_count = self.question_attempts.filter(is_correct=True).count()
        if self.score != correct_count:
            self.score = correct_count
            self.save(update_fields=["score", "updated_at"])
        return self.score
