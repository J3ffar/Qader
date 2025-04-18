from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from apps.api.permissions import IsSubscribed  # Assuming this permission exists
from apps.study.models import (
    EmergencyModeSession,
    UserQuestionAttempt,
    Question,
    UserSkillProficiency,
)
from apps.study.services import (
    generate_emergency_plan,
    EMERGENCY_MODE_TIPS,
    update_user_skill_proficiency,
)
from apps.study.api.serializers.emergency import (
    EmergencyModeStartSerializer,
    EmergencyModeStartResponseSerializer,
    EmergencyModeUpdateSerializer,
    EmergencyModeSessionSerializer,
    EmergencyModeAnswerSerializer,
    EmergencyModeAnswerResponseSerializer,
)

logger = logging.getLogger(__name__)


class EmergencyModeStartView(generics.GenericAPIView):
    """
    POST /api/v1/study/emergency-mode/start/
    Initiates Emergency Mode for the logged-in user and returns a study plan.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeStartSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        user = request.user

        # Generate the plan using the service
        try:
            plan = generate_emergency_plan(
                user=user,
                available_time_hours=validated_data.get("available_time_hours"),
                focus_areas=validated_data.get("focus_areas"),
            )
        except Exception as e:
            logger.error(f"Error generating emergency plan for user {user.id}: {e}")
            raise ValidationError(
                _("Could not generate study plan. Please try again later.")
            )

        # Create the session record
        session = EmergencyModeSession.objects.create(
            user=user,
            reason=validated_data.get("reason"),
            suggested_plan=plan,
            calm_mode_active=False,  # Starts false by default
            shared_with_admin=False,
        )

        response_data = {
            "session_id": session.id,
            "suggested_plan": plan,
            "tips": EMERGENCY_MODE_TIPS,  # Use tips from service/constants
        }
        response_serializer = EmergencyModeStartResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class EmergencyModeSessionUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/study/emergency-mode/{session_id}/
    Updates settings (calm mode, sharing) for an active Emergency Mode session.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeUpdateSerializer
    queryset = EmergencyModeSession.objects.all()
    lookup_field = "id"
    lookup_url_kwarg = "session_id"

    def get_object(self):
        obj = super().get_object()
        # Check ownership
        if obj.user != self.request.user:
            raise PermissionDenied(
                _("You do not have permission to update this session.")
            )
        # Check if session already ended
        if obj.end_time:
            raise ValidationError(_("This session has already ended."))
        return obj

    def perform_update(self, serializer):
        instance = serializer.save()
        # Optional: Trigger notification if shared_with_admin becomes True
        if (
            serializer.validated_data.get("shared_with_admin")
            and not serializer.instance.shared_with_admin
        ):
            logger.info(
                f"User {instance.user.id} shared emergency session {instance.id} with admin."
            )
            # TODO: Implement admin notification logic (e.g., using signals or a task queue)


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

        # --- Validate Session ---
        try:
            session = EmergencyModeSession.objects.get(id=session_id, user=user)
            if session.end_time:
                raise ValidationError(_("This emergency session has already ended."))
        except EmergencyModeSession.DoesNotExist:
            raise NotFound(_("Active emergency session not found."))

        # --- Validate Question ---
        question = get_object_or_404(Question, id=question_id, is_active=True)

        # --- Record Attempt ---
        is_correct = selected_answer == question.correct_answer
        try:
            attempt = UserQuestionAttempt.objects.create(
                user=user,
                question=question,
                # test_attempt=None, # Not linked to a formal test
                # emergency_session=session, # Link if FK is added
                selected_answer=selected_answer,
                is_correct=is_correct,
                time_taken_seconds=None,  # Typically not tracked in calm mode
                used_hint=False,  # Assume no hints in calm mode
                used_elimination=False,
                used_solution_method=False,
                mode=UserQuestionAttempt.Mode.EMERGENCY,
                attempted_at=timezone.now(),
            )
        except Exception as e:
            # Catch potential unique constraint errors if attempt already exists somehow
            logger.error(
                f"Error creating UserQuestionAttempt in emergency mode for user {user.id}, question {question_id}: {e}"
            )
            raise ValidationError(_("Could not record answer attempt."))

        # --- Update Proficiency ---
        if question.skill:
            try:
                update_user_skill_proficiency(
                    user=user, skill=question.skill, is_correct=is_correct
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(
                    f"Error updating skill proficiency during emergency answer for user {user.id}, skill {question.skill.id}: {e}"
                )

        # --- Prepare Response ---
        response_data = {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points_earned": 0,  # Typically no points in emergency mode
        }
        response_serializer = EmergencyModeAnswerResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
