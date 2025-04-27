from rest_framework import generics, status, serializers, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import APIException

from django.db.models import Case, When, IntegerField
from django.http import Http404
import logging
import random

from apps.api.permissions import IsSubscribed
from apps.study.models import UserTestAttempt, UserQuestionAttempt
from apps.study.services import get_filtered_questions  # Use the service
from apps.study.api.serializers import (  # Import specific serializers
    TestStartSerializer,
    TestStartResponseSerializer,
    UserTestAttemptListSerializer,
    UserTestAttemptDetailSerializer,
    TestSubmitSerializer,
    TestSubmitResponseSerializer,
)
from apps.study.api.serializers import (  # Import review serializers used here
    TestReviewSerializer,
    TestReviewQuestionSerializer,  # Though used *by* TestReviewSerializer
)


logger = logging.getLogger(__name__)

# --- General Test Attempt Views ---


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="List User Test Attempts",
    description="Retrieves a paginated list of the authenticated user's previous test attempts (practice, simulations, level assessments).",
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptListSerializer(many=True),
            description="Paginated list.",
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class UserTestAttemptListView(generics.ListAPIView):
    serializer_class = UserTestAttemptListSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    # Default pagination applies

    def get_queryset(self):
        # Model Meta defines default ordering by -start_time
        return UserTestAttempt.objects.filter(user=self.request.user).order_by(
            "-start_time"
        )


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Start New Test (Practice/Simulation)",
    description="Initiates a new practice or simulation test based on the provided configuration. Selects questions according to criteria.",
    request=TestStartSerializer,
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="Test started successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., invalid config, no questions found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
    },
)
class StartTestAttemptView(generics.GenericAPIView):
    serializer_class = TestStartSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        result_data = (
            serializer.save()
        )  # Contains {'attempt_id', 'questions': queryset}
        response_serializer = TestStartResponseSerializer(
            result_data, context={"request": request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Retrieve Test Attempt Details",
    description="Gets details of a specific test attempt (any type), including status, configuration, and associated questions (no answers if ongoing). Requires ownership.",
    responses={
        200: OpenApiResponse(
            response=UserTestAttemptDetailSerializer,
            description="Test attempt details.",
        ),
        403: OpenApiResponse(
            description="Permission Denied (Not owner or no subscription)."
        ),
        404: OpenApiResponse(description="Not Found (Test attempt ID invalid)."),
    },
)
class UserTestAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = UserTestAttemptDetailSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    lookup_url_kwarg = "attempt_id"

    def get_queryset(self):
        # Eager load related data if often needed by serializer/frontend
        return UserTestAttempt.objects.filter(
            user=self.request.user
        )  # .select_related('test_definition')

    def get_serializer_context(self):
        # Pass request context for nested serializers if they need it
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Submit Test Answers (Practice/Simulation)",
    description="Submits answers for an ongoing practice or simulation test. Calculates score, updates status, points, proficiency.",
    request=TestSubmitSerializer,
    responses={
        200: OpenApiResponse(
            response=TestSubmitResponseSerializer,
            description="Test submitted successfully.",
        ),
        400: OpenApiResponse(
            description="Validation Error (e.g., already submitted, wrong answers, profile missing)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(
            description="Not Found (Attempt ID invalid or doesn't belong to user)."
        ),  # Raised by serializer validation
    },
)
class SubmitTestAttemptView(generics.GenericAPIView):
    serializer_class = TestSubmitSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    # No queryset needed, validation happens in serializer

    def post(self, request, attempt_id, *args, **kwargs):
        # Pass view context (includes URL kwargs like attempt_id) to serializer for validation
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )
        serializer.is_valid(raise_exception=True)
        result_data = serializer.save()  # Logic handled in serializer using services
        response_serializer = TestSubmitResponseSerializer(result_data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Review Completed Test",
    description="Retrieves a detailed question-by-question review for a *completed* test attempt (any type), including user/correct answers and explanations.",
    parameters=[
        OpenApiParameter(
            name="incorrect_only",
            description="If 'true' or '1', return only incorrect questions.",
            type=str,
        ),  # Use str for boolean query params
    ],
    responses={
        200: OpenApiResponse(
            response=TestReviewSerializer, description="Detailed review questions."
        ),
        400: OpenApiResponse(description="Bad Request (e.g., Attempt not completed)."),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found."),
    },
)
class ReviewTestAttemptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = TestReviewSerializer  # For response structure definition

    def get_object(self):
        """Get the test attempt, ensuring ownership and completion status."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        try:
            # Ensure attempt exists and belongs to user. get_object_or_404 handles the 404.
            attempt = get_object_or_404(
                UserTestAttempt.objects.select_related("user"),  # Keep select_related
                pk=attempt_id,
                user=user,
            )

            # Check if the attempt is completed. Raise ValidationError (400) if not.
            if attempt.status != UserTestAttempt.Status.COMPLETED:
                logger.warning(
                    f"User {user.id} attempted to review non-completed test attempt {attempt_id} (status: {attempt.status})."
                )
                raise serializers.ValidationError(
                    {"detail": _("Cannot review an ongoing or abandoned test attempt.")}
                )

            return attempt
        except Http404:
            # Let Http404 propagate naturally, DRF will handle it as a 404 response.
            logger.info(
                f"Test attempt {attempt_id} not found for user {user.id} during review request."
            )
            raise
        except serializers.ValidationError:
            # Re-raise validation errors (e.g., from the status check) to be handled as 400.
            raise
        except Exception as e:
            # Catch other unexpected errors during fetch and log them.
            # Return a generic 500 or a specific error if identifiable,
            # but avoid raising ValidationError here for non-validation issues.
            logger.exception(
                f"Unexpected error fetching test attempt {attempt_id} for review by user {user.id}: {e}"
            )
            # Raise a standard APIException for server errors
            raise APIException(
                _("An error occurred while retrieving test attempt details."),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request, attempt_id, *args, **kwargs):
        # No changes needed here if get_object handles exceptions correctly
        try:
            test_attempt = self.get_object()
        except serializers.ValidationError as e:
            # This will now only catch the explicit ValidationError from the status check
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        # Http404 raised by get_object will be handled by DRF's default handler
        # APIException raised by get_object will be handled by DRF's default handler (or custom handler)

        # --- Existing logic for fetching questions/answers ---
        questions_queryset = test_attempt.get_questions_queryset()

        user_attempts = UserQuestionAttempt.objects.filter(
            test_attempt=test_attempt,
            question_id__in=test_attempt.question_ids,
        ).select_related("question")

        incorrect_only_param = request.query_params.get("incorrect_only", "").lower()
        incorrect_only = incorrect_only_param in ["true", "1"]

        if incorrect_only:
            incorrect_attempts = [ua for ua in user_attempts if not ua.is_correct]
            incorrect_question_ids = {ua.question_id for ua in incorrect_attempts}
            questions_queryset = questions_queryset.filter(
                pk__in=incorrect_question_ids
            )
            # Reapply ordering if needed (consider if ordering is crucial after filtering)
            if incorrect_question_ids:
                # Apply original ordering to the filtered set
                filtered_original_ids = [
                    qid
                    for qid in test_attempt.question_ids
                    if qid in incorrect_question_ids
                ]
                if filtered_original_ids:
                    preserved_order = Case(
                        *[
                            When(pk=pk, then=pos)
                            for pos, pk in enumerate(filtered_original_ids)
                        ],
                        output_field=IntegerField(),
                    )
                    questions_queryset = questions_queryset.order_by(preserved_order)
                else:  # Handle empty incorrect set edge case
                    questions_queryset = questions_queryset.none()

            user_attempts_map = {
                attempt.question_id: attempt for attempt in incorrect_attempts
            }
        else:
            user_attempts_map = {
                attempt.question_id: attempt for attempt in user_attempts
            }

        context = {"request": request, "user_attempts_map": user_attempts_map}
        response_data = {
            "attempt_id": test_attempt.id,
            "review_questions": questions_queryset,
        }
        serializer = self.get_serializer(response_data, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Study & Progress - Tests & Practice"],
    summary="Retake Similar Test",
    description="Starts a *new* test attempt using the same configuration as a previous attempt (any type). Generates a fresh set of questions, excluding those in the original attempt if possible.",
    request=None,  # No request body
    responses={
        201: OpenApiResponse(
            response=TestStartResponseSerializer,
            description="New similar test started successfully.",
        ),
        400: OpenApiResponse(
            description="Bad Request (Original attempt config invalid or no questions found)."
        ),
        403: OpenApiResponse(description="Permission Denied."),
        404: OpenApiResponse(description="Not Found (Original attempt ID invalid)."),
    },
)
class RetakeSimilarTestAttemptView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    # Reuse TestStartResponseSerializer as the output structure is the same (attempt_id, questions)
    serializer_class = TestStartResponseSerializer

    def get_object(self):
        """Get the original test attempt, ensuring ownership."""
        user = self.request.user
        attempt_id = self.kwargs.get("attempt_id")
        # Allow retake from any status? Let's allow from any for flexibility.
        return get_object_or_404(UserTestAttempt, pk=attempt_id, user=user)

    def post(self, request, attempt_id, *args, **kwargs):
        try:
            original_attempt = self.get_object()
        except Exception as e:  # Catch potential 404 from get_object_or_404
            logger.warning(
                f"Retake requested for non-existent or inaccessible attempt {attempt_id} by user {request.user.id}: {e}"
            )
            return Response(
                {"detail": _("Original test attempt not found or not accessible.")},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = request.user

        # --- Extract and Validate Original Config ---
        original_config_snapshot = original_attempt.test_configuration
        # Add more robust validation for the snapshot structure
        if (
            not isinstance(original_config_snapshot, dict)
            or "config" not in original_config_snapshot
            or not isinstance(original_config_snapshot["config"], dict)
        ):
            logger.error(
                f"Invalid config snapshot found for original attempt {original_attempt.id} during retake."
            )
            raise serializers.ValidationError(
                _("Original test attempt configuration is missing or invalid.")
            )

        original_config_dict = original_config_snapshot["config"]
        original_attempt_type = (
            original_config_snapshot.get("test_type") or original_attempt.attempt_type
        )

        # --- Extract parameters for question filtering ---
        num_questions = original_config_dict.get("num_questions")
        # Ensure slugs/bools are present, provide defaults if structure might vary
        sub_slugs = original_config_dict.get("subsections", [])
        skill_slugs = original_config_dict.get("skills", [])
        starred = original_config_dict.get("starred", False)
        not_mastered = original_config_dict.get("not_mastered", False)

        if not num_questions:
            raise serializers.ValidationError(
                _("Original configuration missing 'num_questions'.")
            )
        if not isinstance(num_questions, int) or num_questions <= 0:
            raise serializers.ValidationError(
                _("Invalid 'num_questions' in original configuration.")
            )

        # Basic check: Ensure at least one filter criterion exists (optional, depends on desired behavior)
        # if not sub_slugs and not skill_slugs and not starred and not not_mastered:
        #     logger.warning(...)

        # --- Select New Questions using Service Function ---
        try:
            new_questions_queryset = get_filtered_questions(
                user=user,
                limit=num_questions,
                subsections=sub_slugs,
                skills=skill_slugs,
                starred=starred,
                not_mastered=not_mastered,
                exclude_ids=original_attempt.question_ids,  # Exclude original set first
            )
            new_question_ids = list(new_questions_queryset.values_list("id", flat=True))

            # Fallback logic
            if not new_question_ids or len(new_question_ids) < num_questions:
                logger.warning(
                    f"Could not find enough *new* questions for retake of attempt {original_attempt.id}. Trying again including original questions."
                )
                new_questions_queryset_fallback = get_filtered_questions(
                    user=user,
                    limit=num_questions,
                    subsections=sub_slugs,
                    skills=skill_slugs,
                    starred=starred,
                    not_mastered=not_mastered,
                    exclude_ids=None,  # Allow original questions
                )
                new_question_ids = list(
                    new_questions_queryset_fallback.values_list("id", flat=True)
                )

            # Final check and sampling
            if not new_question_ids:
                raise serializers.ValidationError(
                    _("No suitable questions found to generate a similar test.")
                )

            actual_num_to_select = min(num_questions, len(new_question_ids))
            if actual_num_to_select < num_questions:
                logger.warning(
                    f"Only found {actual_num_to_select} questions for retake of attempt {original_attempt.id} (requested {num_questions})."
                )

            # Sample from the available IDs
            final_question_ids = random.sample(new_question_ids, actual_num_to_select)

        except serializers.ValidationError:
            raise  # Re-raise validation errors from get_filtered_questions if any
        except Exception as e:
            logger.exception(
                f"Error selecting questions for retake of attempt {original_attempt.id}: {e}"
            )
            raise serializers.ValidationError(
                _("Failed to select questions for the new test.")
            )

        # --- Create New Test Attempt ---
        new_config_snapshot = original_config_snapshot.copy()  # Start with original
        # Update fields specific to the new attempt
        new_config_snapshot["config"]["actual_num_questions_selected"] = len(
            final_question_ids
        )
        new_config_snapshot["retake_of_attempt_id"] = (
            original_attempt.id
        )  # Add reference

        try:
            new_attempt = UserTestAttempt.objects.create(
                user=user,
                attempt_type=original_attempt_type,  # Use original type
                test_configuration=new_config_snapshot,
                question_ids=final_question_ids,
                status=UserTestAttempt.Status.STARTED,
            )
        except Exception as e:
            logger.exception(
                f"Error creating retake UserTestAttempt for user {user.id} (original: {original_attempt.id}): {e}"
            )
            raise serializers.ValidationError(
                {"non_field_errors": [_("Failed to start the new similar test.")]}
            )

        # --- Prepare and Return Response ---
        final_questions_queryset = new_attempt.get_questions_queryset()
        result_data = {
            "attempt_id": new_attempt.id,
            "questions": final_questions_queryset,
        }
        # Use the serializer for consistent output format
        response_serializer = self.get_serializer(
            result_data, context={"request": request}
        )
        response_data = response_serializer.data
        # Add extra message for clarity if desired (optional)
        # response_data["message"] = _("New test started based on attempt #{}.").format(original_attempt.id)

        return Response(response_data, status=status.HTTP_201_CREATED)
