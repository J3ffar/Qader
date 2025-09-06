import csv
import openpyxl
from io import StringIO, BytesIO
from django.db.models import Q
from django.db import transaction
from django.db.models import Count, QuerySet
from django.utils import timezone
from apps.study.models import UserTestAttempt
from apps.users.models import UserProfile  # NEW IMPORT
from rest_framework.exceptions import ValidationError

from apps.learning.models import (
    Question,
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
    MediaFile,
    Article,
)


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
    queryset = UserProfile.objects.select_related(
        "user", "assigned_mentor__user", "referred_by"
    ).all()

    # --- APPLY FILTERS FROM THE 'filters' DICTIONARY ---
    roles_to_filter = filters.get("role")

    # Check if a list of roles was provided and it's not empty
    if roles_to_filter:
        queryset = queryset.filter(role__in=roles_to_filter)

    # You can add more filters here in the future
    # account_type = filters.get('account_type')
    # if account_type:
    #     queryset = queryset.filter(account_type=account_type)

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


# --- NEW SERVICE FUNCTIONS FOR QUESTION IMPORT/EXPORT ---


def get_filtered_questions(filters: dict) -> QuerySet[Question]:
    """
    Applies filters to the Question queryset for export, mirroring AdminQuestionViewSet.
    """
    queryset = Question.objects.select_related(
        "subsection__section__test_type", "skill", "media_content", "article"
    ).all()

    # Apply filters from the 'filters' dictionary passed by the view
    if filters.get("subsection__section__test_type__id"):
        queryset = queryset.filter(
            subsection__section__test_type__id=filters[
                "subsection__section__test_type__id"
            ]
        )
    if filters.get("subsection__section__id"):
        queryset = queryset.filter(
            subsection__section__id=filters["subsection__section__id"]
        )
    # ... Add any other filters from AdminQuestionViewSet as needed ...
    if filters.get("is_active"):
        is_active_bool = str(filters["is_active"]).lower() in ["true", "1"]
        queryset = queryset.filter(is_active=is_active_bool)

    return queryset.order_by("id")


def generate_question_export_file_content(
    queryset: QuerySet[Question], export_format: str = "xlsx"
):
    """
    Generates a user-friendly Excel (XLSX) file from a question queryset.
    """
    headers = [
        "Question ID",
        "Question Text",
        "Is Active",
        "Option A",
        "Option B",
        "Option C",
        "Option D",
        "Correct Answer",
        "Explanation",
        "Hint",
        "Solution Summary",
        "Difficulty",
        "Test Type Name",
        "Section Name",
        "Sub-Section Name",
        "Skill Name",
        "Media Content Title",
        "Article Title",
    ]
    filename = (
        f"qader_questions_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
    )

    if export_format != "xlsx":
        raise NotImplementedError(
            "Only XLSX format is supported for question export for now."
        )

    output = BytesIO()
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Questions"
    sheet.append(headers)

    for q in queryset.iterator():
        sheet.append(
            [
                q.id,
                q.question_text,
                "TRUE" if q.is_active else "FALSE",
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
                q.correct_answer,
                q.explanation,
                q.hint,
                q.solution_method_summary,
                q.get_difficulty_display(),
                getattr(q.subsection.section.test_type, "name", ""),
                getattr(q.subsection.section, "name", ""),
                getattr(q.subsection, "name", ""),
                getattr(q.skill, "name", ""),
                getattr(q.media_content, "title", ""),
                getattr(q.article, "title", ""),
            ]
        )

    workbook.save(output)
    file_content = output.getvalue()
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return file_content, content_type, filename


