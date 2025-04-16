from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField  # If using PostgreSQL

# from django.db.models import JSONField # For Django 3.1+ with other DBs
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.learning.models import Question, Skill, LearningSection, LearningSubSection


class TestDefinition(models.Model):
    """
    Represents the definition or configuration of a type of test.
    e.g., "Initial Level Assessment", "Quant Practice Set 1", "Full Mock Exam".
    """

    class TestType(models.TextChoices):
        LEVEL_ASSESSMENT = "level_assessment", _("Level Assessment")
        PRACTICE = "practice", _("Practice Set")
        SIMULATION = "simulation", _("Simulation")
        CUSTOM = "custom", _("Custom Test")
        CHALLENGE = "challenge", _(
            "Challenge"
        )  # Added for future challenge integration

    name = models.CharField(_("Test Name"), max_length=255, unique=True)
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        unique=True,
        help_text=_("Unique identifier for API usage"),
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    test_type = models.CharField(
        _("Test Type"),
        max_length=20,
        choices=TestType.choices,
        default=TestType.PRACTICE,
        db_index=True,
    )
    # Configuration for dynamically generated tests (e.g., num questions per section/skill)
    default_configuration = models.JSONField(
        _("Default Configuration"),
        blank=True,
        null=True,
        help_text=_(
            'e.g., {"num_questions": 30, "sections": ["verbal", "quantitative"]}'
        ),
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this test definition can be used."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Test Definition")
        verbose_name_plural = _("Test Definitions")
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserTestAttempt(models.Model):
    """
    Records a user's session taking a specific test instance.
    """

    class Status(models.TextChoices):
        STARTED = "started", _("Started")
        COMPLETED = "completed", _("Completed")
        ABANDONED = "abandoned", _("Abandoned")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="test_attempts",
        verbose_name=_("User"),
    )
    test_definition = models.ForeignKey(
        TestDefinition,
        on_delete=models.SET_NULL,  # Keep attempt history even if definition changes
        related_name="attempts",
        verbose_name=_("Test Definition"),
        null=True,
        blank=True,
    )
    # Snapshot of the configuration used for this specific instance
    # Crucial for dynamically generated tests or custom tests
    configuration = models.JSONField(
        _("Test Configuration Used"), blank=True, null=True
    )
    status = models.CharField(
        _("Status"),
        max_length=15,
        choices=Status.choices,
        default=Status.STARTED,
        db_index=True,
    )
    start_time = models.DateTimeField(_("Start Time"), default=timezone.now)
    end_time = models.DateTimeField(_("End Time"), null=True, blank=True)
    score_percentage = models.FloatField(_("Score Percentage"), null=True, blank=True)
    score_verbal = models.FloatField(_("Verbal Score"), null=True, blank=True)
    score_quantitative = models.FloatField(
        _("Quantitative Score"), null=True, blank=True
    )
    # Store detailed results breakdown (e.g., score per subsection/skill)
    results_summary = models.JSONField(_("Results Summary"), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Test Attempt")
        verbose_name_plural = _("User Test Attempts")
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["user", "test_definition"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.test_definition.name if self.test_definition else 'Custom Test'} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def calculate_scores(self):
        """
        Calculates scores based on associated UserQuestionAttempts.
        Updates score fields and results_summary.
        Should be called upon submission.
        """
        attempts = self.question_attempts.all().select_related(
            "question__subsection__section", "question__skill"
        )
        total_questions = attempts.count()
        if total_questions == 0:
            self.score_percentage = 0.0
            self.score_verbal = 0.0
            self.score_quantitative = 0.0
            self.results_summary = {}
            return

        correct_count = attempts.filter(is_correct=True).count()
        self.score_percentage = (
            (correct_count / total_questions) * 100 if total_questions > 0 else 0.0
        )

        # Calculate section scores
        section_summary = {}
        subsection_summary = {}
        skill_summary = {}

        for section in LearningSection.objects.all():
            section_attempts = attempts.filter(question__subsection__section=section)
            section_total = section_attempts.count()
            section_correct = section_attempts.filter(is_correct=True).count()
            section_score = (
                (section_correct / section_total) * 100 if section_total > 0 else 0.0
            )
            section_summary[section.slug] = {
                "name": section.name,
                "correct": section_correct,
                "total": section_total,
                "score": round(section_score, 2),
            }
            if section.slug == "verbal":
                self.score_verbal = round(section_score, 2)
            elif section.slug == "quantitative":
                self.score_quantitative = round(section_score, 2)

        # Calculate subsection scores
        for subsection in LearningSubSection.objects.filter(
            question__in=attempts.values_list("question", flat=True)
        ).distinct():
            subsection_attempts = attempts.filter(question__subsection=subsection)
            subsection_total = subsection_attempts.count()
            subsection_correct = subsection_attempts.filter(is_correct=True).count()
            subsection_score = (
                (subsection_correct / subsection_total) * 100
                if subsection_total > 0
                else 0.0
            )
            subsection_summary[subsection.slug] = {
                "name": subsection.name,
                "section": subsection.section.slug,
                "correct": subsection_correct,
                "total": subsection_total,
                "score": round(subsection_score, 2),
            }

        # Calculate skill scores (optional, can be intensive)
        for skill in Skill.objects.filter(
            question__in=attempts.values_list("question", flat=True)
        ).distinct():
            skill_attempts = attempts.filter(question__skill=skill)
            skill_total = skill_attempts.count()
            skill_correct = skill_attempts.filter(is_correct=True).count()
            skill_score = (
                (skill_correct / skill_total) * 100 if skill_total > 0 else 0.0
            )
            skill_summary[skill.slug] = {
                "name": skill.name,
                "subsection": skill.subsection.slug,
                "correct": skill_correct,
                "total": skill_total,
                "score": round(skill_score, 2),
            }

        self.results_summary = {
            "overall": {
                "correct": correct_count,
                "total": total_questions,
                "score": round(self.score_percentage, 2),
            },
            "by_section": section_summary,
            "by_subsection": subsection_summary,
            "by_skill": skill_summary,
        }
        self.status = self.Status.COMPLETED
        self.end_time = timezone.now()
        # Consider calling save() here or letting the view handle it


class UserQuestionAttempt(models.Model):
    """
    Records every instance a user attempts to answer a question,
    including the context (test, practice, challenge, etc.).
    """

    class Mode(models.TextChoices):
        TRADITIONAL = "traditional", _("Traditional Learning")
        TEST = "test", _("Test")  # Includes Level Assessment, Practice, Simulation
        EMERGENCY = "emergency", _("Emergency Mode")
        CONVERSATION = "conversation", _("Conversational Learning")
        CHALLENGE = "challenge", _("Challenge")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("User"),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,  # Or PROTECT if attempts should prevent question deletion
        related_name="user_attempts",
        verbose_name=_("Question"),
    )
    # Link to the specific test session, if applicable
    test_attempt = models.ForeignKey(
        UserTestAttempt,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        null=True,
        blank=True,
        verbose_name=_("Test Attempt"),
    )
    # challenge_attempt = models.ForeignKey(...) # Add FK when Challenge model exists

    selected_answer = models.CharField(
        _("Selected Answer"),
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
    )
    is_correct = models.BooleanField(_("Is Correct"))
    time_taken_seconds = models.PositiveIntegerField(
        _("Time Taken (seconds)"), null=True, blank=True
    )
    used_hint = models.BooleanField(_("Used Hint"), default=False)
    used_elimination = models.BooleanField(_("Used Elimination"), default=False)
    used_solution_method = models.BooleanField(_("Used Solution Method"), default=False)
    mode = models.CharField(
        _("Attempt Mode"), max_length=20, choices=Mode.choices, db_index=True
    )
    attempted_at = models.DateTimeField(
        _("Attempted At"), default=timezone.now, db_index=True
    )

    class Meta:
        verbose_name = _("User Question Attempt")
        verbose_name_plural = _("User Question Attempts")
        ordering = ["-attempted_at"]
        indexes = [
            models.Index(fields=["user", "question"]),
            models.Index(fields=["user", "mode"]),
            models.Index(fields=["test_attempt"]),
        ]

    def __str__(self):
        return f"{self.user.username} - Q{self.question_id} - {self.selected_answer} ({'Correct' if self.is_correct else 'Incorrect'})"

    def save(self, *args, **kwargs):
        # Ensure is_correct is set based on selected_answer
        self.is_correct = self.selected_answer == self.question.correct_answer
        super().save(*args, **kwargs)
        # Consider triggering proficiency update here or via a signal/task
        # self.update_skill_proficiency() # See below


