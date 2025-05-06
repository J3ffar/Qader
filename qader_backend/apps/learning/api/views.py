from typing import Type, Any
from django.db.models import QuerySet, Exists, OuterRef
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

from apps.api.permissions import (
    IsSubscribed,
)  # Assuming IsSubscribed checks for active subscription
from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)
from apps.study.models import UserSkillProficiency
from .serializers import (
    LearningSectionSerializer,
    LearningSubSectionDetailSerializer,
    LearningSubSectionSerializer,
    SkillSerializer,
    QuestionListSerializer,
    QuestionDetailSerializer,
    StarActionSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List Learning Sections",
        description="Retrieves a paginated list of main learning sections (e.g., Verbal, Quantitative), ordered by the 'order' field. Requires subscription.",
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Learning Section Details",
        description="Retrieves details of a specific learning section using its unique slug. Requires subscription.",
        tags=["Learning Content"],
    ),
)
class LearningSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Learning Sections.
    Provides read-only access to the main categories of learning content.
    Requires an active subscription.
    """

    queryset = LearningSection.objects.all().order_by("order")
    serializer_class = LearningSectionSerializer
    permission_classes = [IsSubscribed]  # Requires active subscription
    lookup_field = "slug"
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "name"]
    ordering = ["order"]  # Default ordering


@extend_schema_view(
    list=extend_schema(
        summary="List Learning Sub-Sections",
        description="Retrieves a paginated list of learning sub-sections (e.g., Reading Comprehension), optionally filtered by the parent section's slug (`section__slug`). Requires subscription.",
        parameters=[
            OpenApiParameter(
                name="section__slug",
                description="Filter by parent section slug (e.g., 'verbal')",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="page", description="Page number", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="page_size", description="Items per page", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="ordering",
                description="Field to order by (e.g., 'order', 'name')",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Learning Sub-Section Details",
        description="Retrieves details of a specific learning sub-section using its unique slug. Requires subscription.",
        tags=["Learning Content"],
        responses={200: LearningSubSectionDetailSerializer},
    ),
)
class LearningSubSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Learning Sub-Sections.
    Provides read-only access to categories within main learning sections.
    Requires an active subscription. Can be filtered by parent section slug.
    """

    queryset = (
        LearningSubSection.objects.filter(is_active=True)
        .select_related("section")
        .all()
        .order_by("section__order", "order")
    )
    serializer_class = LearningSubSectionSerializer
    permission_classes = [IsSubscribed]  # Requires active subscription
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["section__slug"]  # Allows filtering like ?section__slug=verbal
    ordering_fields = ["order", "name"]
    ordering = ["section__order", "order"]  # Default ordering

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """Return appropriate serializer class based on action."""
        if self.action == "retrieve":
            return (
                LearningSubSectionDetailSerializer  # Use detail serializer for retrieve
            )
        return LearningSubSectionSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List Skills",
        description="Retrieves a paginated list of specific skills (e.g., Solving Linear Equations), optionally filtered by parent sub-section slug (`subsection__slug`) or searched. Requires subscription.",
        parameters=[
            OpenApiParameter(
                name="subsection__slug",
                description="Filter by parent subsection slug (e.g., 'algebra-problems')",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="search",
                description="Search term for skill name or description",
                required=False,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="page", description="Page number", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="page_size", description="Items per page", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="ordering",
                description="Field to order by (e.g., 'name')",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Skill Details",
        description="Retrieves details of a specific skill using its unique slug. Requires subscription.",
        tags=["Learning Content"],
    ),
)
class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Skills.
    Provides read-only access to specific skills within learning sub-sections.
    Requires an active subscription. Can be filtered by parent subsection slug and searched.
    """

    queryset = (
        Skill.objects.select_related("subsection__section")
        .all()
        .order_by("subsection__section__order", "subsection__order", "name")
    )
    serializer_class = SkillSerializer
    permission_classes = [IsSubscribed]  # Requires active subscription
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = [
        "subsection__slug"
    ]  # Allows filtering like ?subsection__slug=algebra-problems
    search_fields = ["name", "description"]  # Allows searching like ?search=linear
    ordering_fields = ["name"]
    ordering = [
        "subsection__section__order",
        "subsection__order",
        "name",
    ]  # Default ordering


@extend_schema_view(
    list=extend_schema(
        summary="List Questions",
        description="Retrieves a paginated list of questions, excluding answers/explanations. Supports extensive filtering. Requires subscription.",
        parameters=[
            OpenApiParameter(
                name="subsection__slug",
                description="Filter by subsection slug (e.g., `algebra-problems`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="subsection__slug__in",
                description="Filter by multiple subsection slugs (e.g., `algebra-problems,geometry`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="skill__slug",
                description="Filter by skill slug",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="skill__slug__in",
                description="Filter by multiple skill slugs",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="difficulty",
                description="Filter by difficulty level (1-5)",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="difficulty__gte",
                description="Filter by difficulty level (>=)",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="difficulty__lte",
                description="Filter by difficulty level (<=)",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="starred",
                description="Filter for questions starred by the current user (`true`/`false`)",
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="not_mastered",
                description="Filter for skills the user has not mastered (`true`) - Requires Study App logic",
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="search",
                description="Search term in question text, options, hints",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="exclude_ids",
                description="Comma-separated list of question IDs to exclude (e.g., `10,25`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="page", description="Page number", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="page_size", description="Items per page", type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="ordering",
                description="Order results by field (e.g., `difficulty`, `-id`)",
                type=OpenApiTypes.STR,
            ),
        ],
        responses={200: QuestionListSerializer(many=True)},
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve Question Details",
        description="Retrieves full details for a single question, including the correct answer and explanation. Requires subscription.",
        responses={200: QuestionDetailSerializer},
        tags=["Learning Content"],
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

    queryset = Question.objects.filter(
        is_active=True
    )  # Base queryset only includes active questions
    permission_classes = [IsSubscribed]  # Requires active subscription
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    # Define filters precisely using a dictionary for DjangoFilterBackend
    filterset_fields = {
        "subsection__slug": ["exact", "in"],
        "skill__slug": ["exact", "in"],
        "difficulty": ["exact", "in", "gte", "lte"],
        # 'starred' is handled in get_queryset
    }
    search_fields = [
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "hint",
        "explanation",  # Search explanation as well
        "solution_method_summary",
    ]
    ordering_fields = [
        "id",
        "difficulty",
        "created_at",
        "subsection__name",
        "skill__name",
    ]
    ordering = ["id"]  # Default ordering

    def get_serializer_class(self) -> Type[BaseSerializer]:
        """Return appropriate serializer class based on action."""
        if self.action == "retrieve":
            return QuestionDetailSerializer
        elif self.action in ["star", "unstar"]:
            return (
                StarActionSerializer  # Use minimal serializer for action documentation
            )
        return QuestionListSerializer

    def get_queryset(self) -> QuerySet[Question]:
        """Applies optimizations and custom filtering."""
        # Start with the base queryset (already filtered by is_active)
        queryset = super().get_queryset()
        user = self.request.user

        # Optimize related object fetching
        queryset = queryset.select_related("subsection", "skill")

        # Annotate with 'user_has_starred' status for the current user if authenticated
        if user.is_authenticated:
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            # The 'user_has_starred' annotation will be used by the serializer
            queryset = queryset.annotate(user_has_starred=Exists(starred_subquery))

        # --- Custom Filtering Logic ---

        # Filter by 'starred=true' or 'starred=false' based on annotation
        is_starred_param = self.request.query_params.get("starred", "").lower()
        if user.is_authenticated:
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
        """Unstars the question identified by pk for the current user."""
        question = self.get_object()  # Handles 404 if question not found
        user = request.user
        # Attempt to delete the star link
        deleted_count, _ = UserStarredQuestion.objects.filter(
            user=user, question=question
        ).delete()

        if deleted_count > 0:
            # Successfully deleted, return 204 No Content
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            # Question exists but wasn't starred by this user, return 404
            return Response(
                {"detail": "Question not found or not starred by this user."},
                status=status.HTTP_404_NOT_FOUND,
            )
