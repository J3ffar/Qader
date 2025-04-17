from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

# Removed unused GenericForeignKey imports for now
# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from django.utils import timezone  # Import timezone

from apps.learning.models import Question, LearningSection, LearningSubSection, Skill

import logging

logger = logging.getLogger(__name__)

# --- Test Definition Model ---


class Test(models.Model):
    """
    Defines the structure or configuration of a reusable test or assessment type.
    (e.g., a predefined Level Assessment template, specific practice sets).
    """

    class TestType(models.TextChoices):
        # Renamed for clarity based on usage context
        LEVEL_ASSESSMENT_TEMPLATE = "level_assessment_template", _(
            "Level Assessment Template"
        )
        PRACTICE_SET = "practice_set", _("Practice Set")
        SIMULATION = "simulation", _("Full Simulation")
        # Removed CUSTOM as UserTestAttempt handles custom configurations directly

    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True, null=True)
    test_type = models.CharField(
        _("test definition type"),  # Clarified field name
        max_length=30,  # Increased length for new choice
        choices=TestType.choices,
        default=TestType.PRACTICE_SET,
        db_index=True,
    )
    # If is_predefined is True, specific questions are linked via M2M.
    is_predefined = models.BooleanField(
        _("is predefined"),
        default=False,
        help_text=_(
            "If true, uses specific questions linked below. If false, relies on configuration rules."
        ),
    )
    questions = models.ManyToManyField(
        Question,
        verbose_name=_("specific questions"),
        blank=True,
        related_name="predefined_tests",
        help_text=_("Specific questions included if 'is_predefined' is true."),
    )
    # If is_predefined is False, this stores rules for dynamic generation based on this template.
    configuration = models.JSONField(
        _("dynamic configuration template"),  # Clarified field name
        blank=True,
        null=True,
        help_text=_(
            "Template rules (e.g., num questions per subsection/skill) if not predefined."
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


# --- User Attempt Models ---


class UserTestAttempt(models.Model):
    """
    Records a user's session taking a specific test instance (e.g., one level assessment).
    This instance can be based on a predefined Test or generated dynamically.
    """

    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")

    # Added TestType specifically for the *attempt* instance
    class AttemptType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Test")
        SIMULATION = "simulation", _("Full Simulation")
        # Removed CUSTOM - configuration dictates custom nature

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        verbose_name=_("user"),
        db_index=True,
    )
    # Link to a predefined Test structure, if this attempt was based on one.
    test_definition = models.ForeignKey(
        Test,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
        verbose_name=_("test definition used"),  # Renamed for clarity
        help_text=_("The predefined Test template used for this attempt, if any."),
    )
    # NEW FIELD: Explicitly store the type of this specific attempt
    attempt_type = models.CharField(
        _("attempt type"),
        max_length=20,
        choices=AttemptType.choices,
        db_index=True,
        help_text=_("The specific type of this test attempt instance."),
    )
    # Snapshot of the configuration used for this specific instance.
    # Critical for dynamically generated tests or overrides.
    # Example: {"sections": ["verbal", "quantitative"], "num_questions": 30}
    # Example: {"subsections": [10, 11], "num_questions": 20, "starred": false}
    test_configuration = models.JSONField(
        _("test configuration snapshot"),
        blank=True,
        null=True,
        help_text=_(
            "Configuration used for this specific test instance (dynamic or custom)."
        ),
    )
    # List of question IDs included in *this specific* attempt instance
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
        attempt_label = self.get_attempt_type_display()
        return f"{self.user.username} - {attempt_label} ({self.get_status_display()}) - {self.start_time.strftime('%Y-%m-%d')}"

    @property
    def duration_seconds(self):
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def num_questions(self):
        return len(self.question_ids) if isinstance(self.question_ids, list) else 0

    def get_questions_queryset(self):
        """Returns a queryset for the questions associated with this attempt."""
        if not self.question_ids or not isinstance(self.question_ids, list):
            return Question.objects.none()
        # Preserve order using a CASE WHEN structure (more robust than relying on IN clause order)
        preserved_order = models.Case(
            *[models.When(pk=pk, then=pos) for pos, pk in enumerate(self.question_ids)],
            output_field=models.IntegerField(),
        )
        return Question.objects.filter(pk__in=self.question_ids).order_by(
            preserved_order
        )


class UserQuestionAttempt(models.Model):
    """
    Records every instance a user attempts to answer a question, in various contexts.
    """

    class Mode(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditional Learning")
        LEVEL_ASSESSMENT = "level_assessment", _(
            "Level Assessment"
        )  # Tied to UserTestAttempt.AttemptType
        TEST = "test", _(
            "Practice Test/Simulation"
        )  # Tied to UserTestAttempt.AttemptType
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
        on_delete=models.CASCADE,  # If question deleted, attempt is less meaningful
        related_name="user_attempts",
        verbose_name=_("question"),
        db_index=True,
    )
    # Link to the specific test session, if applicable
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,  # Attempt details are tied to the test session
        related_name="question_attempts",
        verbose_name=_("test attempt session"),  # Clarified name
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
        null=True,  # Allow null if abandoned before selecting
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"), null=True, blank=True
    )  # Null until graded or if abandoned
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
        _("attempted at"),
        default=timezone.now,
        db_index=True,  # Use default=timezone.now
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        # Ensure a user doesn't accidentally submit multiple answers for the
        # same question within the *same test attempt*. Null test_attempt means not part of a test.
        unique_together = [["user", "question", "test_attempt"]]

    def __str__(self):
        return f"{self.user.username} - Q:{self.question_id} ({self.get_mode_display()}) @ {self.attempted_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # Determine mode from test_attempt if not set AND test_attempt exists
        if self.test_attempt and not self.mode:
            # Map UserTestAttempt.AttemptType to UserQuestionAttempt.Mode
            if (
                self.test_attempt.attempt_type
                == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            ):
                self.mode = self.Mode.LEVEL_ASSESSMENT
            elif self.test_attempt.attempt_type in [
                UserTestAttempt.AttemptType.PRACTICE,
                UserTestAttempt.AttemptType.SIMULATION,
            ]:
                self.mode = self.Mode.TEST
            else:
                # Fallback or handle unexpected attempt types
                logger.warning(
                    f"Unhandled UserTestAttempt type '{self.test_attempt.attempt_type}' for UserQuestionAttempt {self.id}"
                )
                # Decide on a default or leave blank if mode MUST be set externally for other types
                pass  # Or set a default like self.mode = self.Mode.TEST

        # Auto-calculate is_correct if selected_answer is provided and question is loaded
        # Avoids calculating if it's already set (e.g., during bulk operations)
        if self.selected_answer and self.is_correct is None:
            try:
                # Ensure question is accessed correctly (it should be linked)
                if self.question_id:  # Check if FK is set
                    # Efficiently check correctness without loading full question object if possible
                    # This requires the question object or at least its correct_answer
                    # If self.question is already loaded, use it.
                    # If not, this access will trigger a query.
                    correct_ans = self.question.correct_answer
                    self.is_correct = self.selected_answer == correct_ans
                else:
                    logger.error(
                        f"Cannot calculate correctness for UserQuestionAttempt {self.id}: question_id is not set."
                    )
                    self.is_correct = None
            except Question.DoesNotExist:
                logger.warning(
                    f"Question ID {self.question_id} not found during UserQuestionAttempt save for user {self.user_id}."
                )
                self.is_correct = None  # Or handle as error

        super().save(*args, **kwargs)


class UserSkillProficiency(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_proficiencies",
    )
    skill = models.ForeignKey("learning.Skill", on_delete=models.CASCADE)
    proficiency_score = models.FloatField(
        default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    attempts_count = models.IntegerField(default=0)
    correct_count = models.IntegerField(default=0)
    last_calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["user", "skill"]]
        verbose_name = _("User Skill Proficiency")
        verbose_name_plural = _("User Skill Proficiencies")

    def update_proficiency(self, is_correct):
        self.attempts_count += 1
        if is_correct:
            self.correct_count += 1
        # Simple moving average or more complex algorithm
        # Example: Basic accuracy
        if self.attempts_count > 0:
            self.proficiency_score = self.correct_count / self.attempts_count
        else:
            self.proficiency_score = 0.0
        self.save()


# --- Other Study Models (Placeholders) ---

# class EmergencyModeSession(models.Model):
#     # ... fields ...
#     pass

# class ConversationSession(models.Model):
#     # ... fields ...
#     pass
