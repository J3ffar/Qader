from django.contrib import admin
from .models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)


@admin.register(LearningSection)
class LearningSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "order", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningSubSection)
class LearningSubSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "section", "slug", "order", "created_at")
    list_filter = ("section",)
    search_fields = ("name", "section__name")
    prepopulated_fields = {"slug": ("section", "name")}
    list_select_related = ("section",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "subsection", "slug", "created_at")
    list_filter = ("subsection__section", "subsection")
    search_fields = ("name", "subsection__name")
    prepopulated_fields = {"slug": ("subsection", "name")}
    list_select_related = ("subsection__section", "subsection")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
        "subsection",
        "skill",
        "difficulty",
        "is_active",
        "created_at",
    )
    list_filter = (
        "subsection__section",
        "subsection",
        "skill",
        "difficulty",
        "is_active",
    )
    search_fields = (
        "id",
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "explanation",
        "hint",
    )
    list_select_related = ("subsection__section", "subsection", "skill")
    raw_id_fields = (
        "starred_by",
    )  # Better performance for ManyToMany with many users/questions
    fieldsets = (
        (
            None,
            {"fields": ("subsection", "skill", "question_text", "is_active", "image","article")},
        ),
        ("Options", {"fields": ("option_a", "option_b", "option_c", "option_d")}),
        ("Answer & Explanation", {"fields": ("correct_answer", "explanation")}),
        ("Meta", {"fields": ("hint", "solution_method_summary", "difficulty")}),
    )


@admin.register(UserStarredQuestion)
class UserStarredQuestionAdmin(admin.ModelAdmin):
    list_display = ("user", "question_id", "starred_at")
    list_filter = ("starred_at",)
    search_fields = ("user__username", "question__id", "question__question_text")
    list_select_related = (
        "user",
        "question",
    )  # Select related question info efficiently

    # Optimize display of question
    def question_id(self, obj):
        return obj.question.id

    question_id.short_description = "Question ID"

