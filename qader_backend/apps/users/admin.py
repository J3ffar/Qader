from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, SerialCode


# Define an inline admin descriptor for UserProfile which acts a bit like a singleton
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    # Fields to display inline within the User admin page
    fields = (
        "full_name",
        "preferred_name",
        "gender",
        "grade",
        "role",
        "profile_picture",
        "has_taken_qiyas_before",
        "subscription_expires_at",
        "serial_code_used",
        "points",
        "current_streak_days",
        "last_study_activity_at",
        "current_level_verbal",
        "current_level_quantitative",
        "referral_code",
        "referred_by",
    )
    readonly_fields = (
        "serial_code_used",
        "referral_code",
        "referred_by",
        "current_streak_days",
        "last_study_activity_at",
        "points",
        "current_level_verbal",
        "current_level_quantitative",
    )  # Fields calculated or set programmatically


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "get_user_role",
        "get_subscription_status",
    )
    list_select_related = ("profile",)  # Optimize query

    @admin.display(description="Role")
    def get_user_role(self, instance):
        try:
            return instance.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return "No Profile"

    @admin.display(description="Subscribed")
    def get_subscription_status(self, instance):
        try:
            return instance.profile.is_subscribed
        except UserProfile.DoesNotExist:
            return False

    get_subscription_status.boolean = True  # Show as icon

    # You can add profile fields to search/filter if needed, using 'profile__field_name'
    # search_fields = BaseUserAdmin.search_fields + ('profile__full_name',)
    # list_filter = BaseUserAdmin.list_filter + ('profile__role',)


@admin.register(SerialCode)
class SerialCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "duration_days",
        "is_active",
        "is_used",
        "get_used_by_username",
        "used_at",
        "created_at",
    )
    list_filter = ("is_active", "is_used", "duration_days")
    search_fields = ("code", "used_by__username", "notes")
    readonly_fields = ("used_by", "used_at", "created_at", "updated_at")
    list_select_related = ("used_by",)  # Optimize query

    @admin.display(description="Used By")
    def get_used_by_username(self, obj):
        if obj.used_by:
            return obj.used_by.username
        return "-"


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Note: UserProfile is managed inline via UserAdmin, so no separate registration needed.
# If you wanted a separate UserProfile admin page:
# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'full_name', 'role', 'is_subscribed', 'subscription_expires_at')
#     search_fields = ('user__username', 'user__email', 'full_name')
#     list_filter = ('role', )
#     readonly_fields = ('user', 'created_at', 'updated_at', ...) # Many fields would be readonly
