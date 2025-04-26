import datetime
import csv
import openpyxl  # Requires: pip install openpyxl
from io import StringIO, BytesIO
from django.utils import timezone
from django.http import HttpResponse  # Import HttpResponse
from django.db.models import Count, Avg, Q, F, FloatField
from django.db.models.functions import TruncDate, Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)

from apps.users.models import UserProfile
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from apps.learning.models import Question, LearningSection

# Import base serializer if needed for validation, but not for response
from ..serializers import statistics as stats_serializers

# --- Helper Functions (Keep the existing one) ---


def get_date_filters(request):
    """Parses date_from and date_to query parameters"""
    today = timezone.now().date()
    # Default to last 30 days if no params provided
    default_from = today - datetime.timedelta(days=30)

    date_from_str = request.query_params.get("date_from")
    date_to_str = request.query_params.get("date_to")

    try:
        date_from = (
            datetime.datetime.strptime(date_from_str, "%Y-%m-%d").date()
            if date_from_str
            else default_from
        )
    except ValueError:
        raise drf_serializers.ValidationError(
            {"date_from": "Invalid date format. Use YYYY-MM-DD."}
        )

    try:
        # Include the whole 'to' day by setting time to end of day or adding one day for filtering
        date_to = (
            datetime.datetime.strptime(date_to_str, "%Y-%m-%d").date()
            if date_to_str
            else today
        )
        # Make date_to inclusive for filtering (e.g., filter < date_to + 1 day)
        datetime_to = timezone.make_aware(
            datetime.datetime.combine(date_to, datetime.time.max)
        )
    except ValueError:
        raise drf_serializers.ValidationError(
            {"date_to": "Invalid date format. Use YYYY-MM-DD."}
        )

    datetime_from = timezone.make_aware(
        datetime.datetime.combine(date_from, datetime.time.min)
    )

    return (
        datetime_from,
        datetime_to,
        date_from,
        date_to,
    )  # Return both datetime and date versions


# --- API Views ---


