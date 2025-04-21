from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import F, Case, When, IntegerField, QuerySet
import logging
from typing import List, Optional, Dict, Any

# Assuming learning models are correctly imported
from apps.learning.models import Question, LearningSection, LearningSubSection, Skill

logger = logging.getLogger(__name__)

# --- Test Definition Model ---


class Test(models.Model):
    """
    Defines the structure or configuration of a reusable test template or assessment type.
    Examples: Level Assessment Template, Standard Practice Set X, Full Simulation Mock 1.
    """

    class TestType(models.TextChoices):
        LEVEL_ASSESSMENT_TEMPLATE = "level_assessment_template", _(
            "Level Assessment Template"
        )
        PRACTICE_SET = "practice_set", _("Practice Set")
        SIMULATION = "simulation", _("Full Simulation")

    name = models.CharField(_("name"), max_length=255, unique=True)
    description = models.TextField(_("description"), blank=True, null=True)
    test_type = models.CharField(
        _("test definition type"),
        max_length=30,
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
    # If is_predefined is False, this stores rules for dynamic generation *based* on this template.
    configuration = models.JSONField(
        _("dynamic configuration template"),
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
    This instance can be based on a predefined Test definition or generated dynamically.
    """

    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")

    # Added AttemptType specifically for the *attempt* instance
    class AttemptType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Test")
        SIMULATION = "simulation", _("Full Simulation")
        # 'CUSTOM' type isn't needed here; the configuration details its nature.

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
        verbose_name=_("test definition used"),
        help_text=_("The predefined Test template used for this attempt, if any."),
    )
    # Explicitly store the type of this specific attempt instance
    attempt_type = models.CharField(
        _("attempt type"),
        max_length=20,
        choices=AttemptType.choices,
        db_index=True,
        help_text=_("The specific type of this test attempt instance."),
    )
    # Snapshot of the configuration used for this specific instance.
    # Critical for dynamically generated tests or specific overrides.
    test_configuration = models.JSONField(
        _("test configuration snapshot"),
        blank=True,
        null=True,
        help_text=_(
            "Configuration used for this specific test instance (dynamic or custom). Includes criteria like sections, skills, starred, not_mastered, num_questions, etc."
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
    # Stores detailed breakdown, e.g., {"subsection_slug": {"correct": X, "total": Y, "score": Z, "name": "Sub Name"}}
    results_summary = models.JSONField(_("results summary"), null=True, blank=True)
    completion_points_awarded = models.BooleanField(
        _("completion points awarded"),
        default=False,
        help_text=_("Indicates if points for completing this test have been awarded."),
    )
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
    def duration_seconds(self) -> Optional[float]:
        """Calculates the duration of the attempt in seconds, if completed."""
        if self.end_time and self.start_time and self.status == self.Status.COMPLETED:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def num_questions(self) -> int:
        """Returns the number of questions included in this attempt."""
        return len(self.question_ids) if isinstance(self.question_ids, list) else 0

    def get_questions_queryset(self) -> QuerySet[Question]:
        """Returns an ordered queryset for the questions associated with this attempt."""
        if not self.question_ids or not isinstance(self.question_ids, list):
            return Question.objects.none()
        # Preserve order using a CASE WHEN structure (more robust than relying on IN clause order)
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(self.question_ids)],
            output_field=IntegerField(),
        )
        # Eager load related fields likely needed when processing questions
        return (
            Question.objects.filter(pk__in=self.question_ids)
            .select_related("subsection", "subsection__section", "skill")
            .order_by(preserved_order)
        )

    def calculate_and_save_scores(self, question_attempts: List["UserQuestionAttempt"]):
        """
        Calculates scores based on provided question attempts and updates the UserTestAttempt instance.
        Assumes question attempts belong to this UserTestAttempt.
        """
        total_questions = len(question_attempts)
        if total_questions == 0:
            self.score_percentage = 0.0
            self.score_verbal = None
            self.score_quantitative = None
            self.results_summary = {}
            self.save(
                update_fields=[
                    "score_percentage",
                    "score_verbal",
                    "score_quantitative",
                    "results_summary",
                    "updated_at",
                ]
            )
            return

        correct_answers = sum(1 for attempt in question_attempts if attempt.is_correct)
        overall_score = round((correct_answers / total_questions * 100), 1)

        verbal_correct, verbal_total, quant_correct, quant_total = 0, 0, 0, 0
        results_summary_calc = {}

        for attempt in question_attempts:
            question = (
                attempt.question
            )  # Assume question is loaded via FK or select_related
            subsection = question.subsection
            if not subsection:
                continue
            section = subsection.section
            if not section:
                continue

            section_slug = section.slug
            subsection_slug = subsection.slug

            if subsection_slug not in results_summary_calc:
                results_summary_calc[subsection_slug] = {
                    "correct": 0,
                    "total": 0,
                    "name": subsection.name,
                }

            results_summary_calc[subsection_slug]["total"] += 1
            is_section_verbal = section_slug == "verbal"
            is_section_quant = section_slug == "quantitative"

            if is_section_verbal:
                verbal_total += 1
            if is_section_quant:
                quant_total += 1

            if attempt.is_correct:
                results_summary_calc[subsection_slug]["correct"] += 1
                if is_section_verbal:
                    verbal_correct += 1
                if is_section_quant:
                    quant_correct += 1

        # Calculate final scores within the results_summary dict
        for slug, data in results_summary_calc.items():
            data["score"] = (
                round((data["correct"] / data["total"] * 100), 1)
                if data["total"] > 0
                else 0.0
            )

        verbal_score = (
            round((verbal_correct / verbal_total * 100), 1)
            if verbal_total > 0
            else None
        )
        quantitative_score = (
            round((quant_correct / quant_total * 100), 1) if quant_total > 0 else None
        )

        # --- Update Self ---
        self.score_percentage = overall_score
        self.score_verbal = verbal_score
        self.score_quantitative = quantitative_score
        self.results_summary = results_summary_calc
        self.save(
            update_fields=[
                "score_percentage",
                "score_verbal",
                "score_quantitative",
                "results_summary",
                "updated_at",
            ]
        )
        logger.info(f"Scores calculated and saved for UserTestAttempt {self.id}.")


class UserQuestionAttempt(models.Model):
    """
    Records every instance a user attempts to answer a question, in various contexts.
    """

    class Mode(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditional Learning")
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        TEST = "test", _(
            "Practice Test/Simulation"
        )  # Generic type covering practice/simulation
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
        verbose_name=_("test attempt session"),
        null=True,
        blank=True,
        db_index=True,
    )
    conversation_session = models.ForeignKey(
        "ConversationSession",  # Use string quote if defined later
        on_delete=models.SET_NULL,  # Or CASCADE if appropriate
        related_name="question_attempts",
        verbose_name=_("conversation session"),
        null=True,
        blank=True,
        db_index=True,
    )
    # --- Link to other contexts ---
    # challenge_attempt = models.ForeignKey(
    #     'challenges.ChallengeAttempt', # Use string for forward reference
    #     on_delete=models.CASCADE,
    #     related_name='question_attempts',
    #     verbose_name=_("challenge attempt"),
    #     null=True, blank=True, db_index=True
    # )
    # emergency_session = models.ForeignKey(...)
    # ---
    selected_answer = models.CharField(
        _("selected answer"),
        max_length=1,
        choices=AnswerChoice.choices,
        null=True,  # Allow null if abandoned before selecting
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"),
        null=True,  # Null until graded or if abandoned
        blank=True,
        db_index=True,  # Index for faster filtering on correctness
    )
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
        default=timezone.now,  # Use default=timezone.now for flexibility
        db_index=True,
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        # Ensure a user doesn't accidentally submit multiple answers for the
        # same question within the *same test attempt*. Null test_attempt means not part of a test.
        # We only enforce this if test_attempt is not NULL.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question", "test_attempt"],
                condition=models.Q(test_attempt__isnull=False),
                name="unique_user_question_per_test_attempt",
            )
            # Add constraints for other contexts (challenge_attempt etc.) if needed
        ]

    def __str__(self):
        return f"{self.user.username} - Q:{self.question_id} ({self.get_mode_display()}) @ {self.attempted_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # --- Determine Mode if linked to TestAttempt ---
        if self.test_attempt and not self.mode:
            mode_map = {
                UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: self.Mode.LEVEL_ASSESSMENT,
                UserTestAttempt.AttemptType.PRACTICE: self.Mode.TEST,
                UserTestAttempt.AttemptType.SIMULATION: self.Mode.TEST,
            }
            self.mode = mode_map.get(
                self.test_attempt.attempt_type, self.Mode.TEST
            )  # Default to TEST

        # --- Auto-calculate is_correct if possible ---
        # Calculate only if selected_answer is provided AND is_correct is currently None
        if self.selected_answer and self.is_correct is None:
            try:
                # Accessing self.question might trigger a query if not preloaded.
                correct_ans = self.question.correct_answer
                self.is_correct = self.selected_answer == correct_ans
            except Question.DoesNotExist:
                logger.warning(
                    f"Question {self.question_id} not found during UserQuestionAttempt save for user {self.user_id}."
                )
                self.is_correct = None  # Cannot determine correctness
            except AttributeError:
                # Handle case where self.question might be None (e.g., if FK was somehow cleared before save)
                logger.error(
                    f"Question object not available for UserQuestionAttempt with question_id {self.question_id} during save."
                )
                self.is_correct = None

        super().save(*args, **kwargs)


class UserSkillProficiency(models.Model):
    """Stores calculated proficiency score for a user on a specific skill."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_proficiencies",
        db_index=True,  # Index user for faster lookups
    )
    skill = models.ForeignKey(
        "learning.Skill",
        on_delete=models.CASCADE,
        related_name="user_proficiencies",
        db_index=True,  # Index skill
    )
    # Store score between 0.0 and 1.0 (representing 0% to 100%)
    proficiency_score = models.FloatField(
        _("Proficiency Score"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_("Calculated score representing user mastery (0.0 to 1.0)."),
    )
    attempts_count = models.PositiveIntegerField(_("Attempts Count"), default=0)
    correct_count = models.PositiveIntegerField(_("Correct Count"), default=0)
    last_calculated_at = models.DateTimeField(_("Last Calculated At"), auto_now=True)

    class Meta:
        unique_together = [["user", "skill"]]
        verbose_name = _("User Skill Proficiency")
        verbose_name_plural = _("User Skill Proficiencies")
        ordering = ["user", "skill"]

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}: {self.proficiency_score:.2f}"

    def record_attempt(self, is_correct: bool):
        """
        Updates proficiency based on a single question attempt result.
        Uses F() expressions for atomic updates.
        """
        self.attempts_count = F("attempts_count") + 1
        if is_correct:
            self.correct_count = F("correct_count") + 1

        # Save atomic updates first
        self.save(
            update_fields=["attempts_count", "correct_count", "last_calculated_at"]
        )
        # Refresh object to get the actual updated values from the database
        self.refresh_from_db(fields=["attempts_count", "correct_count"])

        # Now calculate and save the new score based on refreshed values
        if self.attempts_count > 0:
            new_score = round(
                self.correct_count / self.attempts_count, 4
            )  # Use round for precision
        else:
            new_score = 0.0

        # Only save if the score actually changed to avoid unnecessary updates
        if self.proficiency_score != new_score:
            self.proficiency_score = new_score
            self.save(update_fields=["proficiency_score"])


class EmergencyModeSession(models.Model):
    """
    Records details when a user enters "Emergency Mode".
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_sessions",
        verbose_name=_("user"),
        db_index=True,
    )
    reason = models.TextField(_("reason"), blank=True, null=True)
    # Stores the plan details: {"focus_skills": ["slug1", "slug2"], "recommended_questions": N, "quick_review_topics": ["topic1", ...]}
    suggested_plan = models.JSONField(_("suggested plan"), null=True, blank=True)
    calm_mode_active = models.BooleanField(_("calm mode active"), default=False)
    start_time = models.DateTimeField(_("start time"), auto_now_add=True, db_index=True)
    end_time = models.DateTimeField(_("end time"), null=True, blank=True)
    shared_with_admin = models.BooleanField(_("shared with admin"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Emergency Mode Session")
        verbose_name_plural = _("Emergency Mode Sessions")
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.user.username} - Emergency Session @ {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_ended(self):
        """Sets the end time for the session."""
        if not self.end_time:
            self.end_time = timezone.now()
            self.save(update_fields=["end_time", "updated_at"])


class ConversationSession(models.Model):
    """Records details of a 'Learning via Conversation' session."""

    class AiTone(models.TextChoices):
        CHEERFUL = "cheerful", _("Cheerful")
        SERIOUS = "serious", _("Serious")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversation_sessions",
        verbose_name=_("user"),
        db_index=True,
    )
    ai_tone = models.CharField(
        _("AI tone"),
        max_length=10,
        choices=AiTone.choices,
        default=AiTone.SERIOUS,
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    # Tracks the main question/concept being discussed for "Got it" testing
    current_topic_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed from Question
        verbose_name=_("current topic question"),
    )
    start_time = models.DateTimeField(_("start time"), auto_now_add=True)
    end_time = models.DateTimeField(_("end time"), null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Conversation Session")
        verbose_name_plural = _("Conversation Sessions")
        ordering = ["-start_time"]

    def __str__(self):
        return f"Conversation for {self.user.username} ({self.get_status_display()}) started {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def end_session(self):
        """Marks the session as completed."""
        if self.status == self.Status.ACTIVE:
            self.status = self.Status.COMPLETED
            self.end_time = timezone.now()
            self.save(update_fields=["status", "end_time", "updated_at"])


class ConversationMessage(models.Model):
    """Stores a single message within a conversation session."""

    class SenderType(models.TextChoices):
        USER = "user", _("User")
        AI = "ai", _("AI")

    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("session"),
        db_index=True,
    )
    sender_type = models.CharField(
        _("sender type"),
        max_length=4,
        choices=SenderType.choices,
        db_index=True,
    )
    message_text = models.TextField(_("message text"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True, db_index=True)
    # Optional: Link message to a specific question if relevant
    related_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed
        verbose_name=_("related question"),
    )

    class Meta:
        verbose_name = _("Conversation Message")
        verbose_name_plural = _("Conversation Messages")
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.get_sender_type_display()} in session {self.session_id} @ {self.timestamp.strftime('%H:%M:%S')}"


# --- Other Study Models (Placeholders) ---
