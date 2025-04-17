# apps/study/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.learning.models import Question, LearningSection, LearningSubSection, Skill

import logging

logger = logging.getLogger(__name__)

# --- Test Attempt Models ---


class Test(models.Model):
    """
    Defines the structure or configuration of a reusable test or assessment type.
    """

    class TestType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Set")
        SIMULATION = "simulation", _("Full Simulation")
        CUSTOM = "custom", _("Custom User Test")

    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True, null=True)
    test_type = models.CharField(
        _("test type"),
        max_length=20,
        choices=TestType.choices,
        default=TestType.PRACTICE,
        db_index=True,
    )
    # If is_predefined is True, specific questions are linked via M2M.
    is_predefined = models.BooleanField(
        _("is predefined"),
        default=False,
        help_text=_(
            "If true, uses specific questions linked below. If false, uses configuration rules."
        ),
    )
    questions = models.ManyToManyField(
        Question,
        verbose_name=_("specific questions"),
        blank=True,
        related_name="predefined_tests",
        help_text=_("Specific questions included if 'is_predefined' is true."),
    )
    # If is_predefined is False, this stores rules for dynamic generation.
    configuration = models.JSONField(
        _("dynamic configuration"),
        blank=True,
        null=True,
        help_text=_(
            "Rules for dynamically generating a test (e.g., num questions per subsection/skill)."
        ),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Test Definition")
        verbose_name_plural = _("Test Definitions")
        ordering = ["name"]

    def __str__(self):
        return f"{self.get_test_type_display()} - {self.name}"


class UserTestAttempt(models.Model):
    """
    Records a user's session taking a specific test instance (e.g., one level assessment attempt).
    """

    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        verbose_name=_("user"),
        db_index=True,
    )
    # Link to a predefined Test structure, or null if fully dynamic/ad-hoc
    test = models.ForeignKey(
        Test,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
        verbose_name=_("test definition"),
    )
    # Snapshot of the configuration used for this specific instance,
    # especially if dynamically generated or based on user input.
    # Example: {"sections": ["verbal", "quantitative"], "num_questions": 30}
    # Example: {"subsections": [10, 11], "num_questions": 20, "starred": false}
    test_configuration = models.JSONField(
        _("test configuration snapshot"),
        blank=True,
        null=True,
        help_text=_("Configuration used for this specific test instance."),
    )
    # List of question IDs included in this specific attempt instance
    question_ids = models.JSONField(
        _("question IDs"),
        default=list,
        help_text=_("Ordered list of question IDs included in this attempt."),
    )
    status = models.CharField(
        _("status"),
        max_length=15,
        choices=Status.choices,
        default=Status.STARTED,
        db_index=True,
    )
    start_time = models.DateTimeField(_("start time"), auto_now_add=True, db_index=True)
    end_time = models.DateTimeField(_("end time"), null=True, blank=True)
    score_percentage = models.FloatField(
        _("overall score percentage"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    score_verbal = models.FloatField(
        _("verbal score percentage"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    score_quantitative = models.FloatField(
        _("quantitative score percentage"),
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    # Stores detailed breakdown, e.g., {"subsection_slug": {"correct": X, "total": Y, "score": Z}}
    results_summary = models.JSONField(_("results summary"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User Test Attempt")
        verbose_name_plural = _("User Test Attempts")
        ordering = ["-start_time"]

    def __str__(self):
        test_name = self.test.name if self.test else _("Ad-hoc Test")
        return f"{self.user.username} - {test_name} ({self.get_status_display()}) - {self.start_time.strftime('%Y-%m-%d')}"

    @property
    def duration_seconds(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def num_questions(self):
        return len(self.question_ids) if self.question_ids else 0

    def get_questions_queryset(self):
        """Returns a queryset for the questions associated with this attempt."""
        if not self.question_ids:
            return Question.objects.none()
        # Preserve order if possible (might not be guaranteed by DB depending on list size)
        # For strict ordering, fetch then sort in Python if needed
        return Question.objects.filter(pk__in=self.question_ids)


class UserQuestionAttempt(models.Model):
    """
    Records every instance a user attempts to answer a question, in various contexts.
    """

    class Mode(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditional Learning")
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        TEST = "test", _("Practice Test/Simulation")
        EMERGENCY = "emergency", _("Emergency Mode")
        CONVERSATION = "conversation", _("Learning via Conversation")
        CHALLENGE = "challenge", _("Challenge")

    class AnswerChoice(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("user"),
        db_index=True,
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,  # Or PROTECT if attempts should prevent question deletion
        related_name="user_attempts",
        verbose_name=_("question"),
        db_index=True,
    )
    # Link to the specific test session, if applicable
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,  # Attempt details are tied to the test session
        related_name="question_attempts",
        verbose_name=_("test attempt"),
        null=True,
        blank=True,
        db_index=True,
    )
    # --- Link to other potential contexts (Challenge, etc.) ---
    # challenge_attempt = models.ForeignKey(
    #     'challenges.ChallengeAttempt', # Use string for forward reference if needed
    #     on_delete=models.CASCADE,
    #     related_name='question_attempts',
    #     verbose_name=_("challenge attempt"),
    #     null=True, blank=True, db_index=True
    # )
    # ---

    selected_answer = models.CharField(
        _("selected answer"),
        max_length=1,
        choices=AnswerChoice.choices,
        # Should not be required if user abandons before answering
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"), null=True, blank=True
    )  # Null until graded
    time_taken_seconds = models.PositiveIntegerField(
        _("time taken (seconds)"),
        null=True,
        blank=True,
        help_text=_("Time spent specifically on this question."),
    )
    used_hint = models.BooleanField(_("used hint"), default=False)
    used_elimination = models.BooleanField(_("used elimination"), default=False)
    used_solution_method = models.BooleanField(_("used solution method"), default=False)
    mode = models.CharField(
        _("mode"),
        max_length=20,
        choices=Mode.choices,
        db_index=True,
        help_text=_("The context in which the question was attempted."),
    )
    attempted_at = models.DateTimeField(
        _("attempted at"), auto_now_add=True, db_index=True
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        # Ensure a user doesn't accidentally submit multiple answers for the
        # same question within the *same test attempt*
        unique_together = [["user", "question", "test_attempt"]]

    def __str__(self):
        return f"{self.user.username} - Q:{self.question_id} ({self.get_mode_display()}) @ {self.attempted_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # Automatically determine mode from test_attempt if not set explicitly
        if self.test_attempt and not self.mode:
            if self.test_attempt.test:
                if self.test_attempt.test.test_type == Test.TestType.LEVEL_ASSESSMENT:
                    self.mode = self.Mode.LEVEL_ASSESSMENT
                else:
                    self.mode = self.Mode.TEST  # Default for other test types
            else:
                # If no test definition, assume ad-hoc test/practice
                self.mode = self.Mode.TEST

        # Auto-calculate is_correct if selected_answer is provided
        if self.selected_answer and self.is_correct is None:
            try:
                self.is_correct = self.selected_answer == self.question.correct_answer
            except Question.DoesNotExist:
                # Handle case where question might have been deleted between attempt and save
                logger.warning(
                    f"Question ID {self.question_id} not found during UserQuestionAttempt save for user {self.user_id}."
                )
                self.is_correct = None  # Or handle as error

        super().save(*args, **kwargs)


# Add other study-related models here later (EmergencyModeSession, ConversationSession, etc.)
