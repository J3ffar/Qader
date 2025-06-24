import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.study.models import Question, UserQuestionAttempt
from apps.api.common.models import BaseModel

logger = logging.getLogger(__name__)


class ChallengeType(models.TextChoices):
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


# --- Custom Manager ---
class ChallengeManager(models.Manager):
    """Custom manager for the Challenge model."""

    def get_for_user(self, user):
        """
        Returns a queryset of challenges where the given user is a participant.
        This includes all necessary prefetching for performance.
        """
        if not user.is_authenticated:
            return self.none()

        return (
            self.get_queryset()
            .filter(models.Q(challenger=user) | models.Q(opponent=user))
            .select_related(
                "challenger__profile", "opponent__profile", "winner__profile"
            )
            .prefetch_related(
                "attempts__user__profile"
            )  # Crucial for serializer performance
            .distinct()
        )


# --- Models ---
class Challenge(BaseModel):
    """Represents a challenge initiated between users."""

    objects = ChallengeManager()  # Assign custom manager

    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="initiated_challenges",
        verbose_name=_("Challenger"),
        db_index=True,
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="received_challenges",
        verbose_name=_("Opponent"),
        null=True,
        blank=True,
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
        default=ChallengeStatus.PENDING_INVITE,
        db_index=True,
    )
    challenge_config = models.JSONField(
        _("challenge configuration"),
        help_text=_("Specific parameters for this challenge instance."),
    )
    question_ids = models.JSONField(
        _("question IDs"),
        default=list,
        help_text=_("Ordered list of question IDs included in this challenge."),
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="won_challenges",
        verbose_name=_("Winner"),
        null=True,
        blank=True,
    )
    accepted_at = models.DateTimeField(_("accepted at"), null=True, blank=True)
    started_at = models.DateTimeField(_("started at"), null=True, blank=True)
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

    def clean(self):
        """Model-level validation."""
        super().clean()
        if self.challenger and self.opponent and self.challenger == self.opponent:
            raise ValidationError(
                _("Challenger and opponent cannot be the same person.")
            )

    @property
    def participants(self):
        """Returns a list of participant users, filtering out None."""
        return list(filter(None, [self.challenger, self.opponent]))

    def is_participant(self, user: settings.AUTH_USER_MODEL) -> bool:
        """Checks if a given user is a participant in this challenge."""
        return user in self.participants

    @property
    def num_questions(self) -> int:
        """Returns the number of questions included in this challenge."""
        return len(self.question_ids) if isinstance(self.question_ids, list) else 0

    def get_questions_queryset(self) -> models.QuerySet[Question]:
        """Returns an ordered queryset for the questions associated with this challenge."""
        if not self.num_questions:
            return Question.objects.none()

        preserved_order = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(self.question_ids)],
            output_field=models.IntegerField(),
        )
        return Question.objects.filter(pk__in=self.question_ids).order_by(
            preserved_order
        )


class ChallengeAttempt(BaseModel):
    """Links a user's participation and score within a single challenge instance."""

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("Challenge"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="challenge_attempts",
        verbose_name=_("User"),
    )
    score = models.IntegerField(_("score"), default=0)
    is_ready = models.BooleanField(
        _("is ready"),
        default=False,
        help_text=_("Indicates if the user is ready to start."),
    )
    start_time = models.DateTimeField(_("user start time"), null=True, blank=True)
    end_time = models.DateTimeField(_("user end time"), null=True, blank=True)
    question_attempts = models.ManyToManyField(
        UserQuestionAttempt,
        related_name="challenge_context",
        blank=True,
        verbose_name=_("Question Attempts"),
    )
    # created_at and updated_at are inherited from BaseModel

    class Meta:
        verbose_name = _("Challenge Attempt")
        verbose_name_plural = _("Challenge Attempts")
        ordering = ["challenge", "user"]
        unique_together = (
            "challenge",
            "user",
        )
        indexes = [
            models.Index(fields=["challenge", "user"]),
        ]

    def __str__(self):
        return f"Attempt by {self.user.username} for Challenge {self.challenge_id} (Score: {self.score})"

    def calculate_and_update_score(self):
        """
        Recalculates the score based on linked question attempts and saves the model.
        This should be called from a service layer function within a transaction.
        """
        correct_count = self.question_attempts.filter(is_correct=True).count()
        if self.score != correct_count:
            self.score = correct_count
            self.save(update_fields=["score", "updated_at"])
        return self.score
