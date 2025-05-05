from django.conf import settings  # Import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.core.validators import MinValueValidator

# User = get_user_model() # This is fine, or use settings.AUTH_USER_MODEL
User = settings.AUTH_USER_MODEL


class PointReason(models.TextChoices):
    """Standardized reason codes for point changes."""

    # Study Related
    QUESTION_SOLVED = "QUESTION_SOLVED", _("Question Solved")
    TEST_COMPLETED = "TEST_COMPLETED", _("Test Completed")
    LEVEL_ASSESSMENT_COMPLETED = "LEVEL_ASSESSMENT_COMPLETED", _(
        "Level Assessment Completed"
    )
    STREAK_BONUS = "STREAK_BONUS", _("Streak Bonus")
    FEATURE_FIRST_USE = "FEATURE_FIRST_USE", _(
        "Feature First Use"
    )  # Generic, specifics in description

    # Challenge Related
    CHALLENGE_PARTICIPATION = "CHALLENGE_PARTICIPATION", _("Challenge Participation")
    CHALLENGE_WIN = "CHALLENGE_WIN", _("Challenge Win")

    # Store & Admin
    REWARD_PURCHASE = "REWARD_PURCHASE", _("Reward Purchase")
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT", _("Admin Adjustment")
    REFERRAL_BONUS = "REFERRAL_BONUS", _("Referral Bonus")

    # Badge Related
    BADGE_EARNED = "BADGE_EARNED", _("Badge Earned")

    # Other/Misc
    OTHER = "OTHER", _("Other")


class PointLog(models.Model):
    """Records every change in a user's points balance."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="point_logs",
        verbose_name=_("User"),
        db_index=True,  # Explicit index on user FK
    )
    points_change = models.IntegerField(verbose_name=_("Points Change"))
    reason_code = models.CharField(
        max_length=50,
        choices=PointReason.choices,
        default=PointReason.OTHER,  # Use default from choices
        db_index=True,
        verbose_name=_("Reason Code"),
        help_text=_("Standardized code indicating the reason for the point change."),
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_(
            "Human-readable explanation, especially for OTHER or specific contexts."
        ),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Object Type"),
        db_index=True,  # Index content_type
    )
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Related Object ID"),
        db_index=True,  # Index object_id
    )
    related_object = GenericForeignKey("content_type", "object_id")

    timestamp = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("Timestamp")
    )

    class Meta:
        verbose_name = _("Point Log")
        verbose_name_plural = _("Point Logs")
        ordering = ["-timestamp"]
        indexes = [  # Explicit index for GenericForeignKey lookups
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        reason_display = self.get_reason_code_display()  # Use display value
        return (
            f"{getattr(self.user, 'username', 'N/A')}: {self.points_change:+} points "
            f"({reason_display}) at {self.timestamp}"
        )


class Badge(models.Model):
    """Defines achievable badges/achievements."""

    class BadgeCriteriaType(models.TextChoices):
        """Defines the type of event or state required to earn the badge."""

        STUDY_STREAK = "STUDY_STREAK", _("Consecutive Study Days")
        QUESTIONS_SOLVED_CORRECTLY = "QUESTIONS_SOLVED", _("Correct Questions Solved")
        TESTS_COMPLETED = "TESTS_COMPLETED", _("Tests Completed (Any Type)")
        # Add more types as needed:
        # CHALLENGES_WON = "CHALLENGES_WON", _("Challenges Won")
        # PROFILE_COMPLETION = "PROFILE_COMPLETION", _("Profile Completion (%)")
        # SPECIFIC_ACTION = "SPECIFIC_ACTION", _("Specific Action Completed") # Needs custom logic tie-in
        OTHER = "OTHER", _("Other / Manual Award")

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(
        unique=True,
        max_length=110,
        verbose_name=_("Slug"),
        help_text=_("Unique identifier used internally and potentially in URLs."),
        db_index=True,
    )
    description = models.TextField(verbose_name=_("Description"))
    icon = models.ImageField(
        upload_to="badges/icons/",  # Store icons in MEDIA_ROOT/badges/icons/
        verbose_name=_("Icon Image"),
        help_text=_("Upload an image file for the badge icon."),
        null=True,
        blank=True,
    )
    criteria_description = models.TextField(
        verbose_name=_("Criteria Description"),
        help_text=_("User-facing text explaining how to earn the badge."),
    )
    criteria_type = models.CharField(
        max_length=50,
        choices=BadgeCriteriaType.choices,
        verbose_name=_("Criteria Type"),
        help_text=_("The type of condition required to earn this badge."),
        db_index=True,
    )
    target_value = models.PositiveIntegerField(
        verbose_name=_("Target Value"),
        help_text=_(
            "The numerical goal for the criteria (e.g., 5 for a 5-day streak, 50 for 50 questions). Not used for 'Other' type."
        ),
        validators=[MinValueValidator(1)],
        null=True,  # Allow null initially or for types not needing it
        blank=True,  # Allow blank in admin
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Inactive badges cannot be earned."),
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Badge")
        verbose_name_plural = _("Badges")
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def icon_preview(self):
        if self.icon:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 40px;" />',
                self.icon.url,
            )
        return _("No icon")


class UserBadge(models.Model):
    """Links users to the badges they have earned."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="earned_badges",
        verbose_name=_("User"),
        db_index=True,  # Explicit index
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="earned_by",
        verbose_name=_("Badge"),
        db_index=True,  # Explicit index
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Earned At"))

    class Meta:
        verbose_name = _("User Badge")
        verbose_name_plural = _("User Badges")
        ordering = ["-earned_at"]
        unique_together = ("user", "badge")  # Implicitly creates a db_index

    def __str__(self):
        return f"{getattr(self.user, 'username', 'N/A')} earned {self.badge.name}"


