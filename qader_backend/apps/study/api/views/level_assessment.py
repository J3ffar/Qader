from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
import logging

from apps.api.permissions import IsSubscribed
from apps.study.api.serializers import (  # Import specific serializers
    LevelAssessmentStartSerializer,
    LevelAssessmentResponseSerializer,
    # LevelAssessmentResultSerializer, # Result serializer now used by CompleteView
)

logger = logging.getLogger(__name__)

# --- Level Assessment Views ---


@extend_schema(
    tags=["Study & Progress - Level Assessment"],  # Keep tag specific
    summary="Start Level Assessment Test",
    # ... (keep existing schema description) ...
    request=LevelAssessmentStartSerializer,
    responses={
        201: OpenApiResponse(
            response=LevelAssessmentResponseSerializer,
            description="Assessment started.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., ongoing assessment, no questions)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Authentication/Subscription)."
        ),
    },
)
class LevelAssessmentStartView(generics.GenericAPIView):
    serializer_class = LevelAssessmentStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()
        response_serializer = LevelAssessmentResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
