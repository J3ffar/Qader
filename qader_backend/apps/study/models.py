from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db import transaction
from django.db.models import F, Case, When, IntegerField, QuerySet, Count
import logging
from typing import List, Optional, Dict, Any

# Assuming learning models are correctly imported
from apps.learning.models import Question, LearningSection, LearningSubSection, Skill

# Import related models needed for FKs (adjust paths if necessary)
# Assuming these models exist in the specified apps
# from apps.challenges.models import ChallengeAttempt

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
            "If true, this definition uses the specific questions linked below. "
            "If false, it acts as a template and relies on 'configuration'."
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
            "JSON defining rules (e.g., {'num_questions_per_skill': {...}, "
            "'total_questions': N}) for dynamically generating tests based "
            "on this template if 'is_predefined' is false."
        ),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    @property
    def question_count(self) -> int:
        """Returns the number of specific questions linked (only relevant for predefined)."""
        if self.is_predefined:
            # Ensure the instance is saved before accessing M2M
            if self.pk:
                return self.questions.count()
            return 0
        return 0

    def clean(self):
        """Validate Test configuration based on is_predefined."""
        super().clean()
        if self.is_predefined:
            if self.configuration:
                raise ValidationError(
                    _(
                        "Configuration must be empty for predefined tests "
                        "(select Questions instead)."
                    )
                )
            # Optional: Add validation check for questions M2M field when saving
            # if self.pk is None and not self.questions.exists(): # Needs rethink for M2M saving
            #     pass
        else:  # Dynamic Test (Template)
            if not self.configuration:
                raise ValidationError(
                    _("Configuration must be set for dynamic (non-predefined) tests.")
                )
            # Prevent linking specific questions if it's dynamic (check after save or in form/serializer)
            if self.pk and self.questions.exists():
                logger.warning(
                    f"Dynamic Test Definition {self.id} unexpectedly has questions linked. "
                    "These will be ignored unless 'is_predefined' is set to True."
                )
                # Optionally raise ValidationError if this state is strictly forbidden
                raise ValidationError(
                    _("Questions should not be selected for dynamic tests.")
                )

    def __str__(self):
        return f"{self.name} ({self.get_test_type_display()})"

    class Meta:
        verbose_name = _("Test Definition")
        verbose_name_plural = _("Test Definitions")
        ordering = ["name"]


