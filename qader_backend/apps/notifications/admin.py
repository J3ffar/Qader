from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient_username",
        "actor_username",
        "verb",
        "notification_type",
        "is_read",
        "created_at_display",
        "target_link",  # Display link to target if possible
    )
    list_filter = ("notification_type", "is_read", "created_at", "recipient__username")
    search_fields = (
        "recipient__username",
        "recipient__email",
        "actor__username",
        "verb",
        "description",
    )
    readonly_fields = (
        "created_at",
        "read_at",
        "target_content_type",
        "target_object_id",
        "action_object_content_type",
        "action_object_object_id",
        "target_admin_link",  # Display link in detail view
        "action_object_admin_link",
    )
    raw_id_fields = ("recipient", "actor")  # For performance with many users
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Core Info"),
            {
                "fields": (
                    "recipient",
                    "actor",
                    "verb",
                    "description",
                    "notification_type",
                    "url",
                    "data",
                )
            },
        ),
        (_("Status"), {"fields": ("is_read", "read_at")}),
        (
            _("Related Objects (Readonly)"),
            {
                "fields": (
                    "target_content_type",
                    "target_object_id",
                    "target_admin_link",
                    "action_object_content_type",
                    "action_object_object_id",
                    "action_object_admin_link",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Timestamps"), {"fields": ("created_at",)}),
    )

    def recipient_username(self, obj: Notification):
        return obj.recipient.username

    recipient_username.short_description = _("Recipient")
    recipient_username.admin_order_field = "recipient__username"

    def actor_username(self, obj: Notification):
        return obj.actor.username if obj.actor else "System"

    actor_username.short_description = _("Actor")
    actor_username.admin_order_field = "actor__username"

    def created_at_display(self, obj: Notification):
        return obj.created_at.strftime("%Y-%m-%d %H:%M")

    created_at_display.short_description = _("Created At")
    created_at_display.admin_order_field = "created_at"

    def _get_admin_link(self, obj_instance, content_type, object_id):
        if content_type and object_id and obj_instance:
            try:
                # Ensure obj_instance (the target/action_object) is not None
                admin_url = admin.utils.get_object_admin_url(obj_instance)
                return format_html('<a href="{}">{}</a>', admin_url, str(obj_instance))
            except Exception:  # Be robust against errors if URL can't be resolved
                return str(obj_instance) if obj_instance else "N/A"
        return "N/A"

    def target_link(self, obj: Notification):
        return self._get_admin_link(
            obj.target, obj.target_content_type, obj.target_object_id
        )

    target_link.short_description = _("Target")
    target_link.allow_tags = True  # For older Django, format_html handles safety

    def target_admin_link(self, obj: Notification):  # For detail view
        return self.target_link(obj)

    target_admin_link.short_description = _("Target (Admin Link)")

    def action_object_admin_link(self, obj: Notification):  # For detail view
        return self._get_admin_link(
            obj.action_object,
            obj.action_object_content_type,
            obj.action_object_object_id,
        )

    action_object_admin_link.short_description = _("Action Object (Admin Link)")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "recipient",
                "actor",
                "target_content_type",
                "action_object_content_type",
            )
        )
