import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.challenges.models import (
    Challenge,
    ChallengeAttempt,
    ChallengeStatus,
    ChallengeType,
)
from apps.learning.api.serializers import UnifiedQuestionSerializer
from apps.users.api.serializers import SimpleUserSerializer
from apps.study.models import UserQuestionAttempt

User = get_user_model()
logger = logging.getLogger(__name__)


class ChallengeAttemptSerializer(serializers.ModelSerializer):
    """Serializer for a single participant's attempt within a challenge."""

    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ChallengeAttempt
        fields = ["id", "user", "score", "is_ready", "start_time", "end_time"]


class ChallengeListSerializer(serializers.ModelSerializer):
    """Serializer for listing challenges, optimized for performance."""

    challenger = SimpleUserSerializer(read_only=True)
    opponent = SimpleUserSerializer(read_only=True)
    winner = SimpleUserSerializer(read_only=True)
    challenge_type_display = serializers.CharField(
        source="get_challenge_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_is_participant = serializers.SerializerMethodField()
    user_is_winner = serializers.SerializerMethodField()
    user_score = serializers.SerializerMethodField()
    opponent_score = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = [
            "id",
            "challenger",
            "opponent",
            "challenge_type",
            "challenge_type_display",
            "status",
            "status_display",
            "winner",
            "created_at",
            "completed_at",
            "user_is_participant",
            "user_is_winner",
            "user_score",
            "opponent_score",
        ]
        read_only_fields = fields

    def _get_current_user(self):
        """
        Safely retrieve the user from the context.
        Returns None if no request or authenticated user is found.
        """
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return request.user
        return None

    def _get_attempt_for_user(
        self, challenge: Challenge, user: User
    ) -> ChallengeAttempt | None:
        """Efficiently find a user's attempt from prefetched data."""
        if not user:
            return None
        # obj.attempts.all() uses prefetched data, so this loop is fast (in-memory).
        for attempt in challenge.attempts.all():
            if attempt.user_id == user.id:
                return attempt
        return None

    def get_user_is_participant(self, obj: Challenge) -> bool:
        user = self._get_current_user()
        return obj.is_participant(user) if user else False

    def get_user_is_winner(self, obj: Challenge) -> bool:
        user = self._get_current_user()
        return obj.winner == user if user and obj.winner else False

    def get_user_score(self, obj: Challenge) -> int | None:
        """Get the score for the requesting user."""
        user = self._get_current_user()
        attempt = self._get_attempt_for_user(obj, user)
        if attempt:
            return attempt.score
        # If user is a participant but no attempt record exists yet, score is 0.
        return 0 if self.get_user_is_participant(obj) else None

    def get_opponent_score(self, obj: Challenge) -> int | None:
        """Get the score for the opponent relative to the requesting user."""
        user = self._get_current_user()
        if not user or not obj.opponent or not self.get_user_is_participant(obj):
            return None

        # Determine who the opponent is relative to the current user
        other_user = obj.challenger if user.id == obj.opponent_id else obj.opponent

        attempt = self._get_attempt_for_user(obj, other_user)
        if attempt:
            return attempt.score
        # If opponent is a participant but no attempt record exists yet, score is 0.
        return 0 if obj.is_participant(other_user) else None


class ChallengeCreateSerializer(serializers.Serializer):
    """Serializer for creating a new challenge."""

    opponent_username = serializers.CharField(
        max_length=150,
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text=_(
            "Username of the opponent for a direct challenge. Leave blank for random matchmaking."
        ),
    )
    challenge_type = serializers.ChoiceField(
        choices=ChallengeType.choices, help_text=_("The type of challenge to create.")
    )

    # Allow custom config in the future?
    # config = serializers.JSONField(required=False)
    def validate(self, attrs):
        challenger = self.context["request"].user
        opponent_username = attrs.get("opponent_username")

        if opponent_username:
            if opponent_username == challenger.username:
                raise serializers.ValidationError(
                    {"opponent_username": _("You cannot challenge yourself.")}
                )
            try:
                opponent = User.objects.get(
                    username__iexact=opponent_username, is_active=True
                )
                attrs["opponent"] = opponent
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"opponent_username": _("Opponent user not found or inactive.")}
                )
        else:
            attrs["opponent"] = None  # Explicitly set for random matchmaking

        # Clean up the raw username field
        attrs.pop("opponent_username", None)

        # TODO: Add validation for challenge_type if needed (e.g., check if user level is suitable?)
        # TODO: Validate if the challenger/opponent already have an active challenge together?

        return attrs

    def create(self, validated_data):
        # The create method delegates the actual object creation to the service layer.
        # This is a key principle: serializers handle data format/validation, not business logic.
        from ..services import start_challenge

        challenger = self.context["request"].user
        try:
            challenge, message, initial_status = start_challenge(
                challenger=challenger, **validated_data
            )
            return challenge
        except serializers.ValidationError as e:
            # Re-raise DRF validation errors to be handled by the framework
            raise e
        except Exception as e:
            # Catch other potential exceptions from the service layer
            logger.error(f"Error creating challenge via serializer: {e}", exc_info=True)
            raise serializers.ValidationError(
                _("An unexpected error occurred while creating the challenge.")
            )


