# apps/study/api/serializers/conversation.py
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
)
from apps.learning.models import Question
from apps.users.api.serializers import (
    SimpleUserSerializer,
)  # Assumes a simple user serializer exists


class ConversationMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual conversation messages."""

    sender_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    # Input only needs message_text
    message_text = serializers.CharField(
        write_only=True, required=True, style={"base_template": "textarea.html"}
    )
    # Output includes text
    message_text_display = serializers.CharField(source="message_text", read_only=True)
    # Optionally include related question info if needed
    # related_question_id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConversationMessage
        fields = [
            "id",
            "sender_type",
            "message_text",  # Write-only field for input
            "message_text_display",  # Read-only field for output
            "timestamp",
            # 'related_question_id',
        ]
        read_only_fields = ["id", "sender_type", "timestamp", "message_text_display"]


class ConversationSessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversation sessions."""

    user = SimpleUserSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="study:conversation-detail", read_only=True
    )

    class Meta:
        model = ConversationSession
        fields = [
            "id",
            "url",
            "user",
            "ai_tone",
            "status",
            "start_time",
            "end_time",
            "updated_at",
        ]


class ConversationSessionDetailSerializer(ConversationSessionListSerializer):
    """Serializer for conversation session details, including messages."""

    messages = ConversationMessageSerializer(many=True, read_only=True)
    # Field to show the question currently being focused on
    current_topic_question_id = serializers.PrimaryKeyRelatedField(
        read_only=True, allow_null=True, source="current_topic_question"
    )

    class Meta(ConversationSessionListSerializer.Meta):
        fields = ConversationSessionListSerializer.Meta.fields + [
            "messages",
            "current_topic_question_id",
        ]


class ConversationSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new conversation session."""

    ai_tone = serializers.ChoiceField(
        choices=ConversationSession.AiTone.choices,
        required=False,  # Default is 'serious' in model
        help_text=_("Choose the desired tone for the AI assistant."),
    )

    class Meta:
        model = ConversationSession
        fields = ["ai_tone"]
        # user is set automatically from request


class ConversationUserMessageInputSerializer(serializers.Serializer):
    """Serializer for user input message within a session."""

    message_text = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )
    # Optional: Allow user to specify the question they are referring to
    related_question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=False,
        allow_null=True,
        help_text=_("Optional: Link this message to a specific question ID."),
    )


class ConfirmUnderstandingSerializer(serializers.Serializer):
    """Input when user clicks 'Got It' for a specific question/concept."""

    # User confirms understanding related to the session's current_topic_question
    pass  # No input needed if using session's context


class ConversationTestQuestionSerializer(serializers.ModelSerializer):
    """Serializer to represent the test question shown to the user."""

    class Meta:
        model = Question
        fields = [
            "id",
            "question_text",
            "option_a",
            "option_b",
            "option_c",
            "option_d",
            # DO NOT include correct_answer or explanation here
        ]


class ConversationTestSubmitSerializer(serializers.Serializer):
    """Input for submitting the answer to the conversation test question."""

    question_id = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(),
        required=True,
        help_text=_("The ID of the question being answered."),
    )
    selected_answer = serializers.ChoiceField(
        choices=UserQuestionAttempt.AnswerChoice.choices,
        required=True,
        help_text=_("The answer selected by the user (A, B, C, or D)."),
    )


class ConversationTestResultSerializer(serializers.ModelSerializer):
    """Output showing the result of the submitted test answer."""

    question = ConversationTestQuestionSerializer(
        read_only=True
    )  # Show the question again for context
    explanation = serializers.CharField(source="question.explanation", read_only=True)
    correct_answer = serializers.CharField(
        source="question.correct_answer", read_only=True
    )

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "id",
            "question",
            "selected_answer",
            "is_correct",
            "correct_answer",
            "explanation",
            "attempted_at",
        ]
