from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, OuterRef
from apps.users.api.permissions import IsSubscribed
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)

from ..models import (
    LearningSection,
    LearningSubSection,
    Skill,
    Question,
    UserStarredQuestion,
)
from .serializers import (
    LearningSectionSerializer,
    LearningSubSectionSerializer,
    SkillSerializer,
    QuestionListSerializer,
    QuestionDetailSerializer,
)


# Decorate ViewSets for better schema documentation
@extend_schema_view(
    list=extend_schema(
        summary="List all Learning Sections",
        description="Retrieves a list of main learning sections (e.g., Verbal, Quantitative), ordered by the 'order' field.",
        tags=["Learning Content"],  # Assign to the correct tag
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific Learning Section",
        description="Retrieves details of a specific learning section using its unique slug.",
        tags=["Learning Content"],
    ),
)
class LearningSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Learning Sections.
    """

    queryset = LearningSection.objects.all().order_by("order")
    serializer_class = LearningSectionSerializer
    permission_classes = [IsSubscribed]
    lookup_field = "slug"
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "name"]


@extend_schema_view(
    list=extend_schema(
        summary="List Learning Sub-Sections",
        description="Retrieves a list of learning sub-sections (e.g., Reading Comprehension), optionally filtered by the parent section's slug (`section__slug`).",
        parameters=[
            OpenApiParameter(
                name="section__slug",
                description="Filter by parent section slug",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific Learning Sub-Section",
        description="Retrieves details of a specific learning sub-section using its unique slug.",
        tags=["Learning Content"],
    ),
)
class LearningSubSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Learning Sub-Sections.
    """

    queryset = (
        LearningSubSection.objects.select_related("section")
        .all()
        .order_by("section__order", "order")
    )
    serializer_class = LearningSubSectionSerializer
    permission_classes = [IsSubscribed]
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["section__slug"]
    ordering_fields = ["order", "name"]


