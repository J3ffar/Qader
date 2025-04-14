from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, OuterRef
from apps.users.api.permissions import IsSubscribed

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


class LearningSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Learning Sections (Verbal, Quantitative).
    """

    queryset = LearningSection.objects.all().order_by("order")
    serializer_class = LearningSectionSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or IsSubscribed if needed
    lookup_field = "slug"
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["order", "name"]


class LearningSubSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Learning Sub-Sections (Reading Comprehension, Algebra).
    """

    queryset = (
        LearningSubSection.objects.select_related("section")
        .all()
        .order_by("section__order", "order")
    )
    serializer_class = LearningSubSectionSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or IsSubscribed
    lookup_field = "slug"
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["section__slug"]  # Filter by parent section slug
    ordering_fields = ["order", "name"]


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing Skills (Solving Linear Equations, Identifying Main Idea).
    """

    queryset = (
        Skill.objects.select_related("subsection__section")
        .all()
        .order_by("subsection__section__order", "subsection__order", "name")
    )
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated]  # Or IsSubscribed
    lookup_field = "slug"
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_fields = ["subsection__slug"]  # Filter by parent subsection slug
    ordering_fields = ["name"]
    search_fields = ["name", "description"]  # Allow searching skills


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
    permission_classes = [
        IsSubscribed
    ]  # Requires active subscription to view questions
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
    ordering_fields = ["id", "difficulty", "created_at"]  # Add more as needed

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

        # Handle 'starred=true' filter
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

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
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

    @action(
        detail=True,
        methods=["delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def unstar(self, request, pk=None):
        """Unstars a question for the current user."""
        question = self.get_object()
        user = request.user
        deleted_count, _ = UserStarredQuestion.objects.filter(
            user=user, question=question
        ).delete()

        if deleted_count > 0:
            return Response(
                {"status": "unstarred"}, status=status.HTTP_200_OK
            )  # Or 204 No Content
        else:
            return Response({"status": "not starred"}, status=status.HTTP_404_NOT_FOUND)
