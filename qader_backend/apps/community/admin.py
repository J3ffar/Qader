from django.contrib import admin
from .models import CommunityPost, CommunityReply


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "author",
        "post_type",
        "section_filter",
        "created_at",
        "is_pinned",
        "is_closed",
        "reply_count_admin",
    )
    list_filter = (
        "post_type",
        "is_pinned",
        "is_closed",
        "section_filter",
        "created_at",
    )
    search_fields = ("title", "content", "author__username", "tags__name")
    raw_id_fields = ("author", "section_filter")
    readonly_fields = ("created_at", "updated_at")
    # Use taggit admin widget if desired (requires separate setup)

    def reply_count_admin(self, obj):
        return obj.reply_count

    reply_count_admin.short_description = "Replies"


@admin.register(CommunityReply)
class CommunityReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "post_id_link", "parent_reply_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username", "post__title")
    raw_id_fields = ("post", "author", "parent_reply")
    readonly_fields = ("created_at", "updated_at")

    def post_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:community_communitypost_change", args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', link, obj.post.id)

    post_id_link.short_description = "Post ID"