@extend_schema_view(
    list=extend_schema(
        summary="List Skills",
        description="Retrieves a list of specific skills within sub-sections (e.g., Solving Linear Equations), optionally filtered by the parent sub-section's slug (`subsection__slug`) or searched by name/description.",
        parameters=[
            OpenApiParameter(
                name="subsection__slug",
                description="Filter by parent subsection slug",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="search",
                description="Search term for skill name or description",
                type=OpenApiTypes.STR,
            ),
        ],
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific Skill",
        description="Retrieves details of a specific skill using its unique slug.",
        tags=["Learning Content"],
    ),
)
class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving Skills.
    """

    queryset = (
        Skill.objects.select_related("subsection__section")
        .all()
        .order_by("subsection__section__order", "subsection__order", "name")
    )
    serializer_class = SkillSerializer
    permission_classes = [IsSubscribed]
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["subsection__slug"]
    ordering_fields = ["name"]
    search_fields = ["name", "description"]


@extend_schema_view(
    list=extend_schema(
        summary="List Questions",
        description="Retrieves a list of questions, potentially filtered by various criteria. Requires subscription.",
        parameters=[
            OpenApiParameter(
                name="subsection__slug",
                description="Filter by subsection slug (exact match or multiple using `in`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="skill__slug",
                description="Filter by skill slug (exact match or multiple using `in`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="difficulty",
                description="Filter by difficulty level (1-5, exact or range using `gte`/`lte`)",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="starred",
                description="Filter for questions starred by the current user (`true`/`false`)",
                type=OpenApiTypes.BOOL,
            ),
            # OpenApiParameter(name='not_mastered', description='Filter for skills the user has not mastered (`true`) - Requires Study App logic', required=False, type=OpenApiTypes.BOOL), # Add when ready
            OpenApiParameter(
                name="search",
                description="Search term in question text, options, hints, explanation",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="ordering",
                description="Order results by field (e.g., `difficulty`, `-difficulty`)",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="exclude_ids",
                description="Comma-separated list of question IDs to exclude",
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="limit",
                description="Number of questions to return (used with pagination)",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="offset",
                description="Offset for pagination",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="page",
                description="Page number for pagination",
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="page_size",
                description="Number of items per page",
                type=OpenApiTypes.INT,
            ),
        ],
        responses={
            200: QuestionListSerializer(many=True)
        },  # Document the response serializer
        tags=["Learning Content"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a specific Question",
        description="Retrieves detailed information for a single question, including the correct answer and explanation. Requires subscription.",
        responses={200: QuestionDetailSerializer},  # Document the response serializer
        tags=["Learning Content"],
    ),
)
class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retrieving Questions.

    Use query parameters for filtering:
    - `subsection`: Filter by subsection slug (e.g., `?subsection=algebra-problems`)
    - `skill`: Filter by skill slug (e.g., `?skill=solving-linear-equations`)
    - `difficulty`: Filter by difficulty level (1-5) (e.g., `?difficulty=3`)
    - `starred`: Filter for questions starred by the current user (e.g., `?starred=true`)
    - `search`: Search question text, options, hints (e.g., `?search=equation`)
    - `ordering`: Order results (e.g., `?ordering=difficulty` or `?ordering=-difficulty`)
    - `exclude_ids`: Comma-separated list of question IDs to exclude (e.g., `?exclude_ids=10,25,30`)

    Provides actions to `star` and `unstar` questions.
    """

    queryset = Question.objects.filter(is_active=True).select_related(
        "subsection", "skill"
    )
    permission_classes = [IsSubscribed]  # Requires active subscription
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = {
        "subsection__slug": ["exact", "in"],
        "skill__slug": ["exact", "in"],
        "difficulty": ["exact", "in", "gte", "lte"],
    }
    search_fields = [
        "question_text",
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "hint",
        "explanation",
    ]
    ordering_fields = ["id", "difficulty", "created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuestionDetailSerializer
        return QuestionListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Annotate with 'is_starred' status for the current user
        if user.is_authenticated:
            starred_subquery = UserStarredQuestion.objects.filter(
                user=user, question=OuterRef("pk")
            )
            queryset = queryset.annotate(user_has_starred=Exists(starred_subquery))

        # --- Filtering Logic ---
        is_starred_filter = self.request.query_params.get("starred", "").lower()
        if is_starred_filter == "true" and user.is_authenticated:
            queryset = queryset.filter(starred_by=user)
        elif is_starred_filter == "false" and user.is_authenticated:
            queryset = queryset.exclude(starred_by=user)

        # Handle 'not_mastered=true' filter (requires Study app/UserSkillProficiency)
        # Placeholder for future implementation:
        # not_mastered_filter = self.request.query_params.get('not_mastered', '').lower()
        # if not_mastered_filter == 'true' and user.is_authenticated:
        #     # Import UserSkillProficiency from study app
        #     from apps.study.models import UserSkillProficiency
        #     mastery_threshold = 0.7 # Example threshold
        #     weak_skills = UserSkillProficiency.objects.filter(
        #         user=user,
        #         proficiency_score__lt=mastery_threshold
        #     ).values_list('skill_id', flat=True)
        #     if weak_skills.exists():
        #           queryset = queryset.filter(skill_id__in=list(weak_skills))
        #      else:
        #           # If no weak skills identified, maybe return empty or handle differently
        #           queryset = queryset.none()

        # Handle 'exclude_ids' filter
        exclude_ids_str = self.request.query_params.get("exclude_ids")
        if exclude_ids_str:
            try:
                exclude_ids = [int(id_str) for id_str in exclude_ids_str.split(",")]
                queryset = queryset.exclude(id__in=exclude_ids)
            except ValueError:
                # Ignore invalid format for exclude_ids
                pass

        return queryset

    # --- Custom Actions for Star/Unstar ---

    @extend_schema(  # Decorate the custom action
        summary="Star a Question",
        description="Marks the specified question as starred (bookmarked) for the currently authenticated user.",
        request=None,  # No request body needed
        responses={
            201: OpenApiResponse(description="Question successfully starred."),
            200: OpenApiResponse(
                description="Question was already starred by the user."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(
                description="User does not have permission (e.g., not subscribed)."
            ),
            404: OpenApiResponse(description="Question not found."),
        },
        tags=["Learning Content"],
    )
    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )  # Ensure IsAuthenticated is sufficient here
    def star(self, request, pk=None):
        """Stars a question for the current user."""
        question = self.get_object()  # Gets the specific question instance
        user = request.user
        _, created = UserStarredQuestion.objects.get_or_create(
            user=user, question=question
        )

        if created:
            return Response({"status": "starred"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"status": "already starred"}, status=status.HTTP_200_OK)

    @extend_schema(  # Decorate the custom action
        summary="Unstar a Question",
        description="Removes the star (bookmark) from the specified question for the currently authenticated user.",
        request=None,  # No request body needed
        responses={
            200: OpenApiResponse(
                description="Question successfully unstarred."
            ),  # Changed from 204 for consistency if returning status
            404: OpenApiResponse(
                description="Question not found or not starred by the user."
            ),
            401: OpenApiResponse(
                description="Authentication credentials were not provided."
            ),
            403: OpenApiResponse(description="User does not have permission."),
        },
        tags=["Learning Content"],
    )
    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[permissions.IsAuthenticated],
    )  # Ensure IsAuthenticated is sufficient here
    def unstar(self, request, pk=None):
        """Unstars a question for the current user."""
        question = self.get_object()
        user = request.user
        deleted_count, _ = UserStarredQuestion.objects.filter(
            user=user, question=question
        ).delete()

        if deleted_count > 0:
            return Response({"status": "unstarred"}, status=status.HTTP_200_OK)
        else:
            # More specific: return 404 if the question exists but wasn't starred by this user
            return Response({"status": "not starred"}, status=status.HTTP_404_NOT_FOUND)
