# apps/study/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import DateFieldListFilter

from .models import Test, UserTestAttempt, UserQuestionAttempt
from apps.learning.models import Question  # Import Question to link to it


class UserQuestionAttemptInline(admin.TabularInline):
    """
    Inline admin configuration for viewing UserQuestionAttempts
    within a UserTestAttempt.
    """

    model = UserQuestionAttempt
    extra = 0  # Don't show extra empty forms
    can_delete = False  # Don't allow deleting individual attempts from here
    show_change_link = True  # Allow clicking to the individual attempt admin view

    fields = (
        "question_link",
        "selected_answer",
        "is_correct",
        "time_taken_seconds",
        "mode",
        "attempted_at",
    )
    readonly_fields = fields  # Make all fields read-only in the inline view

    # Define the custom method to link to the Question admin
    def question_link(self, obj):
        if obj.question_id:
            try:
                # Ensure the related Question model is registered in its app's admin
                question_admin_url = reverse(
                    "admin:learning_question_change", args=[obj.question.pk]
                )
                return format_html(
                    '<a href="{}">Q: {}</a>', question_admin_url, obj.question.pk
                )
            except Exception:  # Catch NoReverseMatch or other errors
                return f"Q: {obj.question.pk} (Link Error)"
        return _("N/A")

    question_link.short_description = _("Question")

    # Improve performance by selecting related question data if needed often
    # Not strictly necessary for just the link, but good practice if showing question text etc.
    # autocomplete_fields = ['question'] # Alternative if you want search lookup

    def has_add_permission(self, request, obj=None):
        # Prevent adding new attempts directly from the inline
        return False


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    """Admin configuration for Test Definitions."""

    list_display = (
        "name",
        "test_type",
        "is_predefined",
        "question_count",
        "created_at",
        "updated_at",
    )
    list_filter = ("test_type", "is_predefined", "created_at")
    search_fields = ("name", "description")
    filter_horizontal = ("questions",)  # Use better widget for M2M selection
    readonly_fields = ("created_at", "updated_at", "question_count")
    ordering = ("name",)

    fieldsets = (
        (None, {"fields": ("name", "test_type", "description", "is_predefined")}),
        (
            _("Configuration"),
            {
                "fields": ("configuration", "questions"),
                "description": _(
                    "Define either dynamic configuration rules OR link specific questions if 'is predefined' is checked."
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("question_count", "created_at", "updated_at"),
                "classes": ("collapse",),  # Keep metadata collapsed by default
            },
        ),
    )

    def question_count(self, obj):
        """Calculates the number of questions linked to a predefined test."""
        if obj.is_predefined:
            return obj.questions.count()
        return _("N/A (Dynamic)")

    question_count.short_description = _("Question Count (Predefined)")


@admin.register(UserTestAttempt)
class UserTestAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for User Test Attempts."""

    list_display = (
        "id",
        "user_link",
        "attempt_type",
        "status",
        "score_percentage",
        "start_time",
        "end_time",
        "num_questions",
    )
    list_filter = (
        "status",
        "attempt_type",
        ("start_time", DateFieldListFilter),  # Use date hierarchy filter
        # Add user filter if needed, but can be slow with many users
        # 'user',
    )
    search_fields = ("user__username", "user__email", "id")
    ordering = ("-start_time",)
    readonly_fields = (
        "id",
        "user_link",
        "test_definition",
        "attempt_type",
        "test_configuration",
        "question_ids",
        "start_time",
        "end_time",
        "score_percentage",
        "score_verbal",
        "score_quantitative",
        "results_summary",
        "created_at",
        "updated_at",
        "num_questions",  # Make property read-only
        "duration_seconds",  # Make property read-only
    )
    list_select_related = (
        "user",
        "test_definition",
    )  # Optimize fetching user/test info for list display

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "user_link",
                    "attempt_type",
                    "status",
                    "test_definition",
                )
            },
        ),
        (
            _("Configuration & Content"),
            {"fields": ("test_configuration", "question_ids", "num_questions")},
        ),
        (
            _("Timestamps & Duration"),
            {
                "fields": (
                    "start_time",
                    "end_time",
                    "duration_seconds",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
        (
            _("Scores & Results"),
            {
                "fields": (
                    "score_percentage",
                    "score_verbal",
                    "score_quantitative",
                    "results_summary",
                ),
                "classes": ("collapse",),  # Collapse scores/results by default
            },
        ),
    )
    inlines = [UserQuestionAttemptInline]  # Show related question attempts

    # Custom method to link to the User admin page
    def user_link(self, obj):
        if obj.user_id:
            try:
                user_admin_url = reverse("admin:auth_user_change", args=[obj.user.pk])
                return format_html(
                    '<a href="{}">{}</a>', user_admin_url, obj.user.username
                )
            except Exception:
                return obj.user.username  # Fallback if link fails
        return _("N/A")

    user_link.short_description = _("User")

    # Prevent adding or changing test attempts directly via admin (should be system-generated)
    def has_add_permission(self, request):
        return False

    # Allow changes only if absolutely necessary for debugging/fixing specific fields (e.g., status)
    # def has_change_permission(self, request, obj=None):
    #     return False # Or conditionally allow based on user permissions


@admin.register(UserQuestionAttempt)
class UserQuestionAttemptAdmin(admin.ModelAdmin):
    """Admin configuration for individual User Question Attempts."""

    list_display = (
        "id",
        "user_link",
        "question_link",
        "test_attempt_link",
        "mode",
        "is_correct",
        "attempted_at",
    )
    list_filter = (
        "mode",
        "is_correct",
        ("attempted_at", DateFieldListFilter),
        # Add user/question filters if needed, but can be slow
        # 'user',
        # 'question__subsection__section',
        # 'question__subsection',
    )
    search_fields = ("user__username", "user__email", "question__question_text", "id")
    ordering = ("-attempted_at",)
    # All fields represent historical data, make them read-only
    readonly_fields = [f.name for f in UserQuestionAttempt._meta.fields] + [
        "question_link",
        "test_attempt_link",
        "user_link",
    ]
    list_select_related = (
        "user",
        "question",
        "test_attempt",
    )  # Optimize list view queries

    # Custom method to link to the User admin page
    def user_link(self, obj):
        if obj.user_id:
            try:
                user_admin_url = reverse("admin:auth_user_change", args=[obj.user.pk])
                return format_html(
                    '<a href="{}">{}</a>', user_admin_url, obj.user.username
                )
            except Exception:
                return obj.user.username  # Fallback if link fails
        return _("N/A")

    user_link.short_description = _("User")

    # Custom method to link to the Question admin page
    def question_link(self, obj):
        if obj.question_id:
            try:
                question_admin_url = reverse(
                    "admin:learning_question_change", args=[obj.question.pk]
                )
                # Show first ~30 chars of question text for context if available
                q_text = obj.question.question_text[:30] + (
                    "..." if len(obj.question.question_text) > 30 else ""
                )
                return format_html(
                    '<a href="{}">Q: {} ({})</a>',
                    question_admin_url,
                    obj.question.pk,
                    q_text,
                )
            except Exception:
                return f"Q: {obj.question.pk} (Link Error)"
        return _("N/A")

    question_link.short_description = _("Question")

    # Custom method to link to the UserTestAttempt admin page
    def test_attempt_link(self, obj):
        if obj.test_attempt_id:
            try:
                attempt_admin_url = reverse(
                    "admin:study_usertestattempt_change", args=[obj.test_attempt.pk]
                )
                return format_html(
                    '<a href="{}">Attempt: {}</a>',
                    attempt_admin_url,
                    obj.test_attempt.pk,
                )
            except Exception:
                return f"Attempt: {obj.test_attempt.pk} (Link Error)"
        return _("N/A (Not part of test)")

    test_attempt_link.short_description = _("Test Attempt")

    # Prevent adding or changing question attempts directly via admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # Usually don't want admins changing historical attempts

    def has_delete_permission(self, request, obj=None):
        return False  # Usually don't want admins deleting historical attempts


# Register other models from the study app here later
# admin.site.register(EmergencyModeSession)
# admin.site.register(ConversationSession)
