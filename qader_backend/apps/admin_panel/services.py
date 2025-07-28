import csv
import openpyxl
from io import StringIO, BytesIO
from django.utils import timezone
from apps.study.models import UserTestAttempt


def get_filtered_test_attempts(filters: dict):
    """
    Retrieves and filters UserTestAttempt queryset based on provided filters.
    This is the single source of truth for querying export data.
    """
    datetime_from = filters.get("datetime_from")
    datetime_to = filters.get("datetime_to")

    # Start with a base queryset and prefetch related data to avoid N+1 queries
    queryset = UserTestAttempt.objects.select_related("user", "test_definition").filter(
        status=UserTestAttempt.Status.COMPLETED
    )

    if datetime_from and datetime_to:
        queryset = queryset.filter(start_time__range=(datetime_from, datetime_to))

    # Add any other future filters here from the 'filters' dict
    # e.g., if filters.get('user_id'): queryset = queryset.filter(...)

    return queryset.order_by("start_time")


def generate_export_file_content(queryset, export_format: str):
    """
    Generates file content (CSV or XLSX) from a queryset.
    This is the single source of truth for file generation logic.
    """
    headers = [
        "Attempt ID",
        "User ID",
        "Username",
        "Test Name",
        "Start Time",
        "Score (%)",
        "Verbal Score",
        "Quant Score",
        "Status",
    ]
    filename = (
        f"qader_stats_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
    )
    content_type = None
    file_content = None

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for attempt in queryset.iterator():
            writer.writerow(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.test_definition.name if attempt.test_definition else "N/A",
                    attempt.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    attempt.score_percentage,
                    attempt.score_verbal,
                    attempt.score_quantitative,
                    attempt.get_status_display(),
                ]
            )
        file_content = output.getvalue().encode("utf-8")
        content_type = "text/csv"

    elif export_format == "xlsx":
        output = BytesIO()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Test Attempts"
        sheet.append(headers)
        for attempt in queryset.iterator():
            sheet.append(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.test_definition.name if attempt.test_definition else "N/A",
                    attempt.start_time.replace(
                        tzinfo=None
                    ),  # Excel doesn't handle tzinfo well
                    attempt.score_percentage,
                    attempt.score_verbal,
                    attempt.score_quantitative,
                    attempt.get_status_display(),
                ]
            )
        workbook.save(output)
        file_content = output.getvalue()
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    return file_content, content_type, filename