class UserSkillProficiency(models.Model):
    """
    Stores a calculated proficiency score for a user on a specific skill.
    Updated periodically based on UserQuestionAttempt data.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_proficiencies",
        verbose_name=_("User"),
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="user_proficiencies",
        verbose_name=_("Skill"),
    )
    # A score from 0.0 to 1.0, could use more complex ELO/IRT later
    proficiency_score = models.FloatField(_("Proficiency Score"), default=0.0)
    attempts_count = models.PositiveIntegerField(_("Attempts Count"), default=0)
    correct_count = models.PositiveIntegerField(_("Correct Count"), default=0)
    last_calculated_at = models.DateTimeField(_("Last Calculated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Skill Proficiency")
        verbose_name_plural = _("User Skill Proficiencies")
        unique_together = ("user", "skill")  # Only one record per user per skill
        ordering = ["user", "skill"]
        indexes = [
            models.Index(fields=["user", "skill"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.skill.name}: {self.proficiency_score:.2f}"

    def update_proficiency(self, is_correct):
        """
        Simple update based on a new attempt. Increments counts and recalculates score.
        More sophisticated algorithms (like moving average, ELO) could be used here.
        """
        self.attempts_count += 1
        if is_correct:
            self.correct_count += 1

        if self.attempts_count > 0:
            # Simple percentage correct
            self.proficiency_score = self.correct_count / self.attempts_count
            # Could add smoothing: e.g., Bayesian average with prior
            # prior_strength = 5
            # prior_mean = 0.5
            # self.proficiency_score = (self.correct_count + prior_strength * prior_mean) / (self.attempts_count + prior_strength)

        self.save()


# --- Utility function/method potentially called by UserQuestionAttempt save/signal ---
def update_skill_proficiency_for_attempt(attempt: UserQuestionAttempt):
    """Updates the UserSkillProficiency based on a UserQuestionAttempt."""
    if not attempt.question.skill:
        return  # No skill associated with the question

    proficiency, created = UserSkillProficiency.objects.get_or_create(
        user=attempt.user, skill=attempt.question.skill
    )

    # Recalculate based on ALL attempts for that skill for accuracy,
    # or use the incremental update method in the model.
    # Using recalculation here for simplicity, but can be less performant.
    all_skill_attempts = UserQuestionAttempt.objects.filter(
        user=attempt.user, question__skill=attempt.question.skill
    )
    total_attempts = all_skill_attempts.count()
    correct_attempts = all_skill_attempts.filter(is_correct=True).count()

    proficiency.attempts_count = total_attempts
    proficiency.correct_count = correct_attempts
    if total_attempts > 0:
        proficiency.proficiency_score = correct_attempts / total_attempts
    else:
        proficiency.proficiency_score = 0.0

    proficiency.save()
