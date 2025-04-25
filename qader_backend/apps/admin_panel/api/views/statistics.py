# qader_backend/apps/admin_panel/api/views/statistics.py
import datetime
from django.utils import timezone
from django.db.models import Count, Avg, Q, F, FloatField
from django.db.models.functions import TruncDate, Cast
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers as drf_serializers  # Use alias
from rest_framework.permissions import (
    IsAdminUser,
)  # Use your specific permission if needed
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from apps.users.models import RoleChoices, UserProfile
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from apps.learning.models import Question, LearningSection
from ..serializers import statistics as stats_serializers

# Import your Celery task if using async export
# from ..tasks import export_statistics_task

# --- Helper Functions (Consider moving to a utils module) ---


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
    Provides aggregated statistics about platform usage for the admin dashboard.
    Supports filtering by date range.
    """

    permission_classes = [IsAdminUser]
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
            # Add other filters like subscription_type, school_id etc. here if implemented
        ],
        responses={200: serializer_class},
        tags=["Admin Panel - Statistics"],
    )
    def get(self, request, *args, **kwargs):
        try:
            datetime_from, datetime_to, date_from, date_to = get_date_filters(request)
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # --- Perform Aggregations ---

        # User Stats
        active_students_q = UserProfile.objects.filter(
            role=RoleChoices.STUDENT,
            subscription_expires_at__gte=timezone.now(),
        )
        total_active_students = active_students_q.count()
        new_registrations_period = UserProfile.objects.filter(
            role=RoleChoices.STUDENT,
            user__date_joined__range=(datetime_from, datetime_to),
        ).count()

        # Activity Stats within the period
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

        # Performance Stats
        overall_average_test_score = completed_tests_in_period.aggregate(
            avg_score=Avg("score_percentage")
        )["avg_score"]

        overall_average_accuracy = attempts_in_period.aggregate(
            avg_acc=Avg(Cast("is_correct", FloatField()))
            * 100  # Cast Boolean to 0.0/1.0 for Avg
        )["avg_acc"]

        # Performance by Section
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

        # Top / Difficult Questions (Limit for performance)
        min_attempts_threshold = (
            10  # Only consider questions attempted at least N times
        )
        most_attempted_q = (
            attempts_in_period.values("question_id")
            .annotate(attempt_count=Count("id"))
            .order_by("-attempt_count")[:5]
        )  # Top 5

        # Fetch question details for the top IDs
        most_attempted_ids = [item["question_id"] for item in most_attempted_q]
        most_attempted_questions_details = Question.objects.filter(
            id__in=most_attempted_ids
        ).values("id", "question_text")
        # Combine counts with details
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
        )  # Lowest 5

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

        # Daily Activity for Charts
        daily_activity_data = (
            attempts_in_period.annotate(date=TruncDate("attempted_at"))
            .values("date")
            .annotate(questions_answered=Count("id"))
            .order_by("date")
        )

        # Combine with daily test completions (might need separate query and merge)
        daily_tests_data = (
            completed_tests_in_period.annotate(date=TruncDate("start_time"))
            .values("date")
            .annotate(tests_completed=Count("id"))
            .order_by("date")
        )

        # Merge daily data (example using dicts - more robust merging might be needed)
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
            else:  # Handle days with only tests completed
                merged_daily[item["date"]] = {
                    "date": item["date"],
                    "questions_answered": 0,
                    "tests_completed": item["tests_completed"],
                }

        # Ensure all dates in the range are present, even with zero activity (more complex - requires date generation)
        # For simplicity now, only include days with activity
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

        serializer = self.serializer_class(instance=data)
        return Response(serializer.data)


class AdminStatisticsExportAPIView(APIView):
    """
    Triggers an asynchronous task to export platform statistics data.
    Supports filtering by date range and export format.
    """

    permission_classes = [IsAdminUser]
    serializer_class = stats_serializers.AdminStatisticsExportSerializer

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
            400: OpenApiTypes.OBJECT,  # For validation errors
        },
        tags=["Admin Panel - Statistics"],
    )
    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        export_format = validated_data.get("format", "csv")

        try:
            datetime_from, datetime_to, date_from, date_to = get_date_filters(
                request
            )  # Reuse helper
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # --- Trigger Asynchronous Task (Requires Celery setup) ---
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

            # --- Placeholder Response (If Celery is not set up yet) ---
            # Simulate task ID generation
            import uuid

            task_id = str(uuid.uuid4())
            print(
                f"Simulating export task start (ID: {task_id}) for format: {export_format} from {date_from} to {date_to}"
            )
            # ----------------------------------------------------------

            response_data = {
                "task_id": task_id,
                "message": f"Export task started in {export_format} format. You will be notified upon completion.",
                # "status_check_url": request.build_absolute_uri(reverse('admin_panel:admin-export-task-status', args=[task.id])) # Optional
            }
            response_serializer = stats_serializers.ExportTaskResponseSerializer(
                response_data
            )
            return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            # Log the error properly in a real application
            print(f"Error triggering export task: {e}")
            return Response(
                {"detail": "Failed to start export task."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# Optional: View to check task status
# class ExportTaskStatusAPIView(APIView):
#     permission_classes = [IsAdminUser]
#     def get(self, request, task_id, *args, **kwargs):
#         # Implementation to check Celery task status by ID
#         # from celery.result import AsyncResult
#         # task_result = AsyncResult(task_id)
#         # response_data = {
#         #     'task_id': task_id,
#         #     'status': task_result.status,
#         #     'result': task_result.result if task_result.ready() else None
#         # }
#         # return Response(response_data)
#         return Response({"detail": "Status check endpoint not fully implemented."}, status=status.HTTP_501_NOT_IMPLEMENTED)
