from rest_framework import (
    generics,
    permissions,
    status,
    serializers,
)  # Added serializers
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from apps.api.permissions import IsSubscribed
from apps.study.models import (
    EmergencyModeSession,
    UserQuestionAttempt,
    Question,  # Need Question model
    UserSkillProficiency,
)
from apps.study.services import (
    EMERGENCY_MODE_DEFAULT_QUESTIONS,
    generate_emergency_plan,
    EMERGENCY_MODE_TIPS,
    update_user_skill_proficiency,
    get_filtered_questions,  # Import question filtering service
)
from apps.study.api.serializers.emergency import (
    EmergencyModeStartSerializer,
    EmergencyModeStartResponseSerializer,
    EmergencyModeUpdateSerializer,
    EmergencyModeSessionSerializer,  # Needed for potential detail view
    EmergencyModeAnswerSerializer,
    EmergencyModeAnswerResponseSerializer,
)

# Import the serializer for the list response
from apps.learning.api.serializers import QuestionListSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse


logger = logging.getLogger(__name__)


@extend_schema(tags=["Study & Progress - Emergency Mode"])
class EmergencyModeStartView(generics.GenericAPIView):
    """
    POST /api/v1/study/emergency-mode/start/
    Initiates Emergency Mode session and returns a study plan.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeStartSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user = request.user

        try:
            plan = generate_emergency_plan(
                user=user,
                available_time_hours=validated_data.get("available_time_hours"),
                focus_areas=validated_data.get("focus_areas"),
            )
        except Exception as e:
            logger.error(
                f"Error generating emergency plan for user {user.id}: {e}",
                exc_info=True,
            )
            # Use DRF validation error for user feedback
            raise serializers.ValidationError(
                _("Could not generate study plan. Please try again later.")
            )

        session = EmergencyModeSession.objects.create(
            user=user,
            reason=validated_data.get("reason"),
            suggested_plan=plan,
            calm_mode_active=False,
            shared_with_admin=False,
        )

        response_data = {
            "session_id": session.id,
            "suggested_plan": plan,
            "tips": EMERGENCY_MODE_TIPS,
        }
        response_serializer = EmergencyModeStartResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Study & Progress - Emergency Mode"])
class EmergencyModeSessionUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/study/emergency-mode/{session_id}/
    Updates settings (calm mode, sharing) for an active Emergency Mode session.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeUpdateSerializer
    queryset = EmergencyModeSession.objects.filter(
        end_time__isnull=True
    )  # Only allow updating active sessions
    lookup_field = "id"
    lookup_url_kwarg = "session_id"

    def get_object(self):
        obj = super().get_object()
        if obj.user != self.request.user:
            raise PermissionDenied(
                _("You do not have permission to update this session.")
            )
        # Removed end_time check as it's now in queryset filter
        return obj

    def perform_update(self, serializer):
        instance = serializer.save()
        # Log sharing action
        if (
            serializer.validated_data.get("shared_with_admin")
            and not serializer.instance.shared_with_admin
        ):
            logger.info(
                f"User {instance.user.id} shared emergency session {instance.id} with admin."
            )
            # TODO: Implement admin notification logic if needed


# --- NEW VIEW ---
@extend_schema(
    tags=["Study & Progress - Emergency Mode"],
    summary="Fetch Questions for Emergency Mode Session",
    description="Retrieves questions based on the suggested plan for an active emergency mode session.",
    responses={
        200: OpenApiResponse(
            response=QuestionListSerializer(many=True),
            description="List of questions for the session.",
        ),
        400: OpenApiResponse(
            description="Bad Request (e.g., Invalid plan in session)."
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or inactive session)."
        ),
        404: OpenApiResponse(description="Not Found (Session ID invalid)."),
    },
)
class EmergencyModeQuestionsView(generics.ListAPIView):
    """
    GET /api/v1/study/emergency-mode/{session_id}/questions/
    Fetches recommended questions based on the active emergency session's plan.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = QuestionListSerializer
    pagination_class = None  # Limit determined by plan

    def get_queryset(self):
        user = self.request.user
        session_id = self.kwargs.get("session_id")

        try:
            # Get active session belonging to the user
            session = get_object_or_404(
                EmergencyModeSession,
                pk=session_id,
                user=user,
                end_time__isnull=True,  # Ensure session is active
            )
        except EmergencyModeSession.DoesNotExist:
            raise NotFound(
                _("Active emergency session not found.")
            )  # Let DRF handle 404

        # --- Extract plan details safely ---
        plan = session.suggested_plan
        if not isinstance(plan, dict):
            logger.error(
                f"Invalid suggested_plan format for emergency session {session.id}. Plan: {plan}"
            )
            raise serializers.ValidationError(
                _("Invalid study plan associated with this session.")
            )

        focus_skill_slugs = plan.get("focus_skills")  # Should be list of slugs
        num_questions = plan.get(
            "recommended_questions", EMERGENCY_MODE_DEFAULT_QUESTIONS
        )

        if not isinstance(focus_skill_slugs, list):
            logger.warning(
                f"Invalid 'focus_skills' format in plan for session {session.id}. Defaulting."
            )
            focus_skill_slugs = (
                None  # Default to no specific skill filter if format is wrong
            )
        if not isinstance(num_questions, int) or num_questions <= 0:
            logger.warning(
                f"Invalid 'recommended_questions' in plan for session {session.id}. Using default {EMERGENCY_MODE_DEFAULT_QUESTIONS}."
            )
            num_questions = EMERGENCY_MODE_DEFAULT_QUESTIONS

        # --- Fetch questions using the service ---
        try:
            queryset = get_filtered_questions(
                user=user,
                limit=num_questions,
                skills=focus_skill_slugs,  # Filter by focus skills from plan
                # Add other filters if needed (e.g., exclude recently answered?)
            )
            return queryset
        except Exception as e:
            logger.error(
                f"Error fetching emergency questions for session {session.id}: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(
                _("Could not retrieve questions for the emergency session plan.")
            )


@extend_schema(tags=["Study & Progress - Emergency Mode"])
class EmergencyModeAnswerView(generics.GenericAPIView):
    """
    POST /api/v1/study/emergency-mode/answer/
    Submits an answer for a question attempted during an emergency mode session.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeAnswerSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user = request.user
        question_id = validated_data["question_id"]
        selected_answer = validated_data["selected_answer"]
        session_id = validated_data["session_id"]

        try:
            session = EmergencyModeSession.objects.get(
                id=session_id, user=user, end_time__isnull=True
            )
        except EmergencyModeSession.DoesNotExist:
            raise NotFound(_("Active emergency session not found."))

        question = get_object_or_404(Question, id=question_id, is_active=True)
        is_correct = selected_answer == question.correct_answer

        try:
            attempt = UserQuestionAttempt.objects.create(
                user=user,
                question=question,
                emergency_session=session,  # Link the attempt to the session
                selected_answer=selected_answer,
                is_correct=is_correct,
                mode=UserQuestionAttempt.Mode.EMERGENCY,
            )
            # Update proficiency immediately
            update_user_skill_proficiency(
                user=user, skill=question.skill, is_correct=is_correct
            )

        except Exception as e:
            logger.error(
                f"Error creating UQA in emergency mode for user {user.id}, q {question_id}: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(_("Could not record answer attempt."))

        response_data = {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points_earned": 0,  # Explicitly 0 for emergency mode
        }
        response_serializer = EmergencyModeAnswerResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
