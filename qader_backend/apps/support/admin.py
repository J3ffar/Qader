from django.contrib import admin
from .models import SupportTicket, SupportTicketReply


class SupportTicketReplyInline(admin.TabularInline):
    """Inline representation of replies within a ticket."""

    model = SupportTicketReply
    fields = ("user", "message", "is_internal_note", "created_at")
    readonly_fields = ("created_at",)
    extra = 0  # Don't show empty forms by default
    # Can limit fields further if needed


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    """Admin configuration for Support Tickets."""

    list_display = (
        "id",
        "subject",
        "user",
        "status",
        "priority",
        "issue_type",
        "assigned_to",
        "created_at",
        "updated_at",
    )
    list_filter = ("status", "priority", "issue_type", "created_at", "assigned_to")
    search_fields = (
        "id",
        "subject",
        "description",
        "user__username",
        "user__email",
        "assigned_to__username",
    )
    readonly_fields = ("created_at", "updated_at", "closed_at")
    list_editable = (
        "status",
        "priority",
        "assigned_to",
    )  # Allow quick edits in list view
    list_per_page = 25
    fieldsets = (
        (
            None,
            {"fields": ("subject", "user", "issue_type", "description", "attachment")},
        ),
        ("Management", {"fields": ("status", "priority", "assigned_to")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "closed_at")}),
    )
    inlines = [SupportTicketReplyInline]


@admin.register(SupportTicketReply)
class SupportTicketReplyAdmin(admin.ModelAdmin):
    """Admin configuration for direct access to replies (less common)."""

    list_display = (
        "id",
        "ticket_id",
        "user",
        "created_at",
        "is_internal_note",
        "message_snippet",
    )
    list_filter = ("created_at", "is_internal_note", "user")
    search_fields = ("ticket__id", "ticket__subject", "user__username", "message")
    readonly_fields = ("created_at",)
    list_per_page = 50

    @admin.display(description="Ticket ID")
    def ticket_id(self, obj):
        return obj.ticket.id

    @admin.display(description="Message Snippet")
    def message_snippet(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
