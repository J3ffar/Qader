from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from drf_spectacular.utils import extend_schema

from apps.api.permissions import IsSubscribed
from apps.study.models import (
    EmergencyModeSession,
    EmergencySupportRequest,
    Question,
    UserQuestionAttempt,
)
from apps.study.services import study as study_services
from apps.learning.api.serializers import UnifiedQuestionSerializer
from apps.study.api.serializers.emergency import (
    EmergencyModeStartSerializer,
    EmergencyModeStartResponseSerializer,
    EmergencyModeUpdateSerializer,
    EmergencyModeAnswerSerializer,
    EmergencyModeAnswerResponseSerializer,
    EmergencyModeCompleteResponseSerializer,
    EmergencySupportRequestSerializer,
)


@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeStartView(APIView):
    """
    Starts a new Emergency Mode session for the authenticated user.

    This is the entry point for the Emergency Mode feature. It generates a personalized,
    hyper-focused study plan based on the user's performance history and any
    constraints they provide (like available time). The generated plan and a new
    session ID are returned, which the frontend will use for subsequent calls
    to fetch questions and submit answers.

    **Workflow:**
    1.  Validates user input (`reason`, `available_time_hours`, `focus_areas`).
    2.  Calls the `generate_emergency_plan` service to analyze the user's weak skills.
    3.  Creates an `EmergencyModeSession` instance, storing the generated plan.
    4.  Returns the session ID and the detailed plan.

    **Endpoint:** `POST /api/v1/study/emergency/start/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeStartSerializer

    @extend_schema(
        summary="Start a New Emergency Mode Session",
        description="Creates a new session and returns a personalized study plan.",
        request=EmergencyModeStartSerializer,
        responses={
            201: EmergencyModeStartResponseSerializer,
            400: {"description": "Invalid input data provided."},
            401: {"description": "Authentication credentials were not provided."},
            403: {"description": "User is not authenticated or not subscribed."},
            500: {
                "description": "An internal error occurred while generating the plan."
            },
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Handles the creation of a new emergency mode session.

        **Request Body:**
        - `days_until_test` (int): Days left for the user's test.
        - `reason` (str, optional): The user's reason for starting the session.
        - `available_time_hours` (int, optional): Hours the user can study now.
        - `focus_areas` (list[str], optional): e.g., `["verbal", "quantitative"]`.

        **Success Response (201 Created):**
        - `session_id` (int): The unique ID for this session.
        - `suggested_plan` (object): A detailed plan object (see `SuggestedPlanSerializer`).
        """
        input_serializer = self.serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        try:
            with transaction.atomic():
                plan = study_services.generate_emergency_plan(
                    user=request.user,
                    available_time_hours=data.get("available_time_hours"),
                    days_until_test=data.get("days_until_test"),
                    focus_areas=data.get("focus_areas"),
                )

                session = EmergencyModeSession.objects.create(
                    user=request.user,
                    reason=data.get("reason"),
                    suggested_plan=plan,
                    days_until_test=data.get("days_until_test"),
                )

            response_data = {"session_id": session.id, "suggested_plan": plan}
            output_serializer = EmergencyModeStartResponseSerializer(response_data)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # logger.exception(f"Error starting emergency mode for user {request.user.id}: {e}")
            return Response(
                {"detail": _("An internal error occurred while generating the plan.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeQuestionsView(APIView):
    """
    Retrieves the list of recommended questions for an active emergency session.

    After starting a session, the frontend calls this endpoint to get the actual
    questions the user needs to answer. The questions are selected based on the
    `suggested_plan` that was generated and stored in the session object.

    **Endpoint:** `GET /api/v1/study/emergency/sessions/{session_id}/questions/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]

    @extend_schema(
        summary="Get Questions for a Session",
        description="Fetches questions based on the session's generated plan.",
        responses={
            200: UnifiedQuestionSerializer(many=True),
            400: {
                "description": "The study plan for the session is missing or invalid."
            },
            404: {
                "description": "Emergency session with the given ID not found for this user."
            },
        },
    )
    def get(self, request, session_id, *args, **kwargs):
        """
        Handles the retrieval of questions for a specific session.

        **Path Parameters:**
        - `session_id` (int): The ID of the emergency session.

        **Success Response (200 OK):**
        - A list of question objects, serialized using `UnifiedQuestionSerializer`.
          Sensitive fields like `correct_answer` and `explanation` are excluded.
        """
        session = get_object_or_404(
            EmergencyModeSession, pk=session_id, user=request.user
        )

        plan = session.suggested_plan
        if (
            not isinstance(plan, dict)
            or "target_skills" not in plan
            or "recommended_question_count" not in plan
        ):
            return Response(
                {"detail": _("The study plan for this session is missing or invalid.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            target_skill_slugs = [
                skill["slug"] for skill in plan.get("target_skills", [])
            ]
            question_limit = plan.get("recommended_question_count", 10)

            questions = study_services.get_filtered_questions(
                user=request.user,
                limit=question_limit,
                skills=target_skill_slugs,
                not_mastered=False,
                min_required=1,
            )
            serializer = UnifiedQuestionSerializer(
                questions, many=True, context={"exclude_sensitive_fields": True}
            )
            return Response(serializer.data)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeSessionUpdateView(generics.UpdateAPIView):
    """
    Updates flags for an ongoing emergency session.

    This endpoint is used to toggle specific boolean flags on the session, such as
    activating "Calm Mode" or sharing the session status with administrators for support.
    It uses the `PATCH` method to allow for partial updates.

    **Endpoint:** `PATCH /api/v1/study/emergency/sessions/{session_id}/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]
    queryset = EmergencyModeSession.objects.all()
    serializer_class = EmergencyModeUpdateSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "session_id"

    @extend_schema(
        summary="Update Session Flags",
        description="Toggles Calm Mode or admin sharing for a session.",
    )
    def patch(self, request, *args, **kwargs):
        """
        Handles partial updates to the session.

        **Path Parameters:**
        - `session_id` (int): The ID of the emergency session to update.

        **Request Body:**
        - `calm_mode_active` (bool, optional): Set to `true` to activate calm mode.
        - `shared_with_admin` (bool, optional): Set to `true` to share status with admin.

        **Success Response (200 OK):**
        - The fully updated `EmergencyModeSession` object.
        """
        return super().patch(request, *args, **kwargs)

    def get_queryset(self):
        """Ensures users can only update their own sessions."""
        return super().get_queryset().filter(user=self.request.user)


@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeAnswerView(APIView):
    """
    Submits an answer for a question within a specific emergency session.

    This endpoint records the user's attempt for a single question and provides
    immediate, simple feedback. Unlike formal tests, the goal here is low-stress
    practice, so feedback is minimal. It reveals the correct answer and explanation
    after each attempt.

    **Endpoint:** `POST /api/v1/study/emergency/sessions/{session_id}/answer/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = EmergencyModeAnswerSerializer

    @extend_schema(
        summary="Submit an Answer",
        description="Records an answer attempt and returns immediate feedback.",
        request=EmergencyModeAnswerSerializer,
        responses={
            200: EmergencyModeAnswerResponseSerializer,
            400: {"description": "Session has ended or invalid input."},
            404: {"description": "Session or Question not found."},
        },
    )
    def post(self, request, session_id, *args, **kwargs):
        """
        Handles the submission of a user's answer.

        **Path Parameters:**
        - `session_id` (int): The ID of the emergency session.

        **Request Body:**
        - `question_id` (int): The ID of the question being answered.
        - `selected_answer` (str): The user's choice (e.g., "A", "B", "C", "D").

        **Success Response (200 OK):**
        - An object containing immediate feedback: `is_correct`, `correct_answer`, `explanation`, and a simple `feedback` message.
        """
        session = get_object_or_404(
            EmergencyModeSession, pk=session_id, user=request.user
        )
        if session.end_time:
            return Response(
                {"detail": _("This session has already ended.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_serializer = self.serializer_class(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        question = get_object_or_404(Question, pk=data["question_id"])

        with transaction.atomic():
            attempt, created = UserQuestionAttempt.objects.update_or_create(
                user=request.user,
                question=question,
                emergency_session=session,
                defaults={
                    "selected_answer": data["selected_answer"],
                    "mode": UserQuestionAttempt.Mode.EMERGENCY,
                },
            )

        is_correct = attempt.is_correct
        feedback_text = (
            _("Correct! Keep focusing.")
            if is_correct
            else _("That was incorrect. Let's review and move on.")
        )

        response_data = {
            "question_id": question.id,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "feedback": feedback_text,
        }
        output_serializer = EmergencyModeAnswerResponseSerializer(response_data)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


# <<< --- NEW VIEW --- >>>
@extend_schema(tags=["Study - Emergency Mode"])
class EmergencyModeCompleteView(APIView):
    """
    Completes an active Emergency Mode session.

    This endpoint finalizes the session, calculates the user's performance scores
    (overall, verbal, quantitative, and by subsection), generates AI-powered
    feedback, and saves these results. It returns a summary of the session's
    performance.

    **Endpoint:** `POST /api/v1/study/emergency/sessions/{session_id}/complete/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]

    @extend_schema(
        summary="Complete an Emergency Session",
        description="Finalizes the session, calculates scores, and returns a results summary with AI feedback.",
        responses={
            200: EmergencyModeCompleteResponseSerializer,
            400: {
                "description": "Session has already been completed or other validation error."
            },
            404: {"description": "Session not found for this user."},
            500: {
                "description": "An internal error occurred during result calculation."
            },
        },
    )
    def post(self, request, session_id, *args, **kwargs):
        """
        Handles the completion of an emergency mode session.

        **Path Parameters:**
        - `session_id` (int): The ID of the emergency session to complete.

        **Success Response (200 OK):**
        - A detailed results object (see `EmergencyModeCompleteResponseSerializer`).
        """
        session = get_object_or_404(
            EmergencyModeSession, pk=session_id, user=request.user
        )

        try:
            results_data = study_services.complete_emergency_session(session)
            serializer = EmergencyModeCompleteResponseSerializer(results_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            # This will catch the "already completed" validation error from the service
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # logger.exception(f"Error completing emergency session {session_id} for user {request.user.id}: {e}")
            return Response(
                {"detail": _("An error occurred while finalizing your session.")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# <<< --- NEW VIEW --- >>>
@extend_schema(tags=["Study - Emergency Mode"])
class EmergencySupportRequestCreateView(generics.CreateAPIView):
    """
    Creates a new support request for a specific emergency session.

    This endpoint allows a user to submit a detailed help request, including the
    type of problem and a description. This is used for the "Share my status with admin" feature.

    **Endpoint:** `POST /api/v1/study/emergency/sessions/{session_id}/request-support/`
    """

    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = EmergencySupportRequestSerializer
    queryset = EmergencySupportRequest.objects.all()

    @extend_schema(
        summary="Request Support During Session",
        description="Submits a form to request help from an administrator.",
        responses={
            201: EmergencySupportRequestSerializer,
            400: {"description": "Invalid data provided in the form."},
            404: {"description": "The specified emergency session was not found."},
        },
    )
    def perform_create(self, serializer):
        """
        Associates the support request with the current user and the session from the URL.
        """
        session = get_object_or_404(
            EmergencyModeSession, pk=self.kwargs["session_id"], user=self.request.user
        )
        serializer.save(user=self.request.user, session=session)
