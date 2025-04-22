from django.contrib import admin
from . import models


@admin.register(models.Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title", "slug", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")


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
    list_editable = ("order", "is_active")  # Allow quick edits in list view


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
    # Add 'response' to fields when editing to allow admin reply
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
        # If admin adds a response, update responder and timestamp
        if "response" in form.changed_data and form.cleaned_data["response"]:
            obj.responder = request.user
            from django.utils import timezone

            obj.responded_at = timezone.now()
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
