import textwrap
from rest_framework import generics, status, views, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction
from django.utils.translation import gettext_lazy as _  # For descriptions

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,  # if needed for specific error examples
)
from drf_spectacular.types import OpenApiTypes

from apps.users.models import UserProfile, RoleChoices
from ..models import Conversation, Message
from .serializers import (
    ChatConversationSerializer,
    ChatMessageSerializer,
    CreateMessageSerializer,
)
from .permissions import IsConversationParticipant

CHAT_COMMON_ERRORS = {
    status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
        description="Unauthorized: Authentication credentials were not provided or are invalid."
    ),
    status.HTTP_403_FORBIDDEN: OpenApiResponse(
        description="Forbidden: You do not have permission to perform this action on this resource."
    ),
    status.HTTP_404_NOT_FOUND: OpenApiResponse(
        description="Not Found: The requested resource (e.g., conversation, mentor) could not be found."
    ),
}


@extend_schema_view(
    get=extend_schema(
        tags=["Chat"],
        summary="Retrieve Student's Active Conversation with Mentor",
        description=textwrap.dedent(
            """
        Retrieves the active chat conversation for the authenticated **student** with their currently assigned mentor.
        If a conversation doesn't exist but a mentor is assigned, it will be created and returned.

        **Access:** Authenticated Students only.
        """
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ChatConversationSerializer,
                description="Conversation details retrieved successfully (or created).",
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden: User is not a student."
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                description="Not Found: Student has no mentor assigned, or an error occurred fetching/creating the conversation."
            ),
            **CHAT_COMMON_ERRORS,
        },
    )
)
class StudentConversationView(generics.RetrieveAPIView):
    """
    Retrieves the student's active conversation with their mentor.
    If a conversation doesn't exist but a mentor is assigned, it's created.
    """

    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        user_profile: UserProfile = self.request.user.profile
        if user_profile.role != RoleChoices.STUDENT:
            raise DjangoPermissionDenied(_("Only students can access this view."))

        mentor_profile = user_profile.assigned_mentor
        if not mentor_profile:
            # Using Http404 directly for cleaner error propagation to DRF
            raise generics.Http404(_("No mentor assigned. Conversation not available."))

        try:
            conversation, created = Conversation.get_or_create_conversation(
                student_profile=user_profile, teacher_profile=mentor_profile
            )
            if created:
                # Log creation if desired
                pass
            return conversation
        except (ValueError, PermissionError, Conversation.DoesNotExist) as e:
            # Log this error
            # logger.error(f"Error in StudentConversationView for user {user_profile.user.username}: {e}")
            raise generics.Http404(str(e))


