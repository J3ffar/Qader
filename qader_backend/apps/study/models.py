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
        ABANDONED = "abandoned", _("Abandoned")  # Renamed from CANCELLED for clarity

    class AttemptType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Test")
        SIMULATION = "simulation", _("Full Simulation")
        # Add other types if needed (e.g., CHALLENGE_TEST, EMERGENCY_TEST)

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
        db_index=True,  # Added index
        help_text=_("The specific type of this test attempt instance."),
    )
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
        db_index=True,  # Added index
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
        indexes = [  # Added explicit index for common filtering
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "attempt_type"]),
        ]

    def __str__(self):
        attempt_label = self.get_attempt_type_display()
        return f"{self.user.username} - {attempt_label} ({self.get_status_display()}) - {self.start_time.strftime('%Y-%m-%d')}"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculates the duration of the attempt in seconds, if completed."""
        if (
            self.end_time
            and self.start_time
            and self.status in [self.Status.COMPLETED, self.Status.ABANDONED]
        ):
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
        # Ensure primary keys are integers before querying
        valid_question_ids = [qid for qid in self.question_ids if isinstance(qid, int)]
        if not valid_question_ids:
            return Question.objects.none()

        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(valid_question_ids)],
            output_field=IntegerField(),
        )
        # Eager load common related fields
        return (
            Question.objects.filter(pk__in=valid_question_ids)
            .select_related("subsection", "subsection__section", "skill")
            .order_by(preserved_order)
        )

    def calculate_and_save_scores(
        self, question_attempts_qs: QuerySet["UserQuestionAttempt"]
    ):
        """
        Calculates scores based on provided question attempts queryset and updates the instance.
        Requires attempts to have related question/subsection/section loaded.
        """
        # Use the queryset directly
        total_questions_in_attempt = (
            self.num_questions
        )  # Total questions defined for the attempt
        answered_attempts = list(
            question_attempts_qs
        )  # Fetch attempts into memory for iteration
        num_answered = len(answered_attempts)

        if num_answered == 0:
            logger.warning(
                f"No question attempts provided for scoring UserTestAttempt {self.id}."
            )
            self.score_percentage = 0.0
            self.score_verbal = None
            self.score_quantitative = None
            self.results_summary = {}
        else:
            correct_answers = sum(
                1 for attempt in answered_attempts if attempt.is_correct
            )
            # Score based on total questions *in the attempt*, not just answered ones
            overall_score = (
                round((correct_answers / total_questions_in_attempt * 100), 1)
                if total_questions_in_attempt > 0
                else 0.0
            )

            verbal_correct, verbal_total, quant_correct, quant_total = 0, 0, 0, 0
            results_summary_calc = {}

            # Get all question IDs associated with this attempt
            all_q_ids = set(self.question_ids)
            # Efficiently fetch sections/subsections for all questions in the attempt
            q_details = (
                Question.objects.filter(id__in=all_q_ids)
                .select_related("subsection__section")
                .values(
                    "id",
                    "subsection_id",
                    "subsection__slug",
                    "subsection__name",
                    "subsection__section__slug",
                )
            )
            q_detail_map = {q["id"]: q for q in q_details}

            # Initialize summary for all subsections involved
            involved_subsections = {
                q["subsection_id"]: {
                    "slug": q["subsection__slug"],
                    "name": q["subsection__name"],
                }
                for q in q_details
                if q["subsection_id"]
            }
            for sub_id, sub_data in involved_subsections.items():
                results_summary_calc[sub_data["slug"]] = {
                    "correct": 0,
                    "total": 0,  # Will count based on questions belonging to this sub in the attempt
                    "name": sub_data["name"],
                    "score": 0.0,
                }

            # Count total questions per subsection *for this specific attempt*
            for qid in all_q_ids:
                detail = q_detail_map.get(qid)
                if detail and detail["subsection__slug"] in results_summary_calc:
                    results_summary_calc[detail["subsection__slug"]]["total"] += 1
                    section_slug = detail["subsection__section__slug"]
                    if section_slug == "verbal":
                        verbal_total += 1
                    elif section_slug == "quantitative":
                        quant_total += 1

            # Process the *answered* attempts to count correct answers
            for attempt in answered_attempts:
                question = attempt.question  # Assumes preloaded
                detail = q_detail_map.get(question.id)

                if (
                    not detail
                    or not detail["subsection__slug"]
                    or not detail["subsection__section__slug"]
                ):
                    logger.warning(
                        f"Missing detail/section/subsection for Q {question.id} in attempt {self.id}"
                    )
                    continue

                subsection_slug = detail["subsection__slug"]
                section_slug = detail["subsection__section__slug"]

                if attempt.is_correct:
                    if subsection_slug in results_summary_calc:
                        results_summary_calc[subsection_slug]["correct"] += 1
                    if section_slug == "verbal":
                        verbal_correct += 1
                    if section_slug == "quantitative":
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
    # --- Context Links ---
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,  # Attempts are part of the test attempt
        related_name="question_attempts",  # Changed related_name for clarity
        verbose_name=_("test attempt session"),
        null=True,
        blank=True,
        db_index=True,  # Added index
    )
    conversation_session = models.ForeignKey(
        "ConversationSession",  # Use quotes if defined later
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("conversation session"),
        null=True,
        blank=True,
        db_index=True,
    )
    challenge_attempt = models.ForeignKey(
        "challenges.ChallengeAttempt",  # Assuming app name 'challenges'
        on_delete=models.CASCADE,
        related_name="user_question_attempts_in_challenge",
        verbose_name=_("challenge participation"),
        null=True,
        blank=True,
        db_index=True,
    )
    emergency_session = models.ForeignKey(
        "EmergencyModeSession",  # Use quotes if defined later
        on_delete=models.SET_NULL,
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
        null=True,  # Allow null if question not answered yet in an ongoing test
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"),
        null=True,  # Calculated on save, can be null if not answered
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
        default=timezone.now,  # Sets when created OR updated via save()
        db_index=True,
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        constraints = [
            # Ensure only ONE answer per question within a specific test attempt
            models.UniqueConstraint(
                fields=["user", "question", "test_attempt"],
                condition=models.Q(test_attempt__isnull=False),
                name="unique_user_question_per_test_attempt",
            ),
            # Keep challenge constraint
            models.UniqueConstraint(
                fields=["user", "question", "challenge_attempt"],
                condition=models.Q(challenge_attempt__isnull=False),
                name="unique_user_question_per_challenge_attempt",
            ),
            # Add more constraints if needed (e.g., unique per conversation session?)
        ]
        indexes = [  # Add index for faster lookup by test_attempt
            models.Index(fields=["test_attempt", "question"]),
        ]

    def __str__(self):
        context = (
            f"Test:{self.test_attempt_id}"
            if self.test_attempt
            else self.get_mode_display()
        )
        return f"{self.user.username} - Q:{self.question_id} ({context}) @ {self.attempted_at.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        # --- Auto-set mode based on context FKs if not explicitly set ---
        # This logic remains useful
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
            else:
                # Default to Traditional if no other context is linked
                # This might happen if created directly outside other flows
                self.mode = self.Mode.TRADITIONAL

        # --- Auto-calculate is_correct if answer selected and correctness not set ---
        # This logic remains crucial
        if self.selected_answer and self.is_correct is None:
            try:
                # Assuming self.question is already loaded or fetched efficiently
                # Avoid DB hit if question is already related object
                if (
                    hasattr(self, "question") and self.question._state.db
                ):  # Check if it's a loaded instance
                    correct_ans = self.question.correct_answer
                else:
                    # Fetch if not loaded (less ideal, caller should optimize)
                    correct_ans = Question.objects.values_list(
                        "correct_answer", flat=True
                    ).get(pk=self.question_id)
                self.is_correct = self.selected_answer == correct_ans
            except Question.DoesNotExist:
                logger.warning(
                    f"Question {self.question_id} not found during UserQuestionAttempt save for user {self.user_id}."
                )
                self.is_correct = None  # Explicitly set to None if question missing
            except AttributeError as e:
                logger.error(
                    f"AttributeError accessing correct_answer for UserQuestionAttempt with question_id {self.question_id}: {e}"
                )
                self.is_correct = None

        # Ensure attempted_at is updated on every save
        self.attempted_at = timezone.now()

        super().save(*args, **kwargs)


# --- User Skill Proficiency Model (No changes needed) ---
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
        ordering = ["user", "skill__name"]

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}: {self.proficiency_score:.2f}"

    def record_attempt(self, is_correct: bool):
        # ... (keep existing record_attempt method) ...
        if not isinstance(is_correct, bool):
            logger.error(
                f"record_attempt called with non-boolean is_correct for UserSkillProficiency user={self.user_id}, skill={self.skill_id}"
            )
            return

        # Atomically increment counters
        updated_rows = UserSkillProficiency.objects.filter(pk=self.pk).update(
            attempts_count=F("attempts_count") + 1,
            correct_count=F("correct_count") + (1 if is_correct else 0),
            last_calculated_at=timezone.now(),
        )

        if updated_rows == 0:
            logger.warning(
                f"Failed to update counters for UserSkillProficiency pk={self.pk}"
            )
            return  # Avoid proceeding if update failed

        # Refresh the instance from DB to get updated counts for score calculation
        self.refresh_from_db(fields=["attempts_count", "correct_count"])

        # Calculate the new score
        if self.attempts_count > 0:
            new_score = round(self.correct_count / self.attempts_count, 4)
        else:
            new_score = 0.0

        # Update score only if it changed
        if abs(self.proficiency_score - new_score) > 1e-5:
            self.proficiency_score = new_score
            self.save(update_fields=["proficiency_score"])


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
