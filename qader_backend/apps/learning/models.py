from django.conf import settings
from django.core.exceptions import ValidationError  # NEW
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.db.models import Exists, OuterRef

# --- Abstract Base Models ---


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TestType(TimeStampedModel):
    """
    Represents the highest-level category for all content (e.g., General Aptitude, SAT).
    """

    class TestTypeStatus(models.TextChoices):
        ACTIVE = "active", _("Active")
        COMING_SOON = "coming_soon", _("Coming Soon")

    name: str = models.CharField(
        _("Name"),
        max_length=100,
        unique=True,
        help_text=_("The primary name of the test type (e.g., General Aptitude)."),
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
        help_text=_("Optional description of the test type."),
    )
    status: str = models.CharField(
        _("Status"),
        max_length=20,
        choices=TestTypeStatus.choices,
        default=TestTypeStatus.ACTIVE,
        db_index=True,
        help_text=_("Controls visibility for users ('Coming Soon' or 'Active')."),
    )
    order: int = models.PositiveIntegerField(
        _("Order"),
        default=0,
        help_text=_("Determines the display order in lists."),
    )

    class Meta:
        verbose_name = _("Test Type")
        verbose_name_plural = _("Test Types")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# --- Main Learning Structure Models ---


class LearningSection(TimeStampedModel):
    """
    Represents the main branches of study (e.g., Verbal, Quantitative),
    now linked to a specific TestType.
    """

    test_type: TestType = models.ForeignKey(
        TestType,
        related_name="learning_sections",
        on_delete=models.PROTECT,  # Prevent deleting a TestType if sections are linked
        verbose_name=_("Test Type"),
        help_text=_("The parent Test Type this section belongs to."),
        null=True,
        blank=True,
    )
    name: str = models.CharField(
        _("Name"), max_length=100, help_text=_("e.g., Verbal Section")
    )
    slug: str = models.SlugField(_("Slug"), max_length=120, unique=True, blank=True)
    description: str | None = models.TextField(_("Description"), blank=True, null=True)
    order: int = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Learning Section")
        verbose_name_plural = _("Learning Sections")
        ordering = [
            "test_type__order",
            "order",
            "name",
        ]  # MODIFIED: Order by parent first
        unique_together = (
            "test_type",
            "name",
        )  # MODIFIED: Name must be unique within a TestType

    def __str__(self) -> str:
        test_type_name = self.test_type.name if self.test_type else "(Inactive)"
        return f"{test_type_name} - {self.name}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(f"{self.test_type.slug}-{self.name}")
        super().save(*args, **kwargs)