@extend_schema_view(
    get=extend_schema(
        tags=["Chat"],
        summary="List Messages in a Conversation",
        description=textwrap.dedent(
            """
        Lists all messages within a specific conversation.
        - **For Students:** Accesses their conversation with their mentor.
        - **For Teachers/Trainers:** Accesses a specific conversation with one of their students via `conversation_pk`.

        Messages retrieved by the recipient are automatically marked as read.
        Results are paginated.

        **Access:** Authenticated Students (for their own conversation), Authenticated Teachers/Trainers (for conversations they are part of).
        """
        ),
        parameters=[
            OpenApiParameter(
                name="conversation_pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=False,  # Only required for teacher/trainer context
                description="The ID of the conversation (Required for Teachers/Trainers).",
            )
        ],
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ChatMessageSerializer(many=True),
                description="List of messages retrieved successfully.",
            ),
            **CHAT_COMMON_ERRORS,
        },
    ),
    post=extend_schema(
        tags=["Chat"],
        summary="Send a Message in a Conversation",
        description=textwrap.dedent(
            """
        Sends a new message within a specific conversation.
        - **For Students:** Sends to their conversation with their mentor.
        - **For Teachers/Trainers:** Sends to a specific conversation with one of their students via `conversation_pk`.

        **Access:** Authenticated Students (for their own conversation), Authenticated Teachers/Trainers (for conversations they are part of).
        """
        ),
        parameters=[
            OpenApiParameter(
                name="conversation_pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=False,  # Only required for teacher/trainer context
                description="The ID of the conversation (Required for Teachers/Trainers).",
            )
        ],
        request=CreateMessageSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=ChatMessageSerializer, description="Message sent successfully."
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Bad Request: Invalid input (e.g., empty message content)."
            ),
            **CHAT_COMMON_ERRORS,
        },
    ),
)
class MessageListCreateView(generics.ListCreateAPIView):
    """
    Handles listing messages for a conversation and creating new messages.
    The conversation is determined by the user's role and URL parameters.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMessageSerializer
        return ChatMessageSerializer

    def _get_student_conversation(self) -> Conversation:
        user_profile: UserProfile = self.request.user.profile
        if user_profile.role != RoleChoices.STUDENT:
            raise DjangoPermissionDenied(_("Access denied for this conversation."))

        mentor_profile = user_profile.assigned_mentor
        if not mentor_profile:
            raise generics.Http404(_("No mentor assigned. Conversation not available."))
        try:
            conversation, _ = Conversation.get_or_create_conversation(
                student_profile=user_profile, teacher_profile=mentor_profile
            )
            return conversation
        except (ValueError, PermissionError, Conversation.DoesNotExist) as e:
            raise generics.Http404(str(e))

    def _get_teacher_conversation(self) -> Conversation:
        user_profile: UserProfile = self.request.user.profile
        if user_profile.role not in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
            raise DjangoPermissionDenied(_("Access denied for this conversation."))

        conversation_pk = self.kwargs.get("conversation_pk")
        if not conversation_pk:
            # This should ideally be caught by URL routing if path param is mandatory
            raise DjangoPermissionDenied(_("Conversation ID not provided."))

        conversation = get_object_or_404(
            Conversation, pk=conversation_pk, teacher=user_profile
        )
        return conversation

    def get_conversation(self) -> Conversation:
        if "conversation_pk" in self.kwargs:
            return self._get_teacher_conversation()
        else:
            return self._get_student_conversation()

    def get_queryset(self):
        conversation = self.get_conversation()
        # Mark messages as read when fetched by the recipient
        with transaction.atomic():
            # Only update messages not sent by the current user that are unread
            Message.objects.filter(conversation=conversation, is_read=False).exclude(
                sender=self.request.user
            ).update(is_read=True)
        return (
            Message.objects.filter(conversation=conversation)
            .select_related("sender__profile")
            .order_by("timestamp")
        )

    def perform_create(self, serializer):
        conversation = self.get_conversation()
        if not (
            self.request.user.profile == conversation.student
            or self.request.user.profile == conversation.teacher
        ):
            raise DjangoPermissionDenied(
                _("You are not a participant in this conversation.")
            )
        serializer.save(sender=self.request.user, conversation=conversation)

    def create(self, request, *args, **kwargs):
        # Use CreateMessageSerializer for validating the request data
        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the conversation (re-using your existing logic)
        conversation = self.get_conversation()
        if not (
            self.request.user.profile == conversation.student
            or self.request.user.profile == conversation.teacher
        ):
            raise DjangoPermissionDenied(
                _("You are not a participant in this conversation.")
            )

        # Save the message instance using validated data from CreateMessageSerializer
        # The perform_create method is not directly called when overriding create, so we replicate its core logic.
        instance = serializer.save(sender=self.request.user, conversation=conversation)

        # Now, serialize the created instance using ChatMessageSerializer for the response
        response_serializer = ChatMessageSerializer(
            instance, context=self.get_serializer_context()
        )
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


@extend_schema_view(
    get=extend_schema(
        tags=["Chat"],
        summary="List Teacher/Trainer's Conversations",
        description=textwrap.dedent(
            """
        Lists all active chat conversations for the authenticated **teacher or trainer**.
        Each conversation represents a chat with one of their assigned students.
        Results are paginated and ordered by the most recently active conversation.

        **Access:** Authenticated Teachers/Trainers only.
        """
        ),
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=ChatConversationSerializer(many=True),
                description="List of conversations retrieved successfully.",
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                description="Forbidden: User is not a teacher or trainer."
            ),
            **CHAT_COMMON_ERRORS,
        },
    )
)
class TeacherConversationListView(generics.ListAPIView):
    """
    Lists all conversations for the authenticated teacher/trainer.
    """

    serializer_class = ChatConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_profile: UserProfile = self.request.user.profile
        if user_profile.role not in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
            raise DjangoPermissionDenied(
                _("Only teachers or trainers can list their conversations.")
            )
        return (
            Conversation.objects.filter(teacher=user_profile)
            .select_related("student__user", "teacher__user")
            .prefetch_related("messages__sender__profile")
            .order_by("-updated_at")
        )


@extend_schema_view(
    post=extend_schema(
        tags=["Chat"],
        summary="Mark Messages in Conversation as Read",
        description=textwrap.dedent(
            """
        Explicitly marks all unread messages (not sent by the current user) within a specific conversation as read.
        This is an alternative to the automatic marking done when messages are listed.

        **Access:** Authenticated users who are participants in the specified conversation.
        """
        ),
        parameters=[
            OpenApiParameter(
                name="conversation_pk",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                required=True,
                description="The ID of the conversation.",
            )
        ],
        request=None,  # No request body needed
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=inline_serializer(
                    name="MarkReadResponse", fields={"detail": serializers.CharField()}
                ),
                description="Messages marked as read successfully.",
                examples=[
                    OpenApiExample(
                        "Success", value={"detail": "3 messages marked as read."}
                    )
                ],
            ),
            **CHAT_COMMON_ERRORS,
        },
    )
)
class MarkMessagesAsReadView(views.APIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def post(self, request, conversation_pk):
        conversation = get_object_or_404(Conversation, pk=conversation_pk)
        # IsConversationParticipant permission checks object-level permission
        self.check_object_permissions(request, conversation)

        updated_count = (
            Message.objects.filter(conversation=conversation, is_read=False)
            .exclude(sender=request.user)
            .update(is_read=True)
        )

        return Response(
            {"detail": _(f"{updated_count} messages marked as read.")},
            status=status.HTTP_200_OK,
        )
