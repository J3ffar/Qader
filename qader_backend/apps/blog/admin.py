from django.contrib import admin
from .models import BlogPost, BlogAdviceRequest


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "author_display_name",
        "status",
        "published_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "tags", "author")
    search_fields = ("title", "content", "slug", "tags__name")
    prepopulated_fields = {"slug": ("title",)}  # Auto-populate slug in admin
    ordering = ("-status", "-published_at")
    date_hierarchy = "published_at"
    # Consider adding filter_horizontal or filter_vertical for 'tags' if using ManyToMany directly without taggit

    fieldsets = (
        (None, {"fields": ("title", "slug", "content", "tags")}),
        ("Publication", {"fields": ("status", "published_at", "author")}),
    )

    # Ensure read-only fields are displayed
    readonly_fields = ("created_at", "updated_at")

    # Override the default queryset to show the display name
    def author_display_name(self, obj):
        return obj.author_display_name

    author_display_name.short_description = "Author Name"
    author_display_name.admin_order_field = (
        "author__username"  # Allow sorting by username
    )


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
