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
    is_predefined = models.BooleanField(
        _("is predefined"),
        default=False,
        help_text=_(
            "If true, this definition uses the specific questions linked below. If false, it acts as a template and relies on 'configuration'."
        ),
    )
    questions = models.ManyToManyField(
        Question,
        verbose_name=_("specific questions"),
        blank=True,
        related_name="predefined_tests",
        help_text=_("Specific questions included if 'is_predefined' is true."),
    )
    configuration = models.JSONField(
        _("dynamic configuration template"),
        blank=True,
        null=True,
        help_text=_(
            "JSON defining rules (e.g., {'num_questions_per_skill': {...}, 'total_questions': N}) for dynamically generating tests based on this template if 'is_predefined' is false."
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
    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")

    class AttemptType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Test")
        SIMULATION = "simulation", _("Full Simulation")
        # Add other types if needed (e.g., CHALLENGE_TEST)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        verbose_name=_("user"),
        db_index=True,
    )
    test_definition = models.ForeignKey(
        Test,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attempts",
        verbose_name=_("test definition used"),
        help_text=_("The predefined Test template used for this attempt, if any."),
    )
    attempt_type = models.CharField(
        _("attempt type"),
        max_length=20,
        choices=AttemptType.choices,
        db_index=True,
        help_text=_("The specific type of this test attempt instance."),
    )
    # Enhanced help_text for test_configuration
    test_configuration = models.JSONField(
        _("test configuration snapshot"),
        blank=True,
        null=True,
        help_text=_(
            "Actual configuration used for this specific instance (especially if dynamic/custom). Includes criteria like sections, skills, starred, not_mastered, num_questions, etc. Ensure consistent structure."
        ),
    )
    question_ids = models.JSONField(
        _("question IDs"),
        default=list,
        help_text=_("Ordered list of question primary keys included in this attempt."),
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
    results_summary = models.JSONField(
        _("results summary"),
        null=True,
        blank=True,
        help_text=_(
            'Detailed breakdown, e.g., {"subsection_slug": {"correct": X, "total": Y, "score": Z, "name": "Sub Name"}}'
        ),
    )
    completion_points_awarded = models.BooleanField(
        _("completion points awarded"),
        default=False,
        help_text=_(
            "Tracks if gamification points for completing this test have been awarded (managed by signals/tasks)."
        ),
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
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(self.question_ids)],
            output_field=IntegerField(),
        )
        # Eager load common related fields
        return (
            Question.objects.filter(pk__in=self.question_ids)
            .select_related("subsection", "subsection__section", "skill")
            .order_by(preserved_order)
        )

    def calculate_and_save_scores(self, question_attempts: List["UserQuestionAttempt"]):
        """
        Calculates scores based on provided question attempts and updates the instance.
        Assumes attempts belong to this instance and have related question/subsection/section loaded.
        """
        total_questions = len(question_attempts)
        if total_questions == 0:
            logger.warning(
                f"No question attempts provided for scoring UserTestAttempt {self.id}."
            )
            self.score_percentage = 0.0
            self.score_verbal = None
            self.score_quantitative = None
            self.results_summary = {}
        else:
            correct_answers = sum(
                1 for attempt in question_attempts if attempt.is_correct
            )
            overall_score = round((correct_answers / total_questions * 100), 1)

            verbal_correct, verbal_total, quant_correct, quant_total = 0, 0, 0, 0
            results_summary_calc = {}

            for attempt in question_attempts:
                # Ensure related objects are loaded for efficiency (should be done by caller)
                question = attempt.question
                subsection = question.subsection
                if not subsection:
                    logger.warning(
                        f"Question {question.id} in attempt {self.id} missing subsection."
                    )
                    continue
                section = subsection.section
                if not section:
                    logger.warning(
                        f"Subsection {subsection.id} in attempt {self.id} missing section."
                    )
                    continue

                section_slug = section.slug
                subsection_slug = subsection.slug

                if subsection_slug not in results_summary_calc:
                    results_summary_calc[subsection_slug] = {
                        "correct": 0,
                        "total": 0,
                        "name": subsection.name,  # Store name for readability
                        "score": 0.0,  # Initialize score
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
                round((quant_correct / quant_total * 100), 1)
                if quant_total > 0
                else None
            )

            # Update fields
            self.score_percentage = overall_score
            self.score_verbal = verbal_score
            self.score_quantitative = quantitative_score
            self.results_summary = results_summary_calc

        # Save updated fields
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
    """Records every instance a user attempts a question, tracking context and outcome."""

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
        on_delete=models.CASCADE,  # If question is deleted, attempt is invalid
        related_name="user_attempts",
        verbose_name=_("question"),
        db_index=True,
    )
    # --- Context Links (Nullable ForeignKeys) ---
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,  # Attempts are part of the test attempt
        related_name="question_attempts",
        verbose_name=_("test attempt session"),
        null=True,
        blank=True,
        db_index=True,
    )
    conversation_session = models.ForeignKey(
        "ConversationSession",
        on_delete=models.CASCADE,  # Link attempts to the conversation
        related_name="question_attempts",
        verbose_name=_("conversation session"),
        null=True,
        blank=True,
        db_index=True,
    )
    challenge_attempt = models.ForeignKey(
        "challenges.ChallengeAttempt",
        on_delete=models.CASCADE,
        related_name="user_question_attempts_in_challenge",
        verbose_name=_("challenge participation"),
        null=True,
        blank=True,
        db_index=True,
    )
    emergency_session = models.ForeignKey(
        "EmergencyModeSession",
        on_delete=models.SET_NULL,  # Keep attempt record even if session deleted
        related_name="question_attempts",
        verbose_name=_("emergency mode session"),
        null=True,
        blank=True,
        db_index=True,
    )
    # --- Attempt Details ---
    selected_answer = models.CharField(
        _("selected answer"),
        max_length=1,
        choices=AnswerChoice.choices,
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"),
        null=True,  # Calculated on save or can be null if not answered
        blank=True,
        db_index=True,
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
        help_text=_("The context (feature) in which the question was attempted."),
    )
    attempted_at = models.DateTimeField(
        _("attempted at"),
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question", "test_attempt"],
                condition=models.Q(test_attempt__isnull=False),
                name="unique_user_question_per_test_attempt",
            ),
            models.UniqueConstraint(
                fields=["user", "question", "challenge_attempt"],
                condition=models.Q(challenge_attempt__isnull=False),
                name="unique_user_question_per_challenge_attempt",
            ),
            # Add more constraints if needed (e.g., unique per conversation session?)
        ]

    def __str__(self):
        return f"{self.user.username} - Q:{self.question_id} ({self.get_mode_display()}) @ {self.attempted_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # --- Auto-set mode based on context FKs if not explicitly set ---
        if not self.mode:
            if self.test_attempt:
                mode_map = {
                    UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: self.Mode.LEVEL_ASSESSMENT,
                    UserTestAttempt.AttemptType.PRACTICE: self.Mode.TEST,
                    UserTestAttempt.AttemptType.SIMULATION: self.Mode.TEST,
                }
                self.mode = mode_map.get(self.test_attempt.attempt_type, self.Mode.TEST)
            elif self.challenge_attempt:
                self.mode = self.Mode.CHALLENGE
            elif self.emergency_session:
                self.mode = self.Mode.EMERGENCY
            elif self.conversation_session:
                self.mode = self.Mode.CONVERSATION
            # Add default or raise error if mode cannot be determined?
            # else: self.mode = self.Mode.TRADITIONAL # Or raise error

        # --- Auto-calculate is_correct if answer selected and correctness not set ---
        if self.selected_answer and self.is_correct is None:
            try:
                # Ensure question is loaded efficiently if possible
                correct_ans = self.question.correct_answer
                self.is_correct = self.selected_answer == correct_ans
            except Question.DoesNotExist:
                logger.warning(
                    f"Question {self.question_id} not found during UserQuestionAttempt save for user {self.user_id}."
                )
                self.is_correct = None
            except AttributeError:
                logger.error(
                    f"Question object or correct_answer not available for UserQuestionAttempt with question_id {self.question_id} during save."
                )
                self.is_correct = None

        super().save(*args, **kwargs)


