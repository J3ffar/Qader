import datetime
import csv
import django_filters
import openpyxl
from io import StringIO, BytesIO
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Count, Avg, Q, F, FloatField, Case, When, IntegerField
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
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


from apps.users.models import UserProfile
from apps.study.models import UserQuestionAttempt, UserTestAttempt
from apps.learning.models import Question, LearningSection
from apps.users.constants import RoleChoices

# Import base serializer if needed for validation, but not for response
from ..serializers import statistics as stats_serializers

from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import the custom permission

# Import the new services
from apps.admin_panel import services as admin_services

# Import the new models and tasks
from apps.admin_panel.models import ExportJob
from apps.admin_panel.tasks import process_export_job

# --- Helper Functions ---


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

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    required_permissions = ["view_aggregated_statistics"]
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
        try:
            datetime_from, datetime_to, date_from, date_to = get_date_filters(request)
        except drf_serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)

        # Define a reusable expression to calculate accuracy
        accuracy_expression = (
            Avg(
                Case(
                    When(is_correct=True, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
            * 100
        )

        # --- Perform Aggregations ---
        active_students_q = UserProfile.objects.filter(
            role=RoleChoices.STUDENT,
            subscription_expires_at__gte=timezone.now(),
        )
        total_active_students = active_students_q.count()
        new_registrations_period = UserProfile.objects.filter(
            role=RoleChoices.STUDENT,
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
            avg_acc=accuracy_expression
        )["avg_acc"]
        section_performance = []
        for section in LearningSection.objects.all().order_by("order"):
            section_attempts = attempts_in_period.filter(
                question__subsection__section=section
            )
            section_agg = section_attempts.aggregate(
                avg_acc=accuracy_expression,
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
            .annotate(
                attempt_count=Count("id"),
                accuracy_rate=accuracy_expression,
            )
            .order_by("-attempt_count")[:5]
        )
        most_attempted_ids = [item["question_id"] for item in most_attempted_q]
        most_attempted_questions_details = Question.objects.filter(
            id__in=most_attempted_ids
        ).values("id", "question_text")

        most_attempted_map = {
            item["question_id"]: {
                "attempt_count": item["attempt_count"],
                "accuracy_rate": item["accuracy_rate"],
            }
            for item in most_attempted_q
        }

        most_attempted_results = [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "attempt_count": most_attempted_map.get(q["id"], {}).get(
                    "attempt_count"
                ),
                "accuracy_rate": most_attempted_map.get(q["id"], {}).get(
                    "accuracy_rate"
                ),
            }
            for q in most_attempted_questions_details
        ]

        lowest_accuracy_q = (
            attempts_in_period.values("question_id")
            .annotate(
                attempt_count=Count("id"),
                accuracy_rate=accuracy_expression,
            )
            .filter(attempt_count__gte=min_attempts_threshold)
            .order_by("accuracy_rate")[:5]
        )
        lowest_accuracy_ids = [item["question_id"] for item in lowest_accuracy_q]
        lowest_accuracy_questions_details = Question.objects.filter(
            id__in=lowest_accuracy_ids
        ).values("id", "question_text")

        lowest_accuracy_map = {
            item["question_id"]: {
                "accuracy_rate": item["accuracy_rate"],
                "attempt_count": item["attempt_count"],
            }
            for item in lowest_accuracy_q
        }

        lowest_accuracy_results = [
            {
                "id": q["id"],
                "question_text": q["question_text"],
                "accuracy_rate": lowest_accuracy_map.get(q["id"], {}).get(
                    "accuracy_rate"
                ),
                "attempt_count": lowest_accuracy_map.get(q["id"], {}).get(
                    "attempt_count"
                ),
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

        serializer = self.serializer_class(instance=data)
        return Response(serializer.data)


class ExportJobFilter(django_filters.FilterSet):
    """
    FilterSet for the ExportJob model.

    Allows filtering by status, job type, format, and creation date range.
    Superusers can also filter by the requesting user's username.
    """

    # Allow filtering by one or more statuses (e.g., ?status=SUCCESS&status=FAILURE)
    status = django_filters.MultipleChoiceFilter(choices=ExportJob.Status.choices)

    # Allow filtering by one or more job types
    job_type = django_filters.MultipleChoiceFilter(choices=ExportJob.JobType.choices)

    # Filter by a date range for when the job was created
    created_at = django_filters.DateFromToRangeFilter()

    # Define a custom filter for username lookup, which is more user-friendly than ID.
    # We will add this field dynamically for superusers only.

    def __init__(self, *args, **kwargs):
        """Dynamically add a username filter if the request is from a superuser."""
        super().__init__(*args, **kwargs)
        request = kwargs.get("request")
        if request and request.user.is_superuser:
            self.filters["requesting_user__username"] = django_filters.CharFilter(
                lookup_expr="icontains",
                label="Requesting User's Username (Superuser only)",
            )

    class Meta:
        model = ExportJob
        fields = {
            "file_format": ["exact"],  # Simple exact match for format
            "created_at": [],  # Base field for the DateFromToRangeFilter
        }


# --- REFACTORED EXPORT VIEW ---
class ExportJobViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet to manage data export jobs.

    - `POST /api/v1/admin/statistics/export-jobs/`: Triggers a new export job for Test Attempts.
    - `POST /api/v1/admin/statistics/export-jobs/users/`: Triggers a new export job for Users.
    - `GET /api/v1/admin/statistics/export-jobs/`: Lists all historical export jobs for the user.
    - `GET /api/v1/admin/statistics/export-jobs/{id}/`: Retrieves the status and details of a specific job.
    """

    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ExportJobFilter
    ordering_fields = ["created_at", "completed_at", "job_type", "status"]
    required_permissions = ["export_data"]

    def get_queryset(self):
        """
        Users should only see their own export jobs, unless they are superadmins.
        """
        user = self.request.user
        if user.is_superuser:
            return ExportJob.objects.all()
        return ExportJob.objects.filter(requesting_user=user)

    def get_serializer_class(self):
        """Return different serializers for create vs. list/retrieve actions."""
        if self.action == "export_users":
            return stats_serializers.UserExportRequestSerializer
        if self.action == "create":
            return stats_serializers.AdminStatisticsExportSerializer
        return stats_serializers.ExportJobSerializer

    @extend_schema(
        summary="Trigger a Test Attempts Data Export",
        request=stats_serializers.AdminStatisticsExportSerializer,
        responses={202: stats_serializers.ExportTaskResponseSerializer},
        tags=["Admin Panel - Exports"],
    )
    def create(self, request, *args, **kwargs):
        """
        Accepts export parameters, creates an ExportJob record for TEST ATTEMPTS,
        and triggers a background task.
        """
        validation_serializer = self.get_serializer(data=request.data)
        validation_serializer.is_valid(raise_exception=True)
        validated_data = validation_serializer.validated_data

        date_from = validated_data.get("date_from")
        date_to = validated_data.get("date_to")

        filters_for_task = {
            "datetime_from": date_from.isoformat() if date_from else None,
            "datetime_to": date_to.isoformat() if date_to else None,
        }

        job = ExportJob.objects.create(
            requesting_user=request.user,
            job_type=ExportJob.JobType.TEST_ATTEMPTS,
            file_format=validated_data["format"],
            status=ExportJob.Status.PENDING,
            filters=filters_for_task,
        )

        # Trigger the generic Celery task
        process_export_job.delay(job_id=job.id)

        status_check_url = reverse(
            "api:v1:admin_panel:export-job-detail",
            kwargs={"pk": job.id},
            request=request,
        )
        response_data = {
            "job_id": job.id,
            "message": "تم استلام طلب التصدير الخاص بك وهو قيد المعالجة.",
            "status_check_url": status_check_url,
        }

        response_serializer = stats_serializers.ExportTaskResponseSerializer(
            data=response_data
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Trigger a User Data Export",
        request=stats_serializers.UserExportRequestSerializer,
        responses={202: stats_serializers.ExportTaskResponseSerializer},
        tags=["Admin Panel - Exports"],
    )
    @action(detail=False, methods=["post"], url_path="users")
    def export_users(self, request, *args, **kwargs):
        """
        Creates an ExportJob record for USER DATA and triggers a background task.
        Supports filtering by user role.
        """
        validation_serializer = stats_serializers.UserExportRequestSerializer(
            data=request.data
        )
        validation_serializer.is_valid(raise_exception=True)
        validated_data = validation_serializer.validated_data

        # `validated_data.get('role')` returns a set. We must convert it to a list.
        roles_filter = validated_data.get("role", [])

        # Prepare the filters dictionary, ensuring the role value is a list for JSON serialization.
        filters_for_task = {"role": list(roles_filter)}

        # The rest of the function remains the same.
        job = ExportJob.objects.create(
            requesting_user=request.user,
            job_type=ExportJob.JobType.USERS,
            file_format=validated_data["format"],
            status=ExportJob.Status.PENDING,
            filters=filters_for_task,
        )

        process_export_job.delay(job_id=job.id)

        status_check_url = reverse(
            "api:v1:admin_panel:export-job-detail",
            kwargs={"pk": job.id},
            request=request,
        )
        response_data = {
            "job_id": job.id,
            "message": "تم استلام طلب التصدير الخاص بك وهو قيد المعالجة.",
            "status_check_url": status_check_url,
        }

        response_serializer = stats_serializers.ExportTaskResponseSerializer(
            data=response_data
        )
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="List Data Export Jobs",
        responses={200: stats_serializers.ExportJobSerializer(many=True)},
        tags=["Admin Panel - Exports"],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a Data Export Job",
        responses={200: stats_serializers.ExportJobSerializer},
        tags=["Admin Panel - Exports"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
