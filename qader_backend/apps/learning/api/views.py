from typing import Type, Any
from django.db.models import QuerySet, Exists, OuterRef, Q  # MODIFIED
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)

from apps.api.permissions import IsSubscribed
from rest_framework.permissions import IsAuthenticated
from ..models import (
    TestType,  # NEW
    LearningSection,
    LearningSubSection,
    Skill,
    MediaFile, # NEW
    Article,   # NEW
    Question,
    UserStarredQuestion,
)
from apps.study.models import UserSkillProficiency
from .serializers import (
    TestTypeSerializer,  # NEW
    LearningSectionSerializer,
    LearningSubSectionDetailSerializer,
    LearningSubSectionSerializer,
    SkillSerializer,
    MediaFileSerializer, # NEW
    ArticleSerializer,   # NEW
    UnifiedQuestionSerializer,
    StarActionSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List Test Types",
        description="Retrieves a list of all available test types (e.g., SAT, TOEFL).",
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Test Type",
        description="Retrieves details for a specific test type.",
        tags=["Learning Content"],
    ),
)
class TestTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and retrieving Test Types."""

    queryset = TestType.objects.filter(status=TestType.TestTypeStatus.ACTIVE).order_by(
        "order"
    )
    serializer_class = TestTypeSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


# --- UPDATED ViewSets with new filtering ---


@extend_schema_view(
    list=extend_schema(
        summary="List Learning Sections",
        description="Retrieves a list of main learning sections, now filterable by `test_type__slug`.",
        parameters=[
            OpenApiParameter(
                name="test_type__slug",
                description="Filter by parent Test Type slug",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Learning Section Details", tags=["Learning Content"]
    ),
)
class LearningSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Learning Sections.
    Provides read-only access to the main categories of learning content.
    Requires an active subscription.
    """

    queryset = (
        LearningSection.objects.select_related("test_type").all().order_by("order")
    )  # MODIFIED
    serializer_class = LearningSectionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["test_type__slug"]
    ordering_fields = ["order", "name"]
    ordering = ["order"]


