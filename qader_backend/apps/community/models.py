from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager

from apps.learning.models import LearningSection  # Assuming LearningSection exists


class CommunityPost(models.Model):
    """Represents a post in the student community forum."""

    class PostType(models.TextChoices):
        DISCUSSION = "discussion", _("Study Discussion")
        ACHIEVEMENT = "achievement", _("Achievement")
        PARTNER_SEARCH = "partner_search", _("Find Study Partners")
        TIP = "tip", _("Tips & Experiences")
        COMPETITION = "competition", _(
            "Monthly Competition"
        )  # Added based on description

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
        verbose_name=_("Author"),
    )
    post_type = models.CharField(
        _("Post Type"), max_length=20, choices=PostType.choices, db_index=True
    )
    section_filter = models.ForeignKey(
        LearningSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="community_posts",
        verbose_name=_("Section Filter"),
        help_text=_("Optional filter by main learning section (e.g., Quant, Verbal)"),
    )
    title = models.CharField(
        _("Title"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Optional title for the post"),
    )
    content = models.TextField(_("Content"))
    is_pinned = models.BooleanField(
        _("Is Pinned"),
        default=False,
        help_text=_("Pinned posts appear at the top (Admin only)"),
    )
    is_closed = models.BooleanField(
        _("Is Closed"),
        default=False,
        help_text=_("Prevents further replies (Admin only)"),
    )
    tags = TaggableManager(blank=True, verbose_name=_("Tags"))

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Community Post")
        verbose_name_plural = _("Community Posts")
        ordering = ["-is_pinned", "-created_at"]  # Pinned first, then newest

    def __str__(self):
        return (
            f"{self.get_post_type_display()} post by {self.author.username} ({self.id})"
        )

    @property
    def reply_count(self):
        # Efficient way to get count if not annotated
        return self.replies.count()

    @property
    def content_excerpt(self, length=150):
        if len(self.content) > length:
            return self.content[:length] + "..."
        return self.content


class CommunityReply(models.Model):
    """Represents a reply to a community post or another reply."""

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name=_("Post"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_replies",
        verbose_name=_("Author"),
    )
    content = models.TextField(_("Content"))
    parent_reply = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_replies",
        verbose_name=_("Parent Reply"),
        help_text=_("Links to the reply being responded to for threading"),
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Community Reply")
        verbose_name_plural = _("Community Replies")
        ordering = ["created_at"]  # Oldest replies first in a thread

    def __str__(self):
        return f"Reply by {self.author.username} on post {self.post.id}"

    @property
    def child_replies_count(self):
        return self.child_replies.count()
