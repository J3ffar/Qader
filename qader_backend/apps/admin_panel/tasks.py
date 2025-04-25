# qader_backend/apps/admin_panel/tasks.py
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


@shared_task(bind=True)
def export_statistics_task(self, user_id, export_format, filters):
    """
    Celery task to export statistics data based on filters.
    """
    User = get_user_model()
    try:
        requesting_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        # Handle error: user not found
        return {"status": "FAILURE", "message": "Requesting user not found."}

    date_from = (
        datetime.datetime.fromisoformat(filters["date_from"]).date()
        if filters.get("date_from")
        else None
    )
    date_to = (
        datetime.datetime.fromisoformat(filters["date_to"]).date()
        if filters.get("date_to")
        else None
    )
    datetime_from = (
        timezone.make_aware(datetime.datetime.combine(date_from, datetime.time.min))
        if date_from
        else None
    )
    datetime_to = (
        timezone.make_aware(datetime.datetime.combine(date_to, datetime.time.max))
        if date_to
        else None
    )

    # --- Query Data Based on Filters ---
    queryset = UserTestAttempt.objects.select_related("user__profile", "test")
    if datetime_from and datetime_to:
        queryset = queryset.filter(start_time__range=(datetime_from, datetime_to))
    queryset = queryset.filter(status=UserTestAttempt.Status.COMPLETED)
    # Add more filters based on 'filters' dict

    # --- Generate File Content ---
    filename = (
        f"qader_stats_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
    )

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        # Write Header
        writer.writerow(
            [
                "Attempt ID",
                "User ID",
                "Username",
                "Test Name",
                "Start Time",
                "Score (%)",
                "Verbal Score",
                "Quant Score",
            ]
        )
        # Write Data
        for attempt in queryset.iterator():  # Use iterator for large datasets
            writer.writerow(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.test.name if attempt.test else "N/A",
                    attempt.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    attempt.score_percentage,
                    attempt.score_verbal,
                    attempt.score_quantitative,
                ]
            )
        file_content = output.getvalue().encode("utf-8")
        content_type = "text/csv"

    elif export_format == "xlsx":
        output = BytesIO()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Test Attempts"
        # Write Header
        headers = [
            "Attempt ID",
            "User ID",
            "Username",
            "Test Name",
            "Start Time",
            "Score (%)",
            "Verbal Score",
            "Quant Score",
        ]
        sheet.append(headers)
        # Write Data
        for attempt in queryset.iterator():
            sheet.append(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.test.name if attempt.test else "N/A",
                    attempt.start_time.replace(
                        tzinfo=None
                    ),  # Remove timezone for Excel
                    attempt.score_percentage,
                    attempt.score_verbal,
                    attempt.score_quantitative,
                ]
            )
        workbook.save(output)
        file_content = output.getvalue()
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    else:
        return {"status": "FAILURE", "message": f"Unsupported format: {export_format}"}

    # --- Save File (Example: To Django default storage) ---
    # from django.core.files.storage import default_storage
    # file_path = default_storage.save(f"exports/{filename}", ContentFile(file_content))
    # file_url = default_storage.url(file_path)

    # For simplicity, just print success for now without saving/emailing
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