@extend_schema_view(
    list=extend_schema(
        summary="List Learning Sub-Sections",
        description="Retrieves a list of learning sub-sections, filterable by `section__slug` or the top-level `section__test_type__slug`.",
        parameters=[
            OpenApiParameter(
                name="section__test_type__slug",
                description="Filter by the grandparent Test Type's slug.",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="section__slug",
                description="Filter by parent section slug.",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Learning Sub-Section Details", tags=["Learning Content"]
    ),
)
class LearningSubSectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        LearningSubSection.objects.filter(is_active=True)
        .select_related("section__test_type")
        .all()
        .order_by("section__order", "order")
    )  # MODIFIED
    serializer_class = LearningSubSectionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["section__slug", "section__test_type__slug"]
    ordering_fields = ["order", "name"]
    ordering = ["section__order", "order"]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action == "retrieve":
            return LearningSubSectionDetailSerializer
        return LearningSubSectionSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List Skills",
        description="Retrieves a list of skills, filterable by various hierarchical levels.",
        parameters=[
            OpenApiParameter(
                name="section__test_type__slug",
                description="Filter by the top-level Test Type's slug.",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="section__slug",
                description="Filter by parent section slug.",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="subsection__slug",
                description="Filter by parent subsection slug.",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(summary="Retrieve Skill Details", tags=["Learning Content"]),
)
class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Skill.objects.select_related(
            "subsection__section__test_type", "section__test_type"
        )
        .filter(is_active=True)
        .all()
    )  # MODIFIED
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["subsection__slug", "section__slug", "section__test_type__slug"]
    search_fields = ["name", "description"]
    ordering_fields = ["name"]
    ordering = ["section__order", "subsection__order", "name"]


# --- NEW: Read-only ViewSets for Content Libraries ---

@extend_schema_view(
    list=extend_schema(
        summary="List Media Files",
        description="Retrieves a list of all available media files (images, audio, video).",
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Media File",
        description="Retrieves details for a specific media file.",
        tags=["Learning Content"],
    ),
)
class MediaFileViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for retrieving media files from the library."""
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['file_type']
    search_fields = ['title']

@extend_schema_view(
    list=extend_schema(
        summary="List Articles",
        description="Retrieves a list of all available articles.",
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Article",
        description="Retrieves details for a specific article.",
        tags=["Learning Content"],
    ),
)
class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for retrieving articles from the library."""
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content']

# --- MODIFIED: QuestionViewSet ---


@extend_schema_view(
    list=extend_schema(
        summary="List Questions",
        description="Retrieves a paginated list of questions. Supports extensive hierarchical filtering.",
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Question Details", tags=["Learning Content"]
    ),
)
class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving Questions.

    Provides read-only access to questions, with different serializers for
    list (no answers) and detail (with answers) views. Supports filtering by
    subsection, skill, difficulty, user stars, search terms, and excluding IDs.
    Requires an active subscription.

    Includes custom actions to `star` and `unstar` questions.
    """

    queryset = Question.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]

    filterset_fields = {
        "subsection__section__test_type__slug": ["exact"],
        "subsection__section__slug": ["exact", "in"],
        "subsection__slug": ["exact", "in"],
        "skill__slug": ["exact", "in"],
        "difficulty": ["exact", "in", "gte", "lte"],
    }

    search_fields = [
        "id",  # Search by Question ID
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
        "subsection__name",
        "skill__name",
    ]
    ordering = ["id"]

    def get_serializer_class(self) -> Type[BaseSerializer]:
        if self.action in ["star", "unstar"]:
            return StarActionSerializer
        return UnifiedQuestionSerializer

    def get_queryset(self) -> QuerySet[Question]:
        queryset = super().get_queryset()
        user = self.request.user
        # MODIFIED: Optimize queries for new relationships
        queryset = queryset.select_related(
            "subsection__section__test_type",
            "skill__section",
            "media_content", # NEW
            "article"        # NEW
        )

        if user.is_authenticated:
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            queryset = queryset.annotate(user_has_starred=Exists(starred_subquery))
            is_starred_param = self.request.query_params.get("starred", "").lower()
            if is_starred_param == "true":
                queryset = queryset.filter(user_has_starred=True)
            elif is_starred_param == "false":
                queryset = queryset.filter(user_has_starred=False)
        elif is_starred_param in ["true", "false"]:
            # Cannot filter by starred status if user is not authenticated
            queryset = (
                queryset.none()
            )  # Return empty if anonymous user tries to filter by starred

        # Handle 'not_mastered=true' filter
        not_mastered_param = self.request.query_params.get("not_mastered", "").lower()
        if not_mastered_param == "true" and user.is_authenticated:
            # --- Add logic here to filter based on UserSkillProficiency ---
            mastery_threshold = (
                0.7  # Define threshold in settings settings.MASTERY_THRESHOLD
            )
            weak_skill_ids = UserSkillProficiency.objects.filter(
                user=user, proficiency_score__lt=mastery_threshold
            ).values_list("skill_id", flat=True)
            if weak_skill_ids.exists():
                queryset = queryset.filter(skill_id__in=list(weak_skill_ids))
            else:
                # If user has no weak skills, return empty or handle as needed
                queryset = queryset.none()
            pass  # Remove pass when implemented

        # Handle 'exclude_ids' filter more robustly
        exclude_ids_str = self.request.query_params.get("exclude_ids")
        if exclude_ids_str:
            try:
                # Split, filter empty strings, convert to int
                exclude_ids = [
                    int(id_val)
                    for id_val in exclude_ids_str.split(",")
                    if id_val.strip().isdigit()
                ]
                if exclude_ids:
                    queryset = queryset.exclude(id__in=exclude_ids)
            except ValueError:
                # Ignore invalid values in exclude_ids, potentially log a warning
                pass

        return queryset

    # --- Custom Actions for Star/Unstar ---

    @extend_schema(
        summary="Star a Question",
        description="Marks the specified question as starred (bookmarked) for the authenticated user. Requires standard authentication (not necessarily subscription).",
        request=None,
        responses={
            201: OpenApiResponse(
                description="Question successfully starred.",
                response=StarActionSerializer,
            ),
            200: OpenApiResponse(
                description="Question was already starred.",
                response=StarActionSerializer,
            ),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(description="Question not found."),
        },
        tags=["Learning Content"],
    )
    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def star(self, request: Request, pk: Any = None) -> Response:
        """Stars the question identified by pk for the current user."""
        question = self.get_object()  # Handles 404 if question not found
        user = request.user
        _, created = UserStarredQuestion.objects.get_or_create(
            user=user, question=question
        )
        serializer = self.get_serializer(
            {"status": "starred" if created else "already starred"}
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)

    @extend_schema(
        summary="Unstar a Question",
        description="Removes the star (bookmark) from the specified question for the authenticated user.",
        request=None,
        responses={
            204: OpenApiResponse(
                description="Question successfully unstarred (No Content)."
            ),
            401: OpenApiResponse(description="Authentication required."),
            404: OpenApiResponse(
                description="Question not found or not starred by this user."
            ),
        },
        tags=["Learning Content"],
    )
    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def unstar(self, request: Request, pk: Any = None) -> Response:
        question = self.get_object()
        deleted_count, _ = UserStarredQuestion.objects.filter(
            user=request.user, question=question
        ).delete()
        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Question exists but wasn't starred by this user, return 404
            return Response(
                {"detail": "Question not found or not starred by this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