class LearningSubSection(TimeStampedModel):
    """
    Represents categories within a main section (e.g., Reading Comprehension within Verbal).
    """

    section: LearningSection = models.ForeignKey(
        LearningSection,
        related_name="subsections",
        on_delete=models.CASCADE,
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
    is_active: bool = models.BooleanField(
        _("Active Status"),
        default=True,
        db_index=True,
        help_text=_(
            "Designates whether this sub-section is active and should be used in question selections, filters, etc."
        ),
    )

    class Meta:
        verbose_name = _("Learning Sub-Section")
        verbose_name_plural = _("Learning Sub-Sections")
        ordering = ["section__order", "order", "name"]
        unique_together = ("section", "name")

    def __str__(self) -> str:
        status = "" if self.is_active else " (Inactive)"
        return f"{self.section} - {self.name}{status}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base_slug = slugify(f"{self.section.slug}-{self.name}")
            self.slug = base_slug
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
    Represents specific skills. Can be linked directly to a Section
    or more granularly to a Sub-Section.
    """

    section: LearningSection = models.ForeignKey(
        LearningSection,
        related_name="skills",
        on_delete=models.CASCADE,
        verbose_name=_("Parent Section"),
        help_text=_("The parent Learning Section this skill belongs to."),
        null=True,
        blank=True,
    )
    subsection: LearningSubSection | None = models.ForeignKey(
        LearningSubSection,
        related_name="skills",
        on_delete=models.CASCADE,
        verbose_name=_("Sub-Section (Optional)"),
        null=True,
        blank=True,
        help_text=_("Optionally refine the skill's category to a sub-section."),
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
        ordering = ["section__order", "subsection__order", "name"]
        unique_together = (
            ("section", "subsection", "name"),
        )  # MODIFIED unique constraint

    def __str__(self) -> str:
        status = "" if self.is_active else " (Inactive)"
        parent = self.subsection if self.subsection else self.section
        if parent:
            return f"{parent} - {self.name}{status}"
        return f"{self.name}{status}"

    def clean(self):
        """Ensure subsection belongs to the parent section."""
        super().clean()
        if self.subsection and self.subsection.section != self.section:
            raise ValidationError(
                _("The selected Sub-Section does not belong to the selected Section.")
            )

    def save(self, *args, **kwargs) -> None:
        # Run validation before saving
        self.clean()
        if not self.slug:
            parent_slug = ""
            if self.subsection:
                parent_slug = self.subsection.slug
            elif self.section:
                parent_slug = self.section.slug
            base_slug = slugify(f"{parent_slug}-{self.name}")
            self.slug = base_slug
            num = 1
            while Skill.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{num}"
                num += 1
        super().save(*args, **kwargs)


# --- Question Model ---


class QuestionQuerySet(models.QuerySet):
    def with_user_annotations(self, user):
        if not user or not user.is_authenticated:
            return self.annotate(
                user_has_starred=models.Value(False, output_field=models.BooleanField())
            )
        starred_subquery = UserStarredQuestion.objects.filter(
            user=user, question_id=OuterRef("pk")
        )
        return self.annotate(user_has_starred=Exists(starred_subquery))


# --- NEW: Reusable Content Library Models (Requirement Fulfillment) ---

class MediaFile(TimeStampedModel):
    """
    A central library for all reusable media files (images, audio, video).
    """
    class FileType(models.TextChoices):
        IMAGE = 'image', _('Image')
        AUDIO = 'audio', _('Audio')
        VIDEO = 'video', _('Video')

    title = models.CharField(
        _("Title/Name"),
        max_length=200,
        help_text=_("A descriptive name for internal use (e.g., 'Pythagorean Theorem Diagram').")
    )
    file = models.FileField(
        _("File"),
        upload_to="media_library/",
        help_text=_("The actual uploaded image, audio, or video file.")
    )
    file_type = models.CharField(
        _("File Type"),
        max_length=10,
        choices=FileType.choices,
        help_text=_("The type of media file, used by the frontend for rendering.")
    )

    class Meta:
        verbose_name = _("Media File")
        verbose_name_plural = _("Media Files")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Article(TimeStampedModel):
    """
    A central library for all reusable articles or passages.
    """
    title = models.CharField(
        _("Title"),
        max_length=255,
        unique=True,
        help_text=_("The unique title of the article or passage.")
    )
    content = models.TextField(
        _("Content"),
        help_text=_("The full text content of the article.")
    )

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")
        ordering = ['title']

    def __str__(self):
        return self.title


# --- MODIFIED: Question Model ---

class Question(TimeStampedModel):
    """
    Stores individual questions, now linked to reusable content.
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
        on_delete=models.PROTECT,
        verbose_name=_("Sub-Section"),
        db_index=True,
    )
    # --- THIS IS THE KEY CHANGE ---
    # REMOVED: The old ForeignKey to Skill
    # skill: Skill | None = models.ForeignKey(...) 

    # ADDED: The new ManyToManyField
    skills = models.ManyToManyField(
        Skill,
        related_name="questions",
        blank=True, # A question can have zero skills
        verbose_name=_("Skills"),
        help_text=_("The skills tested by this question.")
    )
    question_text: str = models.TextField(_("Question Text"))
    
    # --- REPLACED Fields with ForeignKeys to Libraries ---
    # REMOVED: image, article_title, article_content, audio_file
    
    media_content = models.ForeignKey(
        MediaFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
        verbose_name=_("Media Content (Image/Audio/Video)"),
        help_text=_("Link to a media file from the library. Leave blank if not needed.")
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions",
        verbose_name=_("Article/Passage"),
        help_text=_("Link to an article from the library. Leave blank if not needed.")
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

    objects = QuestionQuerySet.as_manager()
    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["subsection", "id"] # ordering by skill is no longer practical

    def __str__(self) -> str:
        limit = 80
        truncated_text = f"{self.question_text[:limit]}..." if len(self.question_text) > limit else self.question_text
        return f"Q{self.id}: {truncated_text}"
    
    def clean(self):
        """
        Enforce the business rule: a question can have media OR an article, but not both.
        """
        super().clean()
        if self.media_content and self.article:
            raise ValidationError(
                _("A question cannot have both Media Content (Image/Audio/Video) and an Article. Please choose one.")
            )


# --- Intermediate Model for Starred Questions ---


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
    starred_at = models.DateTimeField(
        _("Starred At"), auto_now_add=True, editable=False
    )

    class Meta:
        verbose_name = _("User Starred Question")
        verbose_name_plural = _("User Starred Questions")
        unique_together = (
            "user",
            "question",
        )
        ordering = ["-starred_at"]

    def __str__(self) -> str:
        return f"{self.user.username} starred Question {self.question_id}"
