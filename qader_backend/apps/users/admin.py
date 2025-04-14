from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, SerialCode

# --- Inlines ---


class UserProfileInline(admin.StackedInline):
    """Inline editor for UserProfile within the User admin page."""

    model = UserProfile
    can_delete = False  # Don't allow deleting profile from User admin
    verbose_name_plural = _("Profile")
    fk_name = "user"  # Explicitly state the foreign key relationship

    # Fields to display inline
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "full_name",
                    "preferred_name",
                    "gender",
                    "grade",
                    "role",
                    "profile_picture",
                )
            },
        ),
        (_("Qiyas History"), {"fields": ("has_taken_qiyas_before",)}),
        (
            _("Subscription"),
            {
                "fields": (
                    "subscription_expires_at",
                    "serial_code_used",
                    "is_subscribed",
                )
            },
        ),
        (
            _("Gamification & Progress"),
            {
                "fields": (
                    "points",
                    "current_streak_days",
                    "longest_streak_days",
                    "last_study_activity_at",
                )
            },
        ),
        (
            _("Learning Levels"),
            {
                "fields": (
                    "current_level_verbal",
                    "current_level_quantitative",
                    "level_determined",
                )
            },
        ),
        (_("Referral"), {"fields": ("referral_code", "referred_by")}),
        (
            _("Settings"),
            {
                "fields": (
                    "last_visited_study_option",
                    "dark_mode_preference",
                    "notify_reminders_enabled",
                )
            },
        ),
    )
    # Fields calculated or set programmatically should be read-only
    readonly_fields = (
        "serial_code_used",
        "is_subscribed",  # Property
        "level_determined",  # Property
        "referral_code",  # Generated on save
        "referred_by",  # Set via referral process
        "points",
        "current_streak_days",
        "longest_streak_days",
        "last_study_activity_at",  # Updated by system actions
        "current_level_verbal",
        "current_level_quantitative",  # Updated by assessments/tests
    )
    # Adjust raw_id_fields for performance with large numbers of users/codes
    raw_id_fields = (
        "referred_by",
        "serial_code_used",
    )


# --- Model Admins ---


class UserAdmin(BaseUserAdmin):
    """Custom User Admin including the UserProfile inline."""

    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        # 'full_name_from_profile', # Add profile field if desired
        "is_active",
        "is_staff",
        "get_user_role",  # Custom method to display role from profile
        "get_subscription_status",  # Custom method for subscription status
        "date_joined",
        "last_login",
    )
    list_select_related = (
        "profile",
    )  # Optimize query for profile access in list_display
    list_filter = BaseUserAdmin.list_filter + (
        "profile__role",
        "profile__subscription_expires_at",
    )
    search_fields = BaseUserAdmin.search_fields + ("profile__full_name",)

    # Add profile fields to the fieldsets if needed for direct editing (use with caution)
    # fieldsets = BaseUserAdmin.fieldsets + (
    #     (_('Profile Info'), {'fields': ('profile__full_name',)}), # Example syntax
    # )

    @admin.display(description=_("Role"), ordering="profile__role")
    def get_user_role(self, instance):
        try:
            # Ensure profile exists (signal should handle this)
            if hasattr(instance, "profile"):
                return instance.profile.get_role_display()
        except UserProfile.DoesNotExist:
            pass  # Should not happen if signal is working
        return _("No Profile")

    @admin.display(
        description=_("Subscribed"),
        boolean=True,
        ordering="profile__subscription_expires_at",
    )
    def get_subscription_status(self, instance):
        try:
            if hasattr(instance, "profile"):
                return instance.profile.is_subscribed
        except UserProfile.DoesNotExist:
            pass
        return False

    # Optionally, if you want to display full name directly
    # @admin.display(description=_("Full Name"), ordering='profile__full_name')
    # def full_name_from_profile(self, instance):
    #     try:
    #         if hasattr(instance, 'profile'):
    #             return instance.profile.full_name
    #     except UserProfile.DoesNotExist:
    #         pass
    #     return ''


@admin.register(SerialCode)
class SerialCodeAdmin(admin.ModelAdmin):
    """Admin interface for managing Serial Codes."""

    list_display = (
        "code",
        "duration_days",
        "is_active",
        "is_used",
        "get_used_by_username",  # Custom method for username
        "used_at",
        "created_at",
        "get_created_by_username",  # Custom method for creator
    )
    list_filter = ("is_active", "is_used", "duration_days", "created_at")
    search_fields = ("code", "used_by__username", "notes", "created_by__username")
    # Fields that shouldn't be edited directly in the admin
    readonly_fields = ("used_by", "used_at", "created_at", "updated_at")
    list_select_related = ("used_by", "created_by")  # Optimize queries
    # Add actions if needed (e.g., bulk activate/deactivate codes)
    # actions = ['activate_codes', 'deactivate_codes']

    @admin.display(description=_("Used By"), ordering="used_by__username")
    def get_used_by_username(self, obj):
        return obj.used_by.username if obj.used_by else "-"

    @admin.display(description=_("Created By"), ordering="created_by__username")
    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else "-"

    # Example Admin Action
    # @admin.action(description=_('Activate selected codes'))
    # def activate_codes(self, request, queryset):
    #     updated = queryset.update(is_active=True)
    #     self.message_user(request, _(f'{updated} codes were successfully activated.'))

    # @admin.action(description=_('Deactivate selected codes'))
    # def deactivate_codes(self, request, queryset):
    #     updated = queryset.update(is_active=False)
    #     self.message_user(request, _(f'{updated} codes were successfully deactivated.'))


# Re-register User model with the custom UserAdmin
# Ensures the UserProfileInline is used
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
