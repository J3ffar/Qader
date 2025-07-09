import re
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from taggit.managers import TaggableManager
from django.utils.html import strip_tags
from django.template.defaultfilters import truncatewords_html
from django.utils.text import slugify

# Assuming support and users apps exist as defined in settings
# Import related models cautiously to avoid circular dependencies if possible
# from apps.support.models import SupportTicket


class PostStatusChoices(models.TextChoices):
    DRAFT = "draft", _("Draft")
    PUBLISHED = "published", _("Published")
    ARCHIVED = "archived", _("Archived")


class AdviceRequestStatusChoices(models.TextChoices):
    SUBMITTED = "submitted", _("Submitted")
    UNDER_REVIEW = "under_review", _("Under Review")
    ANSWERED_SUPPORT = "answered_support", _("Answered via Support")
    ANSWERED_NOTIFICATION = "answered_notification", _("Answered via Notification")
    PUBLISHED_AS_POST = "published_as_post", _("Published as Blog Post")
    CLOSED = "closed", _("Closed")


class AdviceResponseViaChoices(models.TextChoices):
    SUPPORT = "support", _("Admin Support Ticket")
    NOTIFICATION = "notification", _("Platform Notification")
    BLOG_POST = "blog_post", _("Published Blog Post")


class BlogPost(models.Model):
    """Stores articles for the Blog section."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Author"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        limit_choices_to={"is_staff": True},
        help_text=_("The staff member who authored this post."),
    )
    title = models.CharField(_("Title"), max_length=255)
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=255,
        db_index=True,
        help_text=_("URL-friendly identifier (auto-generated if left blank)."),
    )
    content = models.TextField(
        _("Content"),
        help_text=_("Main content of the post (supports HTML/Markdown)."),
    )
    image = models.ImageField(
        _("Featured Image"),
        upload_to="blog/images/%Y/%m/",  # Store images in a structured path
        null=True,
        blank=True,
        help_text=_(
            "Optional: A featured image for the blog post. Will be shown in listings and at the top of the post."
        ),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=PostStatusChoices.choices,
        default=PostStatusChoices.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField(
        _("Published At"), null=True, blank=True, db_index=True
    )
    tags = TaggableManager(
        verbose_name=_("Tags"), blank=True, help_text=_("Comma-separated tags.")
    )
    created_at = models.DateTimeField(
        _("Created At"), null=True, blank=True, auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Updated At"), null=True, blank=True, auto_now=True
    )

    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    @property
    def excerpt(
        self,
    ) -> str:
        """Generates a short plain text excerpt from the content."""
        content_str = str(self.content) if self.content is not None else ""
        if not content_str:
            return ""

        # Step 1: Replace block-level tags with a space to preserve separation
        # Add more block tags as needed (e.g., <div>, <blockquote>)
        block_tags = re.compile(
            r"</(p|h1|h2|h3|h4|h5|h6|li|div|blockquote|br|hr)>", re.IGNORECASE
        )
        spaced_content = block_tags.sub(" ", content_str)

        # Step 2: Strip all remaining HTML tags
        plain_text = strip_tags(spaced_content)

        # Step 3: Normalize multiple spaces to single spaces and strip leading/trailing whitespace
        normalized_text = " ".join(plain_text.split())

        # Step 4: Truncate
        # truncatewords_html default is 30 words and it handles HTML entities correctly
        # even though we've stripped tags, it's robust for text.
        return truncatewords_html(normalized_text, 130)

    

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)[:255]
            original_slug = self.slug
            counter = 1
            queryset = BlogPost.objects.filter(slug=self.slug)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)

            while queryset.exists():
                max_len = 255 - len(str(counter)) - 1
                self.slug = f"{original_slug[:max_len]}-{counter}"
                counter += 1
                queryset = BlogPost.objects.filter(slug=self.slug)
                if self.pk:
                    queryset = queryset.exclude(pk=self.pk)

        if self.status == PostStatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)


class BlogAdviceRequest(models.Model):
    """Stores requests from users for specific advice."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="advice_requests",
        help_text=_("The user requesting advice."),
    )
    problem_type = models.CharField(
        _("Problem Type/Topic"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Optional: Type of problem or topic user needs advice on."),
    )
    description = models.TextField(
        _("Description"), help_text=_("Detailed description of the issue/request.")
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=AdviceRequestStatusChoices.choices,
        default=AdviceRequestStatusChoices.SUBMITTED,
        db_index=True,
    )
    response_via = models.CharField(
        _("Response Method"),
        max_length=20,
        choices=AdviceResponseViaChoices.choices,
        null=True,
        blank=True,
        help_text=_("How the user was (or will be) answered."),
    )
    related_support_ticket = models.ForeignKey(
        "support.SupportTicket",
        verbose_name=_("Related Support Ticket"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="advice_requests",
        help_text=_("Link if this request was answered via a support ticket."),
    )
    related_blog_post = models.ForeignKey(
        BlogPost,
        verbose_name=_("Related Blog Post"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_advice_requests",
        help_text=_("Link if this request resulted in a published blog post."),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Blog Advice Request")
        verbose_name_plural = _("Blog Advice Requests")
        ordering = ["-created_at"]

    def __str__(self):
        username = getattr(self.user, "username", "Unknown User")
        return f"Advice request from {username} ({self.get_status_display()})"