class AdminStatisticsOverviewAPIView(APIView):
    """
    (Keep this view as it was in the previous step)
    Provides aggregated statistics about platform usage for the admin dashboard.
    Supports filtering by date range.
    """

    permission_classes = [IsAdminUser]
    # Ensure the Overview Serializer is imported and set
    serializer_class = stats_serializers.AdminStatisticsOverviewSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "date_from",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD). Defaults to 30 days ago.",
            ),
            OpenApiParameter(
                "date_to",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD). Defaults to today.",
            ),
        ],
        responses={200: serializer_class},  # Correct serializer reference
        tags=["Admin Panel - Statistics"],  # Correct tag
    )
    def get(self, request, *args, **kwargs):
        # ... (Keep the implementation from the previous step) ...
        try:
            datetime_from, datetime_to, date_from, date_to = get_date_filters(request)
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # --- Perform Aggregations ---
        active_students_q = UserProfile.objects.filter(
            role=UserProfile.RoleChoices.STUDENT,
            subscription_expires_at__gte=timezone.now(),
        )
        total_active_students = active_students_q.count()
        new_registrations_period = UserProfile.objects.filter(
            role=UserProfile.RoleChoices.STUDENT,
            user__date_joined__range=(datetime_from, datetime_to),
        ).count()
        attempts_in_period = UserQuestionAttempt.objects.filter(
            attempted_at__range=(datetime_from, datetime_to)
        )
        tests_in_period = UserTestAttempt.objects.filter(
            start_time__range=(datetime_from, datetime_to)
        )
        completed_tests_in_period = tests_in_period.filter(
            status=UserTestAttempt.Status.COMPLETED
        )
        total_questions_answered_period = attempts_in_period.count()
        total_tests_completed_period = completed_tests_in_period.count()
        overall_average_test_score = completed_tests_in_period.aggregate(
            avg_score=Avg("score_percentage")
        )["avg_score"]
        overall_average_accuracy = attempts_in_period.aggregate(
            avg_acc=Avg(Cast("is_correct", FloatField())) * 100
        )["avg_acc"]
        section_performance = []
        for section in LearningSection.objects.all().order_by("order"):
            section_attempts = attempts_in_period.filter(
                question__subsection__section=section
            )
            section_agg = section_attempts.aggregate(
                avg_acc=Avg(Cast("is_correct", FloatField())) * 100,
                total_attempts=Count("id"),
            )
            section_performance.append(
                {
                    "section_name": section.name,
                    "section_slug": section.slug,
                    "average_accuracy": section_agg["avg_acc"],
                    "total_attempts": section_agg["total_attempts"],
                }
            )
        min_attempts_threshold = 10
        most_attempted_q = (
            attempts_in_period.values("question_id")
            .annotate(attempt_count=Count("id"))
            .order_by("-attempt_count")[:5]
        )
        most_attempted_ids = [item["question_id"] for item in most_attempted_q]
        most_attempted_questions_details = Question.objects.filter(
            id__in=most_attempted_ids
        ).values("id", "question_text")
        most_attempted_map = {
            item["question_id"]: item["attempt_count"] for item in most_attempted_q
        }
        most_attempted_results = [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "attempt_count": most_attempted_map.get(q["id"]),
            }
            for q in most_attempted_questions_details
        ]
        lowest_accuracy_q = (
            attempts_in_period.values("question_id")
            .annotate(
                total_attempts=Count("id"),
                correct_attempts=Count("id", filter=Q(is_correct=True)),
                accuracy_rate=Cast(Count("id", filter=Q(is_correct=True)), FloatField())
                / Cast(Count("id"), FloatField())
                * 100,
            )
            .filter(total_attempts__gte=min_attempts_threshold)
            .order_by("accuracy_rate")[:5]
        )
        lowest_accuracy_ids = [item["question_id"] for item in lowest_accuracy_q]
        lowest_accuracy_questions_details = Question.objects.filter(
            id__in=lowest_accuracy_ids
        ).values("id", "question_text")
        lowest_accuracy_map = {
            item["question_id"]: item["accuracy_rate"] for item in lowest_accuracy_q
        }
        lowest_accuracy_results = [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "accuracy_rate": lowest_accuracy_map.get(q["id"]),
            }
            for q in lowest_accuracy_questions_details
        ]
        daily_activity_data = (
            attempts_in_period.annotate(date=TruncDate("attempted_at"))
            .values("date")
            .annotate(questions_answered=Count("id"))
            .order_by("date")
        )
        daily_tests_data = (
            completed_tests_in_period.annotate(date=TruncDate("start_time"))
            .values("date")
            .annotate(tests_completed=Count("id"))
            .order_by("date")
        )
        merged_daily = {}
        for item in daily_activity_data:
            merged_daily[item["date"]] = {
                "date": item["date"],
                "questions_answered": item["questions_answered"],
                "tests_completed": 0,
            }
        for item in daily_tests_data:
            if item["date"] in merged_daily:
                merged_daily[item["date"]]["tests_completed"] = item["tests_completed"]
            else:
                merged_daily[item["date"]] = {
                    "date": item["date"],
                    "questions_answered": 0,
                    "tests_completed": item["tests_completed"],
                }
        final_daily_activity = sorted(merged_daily.values(), key=lambda x: x["date"])

        # --- Prepare Response Data ---
        data = {
            "total_active_students": total_active_students,
            "new_registrations_period": new_registrations_period,
            "total_questions_answered_period": total_questions_answered_period,
            "total_tests_completed_period": total_tests_completed_period,
            "overall_average_test_score": overall_average_test_score,
            "overall_average_accuracy": overall_average_accuracy,
            "performance_by_section": section_performance,
            "most_attempted_questions": most_attempted_results,
            "lowest_accuracy_questions": lowest_accuracy_results,
            "daily_activity": final_daily_activity,
        }

        serializer = self.serializer_class(
            instance=data
        )  # Use the imported Overview serializer
        return Response(serializer.data)