class ChallengeDetailSerializer(ChallengeListSerializer):
    """Detailed view of a challenge, including attempts and questions."""

    attempts = ChallengeAttemptSerializer(many=True, read_only=True)
    questions = serializers.SerializerMethodField()
    challenge_config = serializers.JSONField(read_only=True)

    class Meta(ChallengeListSerializer.Meta):
        fields = ChallengeListSerializer.Meta.fields + [
            "attempts",
            "challenge_config",
            "questions",
            "accepted_at",
            "started_at",
        ]
        read_only_fields = fields

    def get_questions(self, obj: Challenge) -> list | None:
        """
        Securely returns the list of questions based on the user's role and
        the challenge's status.

        This method ensures that:
        - Only participants can ever see the questions.
        - The challenger can see the questions immediately upon creation.
        - The opponent can only see the questions AFTER accepting the invite.
        - Both participants can see the questions during and after the challenge.
        """
        user = self._get_current_user()

        # Rule 1: Must be a participant.
        if not user or not obj.is_participant(user):
            return None

        # Rule 2: Determine if the user has viewing rights based on status.
        can_view_questions = False

        # Case A: Challenge is accepted, active, or finished. All participants can view.
        if obj.status in [
            ChallengeStatus.ACCEPTED,
            ChallengeStatus.ONGOING,
            ChallengeStatus.COMPLETED,
        ]:
            can_view_questions = True

        # Case B: Challenge is a pending invite. Only the challenger can view.
        # This prevents the opponent from peeking at questions before accepting.
        elif obj.status == ChallengeStatus.PENDING_INVITE and obj.challenger == user:
            can_view_questions = True

        if can_view_questions:
            question_qs = obj.get_questions_queryset()

            # Best Practice: Always pass the context down to nested serializers.
            # This ensures things like the `request` object are available if needed.
            serializer_context = self.context

            return UnifiedQuestionSerializer(
                question_qs, many=True, context=serializer_context
            ).data

        # If no condition is met, do not reveal the questions.
        return None


class ChallengeAnswerSerializer(serializers.Serializer):
    """Serializer for submitting an answer to a question within a challenge."""

    question_id = serializers.IntegerField(
        help_text=_("The ID of the question being answered.")
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices,
        help_text=_("The selected answer choice (e.g., 'A', 'B')."),
    )
    time_taken_seconds = serializers.IntegerField(required=False, min_value=0)

    def validate_question_id(self, value):
        challenge = self.context["view"].get_object()
        if value not in challenge.question_ids:
            raise serializers.ValidationError(
                _("This question is not part of the current challenge.")
            )
        return value

    def validate_selected_answer(self, value):
        # Ensure the choice is valid according to the UserQuestionAttempt model
        valid_choices = UserQuestionAttempt.AnswerChoice.values
        if value not in valid_choices:
            raise serializers.ValidationError(_("Invalid answer choice provided."))
        return value


class ChallengeResultSerializer(ChallengeDetailSerializer):
    """Serializer focused on showing final challenge results. Inherits all detail fields."""

    pass
