# qader_backend/apps/study/api/views/traditional.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
import logging

from apps.api.permissions import IsSubscribed
from apps.learning.api.serializers import QuestionListSerializer  # Used for response
from apps.study.services import get_filtered_questions  # Use the service
from ..serializers.traditional import (  # Import specific serializers
    TraditionalLearningAnswerSerializer,
    TraditionalLearningResponseSerializer,
)

logger = logging.getLogger(__name__)

# --- Traditional Learning Views ---


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Fetch Questions for Traditional Learning",
    description=(
        "Retrieves a list of questions for traditional practice based on filters. "
        "Uses efficient random sampling. Supports filtering by subsections, skills, starred, not_mastered, and excluding IDs."
    ),
    parameters=[
        OpenApiParameter(
            name="limit", description="Max questions.", type=int, default=10
        ),
        OpenApiParameter(
            name="subsection__slug__in",
            description="Subsection slugs (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="skill__slug__in",
            description="Skill slugs (comma-separated).",
            type=str,
        ),
        OpenApiParameter(
            name="starred", description="Filter by starred (`true`/`1`).", type=str
        ),  # Use str for boolean query params
        OpenApiParameter(
            name="not_mastered",
            description="Filter by not mastered skills (`true`/`1`).",
            type=str,
        ),  # Use str
        OpenApiParameter(
            name="exclude_ids",
            description="Question IDs to exclude (comma-separated).",
            type=str,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=QuestionListSerializer(many=True), description="List of questions."
        ),
        400: OpenApiResponse(description="Invalid filter parameters."),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class TraditionalLearningQuestionListView(generics.ListAPIView):
    serializer_class = QuestionListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = None  # Use 'limit' parameter instead of DRF pagination

    def get_queryset(self):
        user = self.request.user
        limit_str = self.request.query_params.get("limit", "10")
        try:
            limit = int(limit_str)
            if limit <= 0:
                limit = 10
        except ValueError:
            limit = 10

        # Helper function to parse boolean query params
        def parse_bool_param(param_name):
            val = self.request.query_params.get(param_name, "").lower()
            return val in ["true", "1"]

        # Helper function to parse comma-separated list params
        def parse_list_param(param_name):
            val_str = self.request.query_params.get(param_name)
            return (
                [s.strip() for s in val_str.split(",") if s.strip()]
                if val_str
                else None
            )

        subsections = parse_list_param("subsection__slug__in")
        skills = parse_list_param("skill__slug__in")
        starred = parse_bool_param("starred")
        not_mastered = parse_bool_param("not_mastered")
        exclude_ids_str = self.request.query_params.get("exclude_ids")

        exclude_ids = []
        if exclude_ids_str:
            try:
                exclude_ids = [
                    int(id_str.strip())
                    for id_str in exclude_ids_str.split(",")
                    if id_str.strip().isdigit()
                ]
            except ValueError:
                logger.warning(
                    f"Invalid non-integer value found in exclude_ids: {exclude_ids_str}"
                )
                # Optionally raise a 400 Bad Request here
                # raise serializers.ValidationError({"exclude_ids": ["Contains non-integer values."]})

        # Use the service function
        return get_filtered_questions(
            user=user,
            limit=limit,
            subsections=subsections,
            skills=skills,
            starred=starred,
            not_mastered=not_mastered,
            exclude_ids=exclude_ids,
            # Optionally pass proficiency_threshold from query params if needed
        )


@extend_schema(
    tags=["Study & Progress - Traditional Learning"],
    summary="Submit Answer for Traditional Learning",
    description=(
        "Submits an answer for a single question in traditional mode. Records attempt, "
        "calculates correctness, updates points, streak, and proficiency. Returns immediate feedback."
    ),
    request=TraditionalLearningAnswerSerializer,
    responses={
        200: OpenApiResponse(
            response=TraditionalLearningResponseSerializer,
            description="Answer processed successfully.",
        ),
        400: OpenApiResponse(description="Invalid input data."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Question Not Found."
        ),  # Handled by serializer field validation
    },
)
class TraditionalLearningAnswerView(generics.GenericAPIView):
    serializer_class = TraditionalLearningAnswerSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Logic is in the serializer using services
        response_serializer = TraditionalLearningResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
