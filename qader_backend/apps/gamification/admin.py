from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import PointLog, Badge, UserBadge, RewardStoreItem, UserRewardPurchase


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon_preview", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("icon_preview",)  # Show preview in detail view as well
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "criteria_description")}),
        (
            _("Icon"),
            {"fields": ("icon", "icon_preview")},  # Show preview next to upload
        ),
        (_("Status"), {"fields": ("is_active",)}),
    )


@admin.register(PointLog)
class PointLogAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "points_change",
        "reason_code",
        "description_snippet",
        "timestamp",
        "related_object",
    )
    list_filter = ("reason_code", "timestamp")
    search_fields = ("user__username", "description")
    raw_id_fields = ("user",)  # Better UI for selecting users
    list_select_related = ("user", "content_type")  # Optimization

    def description_snippet(self, obj):
        if obj.description:
            return obj.description[:50] + ("..." if len(obj.description) > 50 else "")
        return "-"

    description_snippet.short_description = _("Description Snippet")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "earned_at")
    list_filter = ("earned_at", "badge")
    search_fields = ("user__username", "badge__name")
    raw_id_fields = ("user", "badge")
    list_select_related = ("user", "badge")


@admin.register(RewardStoreItem)
class RewardStoreItemAdmin(admin.ModelAdmin):
    list_display = ("name", "item_type", "cost_points", "is_active")
    list_filter = ("is_active", "item_type")
    search_fields = ("name", "description")


@admin.register(UserRewardPurchase)
class UserRewardPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "item", "points_spent", "purchased_at")
    list_filter = ("purchased_at", "item")
    search_fields = ("user__username", "item__name")
    raw_id_fields = ("user", "item")
    list_select_related = ("user", "item")