class RewardStoreItem(models.Model):
    """Defines items available for purchase in the rewards store."""

    class ItemType(models.TextChoices):
        AVATAR = "avatar", _("Avatar/Theme")
        MATERIAL = "material", _("Study Material/Outline")
        COMPETITION_ENTRY = "competition_entry", _("Competition Entry")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=150, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.OTHER,  # Set default here too
        verbose_name=_("Item Type"),
        db_index=True,
    )
    cost_points = models.PositiveIntegerField(verbose_name=_("Cost (Points)"))
    image = models.ImageField(
        upload_to="rewards/images/",
        verbose_name=_("Item Image"),
        help_text=_("Optional visual representation of the reward item."),
        null=True,
        blank=True,
    )
    asset_file = models.FileField(
        upload_to="rewards/assets/",
        verbose_name=_("Asset File"),
        help_text=_(
            "Optional downloadable file associated with the reward (e.g., PDF outline)."
        ),
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=True, db_index=True, verbose_name=_("Is Active")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Reward Store Item")
        verbose_name_plural = _("Reward Store Items")
        ordering = ["item_type", "cost_points", "name"]

    def __str__(self):
        return f"{self.name} ({self.cost_points} points)"

    @property
    def image_preview(self):
        if self.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                self.image.url,
            )
        return _("No image")


class UserRewardPurchase(models.Model):
    """Records instances where a user purchases an item."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reward_purchases",
        verbose_name=_("User"),
        db_index=True,
    )
    item = models.ForeignKey(
        RewardStoreItem,
        on_delete=models.PROTECT,  # Good choice: Protect item def if purchased
        related_name="purchases",
        verbose_name=_("Item"),
    )
    points_spent = models.PositiveIntegerField(verbose_name=_("Points Spent"))
    purchased_at = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("Purchased At")
    )

    class Meta:
        verbose_name = _("User Reward Purchase")
        verbose_name_plural = _("User Reward Purchases")
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"{getattr(self.user, 'username', 'N/A')} purchased {self.item.name} at {self.purchased_at}"


class StudyDayLog(models.Model):
    """Records each unique calendar day a user performs a study activity."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="study_days",
        verbose_name=_("User"),
        db_index=True,
    )
    study_date = models.DateField(
        verbose_name=_("Study Date"),
        db_index=True,
        help_text=_("The calendar date (UTC) of the study activity."),
    )
    # Optional: Add a timestamp if needed, but study_date is the key info
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Logged At"))

    class Meta:
        verbose_name = _("Study Day Log")
        verbose_name_plural = _("Study Day Logs")
        # Ensure a user can only have one entry per day
        unique_together = ("user", "study_date")
        ordering = ["-study_date"]  # Order by most recent date first
        indexes = [
            models.Index(
                fields=["user", "study_date"]
            ),  # Index for unique_together lookup
        ]

    def __str__(self):
        username = getattr(self.user, "username", "N/A")
        return f"{username} studied on {self.study_date.isoformat()}"
