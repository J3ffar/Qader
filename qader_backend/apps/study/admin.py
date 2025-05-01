from typing import Any, Optional  # For type hints
from django.contrib import admin, messages  # Import messages for actions
from django.db.models import QuerySet  # For type hints
from django.http import HttpRequest  # For type hints
from django.urls import reverse
from django.utils.html import format_html

# Removed: from django.utils.translation import gettext_lazy as _
from django.contrib.admin import DateFieldListFilter

from .models import (
    Test,
    UserTestAttempt,
    UserQuestionAttempt,
)  # Assuming TestStatusChoices is not needed for this version
from apps.learning.models import Question  # Import Question to link to it


class UserQuestionAttemptInline(admin.TabularInline):
    model = UserQuestionAttempt
    extra = 0
    can_delete = False
    show_change_link = True

    fields = (
        "question_link",
        "selected_answer",
        "is_correct",
        "time_taken_seconds",
        "mode",
        "attempted_at",
    )
    readonly_fields = fields

    @admin.display(description="Question")  # Plain string
    def question_link(self, obj: UserQuestionAttempt) -> str:
        if obj.question_id:
            try:
                question_admin_url = reverse(
                    "admin:learning_question_change", args=[obj.question.pk]
                )
                return format_html(
                    '<a href="{}">Q: {}</a>', question_admin_url, obj.question.pk
                )
            except Exception:
                return f"Q: {obj.question.pk} (Link Error)"  # Plain string
        return "N/A"  # Plain string

    def has_add_permission(
        self, request: HttpRequest, obj: Optional[UserTestAttempt] = None
    ) -> bool:
        return False


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "test_type",
        "is_predefined",
        "question_count_display",  # Use display method
        "created_at",
    )
    list_filter = ("test_type", "is_predefined", "created_at")
    search_fields = ("name", "description")
    filter_horizontal = ("questions",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "question_count_display",
    )  # Use display method here too
    ordering = ("name",)

    # Use get_fieldsets for conditional display
    def get_fieldsets(
        self, request: HttpRequest, obj: Optional[Test] = None
    ) -> list[tuple[Optional[str], dict[str, Any]]]:
        base_fieldsets = [
            (None, {"fields": ("name", "test_type", "description", "is_predefined")}),
        ]
        if obj and obj.is_predefined:
            base_fieldsets.append(
                (
                    "Predefined Questions",
                    {"fields": ("questions", "question_count_display")},
                )  # Plain string
            )
        else:  # Dynamic test (or new test defaulting to dynamic)
            base_fieldsets.append(
                (
                    "Dynamic Configuration",
                    {"fields": ("configuration",)},
                )  # Plain string
            )

        base_fieldsets.append(
            (
                "Metadata",
                {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
            ),  # Plain string
        )
        return base_fieldsets

    @admin.display(description="Question Count (Predefined)")  # Plain string
    def question_count_display(self, obj: Optional[Test]) -> str:
        if obj and obj.is_predefined:
            return str(obj.question_count)
        return "N/A (Dynamic)"  # Plain string


@admin.register(UserTestAttempt)
class UserTestAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "attempt_type",
        "test_definition_link",  # Added test name link
        "status",
        "score_percentage_display",  # Use display method
        "start_time",
        "end_time",
        "num_questions",
    )
    list_filter = (
        "status",
        "attempt_type",
        ("start_time", DateFieldListFilter),
    )
    search_fields = (
        "user__username",
        "user__email",
        "id",
        "test_definition__name",
    )  # Added test name search
    ordering = ("-start_time",)
    readonly_fields = (
        "id",
        "user_link",
        "test_definition_link",  # Added
        "attempt_type",
        "test_configuration",
        "question_ids",
        "start_time",
        "end_time",
        "score_percentage_display",  # Added
        "score_verbal",
        "score_quantitative",
        "results_summary",
        "created_at",
        "updated_at",
        "num_questions",
        "duration_seconds",
    )
    list_select_related = ("user", "test_definition")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "id",
                    "user_link",
                    "attempt_type",
                    "status",
                    "test_definition_link",
                )
            },
        ),
        (
            "Configuration & Content",
            {"fields": ("test_configuration", "question_ids", "num_questions")},
        ),  # Plain string
        (
            "Timestamps & Duration",
            {
                "fields": (
                    "start_time",
                    "end_time",
                    "duration_seconds",
                    "created_at",
                    "updated_at",
                )
            },
        ),  # Plain string
        (
            "Scores & Results",
            {
                "fields": (
                    "score_percentage_display",
                    "score_verbal",
                    "score_quantitative",
                    "results_summary",
                ),
                "classes": ("collapse",),
            },
        ),  # Plain string
    )
    inlines = [UserQuestionAttemptInline]
    actions = ["mark_as_reviewed"]  # Example action

    @admin.display(description="User", ordering="user__username")  # Plain string
    def user_link(self, obj: UserTestAttempt) -> str:
        if obj.user_id:
            try:
                user_admin_url = reverse("admin:auth_user_change", args=[obj.user.pk])
                return format_html(
                    '<a href="{}">{}</a>', user_admin_url, obj.user.username
                )
            except Exception:
                return obj.user.username
        return "N/A"  # Plain string

    @admin.display(
        description="Test Definition", ordering="test_definition__name"
    )  # Plain string
    def test_definition_link(self, obj: UserTestAttempt) -> str:
        if obj.test_definition_id:
            try:
                test_admin_url = reverse(
                    "admin:study_test_change", args=[obj.test_definition.pk]
                )
                return format_html(
                    '<a href="{}">{}</a>', test_admin_url, obj.test_definition.name
                )
            except Exception:
                return (
                    obj.test_definition.name if obj.test_definition else "N/A"
                )  # Plain string
        return "N/A"  # Plain string

    @admin.display(description="Score (%)", ordering="score_percentage")  # Plain string
    def score_percentage_display(self, obj: UserTestAttempt) -> str:
        if obj.score_percentage is not None:
            return f"{obj.score_percentage:.1f}%"
        return "N/A"  # Plain string

    # --- Example Admin Action ---
    @admin.action(description="Mark selected attempts as Reviewed")  # Plain string
    def mark_as_reviewed(
        self, request: HttpRequest, queryset: QuerySet[UserTestAttempt]
    ):
        # Example: Update status if there was a 'REVIEWED' status
        # updated_count = queryset.update(status=TestStatusChoices.REVIEWED) # Assuming REVIEWED exists
        # self.message_user(request, f"{updated_count} attempts marked as reviewed.", messages.SUCCESS)

        # Placeholder if no 'REVIEWED' status exists
        updated_count = queryset.count()  # Just count them for the message
        self.message_user(
            request,
            f"Action triggered for {updated_count} attempts (no status change implemented).",
            messages.WARNING,
        )  # Plain string

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False


