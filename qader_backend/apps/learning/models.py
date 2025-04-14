from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


# Consider adding shared timestamp model in core app later
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LearningSection(TimeStampedModel):
    """Represents the main branches of study (e.g., Verbal, Quantitative)."""

    name = models.CharField(_("Name"), max_length=100, unique=True)
    slug = models.SlugField(
        _("Slug"),
        max_length=120,
        unique=True,
        blank=True,
        help_text=_("URL-friendly identifier (leave blank to auto-generate)"),
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    order = models.PositiveIntegerField(
        _("Order"), default=0, help_text=_("Display order in UI")
    )

    class Meta:
        verbose_name = _("Learning Section")
        verbose_name_plural = _("Learning Sections")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class LearningSubSection(TimeStampedModel):
    """Represents categories within a main section (e.g., Reading Comprehension)."""

    section = models.ForeignKey(
        LearningSection,
        related_name="subsections",
        on_delete=models.CASCADE,
        verbose_name=_("Section"),
    )
    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(
        _("Slug"),
        max_length=170,
        unique=True,
        blank=True,
        help_text=_("URL-friendly identifier (leave blank to auto-generate)"),
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    order = models.PositiveIntegerField(
        _("Order"), default=0, help_text=_("Display order in UI")
    )

    class Meta:
        verbose_name = _("Learning Sub-Section")
        verbose_name_plural = _("Learning Sub-Sections")
        ordering = ["section__order", "order", "name"]
        unique_together = ("section", "name")  # Name must be unique within a section

    def __str__(self):
        return f"{self.section.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.section.slug}-{self.name}")
        super().save(*args, **kwargs)


class Skill(TimeStampedModel):
    """Represents specific skills tested within a subsection."""

    subsection = models.ForeignKey(
        LearningSubSection,
        related_name="skills",
        on_delete=models.CASCADE,
        verbose_name=_("Sub-Section"),
    )
    name = models.CharField(_("Name"), max_length=200)
    slug = models.SlugField(
        _("Slug"),
        max_length=220,
        unique=True,
        blank=True,
        help_text=_("URL-friendly identifier (leave blank to auto-generate)"),
    )
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["subsection__section__order", "subsection__order", "name"]
        unique_together = (
            "subsection",
            "name",
        )  # Name must be unique within a subsection

    def __str__(self):
        return f"{self.subsection} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.subsection.slug}-{self.name}")
        super().save(*args, **kwargs)


class Question(TimeStampedModel):
    """Stores individual practice or test questions."""

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

    subsection = models.ForeignKey(
        LearningSubSection,
        related_name="questions",
        on_delete=models.PROTECT,  # Prevent deleting subsection if questions exist
        verbose_name=_("Sub-Section"),
        db_index=True,
    )
    skill = models.ForeignKey(
        Skill,
        related_name="questions",
        on_delete=models.SET_NULL,  # Allow skill to be removed without deleting question
        null=True,
        blank=True,
        verbose_name=_("Primary Skill"),
        db_index=True,
    )
    question_text = models.TextField(_("Question Text"))
    option_a = models.TextField(_("Option A"))
    option_b = models.TextField(_("Option B"))
    option_c = models.TextField(_("Option C"))
    option_d = models.TextField(_("Option D"))
    correct_answer = models.CharField(
        _("Correct Answer"), max_length=1, choices=CorrectAnswerChoices.choices
    )
    explanation = models.TextField(_("Explanation"), blank=True, null=True)
    hint = models.TextField(_("Hint"), blank=True, null=True)
    solution_method_summary = models.TextField(
        _("Solution Method Summary"), blank=True, null=True
    )
    difficulty = models.IntegerField(
        _("Difficulty"), choices=DifficultyLevel.choices, default=DifficultyLevel.MEDIUM
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether the question should be used in the platform"),
        db_index=True,
    )
    # ManyToMany relationship for starred questions defined below

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["subsection", "skill", "id"]  # Default ordering

    def __str__(self):
        # Truncate long question text for display
        return f"({self.id}) {self.question_text[:80]}{'...' if len(self.question_text) > 80 else ''}"


class UserStarredQuestion(TimeStampedModel):
    """Links users to questions they have starred/bookmarked."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="starred_questions_link",
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="starrers_link"
    )
    starred_at = models.DateTimeField(_("Starred At"), auto_now_add=True)

    class Meta:
        verbose_name = _("User Starred Question")
        verbose_name_plural = _("User Starred Questions")
        unique_together = (
            "user",
            "question",
        )  # Ensure a user can only star a question once
        ordering = ["-starred_at"]

    def __str__(self):
        return f"{self.user.username} starred Question {self.question.id}"


# Add a ManyToMany field to User model (implicitly via UserStarredQuestion)
# Or add related_name to Question for easier access (optional but helpful):
Question.add_to_class(
    "starred_by",
    models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through=UserStarredQuestion,
        related_name="starred_questions",
        verbose_name=_("Starred By Users"),
        blank=True,
    ),
)
