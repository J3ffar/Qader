from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class AdminPermission(models.Model):
    """
    Defines a specific permission that can be granted to a Sub-Admin.
    """

    # Use a slug for easier identification and use in code/API requests
    slug = models.SlugField(
        _("Slug"),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_(
            "Unique identifier for the permission (e.g., 'view_users', 'manage_content')."
        ),
    )
    name = models.CharField(
        _("Name"),
        max_length=100,
        help_text=_("Human-readable name for the permission."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Detailed explanation of what this permission allows."),
    )

    class Meta:
        verbose_name = _("Admin Permission")
        verbose_name_plural = _("Admin Permissions")
        ordering = ["name"]

    def __str__(self):
        return self.name


# --- NEW MODEL ---
def export_file_path(instance, filename):
    """Generates a unique path for the export file."""
    # File will be uploaded to MEDIA_ROOT/exports/user_<id>/<uuid>.<ext>
    return f"exports/user_{instance.requesting_user.id}/{uuid.uuid4()}_{filename}"


class ExportJob(models.Model):
    """
    Represents an asynchronous data export job initiated by a user.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        SUCCESS = "SUCCESS", _("Success")
        FAILURE = "FAILURE", _("Failure")

    class Format(models.TextChoices):
        CSV = "csv", _("CSV")
        XLSX = "xlsx", _("Excel (XLSX)")

    class JobType(models.TextChoices):
        TEST_ATTEMPTS = "TEST_ATTEMPTS", _("Test Attempts Export")
        USERS = "USERS", _("User Data Export")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requesting_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # Keep job record even if user is deleted
        null=True,
        related_name="export_jobs",
        verbose_name=_("Requesting User"),
    )
    job_type = models.CharField(
        _("Job Type"),
        max_length=20,
        choices=JobType.choices,
        default=JobType.TEST_ATTEMPTS, # Or make it required
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    file_format = models.CharField(
        _("File Format"), max_length=10, choices=Format.choices
    )
    task_id = models.CharField(
        _("Celery Task ID"),
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("The ID of the background task processing this job."),
    )
    filters = models.JSONField(
        _("Applied Filters"),
        default=dict,
        help_text=_("The query parameters used for this export."),
    )
    file = models.FileField(
        _("Exported File"),
        upload_to=export_file_path,
        blank=True,
        null=True,
        help_text=_("The final generated file."),
    )
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        null=True,
        help_text=_("Details of the error if the job failed."),
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    completed_at = models.DateTimeField(_("Completed At"), blank=True, null=True)

    class Meta:
        verbose_name = _("Export Job")
        verbose_name_plural = _("Export Jobs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Export Job {self.id} for {self.requesting_user.username} ({self.get_status_display()})"
