from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class PointLog(models.Model):
    """Records every change in a user's points balance."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="point_logs",
        verbose_name=_("User"),
    )
    points_change = models.IntegerField(verbose_name=_("Points Change"))
    reason_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("Reason Code"),
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    # Generic relation to the object causing the points change
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Object Type"),
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Related Object ID")
    )
    related_object = GenericForeignKey("content_type", "object_id")

    timestamp = models.DateTimeField(
        auto_now_add=True, db_index=True, verbose_name=_("Timestamp")
    )

    class Meta:
        verbose_name = _("Point Log")
        verbose_name_plural = _("Point Logs")
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.user.username}: {self.points_change:+} points at {self.timestamp}"
        )


class Badge(models.Model):
    """Defines achievable badges/achievements."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    slug = models.SlugField(
        unique=True,
        max_length=110,  # Accommodate longer names if needed
        verbose_name=_("Slug"),
    )
    description = models.TextField(verbose_name=_("Description"))
    icon_class_or_image = models.CharField(
        max_length=255,  # Can be a CSS class or image path
        verbose_name=_("Icon Class or Image URL"),
    )
    criteria_description = models.TextField(verbose_name=_("Criteria Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Badge")
        verbose_name_plural = _("Badges")
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Links users to the badges they have earned."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="earned_badges",
        verbose_name=_("User"),
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,  # If badge definition is deleted, link vanishes
        related_name="earned_by",
        verbose_name=_("Badge"),
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Earned At"))

    class Meta:
        verbose_name = _("User Badge")
        verbose_name_plural = _("User Badges")
        ordering = ["-earned_at"]
        unique_together = ("user", "badge")  # User can earn a badge only once

    def __str__(self):
        return f"{self.user.username} earned {self.badge.name}"


class RewardStoreItem(models.Model):
    """Defines items available for purchase in the rewards store."""

    class ItemType(models.TextChoices):
        AVATAR = "avatar", _("Avatar/Theme")  # أشعار/تصاميم
        MATERIAL = "material", _("Study Material/Outline")  # مخطوطات
        COMPETITION_ENTRY = "competition_entry", _("Competition Entry")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=150, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    item_type = models.CharField(
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.OTHER,
        verbose_name=_("Item Type"),
    )
    cost_points = models.PositiveIntegerField(verbose_name=_("Cost (Points)"))
    asset_url_or_data = models.CharField(
        max_length=255, blank=True, null=True, verbose_name=_("Asset URL or Data")
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


class UserRewardPurchase(models.Model):
    """Records instances where a user purchases an item."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reward_purchases",
        verbose_name=_("User"),
    )
    item = models.ForeignKey(
        RewardStoreItem,
        on_delete=models.PROTECT,  # Protect item def if purchased
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
        return f"{self.user.username} purchased {self.item.name} at {self.purchased_at}"
