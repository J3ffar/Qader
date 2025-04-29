from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from taggit.managers import TaggableManager
from django.utils.html import strip_tags
from django.template.defaultfilters import truncatewords_html

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
        blank=True,  # Allow posts without a specific user author (e.g., "Admin Team")
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
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Blog Post")
        verbose_name_plural = _("Blog Posts")
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_excerpt(self, words=30) -> str:  # Should just be 'def', not '@property'
        """Generates a short plain text excerpt from the content."""
        return truncatewords_html(strip_tags(self.content or ""), words)

    @property
    def author_display_name(self) -> str:
        """Returns the author's preferred name or username, or a default."""
        if self.author:
            # Check if the related profile exists
            if hasattr(self.author, "profile") and self.author.profile:
                return self.author.profile.preferred_name or self.author.username
            return self.author.username
        return _("Qader Team")  # Default if no author assigned

    def save(self, *args, **kwargs):
        # Auto-populate slug from title if empty
        if not self.slug and self.title:
            from django.utils.text import slugify

            self.slug = slugify(self.title)[:255]
            # Ensure uniqueness
            original_slug = self.slug
            counter = 1
            while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"[:255]
                counter += 1

        # Set published_at when status changes to published
        if self.status == PostStatusChoices.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        # Clear published_at if status changes away from published (optional behavior)
        # elif self.status != PostStatusChoices.PUBLISHED and self.published_at:
        #     self.published_at = None

        super().save(*args, **kwargs)


class BlogAdviceRequest(models.Model):
    """Stores requests from users for specific advice."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("User"),
        on_delete=models.CASCADE,  # If user is deleted, their requests are too
        related_name="advice_requests",
        help_text=_("The user requesting advice."),
    )
    problem_type = models.CharField(
        _("Problem Type/Topic"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Type of problem or topic user needs advice on."),
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
    # Use string imports to avoid direct dependency/circular issues
    related_support_ticket = models.ForeignKey(
        "support.SupportTicket",  # String reference
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
        return f"Advice request from {self.user.username} ({self.get_status_display()})"
