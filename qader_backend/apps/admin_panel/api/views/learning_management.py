from rest_framework import (
    viewsets,
    permissions,
    filters,
    serializers,
    status,
    exceptions,
)
from rest_framework.parsers import MultiPartParser, FormParser  # NEW
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import ProtectedError
from apps.learning.models import (
    TestType,
    LearningSection,
    LearningSubSection,
    Skill,
    MediaFile,
    Article,
    Question,
)
from ..serializers.learning_management import (
    AdminTestTypeSerializer,
    AdminLearningSectionSerializer,
    AdminLearningSubSectionSerializer,
    AdminSkillSerializer,
    AdminMediaFileSerializer,
    AdminArticleSerializer,
    AdminQuestionSerializer,
)
from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import the custom permission
from django.db.models import Count

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

import openpyxl
from io import BytesIO
from django.http import HttpResponse

from apps.admin_panel.models import ExportJob
from apps.admin_panel import services as admin_services

from ..serializers.statistics import ExportTaskResponseSerializer
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from ...tasks import process_export_job

ADMIN_TAG = "Admin Panel - Learning Management"  # Tag for OpenAPI docs


# --- NEW: ViewSet for managing Test Types ---
@extend_schema_view(
    list=extend_schema(summary="List Test Types (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Create Test Type (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(summary="Retrieve Test Type (Admin)", tags=[ADMIN_TAG]),
    update=extend_schema(summary="Update Test Type (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Test Type (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Test Type (Admin)", tags=[ADMIN_TAG]),
)
class AdminTestTypeViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Test Types."""

    queryset = TestType.objects.all().order_by("order", "name")
    serializer_class = AdminTestTypeSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    lookup_field = "pk"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["order", "name", "status", "created_at"]

    def get_permissions(self):
        # Your permission logic here
        self.required_permissions = ["api_manage_content"]
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(summary="List Learning Sections (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Create Learning Section (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(
        summary="Retrieve Learning Section (Admin)", tags=[ADMIN_TAG]
    ),
    update=extend_schema(summary="Update Learning Section (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Learning Section (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Learning Section (Admin)", tags=[ADMIN_TAG]),
)
class AdminLearningSectionViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Learning Sections."""

    # MODIFIED: Optimized queryset with select_related
    queryset = (
        LearningSection.objects.select_related("test_type")
        .all()
        .order_by("test_type__order", "order", "name")
    )
    serializer_class = AdminLearningSectionSerializer
    permission_classes = [
        IsAdminUserOrSubAdminWithPermission
    ]  # Only allow Django admin users
    lookup_field = "pk"  # Use PK for admin management
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # MODIFIED: Add filtering by parent test type
    filterset_fields = ["test_type__id"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["order", "name", "created_at", "test_type__name"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


@extend_schema_view(
    list=extend_schema(summary="List Learning Sub-Sections (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(
        summary="Create Learning Sub-Section (Admin)", tags=[ADMIN_TAG]
    ),
    retrieve=extend_schema(
        summary="Retrieve Learning Sub-Section (Admin)", tags=[ADMIN_TAG]
    ),
    update=extend_schema(
        summary="Update Learning Sub-Section (Admin)", tags=[ADMIN_TAG]
    ),
    partial_update=extend_schema(
        summary="Partially Update Learning Sub-Section (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(
        summary="Delete Learning Sub-Section (Admin)", tags=[ADMIN_TAG]
    ),
)
class AdminLearningSubSectionViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Learning Sub-Sections."""

    # MODIFIED: Added test_type to select_related for efficiency
    queryset = (
        LearningSubSection.objects.select_related("section__test_type")
        .all()
        .order_by("section__order", "order", "name")
    )
    serializer_class = AdminLearningSubSectionSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    lookup_field = "pk"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # MODIFIED: Added hierarchical filtering
    filterset_fields = ["section__test_type__id", "section__id", "is_active"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["order", "name", "section__name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError as e:
            # Construct the APIException and set its status_code explicitly
            error_message = (
                f"Cannot delete subsection '{instance.name}'. "
                f"It is protected because related items exist (e.g., Questions)."
            )
            # You can optionally add a machine-readable code if desired
            # exc = exceptions.APIException(detail=error_message, code='protected_deletion_conflict')
            exc = exceptions.APIException(detail=error_message)
            exc.status_code = status.HTTP_409_CONFLICT
            raise exc


@extend_schema_view(
    list=extend_schema(summary="List Skills (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Create Skill (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(summary="Retrieve Skill (Admin)", tags=[ADMIN_TAG]),
    update=extend_schema(summary="Update Skill (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Skill (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Skill (Admin)", tags=[ADMIN_TAG]),
)
class AdminSkillViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Skills."""

    # MODIFIED: Updated queryset for new structure
    queryset = (
        Skill.objects.select_related("section", "subsection")
        .all()
        .order_by("section__order", "subsection__order", "name")
    )
    serializer_class = AdminSkillSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    lookup_field = "pk"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # MODIFIED: Updated filtering for new structure
    filterset_fields = ["section__id", "subsection__id", "is_active"]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "section__name", "subsection__name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


# --- NEW: Admin CRUD Viewsets for Content Libraries ---


@extend_schema_view(
    list=extend_schema(summary="List Media Files (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Upload Media File (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(summary="Retrieve Media File (Admin)", tags=[ADMIN_TAG]),
    update=extend_schema(summary="Update Media File (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Media File (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Media File (Admin)", tags=[ADMIN_TAG]),
)
class AdminMediaFileViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing the MediaFile library."""

    queryset = MediaFile.objects.all().order_by("-created_at")
    serializer_class = AdminMediaFileSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    # IMPORTANT: Add parsers to handle file uploads
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["file_type"]
    search_fields = ["title"]


@extend_schema_view(
    list=extend_schema(summary="List Articles (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Create Article (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(summary="Retrieve Article (Admin)", tags=[ADMIN_TAG]),
    update=extend_schema(summary="Update Article (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Article (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Article (Admin)", tags=[ADMIN_TAG]),
)
class AdminArticleViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing the Article library."""

    queryset = Article.objects.all().order_by("title")
    serializer_class = AdminArticleSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "content"]


@extend_schema_view(
    list=extend_schema(summary="List Questions (Admin)", tags=[ADMIN_TAG]),
    create=extend_schema(summary="Create Question (Admin)", tags=[ADMIN_TAG]),
    retrieve=extend_schema(summary="Retrieve Question (Admin)", tags=[ADMIN_TAG]),
    update=extend_schema(summary="Update Question (Admin)", tags=[ADMIN_TAG]),
    partial_update=extend_schema(
        summary="Partially Update Question (Admin)", tags=[ADMIN_TAG]
    ),
    destroy=extend_schema(summary="Delete Question (Admin)", tags=[ADMIN_TAG]),
)
class AdminQuestionViewSet(viewsets.ModelViewSet):
    """Admin ViewSet for managing Questions."""

    # Admin sees ALL questions, active or not
    # queryset is now defined in get_queryset to handle annotations
    serializer_class = AdminQuestionSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    lookup_field = "pk"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    # MODIFIED: Added full hierarchical filtering
    filterset_fields = {
        "subsection__section__test_type__id": ["exact"],
        "subsection__section__id": ["exact"],
        "subsection__id": ["exact"],
        "skills__id": ["exact", "in"], # MODIFIED: was "skill__id"
        "difficulty": ["exact", "in", "gte", "lte"],
        "is_active": ["exact"],
        "correct_answer": ["exact"],
    }
    search_fields = [
        "id",  # Added 'id' to search fields as requested
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "explanation",
        "hint",
        "solution_method_summary",
    ]
    ordering_fields = [
        "id",
        "difficulty",
        "created_at",
        "updated_at",
        "is_active",
        "subsection__name",
        "total_usage_count",
    ]

    def get_queryset(self):
        queryset = Question.objects.all()
        # MODIFIED: Update select_related for new structure
        queryset = queryset.select_related(
            "subsection__section__test_type", "media_content", "article"
        ).prefetch_related("skills") # MODIFIED
        queryset = queryset.annotate(total_usage_count=Count("user_attempts"))
        return queryset.order_by("-created_at")

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]

    @extend_schema(
        summary="Trigger a Question Data Export",
        tags=[ADMIN_TAG],
        description="""
        Triggers an asynchronous export of questions.
        This endpoint uses the **query parameters** from the main list view for filtering.
        For example: `/api/v1/admin/learning/questions/export/?is_active=true&difficulty=3`
        The request body should be empty.
        """,
        # request=None,  # Explicitly state there is no request body
        responses={202: ExportTaskResponseSerializer},
    )
    @action(detail=False, methods=["post"], url_path="export")
    def export_questions(self, request):
        """
        Triggers an asynchronous export of questions based on current filters.
        """
        job = ExportJob.objects.create(
            requesting_user=request.user,
            job_type=ExportJob.JobType.QUESTIONS,
            file_format=ExportJob.Format.XLSX,
            filters=request.query_params.dict(),
        )
        process_export_job.delay(job_id=job.id)
        status_check_url = reverse(
            "api:v1:admin_panel:export-job-detail",
            kwargs={"pk": job.id},
            request=request,
        )
        response_data = {
            "job_id": job.id,
            "message": "Your question export request has been received and is being processed.",
            "status_check_url": status_check_url,
        }
        serializer = ExportTaskResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @extend_schema(
        summary="Import Questions from XLSX",
        tags=[ADMIN_TAG],
        description="""
        Uploads an XLSX file to create new questions or update existing ones.
        The file format must match the template provided by the `/import-template/` endpoint.
        """,
        # THIS IS THE KEY CHANGE: Define the request body for file upload
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "update_strategy": {
                        "type": "string",
                        "enum": ["REPLACE", "SKIP"],
                        "default": "REPLACE",
                    },
                },
            }
        },
        responses={
            200: {
                "description": "Import successful.",
                "examples": {"application/json": {"created": 15, "updated": 5}},
            },
            400: {"description": "Validation error with details."},
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="import",
        parser_classes=[MultiPartParser],
    )
    def import_questions(self, request):
        """
        Imports questions from an uploaded XLSX file.
        - `file`: The XLSX file to upload.
        - `update_strategy`: 'SKIP' or 'REPLACE'. Defaults to 'REPLACE'.
        """
        # The Python logic here is already correct and does not need to change.
        file_obj = request.data.get("file")
        update_strategy = request.data.get("update_strategy", "REPLACE").upper()

        if not file_obj:
            return Response(
                {"error": "File not provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        if update_strategy not in ["SKIP", "REPLACE"]:
            return Response(
                {"error": "Invalid update_strategy. Choose 'SKIP' or 'REPLACE'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = admin_services.process_question_import_file(
                file_obj, update_strategy
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Download Question Import Template",
        tags=[ADMIN_TAG],
        description="Downloads a blank Excel template with the correct headers for importing questions.",
        request=None,  # No request body for a GET
        responses={
            200: {
                "description": "An Excel file template.",
                "content": {
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                        "schema": {"type": "string", "format": "binary"}
                    }
                },
            }
        },
    )
    @action(detail=False, methods=["get"], url_path="import-template")
    def get_import_template(self, request):
        """
        Downloads a blank Excel template with the correct headers for importing questions.
        """
        # The Python logic here is correct and does not need to change.
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

        output = BytesIO()
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Questions Import Template"
        sheet.append(headers)

        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="question_import_template.xlsx"'
        )
        return response
