from rest_framework import (
    viewsets,
    permissions,
    filters,
    serializers,
    status,
    exceptions,
)
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import ProtectedError
from apps.learning.models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
)
from ..serializers.learning_management import (
    AdminLearningSectionSerializer,
    AdminLearningSubSectionSerializer,
    AdminSkillSerializer,
    AdminQuestionSerializer,
)
from ..permissions import (
    IsAdminUserOrSubAdminWithPermission,
)  # Import the custom permission
from django.db.models import Count

ADMIN_TAG = "Admin Panel - Learning Management"  # Tag for OpenAPI docs


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

    queryset = LearningSection.objects.all().order_by(  # pylint: disable=no-member
        "order", "name"
    )
    serializer_class = AdminLearningSectionSerializer
    permission_classes = [
        IsAdminUserOrSubAdminWithPermission
    ]  # Only allow Django admin users
    lookup_field = "pk"  # Use PK for admin management
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["order", "name", "created_at"]

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

    queryset = (
        LearningSubSection.objects.select_related(  # pylint: disable=no-member
            "section"
        )
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
    filterset_fields = ["section__slug", "section__id"]  # Filter by parent section
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

    queryset = (
        Skill.objects.select_related("subsection__section")  # pylint: disable=no-member
        .all()
        .order_by("subsection__section__order", "subsection__order", "name")
    )
    serializer_class = AdminSkillSerializer
    permission_classes = [IsAdminUserOrSubAdminWithPermission]
    lookup_field = "pk"
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = [
        "subsection__slug",
        "subsection__id",
    ]  # Filter by parent subsection
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "subsection__name", "created_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            self.required_permissions = ["api_manage_content"]
        elif self.action in ["create", "update", "partial_update", "destroy"]:
            self.required_permissions = ["api_manage_content"]
        else:
            self.required_permissions = []
        return [permission() for permission in self.permission_classes]


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
    filterset_fields = {
        "subsection__section__id": ["exact", "in"],
        "subsection__slug": ["exact", "in"],
        "subsection__id": ["exact", "in"],
        "skill__slug": ["exact", "in"],
        "skill__id": ["exact", "in"],
        "difficulty": ["exact", "in", "gte", "lte"],
        "is_active": ["exact"],
        "correct_answer": ["exact"],
    }
    search_fields = [
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "explanation",
        "hint",
        "solution_method_summary",
        "id",
    ]
    ordering_fields = [
        "id",
        "difficulty",
        "created_at",
        "updated_at",
        "is_active",
        "subsection__name",
        "skill__name",
        "total_usage_count",  # Allow ordering by the new annotated field
    ]

    def get_queryset(self):
        """
        Overrides the default queryset to include prefetching and annotations
        for performance.
        """
        # Start with the base queryset
        queryset = Question.objects.all()  # pylint: disable=no-member

        # Optimize by prefetching related data needed by the serializer
        queryset = queryset.select_related("subsection__section", "skill")

        # Annotate with the total number of times the question has been attempted.
        # This is highly efficient as it's a single database operation.
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
