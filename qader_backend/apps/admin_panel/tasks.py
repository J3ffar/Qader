import csv
import openpyxl  # Requires installation: pip install openpyxl
from io import StringIO, BytesIO
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime

# Import necessary models
from apps.study.models import UserTestAttempt

# Import the new services
from apps.admin_panel import services as admin_services


@shared_task(bind=True)
def export_statistics_task(self, user_id, export_format, filters):
    """
    Celery task to export statistics data based on filters.
    Calls reusable service functions for querying and file generation.
    """
    User = get_user_model()
    try:
        requesting_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"status": "FAILURE", "message": "Requesting user not found."}

    # --- Step 1: Query Data using the Service ---
    # Note: We are reusing the filters dict directly from the view
    queryset = admin_services.get_filtered_test_attempts(filters)

    # --- Step 2: Generate File Content using the Service ---
    # NOTE: I noticed a bug here. Your original task used `attempt.test.name` but the
    # view used `attempt.test_definition.name`. The service function standardizes
    # this to `test_definition`, fixing the inconsistency.
    file_content, content_type, filename = admin_services.generate_export_file_content(
        queryset, export_format
    )

    if not file_content:
        return {"status": "FAILURE", "message": f"Unsupported format: {export_format}"}

    # --- Step 3: Save file and notify user (your logic here) ---
    # from django.core.files.storage import default_storage
    # file_path = default_storage.save(f"exports/{filename}", ContentFile(file_content))
    # file_url = default_storage.url(file_path)

    print(f"Successfully generated export file: {filename} ({len(file_content)} bytes)")
    file_url = f"/media/exports/{filename}"  # Placeholder URL

    # --- Notify User (Example: Email) ---
    # send_mail(
    #     'Your Qader Statistics Export is Ready',
    #     f'Hello {requesting_user.username},\n\nYour requested data export is complete.\n\nYou can download it here: {file_url}\n\nRegards,\nThe Qader Team',
    #     settings.DEFAULT_FROM_EMAIL,
    #     [requesting_user.email],
    #     fail_silently=False,
    # )

    return {"status": "SUCCESS", "filename": filename, "file_url": file_url}
