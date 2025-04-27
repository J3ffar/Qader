from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

# --- Abstract Base Models ---


# Consider moving TimeStampedModel to a shared 'common' or 'core' app if used elsewhere.
class TimeStampedModel(models.Model):
    """Abstract base model with auto-updating created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# --- Main Learning Structure Models ---


class LearningSection(TimeStampedModel):
    """
    Represents the main branches of study (e.g., Verbal, Quantitative).
    Accessible via API: /api/v1/learning/sections/
    """

    name: str = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        help_text=_("The primary name of the learning section (e.g., Verbal Section)."),
    )
    slug: str = models.SlugField(
        _("Slug"),
        max_length=120,
        unique=True,
        blank=True,
        help_text=_(
            "URL-friendly identifier (leave blank to auto-generate from name)."
        ),
    )
    description: str | None = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Optional description of the learning section."),
    )
    order: int = models.PositiveIntegerField(
        _("Order"),
        default=0,
        help_text=_(
            "Determines the display order in lists (lower numbers appear first)."
        ),
    )

    class Meta:
        verbose_name = _("Learning Section")
        verbose_name_plural = _("Learning Sections")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        """Overrides save method to auto-generate slug if blank."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class LearningSubSection(TimeStampedModel):
    """
    Represents categories within a main section (e.g., Reading Comprehension within Verbal).
    Accessible via API: /api/v1/learning/subsections/
    """

    section: LearningSection = models.ForeignKey(
        LearningSection,
        related_name="subsections",
        on_delete=models.CASCADE,  # Deleting a Section also deletes its SubSections
        verbose_name=_("Section"),
        help_text=_("The parent Learning Section this sub-section belongs to."),
    )
    name: str = models.CharField(
        _("Name"),
        max_length=150,
        help_text=_("The name of the sub-section (e.g., Reading Comprehension)."),
    )
    slug: str = models.SlugField(
        _("Slug"),
        max_length=170,
        unique=True,
        blank=True,
        help_text=_(
            "URL-friendly identifier (leave blank to auto-generate from section and name)."
        ),
    )
    description: str | None = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Optional description of the learning sub-section."),
    )
    order: int = models.PositiveIntegerField(
        _("Order"),
        default=0,
        help_text=_(
            "Determines the display order within its parent section (lower numbers first)."
        ),
    )

    class Meta:
        verbose_name = _("Learning Sub-Section")
        verbose_name_plural = _("Learning Sub-Sections")
        ordering = ["section__order", "order", "name"]
        unique_together = ("section", "name")  # Name must be unique within a section

    def __str__(self) -> str:
        return f"{self.section.name} - {self.name}"

    def save(self, *args, **kwargs) -> None:
        """Overrides save method to auto-generate slug if blank."""
        if not self.slug:
            # Ensure uniqueness and clarity in generated slugs
            base_slug = slugify(f"{self.section.slug}-{self.name}")
            self.slug = base_slug
            # Simple uniqueness check (consider more robust slug uniqueness generation if needed)
            num = 1
            while (
                LearningSubSection.objects.filter(slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{base_slug}-{num}"
                num += 1
        super().save(*args, **kwargs)


class Skill(TimeStampedModel):
    """
    Represents specific skills tested within a subsection (e.g., Identifying Main Idea).
    Accessible via API: /api/v1/learning/skills/
    """

    subsection: LearningSubSection = models.ForeignKey(
        LearningSubSection,
        related_name="skills",
        on_delete=models.CASCADE,  # Deleting a SubSection deletes its Skills
        verbose_name=_("Sub-Section"),
        help_text=_("The parent Learning Sub-Section this skill belongs to."),
    )
    name: str = models.CharField(
        _("Name"),
        max_length=200,
        help_text=_("The name of the specific skill (e.g., Solving Linear Equations)."),
    )
    slug: str = models.SlugField(
        _("Slug"),
        max_length=220,
        unique=True,
        blank=True,
        help_text=_(
            "URL-friendly identifier (leave blank to auto-generate from subsection and name)."
        ),
    )
    description: str | None = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Optional description of the skill."),
    )

    is_active: bool = models.BooleanField(
        _("Active Status"),
        default=True,
        db_index=True,
        help_text=_(
            "Designates whether this skill is active and should be used in question selections, filters, etc."
        ),
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["subsection__section__order", "subsection__order", "name"]
        unique_together = (("subsection", "name"),)

    def __str__(self) -> str:
        status = "" if self.is_active else " (Inactive)"
        return f"{self.subsection} - {self.name}{status}"

    def save(self, *args, **kwargs) -> None:
        """Overrides save method to auto-generate slug if blank."""
        if not self.slug:
            subsection_slug = getattr(self.subsection, "slug", "default-sub")
            base_slug = slugify(f"{subsection_slug}-{self.name}")
            self.slug = base_slug
            num = 1
            while Skill.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{num}"
                num += 1
        super().save(*args, **kwargs)


# --- Question Model ---


class Question(TimeStampedModel):
    """
    Stores individual practice or test questions.
    Accessible via API: /api/v1/learning/questions/
    """

    class DifficultyLevel(models.IntegerChoices):
        VERY_EASY = 1, _("Very Easy")
        EASY = 2, _("Easy")
        MEDIUM = 3, _("Medium")
        HARD = 4, _("Hard")
        VERY_HARD = 5, _("Very Hard")

    class CorrectAnswerChoices(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"
        D = "D", "D"

    subsection: LearningSubSection = models.ForeignKey(
        LearningSubSection,
        related_name="questions",
        on_delete=models.PROTECT,  # Prevent deleting subsection if questions exist
        verbose_name=_("Sub-Section"),
        db_index=True,
        help_text=_("The primary sub-section this question belongs to."),
    )
    skill: Skill | None = models.ForeignKey(
        Skill,
        related_name="questions",
        on_delete=models.SET_NULL,  # Allow skill removal without deleting question
        null=True,
        blank=True,
        verbose_name=_("Primary Skill"),
        db_index=True,
        help_text=_("The main skill tested by this question (optional)."),
    )
    question_text: str = models.TextField(
        _("Question Text"),
        help_text=_("The main text or problem statement of the question."),
    )
    option_a: str = models.TextField(_("Option A"))
    option_b: str = models.TextField(_("Option B"))
    option_c: str = models.TextField(_("Option C"))
    option_d: str = models.TextField(_("Option D"))
    correct_answer: str = models.CharField(
        _("Correct Answer"),
        max_length=1,
        choices=CorrectAnswerChoices.choices,
        help_text=_("The letter corresponding to the correct option."),
    )
    explanation: str | None = models.TextField(
        _("Explanation"),
        blank=True,
        null=True,
        help_text=_(
            "Detailed step-by-step explanation for the solution (supports Markdown/HTML)."
        ),
    )
    hint: str | None = models.TextField(
        _("Hint"),
        blank=True,
        null=True,
        help_text=_(
            "A small hint to guide the student without giving away the answer."
        ),
    )
    solution_method_summary: str | None = models.TextField(
        _("Solution Method Summary"),
        blank=True,
        null=True,
        help_text=_(
            "A brief summary of the general strategy or method to solve the question."
        ),
    )
    difficulty: int = models.IntegerField(
        _("Difficulty"),
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        db_index=True,
        help_text=_("Estimated difficulty level of the question."),
    )
    is_active: bool = models.BooleanField(
        _("Is Active"),
        default=True,
        db_index=True,
        help_text=_(
            "Uncheck this to hide the question from students without deleting it."
        ),
    )
    # ManyToMany relationship defined via UserStarredQuestion below
    starred_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserStarredQuestion",
        related_name="starred_questions",
        verbose_name=_("Starred By Users"),
        blank=True,
    )

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["subsection", "skill", "id"]  # Default ordering

    def __str__(self) -> str:
        # Truncate long question text for display in Admin or logs
        limit = 80
        truncated_text = (
            f"{self.question_text[:limit]}..."
            if len(self.question_text) > limit
            else self.question_text
        )
        return f"Q{self.id}: {truncated_text} ({self.subsection.slug})"


# --- Intermediate Model for Starred Questions ---


class UserStarredQuestion(TimeStampedModel):
    """Links users to questions they have starred/bookmarked."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="starred_questions_link",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="starrers_link",
    )
    starred_at = models.DateTimeField(
        _("Starred At"), auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = _("User Starred Question")
        verbose_name_plural = _("User Starred Questions")
        unique_together = (
            "user",
            "question",
        )  # Ensure a user can only star a question once
        ordering = ["-starred_at"]  # Show most recently starred first

    def __str__(self) -> str:
        return f"{self.user.username} starred Question {self.question_id}"
