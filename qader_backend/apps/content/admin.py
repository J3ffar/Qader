from django.contrib import admin
from django.utils.html import format_html
import json
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters.html import HtmlFormatter
from django.utils.safestring import mark_safe

from . import models


# Helper to pretty-print JSON in the admin
def pretty_print_json(data):
    """
    Takes a dictionary or list, converts it to a formatted JSON string,
    and returns it as a safe HTML string with syntax highlighting.
    """
    if data is None:
        return ""
    response = json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False)
    formatter = HtmlFormatter(style="colorful")
    response = highlight(response, JsonLexer(), formatter)
    style = "<style>" + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + response)


class ContentImageInline(admin.TabularInline):
    """
    Allows managing a Page's associated images directly from the Page admin screen.
    """

    model = models.ContentImage
    extra = 0  # Don't show extra empty forms by default
    fields = ("image_preview", "name", "slug", "image", "alt_text")
    readonly_fields = (
        "image_preview",
        "slug",
    )

    def image_preview(self, obj):
        # Create a thumbnail preview for the admin list
        if obj.image:
            return format_html(
                '<a href="{}"><img src="{}" width="150" /></a>',
                obj.image.url,
                obj.image.url,
            )
        return "No Image"

    image_preview.short_description = "Image Preview"


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "pretty_content_structured")

    fieldsets = (
        (None, {"fields": ("title", "slug", "is_published")}),
        (
            "Simple Content (Legacy)",
            {
                "classes": ("collapse",),
                "fields": ("content",),
            },
        ),
        (
            "Structured Content (Template-based)",
            {
                "fields": ("content_structured", "pretty_content_structured"),
                "description": """
                <p>Use this JSON field to define content for template-based pages.
                For any image, use its unique <strong>slug</strong> as the value.</p>
                <p>Example: <code>{"main_image": {"type": "image", "value": "my-image-slug"}}</code></p>
            """,
            },
        ),
    )
    inlines = [ContentImageInline]

    def pretty_content_structured(self, instance):
        """Displays a read-only, pretty-printed version of the structured content JSON."""
        return pretty_print_json(instance.content_structured)

    pretty_content_structured.short_description = "Formatted JSON Preview"


@admin.register(models.ContentImage)
class ContentImageAdmin(admin.ModelAdmin):
    """
    Admin view for managing all ContentImages in the media library.
    """

    list_display = ("name", "slug", "image_preview", "page", "created_at")
    list_filter = ("page",)
    search_fields = ("name", "slug", "alt_text")
    readonly_fields = ("slug", "image_preview", "created_at", "updated_at")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="150" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Preview"


class FAQItemInline(admin.TabularInline):
    model = models.FAQItem
    extra = 1
    ordering = ("order",)


@admin.register(models.FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    search_fields = ("name",)
    inlines = [FAQItemInline]


@admin.register(models.FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("question", "answer")
    list_editable = ("order", "is_active")


@admin.register(models.PartnerCategory)
class PartnerCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active", "google_form_link")
    search_fields = ("name", "description")
    list_editable = ("order", "is_active")


@admin.register(models.ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "full_name",
        "email",
        "status",
        "created_at",
        "responder",
    )
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "subject", "message")
    readonly_fields = (
        "full_name",
        "email",
        "subject",
        "message",
        "attachment",
        "created_at",
        "updated_at",
        "responded_at",
    )
    fields = (
        "full_name",
        "email",
        "subject",
        "message",
        "attachment",
        "status",
        "responder",
        "response",
        "created_at",
        "updated_at",
        "responded_at",
    )

    def save_model(self, request, obj, form, change):
        if "response" in form.changed_data and form.cleaned_data["response"]:
            obj.responder = request.user
            from django.utils import timezone

            obj.responded_at = timezone.now()
            if (
                obj.status == models.ContactMessage.STATUS_NEW
                or obj.status == models.ContactMessage.STATUS_READ
            ):
                obj.status = models.ContactMessage.STATUS_REPLIED
        super().save_model(request, obj, form, change)


@admin.register(models.HomepageFeatureCard)
class HomepageFeatureCardAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    search_fields = ("title", "text")
    list_editable = ("order", "is_active")


@admin.register(models.HomepageStatistic)
class HomepageStatisticAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "order", "is_active")
    search_fields = ("label", "value")
    list_editable = ("order", "is_active")
