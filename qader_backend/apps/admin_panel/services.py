import csv
import openpyxl
from io import StringIO, BytesIO

from django.db.models import Count
from django.utils import timezone
from apps.study.models import UserTestAttempt
from apps.users.models import UserProfile  # NEW IMPORT


def get_filtered_test_attempts(filters: dict):
    """
    Retrieves and filters UserTestAttempt queryset based on provided filters.
    This is the single source of truth for querying export data.
    """
    datetime_from = filters.get("datetime_from")
    datetime_to = filters.get("datetime_to")

    # Start with a base queryset.
    queryset = UserTestAttempt.objects.filter(status=UserTestAttempt.Status.COMPLETED)

    # Apply date filters if they exist.
    # Note: The view now passes date strings, so we can filter directly.
    if datetime_from and datetime_to:
        queryset = queryset.filter(start_time__range=(datetime_from, datetime_to))
    elif datetime_from:
        queryset = queryset.filter(start_time__gte=datetime_from)
    elif datetime_to:
        queryset = queryset.filter(start_time__lte=datetime_to)

    # --- OPTIMIZATION & ENRICHMENT ---
    # Eagerly load related data to prevent N+1 queries in the loop.
    # We need user details and test definition details.
    queryset = queryset.select_related("user", "test_definition")

    # Use annotation to efficiently count answered questions for each attempt.
    # This prevents a separate DB query for every row in the export.
    queryset = queryset.annotate(answered_question_count_agg=Count("question_attempts"))

    # Add any other future filters here from the 'filters' dict
    # e.g., if filters.get('user_id'): queryset = queryset.filter(...)

    return queryset.order_by("-start_time")


