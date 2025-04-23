from rest_framework import viewsets, status, mixins
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
    ViewSet for managing Challenges.
    """

    queryset = (
        Challenge.objects.select_related(
            "challenger__profile", "opponent__profile", "winner__profile"
        )
        .prefetch_related("attempts__user__profile")
        .all()
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = ChallengeFilter  # Define this filter class

    def get_serializer_class(self):
        if self.action == "list":
            return ChallengeListSerializer
        elif self.action == "create":
            return ChallengeCreateSerializer
        elif self.action == "retrieve":
            return ChallengeDetailSerializer
        elif self.action == "answer":
            return ChallengeAnswerSerializer
        elif self.action == "results":
            return ChallengeResultSerializer
        # Default or other actions might use Detail
        return ChallengeDetailSerializer

    def get_permissions(self):
        """Instantiates and returns the list of permissions for the action."""
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
            # Retrieve needs participant check on object level
            permission_classes = [IsAuthenticated, IsSubscribed, IsParticipant]
        elif self.action == "accept" or self.action == "decline":
            permission_classes = [IsAuthenticated, IsSubscribed, IsInvitedOpponent]
        elif self.action == "cancel":
            permission_classes = [IsAuthenticated, IsSubscribed, IsChallengeOwner]
        else:
            permission_classes = [IsAuthenticated]  # Default deny? Or IsAdminUser?
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Filter queryset to only show challenges the user is part of."""
        user = self.request.user
        if user.is_authenticated:
            # Using Q objects to get challenges where user is challenger OR opponent
            return (
                super()
                .get_queryset()
                .filter(models.Q(challenger=user) | models.Q(opponent=user))
                .distinct()
            )
        return Challenge.objects.none()  # Should not happen due to permissions

    def perform_create(self, serializer):
        # The create logic is now handled within ChallengeCreateSerializer using the service
        challenge = serializer.save()  # This calls serializer.create -> start_challenge
        # We need to return the newly created challenge instance data
        # Use the Detail serializer for the response
        response_serializer = ChallengeDetailSerializer(
            challenge, context=self.get_serializer_context()
        )
        # Manually construct response as perform_create expects None return, but CreateModelMixin handles response
        # This override is needed because we use a different serializer for response than for request
        self.response_on_create = Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )

    def create(self, request, *args, **kwargs):
        """Override create to use the custom response pattern."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        # Use the response set in perform_create or default if something went wrong
        response = getattr(
            self,
            "response_on_create",
            Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers),
        )
        return response

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsInvitedOpponent],
    )
    def accept(self, request, pk=None):
        """Accept a challenge invitation."""
        challenge = self.get_object()
        try:
            updated_challenge = accept_challenge(challenge, request.user)
            serializer = self.get_serializer(updated_challenge)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsInvitedOpponent],
    )
    def decline(self, request, pk=None):
        """Decline a challenge invitation."""
        challenge = self.get_object()
        try:
            updated_challenge = decline_challenge(challenge, request.user)
            # Return minimal response for decline
            return Response({"status": "declined"}, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsChallengeOwner],
    )
    def cancel(self, request, pk=None):
        """Cancel a challenge invitation (challenger only)."""
        challenge = self.get_object()
        try:
            updated_challenge = cancel_challenge(challenge, request.user)
            return Response({"status": "cancelled"}, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsParticipant],
    )
    def ready(self, request, pk=None):
        """Mark participant as ready."""
        challenge = self.get_object()
        try:
            updated_challenge, started = set_participant_ready(challenge, request.user)
            response_data = {
                "user_status": "ready",
                "challenge_status": updated_challenge.status,
                "challenge_started": started,
            }
            # Optionally include full challenge details if it just started
            # if started:
            #    serializer = ChallengeDetailSerializer(updated_challenge, context=self.get_serializer_context())
            #    response_data['challenge_details'] = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsParticipant],
    )
    def answer(self, request, pk=None):
        """Submit an answer for a question in the challenge."""
        challenge = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if challenge.status != ChallengeStatus.ONGOING:
            return Response(
                {"detail": "Challenge is not ongoing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            question_attempt, challenge_ended = process_challenge_answer(
                challenge=challenge,
                user=request.user,
                question_id=serializer.validated_data["question_id"],
                selected_answer=serializer.validated_data["selected_answer"],
                time_taken=serializer.validated_data.get("time_taken_seconds"),
            )
            response_data = {
                "status": "answer_received",
                "is_correct": question_attempt.is_correct,  # Provide immediate feedback
                "challenge_ended": challenge_ended,
            }
            if challenge_ended:
                # Refresh challenge object to get updated status/winner after finalization
                challenge.refresh_from_db()
                result_serializer = ChallengeResultSerializer(
                    challenge, context=self.get_serializer_context()
                )
                response_data["final_results"] = result_serializer.data

            return Response(response_data, status=status.HTTP_200_OK)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsParticipant],
    )
    def results(self, request, pk=None):
        """Get the results of a completed challenge."""
        challenge = self.get_object()
        if challenge.status != ChallengeStatus.COMPLETED:
            return Response(
                {"detail": "Challenge is not completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ChallengeResultSerializer(
            challenge, context=self.get_serializer_context()
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsSubscribed, IsParticipant],
    )
    def rematch(self, request, pk=None):
        """Initiate a rematch."""
        original_challenge = self.get_object()
        try:
            new_challenge = create_rematch(original_challenge, request.user)
            serializer = ChallengeDetailSerializer(
                new_challenge, context=self.get_serializer_context()
            )
            # Use 201 Created for the new resource
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (ValidationError, PermissionDenied) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --- Utility View (Optional) ---
# class ChallengeTypeListView(generics.ListAPIView):
#     serializer_class = ChallengeTypeSerializer # Define this serializer
#     permission_classes = [IsAuthenticated, IsSubscribed]
#     queryset = # Logic to get challenge types from settings/db
