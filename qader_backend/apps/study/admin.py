from django.contrib import admin
from .models import (
    TestDefinition,
    UserTestAttempt,
    UserQuestionAttempt,
    UserSkillProficiency,
)


@admin.register(TestDefinition)
class TestDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "test_type", "is_active", "created_at")
    list_filter = ("test_type", "is_active")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


class UserQuestionAttemptInline(admin.TabularInline):
    model = UserQuestionAttempt
    fields = (
        "question",
        "selected_answer",
        "is_correct",
        "time_taken_seconds",
        "mode",
        "attempted_at",
    )
    readonly_fields = ("attempted_at",)
    extra = 0
    ordering = ("attempted_at",)  # Order inline attempts by time


@admin.register(UserTestAttempt)
class UserTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "test_definition",
        "status",
        "score_percentage",
        "start_time",
        "end_time",
    )
    list_filter = (
        "status",
        "test_definition__test_type",
        "test_definition",
        "start_time",
    )
    search_fields = ("user__username", "user__email", "test_definition__name")
    readonly_fields = (
        "start_time",
        "created_at",
        "updated_at",
        "results_summary",
    )  # Make results read-only in admin
    list_select_related = ("user", "test_definition")
    inlines = [UserQuestionAttemptInline]


@admin.register(UserQuestionAttempt)
class UserQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "question_id",
        "test_attempt_id",
        "mode",
        "is_correct",
        "attempted_at",
    )
    list_filter = (
        "mode",
        "is_correct",
        "attempted_at",
        "question__subsection__section",
        "question__subsection",
    )
    search_fields = ("user__username", "question__question_text", "test_attempt__id")
    readonly_fields = ("attempted_at",)
    list_select_related = ("user", "question", "test_attempt")


@admin.register(UserSkillProficiency)
class UserSkillProficiencyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "skill",
        "proficiency_score",
        "attempts_count",
        "correct_count",
        "last_calculated_at",
    )
    search_fields = ("user__username", "skill__name", "skill__slug")
    list_filter = ("skill__subsection__section", "skill__subsection")
    readonly_fields = ("last_calculated_at",)
    list_select_related = ("user", "skill")
