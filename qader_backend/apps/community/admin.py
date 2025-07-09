from django.contrib import admin
from django.utils.html import format_html
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
        "like_count",
        "image_tag",
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
    readonly_fields = ("created_at", "updated_at", "image_tag", "like_count")
    # Use taggit admin widget if desired (requires separate setup)

    def reply_count_admin(self, obj):
        return obj.reply_count

    reply_count_admin.short_description = "Replies"

    def like_count(self, obj):
        return obj.likes.count()

    like_count.short_description = "Likes"

    def image_tag(self, obj):
        if obj.image:
            return format_html(f'<a href="{obj.image.url}" target="_blank"><img src="{obj.image.url}" style="max-height: 100px;"/></a>')
        return "No Image"

    image_tag.short_description = "Image"


@admin.register(CommunityReply)
class CommunityReplyAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "post_id_link", "parent_reply_id", "created_at", "like_count")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username", "post__title")
    raw_id_fields = ("post", "author", "parent_reply")
    readonly_fields = ("created_at", "updated_at", "like_count")

    def post_id_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        link = reverse("admin:community_communitypost_change", args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', link, obj.post.id)

    post_id_link.short_description = "Post ID"

    def like_count(self, obj):
        return obj.likes.count()

    like_count.short_description = "Likes"
