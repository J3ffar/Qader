from django.contrib import admin
from .models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase


@admin.register(PointLog)
class PointLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "points_change",
        "reason_code",
        "timestamp",
        "related_object",
    )
    list_filter = ("reason_code", "timestamp", "user")
    search_fields = ("user__username", "description", "reason_code")
    readonly_fields = (
        "user",
        "points_change",
        "reason_code",
        "description",
        "content_type",
        "object_id",
        "related_object",
        "timestamp",
    )
    date_hierarchy = "timestamp"


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active",)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "earned_at")
    list_filter = ("badge", "earned_at", "user")
    search_fields = ("user__username", "badge__name")
    readonly_fields = ("user", "badge", "earned_at")
    date_hierarchy = "earned_at"


@admin.register(RewardStoreItem)
class RewardStoreItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "cost_points", "is_active", "created_at")
    list_filter = ("item_type", "is_active")
    search_fields = ("name", "description")


@admin.register(UserRewardPurchase)
class UserRewardPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "points_spent", "purchased_at")
    list_filter = ("item", "purchased_at", "user")
    search_fields = ("user__username", "item__name")
    readonly_fields = ("user", "item", "points_spent", "purchased_at")
    date_hierarchy = "purchased_at"