# --- User Attempt Models ---
class UserTestAttempt(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")
        ERROR = "error", _("Error")

    class AttemptType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Test")
        SIMULATION = "simulation", _("Full Simulation")
        TRADITIONAL = "traditional", _("Traditional Practice Session")
        # Add other types like 'EMERGENCY'? Maybe map emergency actions to TRADITIONAL?
        # Let's keep TRADITIONAL for now to represent unstructured practice.

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
        help_text=_("The Test Definition used for this attempt, if based on one."),
    )
    attempt_type = models.CharField(
        _("attempt type"),
        max_length=20,
        choices=AttemptType.choices,
        db_index=True,
        help_text=_("The specific type of this test attempt instance."),
    )
    test_configuration = models.JSONField(
        _("test configuration snapshot"),
        blank=True,
        null=True,
        help_text=_(
            "Snapshot of the configuration used to generate this attempt "
            "(e.g., sections, skills, num_questions). Ensure consistent structure."
        ),
    )
    # Store question IDs as JSON list for flexibility and order preservation
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
            "Tracks if gamification points for completing this attempt have been awarded."
        ),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("User Test Attempt")
        verbose_name_plural = _("User Test Attempts")
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "attempt_type"]),
            models.Index(fields=["user", "start_time"]),
        ]

    def __str__(self):
        attempt_label = self.get_attempt_type_display()
        user_display = self.user.username if self.user else "N/A"
        start_display = (
            self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else "N/A"
        )
        return f"{user_display} - {attempt_label} ({self.get_status_display()}) - {start_display}"

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculates the duration of the attempt in seconds, if ended."""
        if self.end_time and self.start_time:
            # No need to check status, duration is valid if end_time is set
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def num_questions(self) -> int:
        """Returns the number of questions included in this attempt based on question_ids field."""
        return len(self.question_ids) if isinstance(self.question_ids, list) else 0

    @property
    def answered_question_count(self) -> int:
        """
        Returns the number of questions answered in this attempt.
        Relies on the related 'question_attempts' count or an annotation.
        """
        # Prefer annotation if provided by the view/queryset
        if hasattr(self, "answered_question_count_agg"):
            return self.answered_question_count_agg
        # Fallback: query related objects if not annotated (less efficient in loops)
        if self.pk:
            return self.question_attempts.count()
        return 0

    def get_questions_queryset(self) -> QuerySet[Question]:
        """Returns an ordered queryset for the questions associated with this attempt."""
        if not self.question_ids or not isinstance(self.question_ids, list):
            return Question.objects.none()

        # Ensure IDs are integers before querying
        valid_question_ids = [
            qid
            for qid in self.question_ids
            if isinstance(qid, (int, str)) and str(qid).isdigit()
        ]
        if not valid_question_ids:
            return Question.objects.none()
        valid_question_ids = [
            int(qid) for qid in valid_question_ids
        ]  # Convert valid ones to int

        # Use Case/When to preserve the order defined in self.question_ids
        preserved_order = Case(
            *[When(pk=pk, then=pos) for pos, pk in enumerate(valid_question_ids)],
            output_field=IntegerField(),
        )
        # Eager load common related fields used in serializers/views
        return (
            Question.objects.filter(pk__in=valid_question_ids)
            .select_related("subsection", "subsection__section", "skill")
            .order_by(preserved_order)
        )

    @transaction.atomic  # Ensure score calculation and saving are atomic
    def calculate_and_save_scores(
        self, question_attempts_qs: Optional[QuerySet["UserQuestionAttempt"]] = None
    ):
        """
        Calculates scores based on provided or fetched question attempts and updates the instance.
        Prefetches related data if queryset is not provided.

        Args:
            question_attempts_qs: Optional pre-fetched queryset of UserQuestionAttempt
                                  related to this test_attempt. If None, it will be fetched.
        """
        if not question_attempts_qs:
            # Fetch attempts if not provided, ensuring necessary related data is loaded
            question_attempts_qs = self.question_attempts.select_related(
                "question__subsection__section", "question__skill"
            ).all()

        total_questions_in_attempt = self.num_questions
        answered_attempts = list(
            question_attempts_qs
        )  # Fetch into memory for processing
        num_answered = len(answered_attempts)

        if total_questions_in_attempt == 0:
            logger.warning(
                f"Attempt {self.id} has 0 questions defined in question_ids. Setting scores to zero/null."
            )
            self.score_percentage = 0.0
            self.score_verbal = None
            self.score_quantitative = None
            self.results_summary = {}
        else:
            correct_answers = sum(
                1 for attempt in answered_attempts if attempt.is_correct
            )
            # Overall score based on total questions *in the attempt* definition
            overall_score = round(
                (correct_answers / total_questions_in_attempt * 100.0), 1
            )

            verbal_correct, verbal_total, quant_correct, quant_total = 0, 0, 0, 0
            results_summary_calc = {}

            all_q_ids = set(self.question_ids)
            if not all_q_ids:
                logger.warning(
                    f"Attempt {self.id} has empty question_ids list during scoring calculation."
                )
                q_detail_map = {}
            else:
                # Ensure IDs are integers for the query
                valid_q_ids = [int(qid) for qid in all_q_ids if str(qid).isdigit()]
                if not valid_q_ids:
                    logger.warning(
                        f"Attempt {self.id} has no valid integer question IDs for scoring."
                    )
                    q_detail_map = {}
                else:
                    # Fetch details for ALL questions defined in the attempt
                    q_details = (
                        Question.objects.filter(id__in=valid_q_ids)
                        .select_related(
                            "subsection__section"
                        )  # Ensure section is loaded
                        .values(
                            "id",
                            "subsection_id",
                            "subsection__slug",
                            "subsection__name",
                            "subsection__section__slug",  # Get section slug directly
                        )
                    )
                    q_detail_map = {q["id"]: q for q in q_details}

            # Initialize results summary based on involved subsections from ALL questions
            involved_subsections = {}
            for qid, q_detail in q_detail_map.items():
                sub_id = q_detail.get("subsection_id")
                if sub_id and sub_id not in involved_subsections:
                    involved_subsections[sub_id] = {
                        "slug": q_detail.get("subsection__slug"),
                        "name": q_detail.get("subsection__name"),
                    }
                    if q_detail.get(
                        "subsection__slug"
                    ):  # Initialize summary only if slug exists
                        results_summary_calc[q_detail["subsection__slug"]] = {
                            "correct": 0,
                            "total": 0,
                            "name": q_detail.get("subsection__name", "Unknown"),
                            "score": 0.0,
                        }

            # Count totals per section/subsection based on ALL questions in the attempt
            for qid in all_q_ids:
                # Ensure qid is integer before map lookup
                qid_int = int(qid) if str(qid).isdigit() else None
                if qid_int is None:
                    continue

                detail = q_detail_map.get(qid_int)
                if not detail:
                    logger.warning(
                        f"Missing details for Question ID {qid_int} in Attempt {self.id} during scoring total count."
                    )
                    continue

                sub_slug = detail.get("subsection__slug")
                if sub_slug and sub_slug in results_summary_calc:
                    results_summary_calc[sub_slug]["total"] += 1

                section_slug = detail.get("subsection__section__slug")
                if section_slug == "verbal":
                    verbal_total += 1
                elif section_slug == "quantitative":
                    quant_total += 1

            # Count correct answers from the *answered* attempts
            for attempt in answered_attempts:
                question_id = attempt.question_id  # Use FK directly
                detail = q_detail_map.get(question_id)

                if not detail:
                    logger.warning(
                        f"Missing detail for answered Q {question_id} in attempt {self.id} during scoring correct count."
                    )
                    continue

                subsection_slug = detail.get("subsection__slug")
                section_slug = detail.get("subsection__section__slug")

                if attempt.is_correct:
                    if subsection_slug and subsection_slug in results_summary_calc:
                        results_summary_calc[subsection_slug]["correct"] += 1
                    if section_slug == "verbal":
                        verbal_correct += 1
                    elif section_slug == "quantitative":
                        quant_correct += 1

            # Calculate final scores for summary and sections
            for slug, data in results_summary_calc.items():
                data["score"] = (
                    round((data["correct"] / data["total"] * 100.0), 1)
                    if data["total"] > 0
                    else 0.0
                )

            verbal_score = (
                round((verbal_correct / verbal_total * 100.0), 1)
                if verbal_total > 0
                else None
            )
            quantitative_score = (
                round((quant_correct / quant_total * 100.0), 1)
                if quant_total > 0
                else None
            )

            # Assign calculated scores to the instance
            self.score_percentage = overall_score
            self.score_verbal = verbal_score
            self.score_quantitative = quantitative_score
            self.results_summary = results_summary_calc

        # Save the updated fields efficiently
        update_fields_list = [
            "score_percentage",
            "score_verbal",
            "score_quantitative",
            "results_summary",
            "updated_at",
        ]
        self.save(update_fields=update_fields_list)
        logger.info(f"Scores calculated and saved for UserTestAttempt {self.id}.")


class UserQuestionAttempt(models.Model):
    """Records every instance a user attempts a question, tracking context and outcome."""

    class Mode(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditional Learning")
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        TEST = "test", _("Practice Test/Simulation")  # Consolidated
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
        on_delete=models.CASCADE,
        related_name="user_attempts",
        verbose_name=_("question"),
        db_index=True,
    )
    # --- Context Links ---
    # Ensure only ONE context link is set per record (validation in forms/serializers/services)
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,  # If UserTestAttempt is deleted, associated question attempts go too
        related_name="question_attempts",
        verbose_name=_("test attempt session"),
        null=True,
        blank=True,
        db_index=True,
    )
    conversation_session = models.ForeignKey(
        "ConversationSession",  # Keep as string if defined later or circular
        on_delete=models.CASCADE,  # If ConversationSession deleted, attempts go too
        related_name="question_attempts",
        verbose_name=_("conversation session"),
        null=True,
        blank=True,
        db_index=True,
    )
    challenge_attempt = models.ForeignKey(
        "challenges.ChallengeAttempt",  # Use app_label.ModelName string format
        on_delete=models.CASCADE,  # If ChallengeAttempt deleted, attempts go too
        related_name="user_question_attempts_in_challenge",  # Keep specific name if needed elsewhere
        verbose_name=_("challenge participation"),
        null=True,
        blank=True,
        db_index=True,
    )
    emergency_session = models.ForeignKey(
        "EmergencyModeSession",  # Keep as string if defined later or circular
        on_delete=models.CASCADE,  # Consider if deleting session should delete attempts? CASCADE seems logical.
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
        null=True,  # Allow null if question not answered yet (e.g., just used hint)
        blank=True,
    )
    is_correct = models.BooleanField(
        _("is correct"),
        null=True,  # Calculated on save based on selected_answer, can be null initially
        blank=True,
        db_index=True,
    )
    time_taken_seconds = models.PositiveIntegerField(
        _("time taken (seconds)"),
        null=True,
        blank=True,
        help_text=_("Time spent specifically on this question."),
    )
    # Flags for user actions (useful for traditional mode feedback and analytics)
    used_hint = models.BooleanField(_("used hint"), default=False)
    used_elimination = models.BooleanField(_("used elimination"), default=False)
    revealed_answer = models.BooleanField(
        _("revealed correct answer"),
        default=False,
        help_text=_("Track if the user explicitly revealed the correct answer choice."),
    )
    revealed_explanation = models.BooleanField(
        _("revealed explanation"),
        default=False,
        help_text=_("Track if the user explicitly revealed the explanation."),
    )

    mode = models.CharField(
        _("mode"),
        max_length=20,
        choices=Mode.choices,
        db_index=True,  # Add index
        help_text=_("The context (feature) in which the question was attempted."),
    )
    attempted_at = models.DateTimeField(
        _("attempted at"),
        default=timezone.now,  # Set on creation
        db_index=True,  # Add index
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        constraints = [
            # Ensure only ONE answer per question within a specific CONTEXT
            # We assume only one context FK (test_attempt, conversation_session, etc.) is set.
            # A single constraint per context is cleaner.
            models.UniqueConstraint(
                fields=["user", "question", "test_attempt"],
                condition=models.Q(test_attempt__isnull=False),
                name="uq_user_question_per_test_attempt",  # Use 'uq_' prefix convention
            ),
            models.UniqueConstraint(
                fields=["user", "question", "challenge_attempt"],
                condition=models.Q(challenge_attempt__isnull=False),
                name="uq_user_question_per_challenge_attempt",
            ),
            models.UniqueConstraint(
                fields=["user", "question", "conversation_session"],
                condition=models.Q(conversation_session__isnull=False),
                name="uq_user_question_per_conversation",
            ),
            # models.UniqueConstraint(
            #     fields=["user", "question", "emergency_session"],
            #     condition=models.Q(emergency_session__isnull=False),
            #     name="uq_user_question_per_emergency",
            # ),
            # Add CHECK constraint if DB supports it to ensure only one context FK is non-null?
            # models.CheckConstraint(...)
        ]
        indexes = [  # Explicit indexes for common lookups
            models.Index(fields=["user", "mode"]),
            models.Index(fields=["user", "question", "is_correct"]),
            # Index for faster lookup of attempts within a specific context
            models.Index(fields=["test_attempt", "question"]),
            models.Index(fields=["challenge_attempt", "question"]),
            models.Index(fields=["conversation_session", "question"]),
            models.Index(fields=["emergency_session", "question"]),
        ]

    def __str__(self):
        context_str = ""
        if self.test_attempt_id:
            context_str = f"Test:{self.test_attempt_id}"
        elif self.challenge_attempt_id:
            context_str = f"Challenge:{self.challenge_attempt_id}"
        elif self.conversation_session_id:
            context_str = f"Convo:{self.conversation_session_id}"
        elif self.emergency_session_id:
            context_str = f"Emergency:{self.emergency_session_id}"
        else:
            context_str = (
                f"Mode:{self.get_mode_display()}"  # Fallback to mode if no context FK
            )

        q_id = self.question_id or "N/A"
        user_name = self.user.username if self.user else "N/A"
        timestamp = (
            self.attempted_at.strftime("%Y-%m-%d %H:%M") if self.attempted_at else "N/A"
        )

        return f"{user_name} - Q:{q_id} ({context_str}) @ {timestamp}"

    def _determine_mode(self):
        """Determines the mode based on the set context FK."""
        if self.test_attempt_id:
            # Map UserTestAttempt.AttemptType to UserQuestionAttempt.Mode
            mode_map = {
                UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: self.Mode.LEVEL_ASSESSMENT,
                UserTestAttempt.AttemptType.PRACTICE: self.Mode.TEST,
                UserTestAttempt.AttemptType.SIMULATION: self.Mode.TEST,
                UserTestAttempt.AttemptType.TRADITIONAL: self.Mode.TRADITIONAL,
            }
            # Use getattr to safely access attempt_type if test_attempt is loaded
            attempt_type = getattr(self.test_attempt, "attempt_type", None)
            if not attempt_type and self.test_attempt_id:  # Fetch if not loaded
                try:
                    attempt_type = UserTestAttempt.objects.values_list(
                        "attempt_type", flat=True
                    ).get(pk=self.test_attempt_id)
                except UserTestAttempt.DoesNotExist:
                    logger.error(
                        f"Could not find TestAttempt {self.test_attempt_id} referenced in UserQuestionAttempt during mode determination."
                    )
                    return self.Mode.TEST  # Fallback
            return mode_map.get(
                attempt_type, self.Mode.TEST
            )  # Fallback to generic TEST
        elif self.challenge_attempt_id:
            return self.Mode.CHALLENGE
        elif self.emergency_session_id:
            return self.Mode.EMERGENCY
        elif self.conversation_session_id:
            return self.Mode.CONVERSATION
        else:
            # This case should ideally not happen if attempts are always created via a service
            # that sets the context link. Log a warning.
            logger.warning(
                f"UserQuestionAttempt created (User: {self.user_id}, Q: {self.question_id}) "
                f"without a context link. Mode cannot be reliably determined automatically. "
                f"Falling back to TRADITIONAL, but this might be incorrect."
            )
            return self.Mode.TRADITIONAL  # Fallback, but indicates potential issue

    def _calculate_correctness(self):
        """Calculates and sets is_correct based on selected_answer and question's correct_answer."""
        if self.selected_answer and self.question_id:
            try:
                # Try to use related object if already fetched
                correct_ans = getattr(self.question, "correct_answer", None)
                if correct_ans is None:
                    # Fetch if necessary (less efficient, caller should ideally prefetch)
                    correct_ans = Question.objects.values_list(
                        "correct_answer", flat=True
                    ).get(pk=self.question_id)

                self.is_correct = self.selected_answer == correct_ans
            except Question.DoesNotExist:
                logger.error(
                    f"Question {self.question_id} not found during UserQuestionAttempt save "
                    f"(User: {self.user_id}). Cannot calculate is_correct."
                )
                self.is_correct = None  # Explicitly set to None if question missing
            except Exception as e:
                logger.exception(
                    f"Unexpected error calculating is_correct for Q:{self.question_id}, User:{self.user_id}: {e}"
                )
                self.is_correct = None
        elif self.selected_answer is None:
            # If no answer selected (e.g., only used hint), correctness is undefined (null)
            self.is_correct = None
        # Else: is_correct might have been explicitly set (e.g. by admin), leave it alone.

    def save(self, *args, **kwargs):
        # 1. Determine Mode if not explicitly set
        # We trust that only one context FK is set, validation should happen elsewhere.
        if not self.mode:
            self.mode = self._determine_mode()

        # 2. Calculate is_correct if an answer is selected and correctness not already set
        # Allow explicit setting of is_correct to override calculation if needed.
        if self.selected_answer and self.is_correct is None:
            self._calculate_correctness()
        elif self.selected_answer is None and self.is_correct is None:
            # Ensure is_correct is None if no answer selected
            self.is_correct = None

        # 3. Ensure attempted_at reflects save time on creation (handled by default=timezone.now)
        # If you need to update attempted_at on *every* save (last interaction time), uncomment below:
        # self.attempted_at = timezone.now()

        super().save(*args, **kwargs)


