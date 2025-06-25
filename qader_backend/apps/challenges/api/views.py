from django.db.models import Q
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets, status, mixins
from rest_framework.serializers import ValidationError
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.api.permissions import IsSubscribed

from ..models import Challenge, ChallengeStatus
from .serializers import (
    ChallengeListSerializer,
    ChallengeDetailSerializer,
    ChallengeCreateSerializer,
    ChallengeAnswerSerializer,
    ChallengeResultSerializer,
    ChallengeTypeSerializer,
)
from .permissions import (
    IsParticipant,
    IsInvitedOpponent,
    IsChallengeOwner,
)
from ..services import (
    accept_challenge,
    decline_challenge,
    cancel_challenge,
    set_participant_ready,
    process_challenge_answer,
    create_rematch,
    finalize_challenge,  # May not be called directly by user, but good practice to import
)
from ..filters import ChallengeFilter  # Create this filter class
from rest_framework import generics
from ..models import ChallengeType
from ..services import CHALLENGE_CONFIGS


@extend_schema_view(
    list=extend_schema(summary="List User Challenges", tags=["Challenges"]),
    create=extend_schema(summary="Start a New Challenge", tags=["Challenges"]),
    retrieve=extend_schema(summary="Get Challenge Details", tags=["Challenges"]),
    accept=extend_schema(
        summary="Accept Challenge Invite", request=None, tags=["Challenges"]
    ),
    decline=extend_schema(
        summary="Decline Challenge Invite", request=None, tags=["Challenges"]
    ),
    cancel=extend_schema(
        summary="Cancel Pending Challenge (Challenger only)",
        request=None,
        tags=["Challenges"],
    ),
    ready=extend_schema(
        summary="Mark Self as Ready for Challenge", request=None, tags=["Challenges"]
    ),
    answer=extend_schema(summary="Submit Answer in Challenge", tags=["Challenges"]),
    results=extend_schema(summary="Get Challenge Results", tags=["Challenges"]),
    rematch=extend_schema(
        summary="Initiate a Rematch", request=None, tags=["Challenges"]
    ),
)
class ChallengeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for creating, viewing, and interacting with user challenges.
    Provides actions for the entire challenge lifecycle, from creation to completion.
    """

    serializer_class = ChallengeDetailSerializer  # Default serializer
    permission_classes = [IsAuthenticated, IsSubscribed]  # Default permissions
    filter_backends = [DjangoFilterBackend]
    filterset_class = ChallengeFilter
    queryset = Challenge.objects.all()

    def get_queryset(self):
        """
        Returns a queryset of challenges relevant to the authenticated user.
        Leverages the custom ChallengeManager for optimized data fetching.
        """
        return Challenge.objects.get_for_user(self.request.user)

    def get_serializer_class(self):
        """Returns the appropriate serializer class based on the action."""
        action_serializer_map = {
            "list": ChallengeListSerializer,
            "create": ChallengeCreateSerializer,
            "answer": ChallengeAnswerSerializer,
            "results": ChallengeResultSerializer,
        }
        return action_serializer_map.get(self.action, self.serializer_class)

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated, IsSubscribed]
        elif self.action in [
            "list",
            "retrieve",
            "ready",
            "answer",
            "results",
            "rematch",
        ]:
            permission_classes = [IsAuthenticated, IsSubscribed, IsParticipant]
        elif self.action in ["accept", "decline"]:
            permission_classes = [IsAuthenticated, IsSubscribed, IsInvitedOpponent]
        elif self.action == "cancel":
            permission_classes = [IsAuthenticated, IsSubscribed, IsChallengeOwner]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Creates a new challenge using the service layer.
        Uses the `ChallengeCreateSerializer` for input validation and the
        `ChallengeDetailSerializer` for the response payload.
        """
        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        # The serializer's .save() method calls our service function.
        instance = create_serializer.save()

        response_serializer = ChallengeDetailSerializer(
            instance, context=self.get_serializer_context()
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    # Note: perform_create is no longer needed with the refactored create method.

    @action(detail=True, methods=["post"])  # Permissions defined in get_permissions
    def accept(self, request, pk=None):
        challenge = self.get_object()
        try:
            updated_challenge = accept_challenge(challenge, request.user)
            serializer = ChallengeDetailSerializer(
                updated_challenge, context=self.get_serializer_context()
            )
            return Response(serializer.data)
        except (ValidationError, PermissionDenied) as e:
            raise e  # Let DRF's exception handler manage the response format

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        challenge = self.get_object()
        decline_challenge(challenge, request.user)
        return Response({"status": "declined"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        challenge = self.get_object()
        cancel_challenge(challenge, request.user)
        return Response({"status": "cancelled"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def ready(self, request, pk=None):
        """Marks the current user as ready to start the challenge."""
        challenge = self.get_object()
        updated_challenge, started = set_participant_ready(challenge, request.user)
        response_data = {
            "user_status": "ready",
            "challenge_status": updated_challenge.status,
            "challenge_started": started,
            "detail": (
                "Your status is set to ready. Waiting for opponent."
                if not started
                else "Challenge is starting now!"
            ),
        }
        return Response(response_data)

    @action(detail=True, methods=["post"])
    def answer(self, request, pk=None):
        challenge = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_attempt, challenge_ended = process_challenge_answer(
            challenge=challenge, user=request.user, **serializer.validated_data
        )
        response_data = {
            "status": "answer_received",
            "is_correct": question_attempt.is_correct,
            "challenge_ended": challenge_ended,
        }
        if challenge_ended:
            challenge.refresh_from_db()
            result_serializer = ChallengeResultSerializer(
                challenge, context=self.get_serializer_context()
            )
            response_data["final_results"] = result_serializer.data
        return Response(response_data)

    @action(detail=True, methods=["get"])
    def results(self, request, pk=None):
        challenge = self.get_object()
        if challenge.status != ChallengeStatus.COMPLETED:
            return Response(
                {"detail": "Challenge is not completed yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(challenge)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def rematch(self, request, pk=None):
        """Initiates a rematch for a completed challenge."""
        original_challenge = self.get_object()
        try:
            new_challenge = create_rematch(original_challenge, request.user)
            serializer = ChallengeDetailSerializer(
                new_challenge, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, PermissionDenied, ValidationError) as e:
            # Let DRF's default exception handler manage the response format.
            raise e


@extend_schema_view(
    get=extend_schema(
        summary="List Available Challenge Types",
        description="Retrieves a list of all predefined challenge types that users can select from. This endpoint allows the frontend to dynamically display challenge options without needing to hardcode them.",
        tags=["Challenges"],
    )
)
class ChallengeTypeListView(generics.ListAPIView):
    """
    Provides a read-only list of available challenge types and their configurations.
    """

    # This view does not require a queryset as it sources data from a settings dictionary.
    queryset = []
    serializer_class = ChallengeTypeSerializer
    permission_classes = [
        IsAuthenticated
    ]  # Ensure only authenticated users can see the types
    pagination_class = None  # We want to return all types, not paginate them.

    def get_queryset(self):
        """
        Constructs a list of challenge type objects from the CHALLENGE_CONFIGS dictionary.
        """
        challenge_types = []
        for choice in ChallengeType.choices:
            key, name = choice
            config = CHALLENGE_CONFIGS.get(key)

            # Only include types that have a defined configuration
            if config:
                challenge_types.append(
                    {
                        "key": key,
                        "name": name,
                        "description": config.get("description", ""),
                        "num_questions": config.get("num_questions"),
                        "time_limit_seconds": config.get("time_limit_seconds"),
                        "allow_hints": config.get("allow_hints", False),
                    }
                )

        return challenge_types
