from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Import the models from this app
from .models import AdminPermission, ExportJob

# Import the celery task to allow re-queueing
from .tasks import process_export_job


@admin.register(AdminPermission)
class AdminPermissionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing granular permissions for Sub-Admins.
    """

    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    # Automatically populates the slug field from the name for ease of use.
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ExportJob)
class ExportJobAdmin(admin.ModelAdmin):
    """
    Admin interface for monitoring and managing asynchronous export jobs.

    This interface is primarily for monitoring and debugging. Most fields are
    read-only as they are set by the system during the job lifecycle.
    """

    list_display = (
        "id",
        "requesting_user",
        "job_type",
        "status",
        "file_format",
        "created_at",
        "completed_at",
        "download_file_link",
    )
    list_filter = ("status", "job_type", "file_format", "created_at")
    search_fields = ("id__iexact", "requesting_user__username", "task_id")
    ordering = ("-created_at",)

    # Define custom actions
    actions = ["requeue_jobs"]

    # Make the admin view mostly read-only to prevent data corruption.
    # An admin should not manually change the status of a job.
    readonly_fields = (
        "id",
        "requesting_user",
        "job_type",
        "status",
        "file_format",
        "task_id",
        "filters",
        "error_message",
        "created_at",
        "completed_at",
        "download_file_link",  # Also show the link in the detail view
    )

    fieldsets = (
        (
            _("Job Overview"),
            {"fields": ("id", "job_type", "status", "requesting_user", "task_id")},
        ),
        (_("File Details"), {"fields": ("file_format", "download_file_link")}),
        (_("Timestamps"), {"fields": ("created_at", "completed_at")}),
        (
            _("Job Data & Diagnostics"),
            {
                "classes": ("collapse",),  # Collapsible section for less critical info
                "fields": ("filters", "error_message"),
            },
        ),
    )

    def has_add_permission(self, request):
        # Prevent manual creation of ExportJob instances from the admin.
        # They should only be created via the API.
        return False

    @admin.display(description=_("Download File"))
    def download_file_link(self, obj: ExportJob):
        """
        Creates a safe HTML link to the generated file if it exists.
        """
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>', obj.file.url
            )
        return "N/A"

    @admin.action(description=_("Re-queue selected failed/pending jobs"))
    def requeue_jobs(self, request, queryset):
        """
        Admin action to re-trigger the Celery task for selected jobs.
        This is useful for retrying failed jobs.
        """
        requeued_count = 0
        for job in queryset:
            # It's safest to only requeue jobs that have failed or are stuck in pending.
            if job.status in [ExportJob.Status.FAILURE, ExportJob.Status.PENDING]:
                # Reset the job's state to give clear feedback
                job.status = ExportJob.Status.PENDING
                job.error_message = None
                job.completed_at = None
                job.save(update_fields=["status", "error_message", "completed_at"])

                # Dispatch the task again
                process_export_job.delay(job_id=job.id)
                requeued_count += 1

        if requeued_count > 0:
            self.message_user(
                request,
                f"{requeued_count} job(s) have been successfully re-queued for processing.",
                level="success",
            )
        else:
            self.message_user(
                request,
                "No jobs were re-queued. This action only applies to jobs with 'Failure' or 'Pending' status.",
                level="warning",
            )
