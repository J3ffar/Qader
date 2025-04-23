import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from apps.study.models import UserQuestionAttempt

from ..models import Challenge, ChallengeAttempt, ChallengeType, ChallengeStatus
from apps.users.api.serializers import (
    SimpleUserSerializer,
)  # Assuming a simple user serializer exists
from apps.learning.api.serializers import (
    QuestionListSerializer,
)  # To show questions during challenge
from ..services import start_challenge  # Import the service function

User = get_user_model()

logger = logging.getLogger(__name__)

# --- Nested Serializers ---


class ChallengeAttemptSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ChallengeAttempt
        fields = ["id", "user", "score", "is_ready", "start_time", "end_time"]


# --- Main Challenge Serializers ---


class ChallengeListSerializer(serializers.ModelSerializer):
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
        read_only_fields = fields  # List view is read-only

    def get_user_is_participant(self, obj) -> bool:
        user = self.context["request"].user
        return obj.is_participant(user)

    def get_user_is_winner(self, obj) -> bool | None:
        user = self.context["request"].user
        if obj.status != ChallengeStatus.COMPLETED:
            return None
        return obj.winner == user

    def _get_attempt_score(self, obj, user) -> int | None:
        if not user or not obj.is_participant(user):
            return None
        try:
            # Fetch attempt score efficiently
            attempt = (
                obj.attempts.filter(user=user).values_list("score", flat=True).first()
            )
            return attempt if attempt is not None else 0
        except Exception:  # Broad except for safety in serializer method
            return None

    def get_user_score(self, obj) -> int | None:
        user = self.context["request"].user
        return self._get_attempt_score(obj, user)

    def get_opponent_score(self, obj) -> int | None:
        user = self.context["request"].user
        other_user = None
        if obj.challenger == user and obj.opponent:
            other_user = obj.opponent
        elif obj.opponent == user:
            other_user = obj.challenger

        return self._get_attempt_score(obj, other_user)


class ChallengeCreateSerializer(serializers.Serializer):
    opponent_username = serializers.CharField(
        max_length=150, required=False, allow_null=True, allow_blank=True
    )
    challenge_type = serializers.ChoiceField(choices=ChallengeType.choices)
    # Allow custom config in the future?
    # config = serializers.JSONField(required=False)

    def validate(self, attrs):
        challenger = self.context["request"].user
        opponent_username = attrs.get("opponent_username")

        if opponent_username:
            if opponent_username == challenger.username:
                raise serializers.ValidationError(_("You cannot challenge yourself."))
            try:
                opponent = User.objects.get(username=opponent_username, is_active=True)
                attrs["opponent"] = opponent
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    _("Opponent user not found or inactive.")
                )
        else:
            # Logic for random matchmaking (requires opponent=None initially)
            attrs["opponent"] = None

        # TODO: Add validation for challenge_type if needed (e.g., check if user level is suitable?)
        # TODO: Validate if the challenger/opponent already have an active challenge together?

        return attrs

    def create(self, validated_data):
        # Use the service layer to handle challenge creation logic
        challenger = self.context["request"].user
        opponent = validated_data.get("opponent")
        challenge_type = validated_data["challenge_type"]

        try:
            challenge, message, initial_status = start_challenge(
                challenger=challenger,
                opponent=opponent,  # Can be None for random
                challenge_type=challenge_type,
            )
            # Attach message to the serializer context or return it if needed
            # For now, just return the created challenge instance
            return challenge
        except ValidationError as e:
            # Convert service validation errors to DRF validation errors
            raise serializers.ValidationError(e.detail)
        except Exception as e:
            # Handle unexpected errors from the service
            logger.error(f"Error creating challenge via service: {e}", exc_info=True)
            raise serializers.ValidationError(
                _("Failed to start challenge due to an internal error.")
            )


class ChallengeDetailSerializer(ChallengeListSerializer):  # Inherit list fields
    attempts = ChallengeAttemptSerializer(many=True, read_only=True)
    questions = serializers.SerializerMethodField()
    challenge_config = serializers.JSONField(read_only=True)  # Show config used

    class Meta(ChallengeListSerializer.Meta):  # Inherit Meta
        fields = ChallengeListSerializer.Meta.fields + [
            "attempts",
            "challenge_config",
            "questions",
            "accepted_at",
            "started_at",
        ]
        read_only_fields = fields  # Detail view primarily read-only via GET

    def get_questions(self, obj) -> list | None:
        """Only return questions if the challenge is ongoing and user is participant."""
        user = self.context["request"].user
        if obj.status == ChallengeStatus.ONGOING and obj.is_participant(user):
            # Use the efficient QuestionListSerializer
            question_qs = obj.get_questions_queryset()
            # Pass user context to QuestionListSerializer if it needs it (e.g., for is_starred)
            serializer_context = {"request": self.context["request"]}
            return QuestionListSerializer(
                question_qs, many=True, context=serializer_context
            ).data
        return None


class ChallengeAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices
    )
    time_taken_seconds = serializers.IntegerField(required=False, min_value=0)

    def validate_question_id(self, value):
        # Check if the question belongs to the challenge being answered
        challenge = self.context["view"].get_object()  # Get challenge from view context
        if value not in challenge.question_ids:
            raise serializers.ValidationError(
                _("Invalid question ID for this challenge.")
            )
        return value


class ChallengeResultSerializer(ChallengeDetailSerializer):
    """Serializer focused on showing final results."""

    # Potentially add more result-specific fields if needed later
    class Meta(ChallengeDetailSerializer.Meta):
        # Exclude fields not relevant for results view?
        # exclude = ['questions'] # Don't show questions again in results view
        pass
