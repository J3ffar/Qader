from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone
import logging

from apps.admin_panel.models import ExportJob
from apps.admin_panel import services as admin_services

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def process_export_job(self, job_id):
    """
    Generic Celery task to process an export job.
    It inspects the job's `job_type` and delegates to the appropriate logic.
    """
    try:
        job = ExportJob.objects.get(id=job_id)
    except ExportJob.DoesNotExist:
        logger.error(f"ExportJob with id={job_id} not found.")
        return {"status": "FAILURE", "message": "Job record not found."}

    job.status = ExportJob.Status.IN_PROGRESS
    job.task_id = self.request.id  # Save celery task ID
    job.save(update_fields=["status", "task_id"])

    try:
        # --- DELEGATION LOGIC ---
        if job.job_type == ExportJob.JobType.TEST_ATTEMPTS:
            queryset = admin_services.get_filtered_test_attempts(job.filters)
            file_content, _, filename = admin_services.generate_export_file_content(
                queryset, job.file_format
            )
        elif job.job_type == ExportJob.JobType.USERS:
            queryset = admin_services.get_filtered_users(job.filters)
            file_content, _, filename = (
                admin_services.generate_user_export_file_content(
                    queryset, job.file_format
                )
            )
        else:
            raise ValueError(f"Unknown job type: {job.job_type}")

        # --- Common success logic ---
        if not file_content:
            raise ValueError(f"Generated file content is empty for job {job_id}.")

        job.file.save(filename, ContentFile(file_content))
        job.status = ExportJob.Status.SUCCESS
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "file", "completed_at"])

        logger.info(
            f"Successfully completed ExportJob {job_id} of type {job.job_type}. File: {job.file.name}"
        )
        return {"status": "SUCCESS", "file_path": job.file.path}

    except Exception as e:
        logger.exception(f"Failed to process ExportJob {job_id}. Error: {e}")
        job.status = ExportJob.Status.FAILURE
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
        return {"status": "FAILURE", "message": str(e)}
