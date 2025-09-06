from django.contrib import admin
from .models import (
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
    Article,
    MediaFile,
    Question,
    UserStarredQuestion,
)


@admin.register(TestType)
class TestTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "status", "order", "created_at")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningSection)
class LearningSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "test_type", "slug", "order", "created_at")
    list_filter = ("test_type",)
    search_fields = ("name", "test_type__name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LearningSubSection)
class LearningSubSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "section", "slug", "order", "created_at")
    list_filter = ("section__test_type", "section")
    search_fields = ("name", "section__name")
    prepopulated_fields = {"slug": ("section", "name")}
    list_select_related = ("section", "section__test_type")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "section", "subsection", "slug", "created_at")
    list_filter = ("section__test_type", "section", "subsection")
    search_fields = ("name", "section__name", "subsection__name")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("section__test_type", "section", "subsection")

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title", "content")

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "file_type", "created_at")
    list_filter = ("file_type",)
    search_fields = ("title",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "__str__",
        "subsection",
        "display_skills",
        "difficulty",
        "is_active",
        "created_at",
    )
    list_filter = (
        "subsection__section__test_type",
        "subsection__section",
        "subsection",
        "skills",
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
    list_select_related = (
        "subsection__section__test_type",
        "subsection__section",
        "subsection",
        "media_content",
        "article",
    )
    raw_id_fields = (
        "starred_by",
        "media_content",
        "article",
        "skills",
    )  # Better performance for ManyToMany with many users/questions
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "subsection",
                    "skills",
                    "question_text",
                    "is_active",
                    "media_content",
                    "article",
                )
            },
        ),
        ("Options", {"fields": ("option_a", "option_b", "option_c", "option_d")}),
        ("Answer & Explanation", {"fields": ("correct_answer", "explanation")}),
        ("Meta", {"fields": ("hint", "solution_method_summary", "difficulty")}),
    )

    def display_skills(self, obj):
        return ", ".join([skill.name for skill in obj.skills.all()])

    display_skills.short_description = "Skills"


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
