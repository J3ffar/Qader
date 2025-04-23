from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from apps.learning.models import LearningSection


class CommunityPost(models.Model):
    """
    Represents a post within the student community forum.

    Adheres to SOLID:
    - SRP: Defines the structure and core data of a community post.
    - OCP: Extensible via new PostType choices or adding fields.
    """

    class PostType(models.TextChoices):
        DISCUSSION = "discussion", _("Study Discussion")
        ACHIEVEMENT = "achievement", _("Achievement")
        PARTNER_SEARCH = "partner_search", _("Find Study Partners")
        TIP = "tip", _("Tips & Experiences")
        COMPETITION = "competition", _(
            "Monthly Competition"
        )  # Added based on requirements

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
        verbose_name=_("Author"),
        help_text=_("The user who created this post."),
    )
    post_type = models.CharField(
        _("Post Type"),
        max_length=20,
        choices=PostType.choices,
        db_index=True,  # Indexed for efficient filtering
        help_text=_("The category or purpose of the post."),
    )
    # Use a string reference to avoid potential circular imports
    section_filter = models.ForeignKey(
        "learning.LearningSection",
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
        help_text=_("Optional title for the post."),
    )
    content = models.TextField(
        _("Content"),
        help_text=_("The main body of the post."),
    )
    is_pinned = models.BooleanField(
        _("Is Pinned"),
        default=False,
        db_index=True,  # Indexed for ordering/filtering
        help_text=_("Pinned posts appear at the top (Admin/Moderator action)."),
    )
    is_closed = models.BooleanField(
        _("Is Closed"),
        default=False,
        help_text=_("Prevents further replies (Admin/Moderator action)."),
    )
    # Using TaggableManager adheres to DRY principle for tagging functionality
    tags = TaggableManager(
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Relevant keywords or topics for the post."),
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Community Post")
        verbose_name_plural = _("Community Posts")
        ordering = ["-is_pinned", "-created_at"]  # Pinned first, then newest
        indexes = [
            models.Index(fields=["-created_at"]),  # Explicit index for default ordering
            models.Index(fields=["post_type"]),
        ]

    def __str__(self):
        title_part = f' "{self.title}"' if self.title else ""
        return f"{self.get_post_type_display()}: {title_part} by {self.author.username} ({self.id})"

    @property
    def reply_count(self):
        """
        Calculates the number of direct replies.
        Note: Using annotation in views (`Count('replies')`) is generally more efficient for list views.
        """
        # Consider only top-level replies if that's the definition needed
        # return self.replies.filter(parent_reply__isnull=True).count()
        return self.replies.count()

    @property
    def content_excerpt(self, length=150):
        """Provides a short preview of the content."""
        if len(self.content) > length:
            # Ensure clean cut (avoid cutting mid-word if complex logic needed)
            # For simplicity, just truncate for now.
            return self.content[:length].strip() + "..."
        return self.content


class CommunityReply(models.Model):
    """
    Represents a reply to a community post or another reply (threading).

    Adheres to SOLID:
    - SRP: Defines the structure and data of a reply.
    - OCP: Extensible if replies need types, flags, etc.
    """

    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,  # Replies deleted if post is deleted
        related_name="replies",
        verbose_name=_("Post"),
        help_text=_("The post this reply belongs to."),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,  # Replies deleted if author account is deleted
        related_name="community_replies",
        verbose_name=_("Author"),
        help_text=_("The user who wrote this reply."),
    )
    content = models.TextField(
        _("Content"),
        help_text=_("The body of the reply."),
    )
    parent_reply = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,  # Nested replies deleted if parent is deleted
        null=True,
        blank=True,
        related_name="child_replies",
        verbose_name=_("Parent Reply"),
        help_text=_("Links to the reply being responded to for threading."),
        db_index=True,  # Index for efficiently fetching child replies
    )

    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Community Reply")
        verbose_name_plural = _("Community Replies")
        # Ordering by creation time is standard for conversations
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["post", "created_at"]
            ),  # Index for fetching replies per post
        ]

    def __str__(self):
        return f"Reply by {self.author.username} on Post {self.post.id} ({self.id})"

    @property
    def child_replies_count(self):
        """Calculates the number of direct child replies."""
        return self.child_replies.count()
