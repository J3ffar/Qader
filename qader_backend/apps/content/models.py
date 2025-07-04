from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class TimeStampedModel(models.Model):
    """Abstract base model for created_at and updated_at fields."""

    created_at = models.DateTimeField(
        _("Created At"), blank=True, null=True, auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Updated At"), blank=True, null=True, auto_now=True
    )

    class Meta:
        abstract = True


class Page(TimeStampedModel):
    """Stores content for static pages like Terms, Story, etc."""

    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=100,
        help_text=_(
            "Unique identifier for the page/content (e.g., 'our-story'). Used in URLs."
        ),
    )
    title = models.CharField(_("Title"), max_length=200)
    content = models.TextField(
        _("Content (Simple/Legacy)"),
        blank=True,
        null=True,
        help_text=_(
            "For simple HTML content. Use 'Structured Content' for modern, template-based pages."
        ),
    )
    content_structured = models.JSONField(
        _("Structured Content (Template-based)"),
        blank=True,
        null=True,
        help_text=_(
            "Key-value JSON for template-based pages. E.g., {'hero_title': {'value': '...'}}"
        ),
    )
    icon_class = models.CharField(
        _("Icon Class"), max_length=100, blank=True, null=True
    )
    is_published = models.BooleanField(_("Is Published"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Page")
        verbose_name_plural = _("Pages")
        ordering = ["title"]

    def __str__(self):
        return self.title


class ContentImage(TimeStampedModel):
    """
    Stores images that can be embedded into dynamic content pages.
    Can be associated with a specific Page or be part of a general media library.
    """

    page = models.ForeignKey(
        Page,
        related_name="images",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Associated Page"),
        help_text=_(
            "The page this image is primarily used on. Leave blank for general use."
        ),
    )
    slug = models.SlugField(
        _("Image Slug"),
        max_length=100,
        unique=True,
        help_text=_(
            "A unique identifier for the image (e.g., 'our-story-hero'). Auto-generated if left blank."
        ),
        blank=True,
    )
    name = models.CharField(
        _("Image Name"),
        max_length=255,
        help_text=_(
            "An internal name for organizing images (e.g., 'Our Story Hero Image')."
        ),
    )
    image = models.ImageField(
        _("Image File"),
        upload_to="content_images/%Y/%m/",
        help_text=_("Upload the image file."),
        blank=True,
        null=True,
    )
    alt_text = models.CharField(
        _("Alt Text"),
        max_length=255,
        blank=True,
        help_text=_("Descriptive text for accessibility (SEO)."),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="content_images",
    )

    class Meta:
        verbose_name = _("Content Image")
        verbose_name_plural = _("Content Images")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "image"
            unique_slug = base_slug
            num = 1
            while ContentImage.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FAQCategory(TimeStampedModel):
    """Categorizes FAQ items."""

    name = models.CharField(_("Name"), max_length=100, unique=True)
    order = models.PositiveIntegerField(
        _("Display Order"), default=0, help_text=_("Order in which categories appear.")
    )

    class Meta:
        verbose_name = _("FAQ Category")
        verbose_name_plural = _("FAQ Categories")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class FAQItem(TimeStampedModel):
    """Stores individual Frequently Asked Questions and their answers."""

    category = models.ForeignKey(
        FAQCategory,
        related_name="items",
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
    )
    question = models.TextField(_("Question"))
    answer = models.TextField(_("Answer"))
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)
    order = models.PositiveIntegerField(
        _("Display Order"), default=0, help_text=_("Order within the category.")
    )

    class Meta:
        verbose_name = _("FAQ Item")
        verbose_name_plural = _("FAQ Items")
        ordering = ["category__order", "category__name", "order", "question"]

    def __str__(self):
        return self.question[:80]


class PartnerCategory(TimeStampedModel):
    """Stores information about success partner categories."""

    name = models.CharField(_("Name"), max_length=150, unique=True)
    description = models.TextField(
        _("Description"), help_text=_("Description displayed on the card.")
    )
    icon_svg_or_class = models.CharField(
        _("Icon SVG or Class"), max_length=255, blank=True, null=True
    )
    google_form_link = models.URLField(_("Google Form Link"), max_length=500)
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Partner Category")
        verbose_name_plural = _("Partner Categories")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ContactMessage(TimeStampedModel):
    """Stores messages submitted through the Contact Us form."""

    STATUS_NEW = "new"
    STATUS_READ = "read"
    STATUS_REPLIED = "replied"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_NEW, _("New")),
        (STATUS_READ, _("Read")),
        (STATUS_REPLIED, _("Replied")),
        (STATUS_ARCHIVED, _("Archived")),
    ]
    full_name = models.CharField(_("Full Name"), max_length=150)
    email = models.EmailField(_("Email"))
    subject = models.CharField(_("Subject"), max_length=200)
    message = models.TextField(_("Message"))
    attachment = models.FileField(
        _("Attachment"), upload_to="contact_attachments/%Y/%m/", blank=True, null=True
    )
    status = models.CharField(
        _("Status"),
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True,
    )
    responder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="responded_messages",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Responder"),
    )
    response = models.TextField(_("Response"), blank=True, null=True)
    responded_at = models.DateTimeField(_("Responded At"), blank=True, null=True)

    class Meta:
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Message from {self.full_name} ({self.subject})"


class HomepageFeatureCard(TimeStampedModel):
    """Configurable 'Why Choose Us' cards for the homepage."""

    title = models.CharField(_("Title"), max_length=100)
    text = models.TextField(_("Text"))
    svg_image = models.TextField(_("SVG Image Code"), blank=True, null=True)
    icon_class = models.CharField(
        _("Icon Class"), max_length=100, blank=True, null=True
    )
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Homepage Feature Card")
        verbose_name_plural = _("Homepage Feature Cards")
        ordering = ["order"]

    def __str__(self):
        return self.title


class HomepageStatistic(TimeStampedModel):
    """Configurable key statistics displayed on the homepage."""

    label = models.CharField(_("Label"), max_length=100)
    value = models.CharField(_("Value"), max_length=50)
    icon_class = models.CharField(
        _("Icon Class"), max_length=100, blank=True, null=True
    )
    order = models.PositiveIntegerField(_("Display Order"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Homepage Statistic")
        verbose_name_plural = _("Homepage Statistics")
        ordering = ["order"]

    def __str__(self):
        return f"{self.label}: {self.value}"
