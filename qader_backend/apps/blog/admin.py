from django.contrib import admin
from .models import BlogPost, BlogAdviceRequest


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "author",
        "status",
        "published_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "tags", "author")
    search_fields = ("title", "content", "slug", "tags__name", "author__username")
    prepopulated_fields = {"slug": ("title",)}  # Auto-populate slug in admin
    raw_id_fields = ("author",)
    ordering = ("-status", "-published_at")
    date_hierarchy = "published_at"
    # Consider adding filter_horizontal or filter_vertical for 'tags' if using ManyToMany directly without taggit

    fieldsets = (
        (None, {"fields": ("title", "slug", "content", "image", "tags")}),
        ("Publication", {"fields": ("status", "published_at", "author")}),
    )

    # Ensure read-only fields are displayed
    readonly_fields = ("created_at", "updated_at")


@admin.register(BlogAdviceRequest)
class BlogAdviceRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "problem_type", "status", "response_via", "created_at")
    list_filter = ("status", "response_via", "created_at")
    search_fields = ("user__username", "user__email", "problem_type", "description")
    list_editable = ("status", "response_via")  # Allow quick updates from list view
    autocomplete_fields = [
        "user",
        "related_support_ticket",
        "related_blog_post",
    ]  # Easier linking
    ordering = ("-created_at",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "user",
        "problem_type",
        "description",
    )  # Make user-submitted fields read-only

    fieldsets = (
        (
            "Request Details",
            {
                "fields": (
                    "user",
                    "problem_type",
                    "description",
                    "created_at",
                    "updated_at",
                )
            },
        ),
        (
            "Admin Processing",
            {
                "fields": (
                    "status",
                    "response_via",
                    "related_support_ticket",
                    "related_blog_post",
                )
            },
        ),
    )