# --- User Skill Proficiency Model ---
class UserSkillProficiency(models.Model):
    """Stores calculated proficiency score for a user on a specific skill."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_proficiencies",
        db_index=True,
    )
    skill = models.ForeignKey(
        Skill,
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
        # Ensure a user can only have one proficiency record per skill
        unique_together = [["user", "skill"]]
        verbose_name = _("User Skill Proficiency")
        verbose_name_plural = _("User Skill Proficiencies")
        ordering = ["user", "skill__name"]
        indexes = [
            # Added index for filtering/ordering by score
            models.Index(fields=["user", "proficiency_score"]),
        ]

    def __str__(self):
        skill_name = getattr(self.skill, "name", "N/A")
        user_name = getattr(self.user, "username", "N/A")
        return f"{user_name} - {skill_name}: {self.proficiency_score:.2f}"

    @transaction.atomic  # Ensure atomic updates for counters and score
    def record_attempt(self, is_correct: bool):
        """
        Atomically updates counters and recalculates proficiency score for this record.
        Should be called after a UserQuestionAttempt related to this user/skill is saved.
        """
        if not isinstance(is_correct, bool):
            logger.error(
                f"record_attempt called with non-boolean is_correct for UserSkillProficiency pk={self.pk}"
            )
            return

        # Lock the row for update to prevent race conditions
        # Note: select_for_update() needs to be called on the queryset *before* the update
        try:
            # Re-fetch with select_for_update within the transaction
            locked_self = UserSkillProficiency.objects.select_for_update().get(
                pk=self.pk
            )

            # Increment counters using the locked instance's values
            locked_self.attempts_count += 1
            if is_correct:
                locked_self.correct_count += 1
            locked_self.last_calculated_at = (
                timezone.now()
            )  # Keep track of last update time

            # Recalculate the new score
            if locked_self.attempts_count > 0:
                # Round to a reasonable number of decimal places (e.g., 4)
                new_score = round(
                    locked_self.correct_count / locked_self.attempts_count, 4
                )
            else:
                new_score = 0.0  # Should not happen if attempts_count was incremented, but safe fallback

            # Update score only if it has changed significantly (avoid unnecessary writes/signals)
            # Use a small tolerance for float comparison
            if abs(locked_self.proficiency_score - new_score) > 1e-5:
                locked_self.proficiency_score = new_score

            # Save all changes at once
            locked_self.save(
                update_fields=[
                    "attempts_count",
                    "correct_count",
                    "proficiency_score",
                    "last_calculated_at",
                ]
            )

            # Update the current in-memory object to reflect changes if needed by caller
            self.attempts_count = locked_self.attempts_count
            self.correct_count = locked_self.correct_count
            self.proficiency_score = locked_self.proficiency_score
            self.last_calculated_at = locked_self.last_calculated_at

        except UserSkillProficiency.DoesNotExist:
            logger.error(
                f"UserSkillProficiency pk={self.pk} not found during record_attempt update."
            )
        except Exception as e:
            logger.exception(
                f"Error during UserSkillProficiency.record_attempt for pk={self.pk}: {e}"
            )
            # Transaction will be rolled back


# --- Emergency Mode Session Model ---
class EmergencyModeSession(models.Model):
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
            'Stores plan details: {"focus_skills": ["slug1", ...], '
            '"recommended_questions": N, "quick_review_topics": [...]}'
        ),
    )
    calm_mode_active = models.BooleanField(_("calm mode active"), default=False)
    start_time = models.DateTimeField(_("start time"), auto_now_add=True, db_index=True)
    end_time = models.DateTimeField(_("end time"), null=True, blank=True)
    overall_score = models.FloatField(
        null=True, blank=True, help_text="Overall score percentage."
    )
    verbal_score = models.FloatField(
        null=True, blank=True, help_text="Verbal section score percentage."
    )
    quantitative_score = models.FloatField(
        null=True, blank=True, help_text="Quantitative section score percentage."
    )
    results_summary = models.JSONField(
        null=True, blank=True, help_text="Detailed breakdown of scores by subsection."
    )
    ai_feedback = models.TextField(
        blank=True, help_text="AI-generated feedback on session performance."
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Emergency Mode Session")
        verbose_name_plural = _("Emergency Mode Sessions")
        ordering = ["-start_time"]

    def __str__(self):
        status_display = _("Ended") if self.end_time else _("Active")
        user_name = getattr(self.user, "username", "N/A")
        timestamp = (
            self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else "N/A"
        )
        return f"{user_name} - Emergency Session ({status_display}) @ {timestamp}"

    def mark_as_ended(self):
        """Sets the end time for the session if not already set."""
        if not self.end_time:
            self.end_time = timezone.now()
            self.save(update_fields=["end_time", "updated_at"])


class EmergencySupportRequest(models.Model):
    """
    Stores a specific support request submitted by a user during an emergency session.
    """

    class ProblemType(models.TextChoices):
        TECHNICAL = "technical", _("Technical Issue")
        ACADEMIC = "academic", _("Academic Question")
        CONTENT = "content", _("Problem with a Question")
        OTHER = "other", _("Other")

    class RequestStatus(models.TextChoices):
        OPEN = "open", _("Open")
        IN_PROGRESS = "in_progress", _("In Progress")
        RESOLVED = "resolved", _("Resolved")
        CLOSED = "closed", _("Closed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_requests",
    )
    session = models.ForeignKey(
        EmergencyModeSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_requests",
        help_text=_("The emergency session during which the request was made."),
    )
    problem_type = models.CharField(
        _("Problem Type"),
        max_length=20,
        choices=ProblemType.choices,
        default=ProblemType.OTHER,
    )
    description = models.TextField(
        _("Description"),
        help_text=_("Detailed description of the problem or question from the user."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=RequestStatus.choices,
        default=RequestStatus.OPEN,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Support Request #{self.id} from {self.user} ({self.get_problem_type_display()})"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Emergency Support Request")
        verbose_name_plural = _("Emergency Support Requests")


# --- Conversation Session Model ---
class ConversationSession(models.Model):
    class AiTone(models.TextChoices):
        CHEERFUL = "cheerful", _("Cheerful")
        SERIOUS = "serious", _("Serious")
        # Add more tones as needed

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMPLETED = "completed", _("Completed")
        # Add other statuses like 'PAUSED'?

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
    # Tracks the specific question/concept being discussed for targeted testing/clarification
    current_topic_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,  # Don't delete session if question is deleted
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed from Question
        verbose_name=_("current topic question"),
        help_text=_("The question/concept currently being focused on."),
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
        user_name = getattr(self.user, "username", "N/A")
        timestamp = (
            self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else "N/A"
        )
        return f"Conversation for {user_name} ({self.get_status_display()}) started {timestamp}"

    def end_session(self):
        """Marks the session as completed if it's currently active."""
        if self.status == self.Status.ACTIVE:
            self.status = self.Status.COMPLETED
            self.end_time = timezone.now()
            self.save(update_fields=["status", "end_time", "updated_at"])