@admin.register(UserQuestionAttempt)
class UserQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "question_link",
        "test_attempt_link",
        "selected_answer_display",  # Added
        "correct_answer_display",  # Added
        "is_correct",
        "mode",
        "attempted_at",
    )
    list_filter = (
        "mode",
        "is_correct",
        ("attempted_at", DateFieldListFilter),
    )
    search_fields = (
        "user__username",
        "user__email",
        "question__question_text",
        "id",
        "test_attempt__id",
    )  # Added test attempt id search
    ordering = ("-attempted_at",)
    readonly_fields = [f.name for f in UserQuestionAttempt._meta.fields] + [
        "user_link",
        "question_link",
        "test_attempt_link",
        "selected_answer_display",
        "correct_answer_display",
    ]
    list_select_related = ("user", "question", "test_attempt")

    @admin.display(description="User", ordering="user__username")  # Plain string
    def user_link(self, obj: UserQuestionAttempt) -> str:
        if obj.user_id:
            try:
                user_admin_url = reverse("admin:auth_user_change", args=[obj.user.pk])
                return format_html(
                    '<a href="{}">{}</a>', user_admin_url, obj.user.username
                )
            except Exception:
                return obj.user.username
        return "N/A"  # Plain string

    @admin.display(description="Question", ordering="question__pk")  # Plain string
    def question_link(self, obj: UserQuestionAttempt) -> str:
        if obj.question_id:
            try:
                question_admin_url = reverse(
                    "admin:learning_question_change", args=[obj.question.pk]
                )
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
                return f"Q: {obj.question.pk} (Link Error)"  # Plain string
        return "N/A"  # Plain string

    @admin.display(
        description="Test Attempt", ordering="test_attempt__pk"
    )  # Plain string
    def test_attempt_link(self, obj: UserQuestionAttempt) -> str:
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
                return f"Attempt: {obj.test_attempt.pk} (Link Error)"  # Plain string
        # Check if it's a conversational attempt (not linked to a UserTestAttempt)
        elif (
            hasattr(obj, "mode") and obj.mode == "conversational"
        ):  # Assuming you have a 'mode' field
            return "Conversational"  # Plain string
        return "N/A"  # Plain string

    @admin.display(description="Selected Answer")  # Plain string
    def selected_answer_display(self, obj: UserQuestionAttempt) -> str:
        if (
            obj.selected_answer
            and obj.question
            and hasattr(obj.question, "choices")
            and obj.question.choices
        ):
            choice_text = obj.question.choices.get(
                obj.selected_answer, obj.selected_answer
            )
            return f"{obj.selected_answer}) {choice_text}"
        return obj.selected_answer or "N/A"  # Plain string

    @admin.display(description="Correct Answer")  # Plain string
    def correct_answer_display(self, obj: UserQuestionAttempt) -> str:
        if obj.question_id and obj.question.correct_answer:
            if hasattr(obj.question, "choices") and obj.question.choices:
                correct_choice = obj.question.correct_answer
                choice_text = obj.question.choices.get(correct_choice, correct_choice)
                return f"{correct_choice}) {choice_text}"
            else:
                return (
                    obj.question.correct_answer
                )  # Fallback if choices aren't structured well
        return "N/A"  # Plain string

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Optional[UserQuestionAttempt] = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Optional[UserQuestionAttempt] = None
    ) -> bool:
        return False
