from typing import Any
from unittest.mock import MagicMock
from rest_framework import (
    generics,
    permissions,
    status,
    serializers,
)  # Added serializers
from rest_framework.response import Response
from rest_framework.exceptions import (
    PermissionDenied,
    NotFound,
    ValidationError,
)  # Added ValidationError
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
from apps.study.services.study import (
    EMERGENCY_MODE_DEFAULT_QUESTIONS,
    generate_emergency_plan,
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

from django.utils.functional import Promise
from django.utils.encoding import force_str

# Import the serializer for the list response
from apps.learning.api.serializers import QuestionListSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse


logger = logging.getLogger(__name__)


def _clean_dict_for_json(d: Any) -> Any:
    """Recursively converts Django translation proxies to strings within a dict/list."""
    if isinstance(d, dict):
        return {k: _clean_dict_for_json(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [_clean_dict_for_json(v) for v in d]
    elif isinstance(d, Promise):  # Check if it's a Django lazy translation object
        return force_str(d)
    elif isinstance(d, MagicMock):  # Handle MagicMock for robustness in tests
        return f"MagicMock(name='{d._extract_mock_name() or 'unknown'}')"
    return d


@extend_schema(tags=["Study - Emergency Mode"])
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
        except ValidationError as drf_ve:
            logger.warning(
                f"Validation error generating plan for user {user.id}: {drf_ve.detail}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error generating emergency plan for user {user.id}: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(
                _(
                    "Could not generate study plan due to an unexpected issue. Please try again later."
                )
            )

        if not plan or not isinstance(plan.get("target_skills"), list):
            logger.error(
                f"generate_emergency_plan returned invalid plan for user {user.id}: {plan}"
            )
            raise serializers.ValidationError(
                _("Failed to generate a valid study plan structure.")
            )

        # Ensure the plan is cleaned of any Django Promise objects before use
        cleaned_plan = _clean_dict_for_json(plan)

        session = EmergencyModeSession.objects.create(
            user=user,
            reason=validated_data.get("reason"),
            suggested_plan=cleaned_plan,  # Use cleaned_plan for saving
            calm_mode_active=False,
            shared_with_admin=False,
        )

        response_data = {
            "session_id": session.id,
            "suggested_plan": cleaned_plan,  # MODIFIED: Use cleaned_plan for response
        }
        response_serializer = EmergencyModeStartResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeSessionUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/v1/study/emergency-mode/{session_id}/
    Updates settings (calm mode, sharing) for an active Emergency Mode session.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = (
        EmergencyModeSessionSerializer  # Serializes the full session for response
    )
    queryset = EmergencyModeSession.objects.all()  # Initial queryset
    lookup_field = "id"
    lookup_url_kwarg = "session_id"

    def get_serializer_class(self):
        if self.request.method == "PATCH" or self.request.method == "PUT":
            return EmergencyModeUpdateSerializer
        return EmergencyModeSessionSerializer  # For GET (if enabled) or general context

    # Override update to control response serialization
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Use the input serializer (EmergencyModeUpdateSerializer) for validation and saving
        # Note: self.get_serializer() will use get_serializer_class()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)  # perform_update calls serializer.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been used, clear the cache to reflect changes.
            instance._prefetched_objects_cache = {}

        # For the response, explicitly use the output serializer (EmergencyModeSessionSerializer)
        output_serializer = EmergencyModeSessionSerializer(instance)
        return Response(output_serializer.data)

    def get_queryset(self):
        return EmergencyModeSession.objects.filter(
            user=self.request.user, end_time__isnull=True
        )


@extend_schema(
    tags=["Study - Emergency Mode"],
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
        ),  # Should be 404 due to get_object_or_404
        404: OpenApiResponse(
            description="Not Found (Session ID invalid or not accessible)."
        ),
    },
)
class EmergencyModeQuestionsView(generics.ListAPIView):
    """
    GET /api/v1/study/emergency-mode/{session_id}/questions/
    Fetches recommended questions based on the active emergency session's plan.
    """

    permission_classes = [permissions.IsAuthenticated, IsSubscribed]
    serializer_class = QuestionListSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        session_id = self.kwargs.get("session_id")

        # get_object_or_404 will raise NotFound if session doesn't exist,
        # or doesn't match user, or is not active.
        session = get_object_or_404(
            EmergencyModeSession,
            pk=session_id,
            user=user,
            end_time__isnull=True,
        )

        plan = session.suggested_plan
        if not isinstance(plan, dict):
            logger.error(
                f"Invalid suggested_plan format for emergency session {session.id}. Plan: {plan}"
            )
            raise serializers.ValidationError(  # Use DRF's serializers.ValidationError
                _("Invalid study plan associated with this session.")
            )

        target_skills_in_plan = plan.get("target_skills")
        focus_skill_slugs = []
        if isinstance(target_skills_in_plan, list):
            for skill_detail in target_skills_in_plan:
                if isinstance(skill_detail, dict) and "slug" in skill_detail:
                    focus_skill_slugs.append(skill_detail["slug"])

        num_questions = plan.get(
            "recommended_question_count", EMERGENCY_MODE_DEFAULT_QUESTIONS
        )

        if not focus_skill_slugs:  # If no target skills, can log or use broader filter
            logger.warning(
                f"No target skill slugs found in plan for session {session.id}. Fetching general questions."
            )
            # Consider if this should default to focus_area_names from plan if target_skills is empty

        if not isinstance(num_questions, int) or num_questions <= 0:
            logger.warning(
                f"Invalid 'recommended_question_count' ({num_questions}) in plan for session {session.id}. Using default {EMERGENCY_MODE_DEFAULT_QUESTIONS}."
            )
            num_questions = EMERGENCY_MODE_DEFAULT_QUESTIONS

        try:
            queryset = get_filtered_questions(
                user=user,
                limit=num_questions,
                skills=(
                    focus_skill_slugs if focus_skill_slugs else None
                ),  # Pass None if empty
            )
            return queryset
        except (
            serializers.ValidationError
        ):  # Catch validation error from get_filtered_questions
            raise  # Re-raise it
        except Exception as e:
            logger.error(
                f"Error fetching emergency questions for session {session.id}: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(  # Use DRF's serializers.ValidationError
                _("Could not retrieve questions for the emergency session plan.")
            )


@extend_schema(tags=["Study - Emergency Mode"])
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

        skill_feedback = None
        updated_proficiency_score = None  # Placeholder, can be populated if needed
        session_progress_data = None

        session = get_object_or_404(
            EmergencyModeSession, id=session_id, user=user, end_time__isnull=True
        )
        question = get_object_or_404(Question, id=question_id, is_active=True)

        is_correct = selected_answer == question.correct_answer

        # FIX: Initialize feedback_message with "Correct!" or "Incorrect."
        if is_correct:
            feedback_message = _("Correct!")
        else:
            feedback_message = _("Incorrect.")

        try:
            UserQuestionAttempt.objects.create(
                user=user,
                question=question,
                emergency_session=session,
                selected_answer=selected_answer,
                is_correct=is_correct,
                mode=UserQuestionAttempt.Mode.EMERGENCY,
            )
            if question.skill:
                update_user_skill_proficiency(
                    user=user, skill=question.skill, is_correct=is_correct
                )
                # FIX: Populate skill_feedback if question.skill exists
                skill_feedback = {
                    "slug": question.skill.slug,
                    "name": question.skill.name,
                    # Add other relevant skill details if needed
                }
                # Optionally, get updated proficiency if service returns it
                # usp_record = UserSkillProficiency.objects.get(user=user, skill=question.skill)
                # updated_proficiency_score = usp_record.proficiency_score

        except Exception as e:
            logger.error(
                f"Error creating UQA or updating proficiency in emergency mode for user {user.id}, q {question_id}: {e}",
                exc_info=True,
            )
            raise serializers.ValidationError(_("Could not record answer attempt."))

        plan = session.suggested_plan
        if isinstance(plan, dict):
            recommended_total = plan.get("recommended_question_count")
            if isinstance(recommended_total, int) and recommended_total > 0:
                try:
                    answered_count = UserQuestionAttempt.objects.filter(
                        emergency_session=session
                    ).count()
                    session_progress_data = {
                        "answered_count": answered_count,
                        "recommended_total": recommended_total,
                    }
                    # Append progress to feedback_message
                    feedback_message += _(  # Note: += works because Promise becomes str on concat
                        " You've answered {answered}/{total} questions in this session."
                    ).format(
                        answered=answered_count, total=recommended_total
                    )
                except Exception as prog_err:
                    logger.error(
                        f"Error calculating session progress for session {session.id}: {prog_err}"
                    )
            else:
                logger.warning(
                    f"Invalid recommended_total in plan for session {session.id}"
                )
        else:
            logger.warning(f"Invalid plan type for session {session.id}")

        insightful_feedback = {
            "skill_tested": skill_feedback,
            "skill_proficiency_after_attempt": updated_proficiency_score,
            "message": str(feedback_message),  # Ensure it's a string
            "session_progress": session_progress_data,
        }

        response_data = {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "points_earned": 0,
            "feedback": insightful_feedback,
        }
        response_serializer = EmergencyModeAnswerResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