@transaction.atomic
def process_question_import_file(file_obj, update_strategy: str):
    """
    Processes an uploaded Excel file to create or update questions.
    If classification items (Test Type, Section, etc.) do not exist, they are created automatically.
    """
    try:
        workbook = openpyxl.load_workbook(file_obj)
        sheet = workbook.active
    except Exception as e:
        raise ValidationError(f"Could not read the Excel file. Error: {str(e)}")

    headers = [cell.value for cell in sheet[1]]
    expected_headers = [
        "Question ID",
        "Question Text",
        "Is Active",
        "Option A",
        "Option B",
        "Option C",
        "Option D",
        "Correct Answer",
        "Explanation",
        "Hint",
        "Solution Summary",
        "Difficulty",
        "Test Type Name",
        "Section Name",
        "Sub-Section Name",
        "Skill Name",
        "Media Content Title",
        "Article Title",
    ]
    if headers != expected_headers:
        raise ValidationError(
            {
                "error": "Invalid file headers.",
                "expected_headers": expected_headers,
                "found_headers": headers,
            }
        )

    errors = []
    created_count = 0
    updated_count = 0
    difficulty_map = {v: k for k, v in Question.DifficultyLevel.choices}

    for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        data = dict(zip(headers, [cell.value for cell in row]))
        if not any(data.values()):
            continue  # Skip empty rows

        try:
            # --- MODIFIED: Use get_or_create for the entire hierarchy ---

            # 1. Get or Create Test Type
            test_type_name = data.get("Test Type Name")
            if not test_type_name:
                raise ValueError("'Test Type Name' is required.")
            test_type, created = TestType.objects.get_or_create(
                name=test_type_name,
                defaults={
                    "status": TestType.TestTypeStatus.ACTIVE
                },  # Sensible default if created
            )

            # 2. Get or Create Learning Section (linked to the Test Type)
            section_name = data.get("Section Name")
            if not section_name:
                raise ValueError("'Section Name' is required.")
            section, created = LearningSection.objects.get_or_create(
                name=section_name, test_type=test_type
            )

            # 3. Get or Create Learning Sub-Section (linked to the Section)
            subsection_name = data.get("Sub-Section Name")
            if not subsection_name:
                raise ValueError("'Sub-Section Name' is required.")
            subsection, created = LearningSubSection.objects.get_or_create(
                name=subsection_name, section=section, defaults={"is_active": True}
            )

            # 4. Get or Create Skill (if provided, linked to the Section and Sub-Section)
            skill = None
            skill_name = data.get("Skill Name")
            if skill_name:
                skill, created = Skill.objects.get_or_create(
                    name=skill_name,
                    section=section,
                    subsection=subsection,  # Create the skill in the most specific context
                    defaults={"is_active": True},
                )

            # --- End of Modified Section ---

            # Media and Article are still lookups only. We don't want to auto-create
            # empty library items. The admin should create these intentionally.
            media_content = (
                MediaFile.objects.get(title=data["Media Content Title"])
                if data.get("Media Content Title")
                else None
            )
            article = (
                Article.objects.get(title=data["Article Title"])
                if data.get("Article Title")
                else None
            )

            if media_content and article:
                raise ValueError("Cannot link both Media Content and an Article.")

            # --- Create or Update Logic (Unchanged) ---
            question_id = data.get("Question ID")
            question = (
                Question.objects.filter(id=question_id).first() if question_id else None
            )

            if question and update_strategy == "SKIP":
                continue

            if not question:
                question = Question()
                is_update = False
            else:
                is_update = True

            # Assigning values...
            question.question_text = data["Question Text"]
            question.is_active = str(data["Is Active"]).upper() == "TRUE"
            question.option_a, question.option_b = data["Option A"], data["Option B"]
            question.option_c, question.option_d = data["Option C"], data["Option D"]
            question.correct_answer = str(data["Correct Answer"]).upper()
            question.difficulty = difficulty_map[data["Difficulty"]]
            question.explanation, question.hint = data["Explanation"], data["Hint"]
            question.solution_method_summary = data["Solution Summary"]
            question.subsection = subsection
            question.skill, question.media_content, question.article = (
                skill,
                media_content,
                article,
            )

            question.full_clean()
            question.save()

            if is_update:
                updated_count += 1
            else:
                created_count += 1

        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")

    if errors:
        raise ValidationError(
            {"detail": "Import failed due to errors.", "errors": errors}
        )

    return {"created": created_count, "updated": updated_count}