class UserSkillProficiency(models.Model):
    """Stores calculated proficiency score for a user on a specific skill."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_proficiencies",
        db_index=True,
    )
    skill = models.ForeignKey(
        Skill,  # Direct reference now, ensure Skill model import
        on_delete=models.CASCADE,
        related_name="user_proficiencies",
        db_index=True,
    )
    proficiency_score = models.FloatField(
        _("Proficiency Score"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_("User mastery score (0.0 to 1.0). Updated after attempts."),
    )
    attempts_count = models.PositiveIntegerField(_("Attempts Count"), default=0)
    correct_count = models.PositiveIntegerField(_("Correct Count"), default=0)
    last_calculated_at = models.DateTimeField(_("Last Calculated At"), auto_now=True)

    class Meta:
        unique_together = [["user", "skill"]]
        verbose_name = _("User Skill Proficiency")
        verbose_name_plural = _("User Skill Proficiencies")
        ordering = ["user", "skill__name"]  # Order by skill name for consistency

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}: {self.proficiency_score:.2f}"

    def record_attempt(self, is_correct: bool):
        """
        Updates proficiency based on a single attempt result using atomic operations.
        """
        if not isinstance(is_correct, bool):
            logger.error(
                f"record_attempt called with non-boolean is_correct for UserSkillProficiency user={self.user_id}, skill={self.skill_id}"
            )
            return  # Avoid processing invalid input

        # Atomically increment counters
        UserSkillProficiency.objects.filter(pk=self.pk).update(
            attempts_count=F("attempts_count") + 1,
            correct_count=F("correct_count") + (1 if is_correct else 0),
            last_calculated_at=timezone.now(),
        )

        # Refresh the instance from DB to get updated counts for score calculation
        self.refresh_from_db(fields=["attempts_count", "correct_count"])

        # Calculate the new score
        if self.attempts_count > 0:
            new_score = round(self.correct_count / self.attempts_count, 4)
        else:
            new_score = 0.0  # Should not happen if attempts_count was just incremented

        # Update score only if it changed to avoid unnecessary writes/signals
        if (
            abs(self.proficiency_score - new_score) > 1e-5
        ):  # Use tolerance for float comparison
            self.proficiency_score = new_score
            self.save(update_fields=["proficiency_score"])  # Save only the score


class EmergencyModeSession(models.Model):
    """Records details when a user enters "Emergency Mode"."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="emergency_sessions",
        verbose_name=_("user"),
        db_index=True,
    )
    reason = models.TextField(_("reason"), blank=True, null=True)
    suggested_plan = models.JSONField(
        _("suggested plan"),
        null=True,
        blank=True,
        help_text=_(
            'Stores plan details: {"focus_skills": ["slug1", ...], "recommended_questions": N, ...}'
        ),
    )
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
        status = "Ended" if self.end_time else "Active"
        return f"{self.user.username} - Emergency Session ({status}) @ {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_ended(self):
        """Sets the end time for the session if not already set."""
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
        _("AI tone"), max_length=10, choices=AiTone.choices, default=AiTone.SERIOUS
    )
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    current_topic_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("current topic question"),
        help_text=_(
            "The question/concept currently being discussed for 'Got It' testing."
        ),
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
        """Marks the session as completed if it's currently active."""
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
        _("sender type"), max_length=4, choices=SenderType.choices, db_index=True
    )
    message_text = models.TextField(_("message text"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True, db_index=True)
    related_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("related question"),
        help_text=_("Optional link to a specific question discussed in the message."),
    )

    class Meta:
        verbose_name = _("Conversation Message")
        verbose_name_plural = _("Conversation Messages")
        ordering = ["timestamp"]  # Ensure chronological order

    def __str__(self):
        return f"{self.get_sender_type_display()} in session {self.session_id} @ {self.timestamp.strftime('%H:%M:%S')}"