def generate_export_file_content(queryset, export_format: str):
    """
    Generates file content (CSV or XLSX) from a queryset.
    This is the single source of truth for file generation logic.
    Provides a rich, meaningful set of columns for analysis.
    """
    # --- NEW, MORE INFORMATIVE HEADERS ---
    headers = [
        "Attempt ID",
        "User ID",
        "Username",
        "User Full Name",
        "User Email",
        "Attempt Type",
        "Test Name",
        "Test Definition Type",
        "Status",
        "Start Time (UTC)",
        "End Time (UTC)",
        "Duration (Minutes)",
        "Total Questions in Test",
        "Questions Answered",
        "Overall Score (%)",
        "Verbal Score (%)",
        "Quantitative Score (%)",
    ]
    filename = f"qader_test_attempts_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
    content_type = None
    file_content = None

    # Use iterator() to handle large querysets efficiently by processing
    # records in chunks, reducing memory usage.
    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for attempt in queryset.iterator():
            # Handle cases where related objects might be null
            test_def_name = (
                attempt.test_definition.name
                if attempt.test_definition
                else "N/A (Traditional Practice)"
            )
            test_def_type = (
                attempt.test_definition.get_test_type_display()
                if attempt.test_definition
                else "N/A"
            )
            duration_minutes = (
                round(attempt.duration_seconds / 60, 2)
                if attempt.duration_seconds is not None
                else None
            )

            writer.writerow(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.user.get_full_name(),
                    attempt.user.email,
                    attempt.get_attempt_type_display(),
                    test_def_name,
                    test_def_type,
                    attempt.get_status_display(),
                    attempt.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        attempt.end_time.strftime("%Y-%m-%d %H:%M:%S")
                        if attempt.end_time
                        else None
                    ),
                    duration_minutes,
                    attempt.num_questions,
                    attempt.answered_question_count_agg,  # Use the efficient annotated value
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
        sheet.append(headers)
        for attempt in queryset.iterator():
            # Handle cases where related objects might be null
            test_def_name = (
                attempt.test_definition.name
                if attempt.test_definition
                else "N/A (Traditional Practice)"
            )
            test_def_type = (
                attempt.test_definition.get_test_type_display()
                if attempt.test_definition
                else "N/A"
            )
            duration_minutes = (
                round(attempt.duration_seconds / 60, 2)
                if attempt.duration_seconds is not None
                else None
            )

            # Excel doesn't handle timezone-aware datetimes well, so we remove tzinfo
            start_time_naive = attempt.start_time.replace(tzinfo=None)
            end_time_naive = (
                attempt.end_time.replace(tzinfo=None) if attempt.end_time else None
            )

            sheet.append(
                [
                    attempt.id,
                    attempt.user.id,
                    attempt.user.username,
                    attempt.user.get_full_name(),
                    attempt.user.email,
                    attempt.get_attempt_type_display(),
                    test_def_name,
                    test_def_type,
                    attempt.get_status_display(),
                    start_time_naive,
                    end_time_naive,
                    duration_minutes,
                    attempt.num_questions,
                    attempt.answered_question_count_agg,  # Use the efficient annotated value
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

    return file_content, content_type, filename


# --- NEW SERVICE FUNCTIONS FOR USER EXPORT ---


def get_filtered_users(filters: dict):
    """
    Retrieves and filters UserProfile queryset based on provided filters.
    This is the single source of truth for querying user export data.
    """
    # Eagerly load related data to prevent N+1 queries.
    queryset = UserProfile.objects.select_related(
        "user", "assigned_mentor__user", "referred_by"
    ).all()

    # --- APPLY FILTERS ---
    # Example: You could add filters from the user management list here
    # if filters.get('role'):
    #     queryset = queryset.filter(role__in=filters.get('role'))
    # if filters.get('account_type'):
    #     queryset = queryset.filter(account_type=filters.get('account_type'))
    # if filters.get('is_active'):
    #     queryset = queryset.filter(user__is_active=filters.get('is_active'))

    return queryset.order_by("-user__date_joined")


def generate_user_export_file_content(queryset, export_format: str):
    """
    Generates file content (CSV or XLSX) for User data from a queryset.
    """
    headers = [
        "User ID",
        "Username",
        "Full Name",
        "Preferred Name",
        "Email",
        "Role",
        "Account Type",
        "Is Active",
        "Is Subscribed",
        "Subscription Expires At (UTC)",
        "Date Joined (UTC)",
        "Last Login (UTC)",
        "Gender",
        "Grade",
        "Taken Qiyas Before",
        "Points",
        "Current Streak (Days)",
        "Longest Streak (Days)",
        "Verbal Level (%)",
        "Quantitative Level (%)",
        "Referral Code",
        "Referred By (Username)",
        "Assigned Mentor",
    ]
    filename = f"qader_users_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
    content_type = None
    file_content = None

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for profile in queryset.iterator():
            writer.writerow(
                [
                    profile.user_id,
                    profile.user.username,
                    profile.full_name,
                    profile.preferred_name,
                    profile.user.email,
                    profile.get_role_display(),
                    profile.get_account_type_display(),
                    profile.user.is_active,
                    profile.is_subscribed,
                    (
                        profile.subscription_expires_at.strftime("%Y-%m-%d %H:%M:%S")
                        if profile.subscription_expires_at
                        else None
                    ),
                    profile.user.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        profile.user.last_login.strftime("%Y-%m-%d %H:%M:%S")
                        if profile.user.last_login
                        else None
                    ),
                    profile.get_gender_display(),
                    profile.get_grade_display(),
                    profile.has_taken_qiyas_before,
                    profile.points,
                    profile.current_streak_days,
                    profile.longest_streak_days,
                    profile.current_level_verbal,
                    profile.current_level_quantitative,
                    profile.referral_code,
                    profile.referred_by.username if profile.referred_by else None,
                    (
                        profile.assigned_mentor.user.username
                        if profile.assigned_mentor
                        else None
                    ),
                ]
            )
        file_content = output.getvalue().encode("utf-8")
        content_type = "text/csv"

    elif export_format == "xlsx":
        output = BytesIO()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Users"
        sheet.append(headers)
        for profile in queryset.iterator():
            sheet.append(
                [
                    profile.user_id,
                    profile.user.username,
                    profile.full_name,
                    profile.preferred_name,
                    profile.user.email,
                    profile.get_role_display(),
                    profile.get_account_type_display(),
                    profile.user.is_active,
                    profile.is_subscribed,
                    (
                        profile.subscription_expires_at.replace(tzinfo=None)
                        if profile.subscription_expires_at
                        else None
                    ),
                    profile.user.date_joined.replace(tzinfo=None),
                    (
                        profile.user.last_login.replace(tzinfo=None)
                        if profile.user.last_login
                        else None
                    ),
                    profile.get_gender_display(),
                    profile.get_grade_display(),
                    profile.has_taken_qiyas_before,
                    profile.points,
                    profile.current_streak_days,
                    profile.longest_streak_days,
                    profile.current_level_verbal,
                    profile.current_level_quantitative,
                    profile.referral_code,
                    profile.referred_by.username if profile.referred_by else None,
                    (
                        profile.assigned_mentor.user.username
                        if profile.assigned_mentor
                        else None
                    ),
                ]
            )
        workbook.save(output)
        file_content = output.getvalue()
        content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    return file_content, content_type, filename