class AdminStatisticsExportAPIView(APIView):
    """
    Generates and returns a statistics data export file (CSV or XLSX) synchronously.
    Supports filtering by date range and export format.
    **Note:** May time out for very large datasets. Consider async implementation for production.
    """

    permission_classes = [IsAdminUser]
    # No serializer_class needed here for the response itself

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "format",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Export format ('csv' or 'xlsx'). Default: 'csv'.",
            ),
            OpenApiParameter(
                "date_from",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Start date for filtering (YYYY-MM-DD). Defaults to 30 days ago.",
            ),
            OpenApiParameter(
                "date_to",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="End date for filtering (YYYY-MM-DD). Defaults to today.",
            ),
            # Add other filters mirroring the overview endpoint if needed
        ],
        request=None,  # No request body for GET
        responses={
            202: stats_serializers.ExportTaskResponseSerializer,
            400: OpenApiResponse(description="Bad Request - Invalid parameters"),
            403: OpenApiResponse(
                description="Forbidden - User does not have permission"
            ),
        },
        tags=["Admin Panel - Statistics"],  # Correct tag
    )
    def get(self, request, *args, **kwargs):
        export_format = request.query_params.get("format", "csv").lower()
        if export_format not in ["csv", "xlsx"]:
            return Response(
                {"format": "Invalid format. Choose 'csv' or 'xlsx'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            datetime_from, datetime_to, date_from, date_to = get_date_filters(
                request
            )  # Reuse helper
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # --- Query Data Based on Filters ---
        # Example: Exporting completed test attempts data
        queryset = UserTestAttempt.objects.select_related(
            "user__profile", "test_definition"
        )
        if datetime_from and datetime_to:
            queryset = queryset.filter(start_time__range=(datetime_from, datetime_to))
        queryset = queryset.filter(status=UserTestAttempt.Status.COMPLETED).order_by(
            "start_time"
        )
        # Add more complex filtering based on query params if needed

        # --- Generate File Content ---
        filename = f"qader_stats_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        content_type = None
        file_content = None

        try:
            # Example assuming you have a Celery task defined
            # task = export_statistics_task.delay(
            #     user_id=request.user.id, # ID of admin requesting
            #     export_format=export_format,
            #     filters={
            #         'date_from': date_from.isoformat(),
            #         'date_to': date_to.isoformat(),
            #         # Pass other filters here
            #     }
            # )
            if export_format == "csv":
                output = StringIO()
                writer = csv.writer(output)
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
                    "Status",
                ]
                writer.writerow(headers)
                # Write Data
                for (
                    attempt
                ) in queryset.iterator():  # Use iterator for potentially large datasets
                    writer.writerow(
                        [
                            attempt.id,
                            attempt.user.id,
                            attempt.user.username,
                            (
                                attempt.test_definition.name
                                if attempt.test_definition
                                else "N/A (e.g., Level Assessment)"
                            ),
                            attempt.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            attempt.score_percentage,
                            attempt.score_verbal,
                            attempt.score_quantitative,
                            attempt.get_status_display(),  # Get human-readable status
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
                    "Status",
                ]
                sheet.append(headers)
                # Write Data
                for attempt in queryset.iterator():
                    sheet.append(
                        [
                            attempt.id,
                            attempt.user.id,
                            attempt.user.username,
                            (
                                attempt.test_definition.name
                                if attempt.test_definition
                                else "N/A (e.g., Level Assessment)"
                            ),
                            attempt.start_time.replace(
                                tzinfo=None
                            ),  # Remove timezone for Excel
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

            # --- Create and Return HttpResponse ---
            response = HttpResponse(file_content, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            # Log the error properly in a real application
            print(f"Error generating export file: {e}")
            # Return a standard DRF error response instead of generic HTTP 500
            return Response(
                {"detail": "An error occurred while generating the export file."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
