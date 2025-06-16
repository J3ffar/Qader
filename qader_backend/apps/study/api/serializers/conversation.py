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
)
from apps.learning.api.serializers import (
    UnifiedQuestionSerializer,
)  # Assumes a simple user serializer exists


class ConversationMessageSerializer(serializers.ModelSerializer):
    """Serializer for individual conversation messages."""

    sender_type = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True, format="%Y-%m-%d %H:%M:%S")

    # Use a single field for both read and write, applying write_only=True for input phase if needed
    message_text = serializers.CharField(
        required=True, style={"base_template": "textarea.html"}
    )

    # Display related question ID if it exists
    related_question_id = serializers.PrimaryKeyRelatedField(
        read_only=True, source="related_question"
    )

    class Meta:
        model = ConversationMessage
        fields = [
            "id",
            "session",  # Useful for debugging/context sometimes
            "sender_type",
            "message_text",
            "related_question_id",
            "timestamp",
        ]
        read_only_fields = [
            "id",
            "session",
            "sender_type",
            "timestamp",
            "related_question_id",
        ]


class ConversationSessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing conversation sessions."""

    user = SimpleUserSerializer(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="api:v1:study:conversation-detail", read_only=True
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
    current_topic_question = UnifiedQuestionSerializer(
        read_only=True, allow_null=True, context={"exclude_sensitive_fields": True}
    )

    class Meta(ConversationSessionListSerializer.Meta):
        fields = ConversationSessionListSerializer.Meta.fields + [
            "messages",
            "current_topic_question",
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


class AIConfirmUnderstandingResponseSerializer(serializers.Serializer):
    """
    Serializer for the response when the user confirms understanding ('Got It').
    It includes a message from the AI and a new question to test the user.
    """

    ai_message = serializers.CharField(
        read_only=True,
        help_text=_("A transitional or encouraging message from the AI."),
    )
    test_question = UnifiedQuestionSerializer(
        read_only=True, help_text=_("The related test question posed by the AI.")
    )


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
    """
    Output showing the result of the submitted test answer.
    Now uses the UnifiedQuestionSerializer for consistency.
    """

    # Use the unified serializer to show the full question details for review
    question = UnifiedQuestionSerializer(read_only=True)
    ai_feedback = serializers.CharField(
        read_only=True,
        help_text=_("Feedback generated by the AI on the user's answer."),
    )

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "id",
            "question",  # This nested object now contains all question details
            "selected_answer",
            "is_correct",
            "attempted_at",
            "ai_feedback",  # Formalizing this field
        ]


class AIQuestionResponseSerializer(serializers.Serializer):
    """Serializer for the response when the AI asks a question."""

    ai_message = serializers.CharField(
        read_only=True, help_text=_("The encouraging message from the AI.")
    )
    # Embed the simple question details directly
    question = UnifiedQuestionSerializer(
        read_only=True, help_text=_("The question posed by the AI.")
    )
