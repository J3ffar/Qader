from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
import logging

# Import the new model
from apps.admin_panel.models import ExportJob
from apps.admin_panel import services as admin_services

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def export_statistics_task(self, job_id):
    """
    Celery task to generate a statistics file and save it to an ExportJob record.
    """
    try:
        job = ExportJob.objects.get(id=job_id)
    except ExportJob.DoesNotExist:
        logger.error(f"ExportJob with id={job_id} not found.")
        return {"status": "FAILURE", "message": "Job record not found."}

    # --- Step 1: Update Job Status ---
    job.status = ExportJob.Status.IN_PROGRESS
    job.save(update_fields=["status"])

    try:
        # --- Step 2: Query Data using the Service ---
        # Filters are now stored on the job model
        queryset = admin_services.get_filtered_test_attempts(job.filters)

        # --- Step 3: Generate File Content using the Service ---
        file_content, content_type, filename = (
            admin_services.generate_export_file_content(queryset, job.file_format)
        )

        if not file_content:
            raise ValueError(
                f"Unsupported or empty file content for format: {job.file_format}"
            )

        # --- Step 4: Save file to the model's FileField ---
        job.file.save(filename, ContentFile(file_content))

        # --- Step 5: Finalize Job as Success ---
        job.status = ExportJob.Status.SUCCESS
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "file", "completed_at"])

        logger.info(f"Successfully completed ExportJob {job_id}. File: {job.file.name}")
        return {"status": "SUCCESS", "file_path": job.file.path}

    except Exception as e:
        logger.exception(f"Failed to process ExportJob {job_id}. Error: {e}")
        # --- Handle Failure ---
        job.status = ExportJob.Status.FAILURE
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
        return {"status": "FAILURE", "message": str(e)}