# --- Conversation Message Model ---
class ConversationMessage(models.Model):
    class SenderType(models.TextChoices):
        USER = "user", _("User")
        AI = "ai", _("AI")

    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,  # Messages belong to a session
        related_name="messages",
        verbose_name=_("session"),
        db_index=True,
    )
    sender_type = models.CharField(
        _("sender type"), max_length=4, choices=SenderType.choices, db_index=True
    )
    message_text = models.TextField(_("message text"))
    timestamp = models.DateTimeField(_("timestamp"), auto_now_add=True, db_index=True)
    # Optional link to a specific question discussed/referenced in the message
    related_question = models.ForeignKey(
        Question,
        on_delete=models.SET_NULL,  # Keep message even if question is deleted
        null=True,
        blank=True,
        related_name="+",  # No reverse relation needed from Question
        verbose_name=_("related question"),
    )

    class Meta:
        verbose_name = _("Conversation Message")
        verbose_name_plural = _("Conversation Messages")
        ordering = ["timestamp"]  # Ensure chronological order within a session

    def __str__(self):
        session_id = self.session_id or "N/A"
        timestamp = self.timestamp.strftime("%H:%M:%S") if self.timestamp else "N/A"
        return f"{self.get_sender_type_display()} in session {session_id} @ {timestamp}"
