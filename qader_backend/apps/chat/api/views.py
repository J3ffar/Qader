from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import transaction

from apps.users.models import UserProfile, RoleChoices
from ..models import Conversation, Message
from .serializers import (
    ChatConversationSerializer,
    ChatMessageSerializer,
    CreateMessageSerializer,
)
from .permissions import IsConversationParticipant


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
            raise DjangoPermissionDenied("Only students can access this view.")

        mentor_profile = user_profile.assigned_mentor
        if not mentor_profile:
            raise generics.Http404("No mentor assigned. Conversation not available.")

        try:
            # Use the robust get_or_create_conversation method
            conversation, created = Conversation.get_or_create_conversation(
                student_profile=user_profile, teacher_profile=mentor_profile
            )
            return conversation
        except (ValueError, PermissionError, Conversation.DoesNotExist) as e:
            # Log this error
            print(
                f"Error in StudentConversationView: {e}"
            )  # Replace with proper logging
            raise generics.Http404(str(e))


class MessageListCreateView(generics.ListCreateAPIView):
    """
    Handles listing messages for a conversation and creating new messages.
    The conversation is determined by the user's role and URL parameters.
    """

    permission_classes = [
        IsAuthenticated
    ]  # Specific object permissions handled in get_conversation

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMessageSerializer
        return ChatMessageSerializer

    def _get_student_conversation(self) -> Conversation:
        user_profile: UserProfile = self.request.user.profile
        if user_profile.role != RoleChoices.STUDENT:
            raise DjangoPermissionDenied("Access denied for this conversation.")

        mentor_profile = user_profile.assigned_mentor
        if not mentor_profile:
            raise generics.Http404("No mentor assigned. Conversation not available.")
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
            raise DjangoPermissionDenied("Access denied for this conversation.")

        conversation_pk = self.kwargs.get("conversation_pk")
        if not conversation_pk:
            raise DjangoPermissionDenied("Conversation ID not provided.")

        conversation = get_object_or_404(
            Conversation, pk=conversation_pk, teacher=user_profile
        )
        return conversation

    def get_conversation(self) -> Conversation:
        # Determine if student or teacher context
        if "conversation_pk" in self.kwargs:  # Teacher accessing specific conversation
            return self._get_teacher_conversation()
        else:  # Student accessing their 'my-conversation'
            return self._get_student_conversation()

    def get_queryset(self):
        conversation = self.get_conversation()
        # Mark messages as read when fetched (basic approach)
        with transaction.atomic():
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
        # Ensure sender is part of this conversation (double check, model clean also does this)
        if not (
            self.request.user.profile == conversation.student
            or self.request.user.profile == conversation.teacher
        ):
            raise DjangoPermissionDenied(
                "You are not a participant in this conversation."
            )

        serializer.save(sender=self.request.user, conversation=conversation)
        # Mark this message as read by the sender implicitly
        # No, this is wrong. is_read is for the *recipient*.
        # The unread_message_count should handle this.


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
                "Only teachers or trainers can list their conversations."
            )
        return (
            Conversation.objects.filter(teacher=user_profile)
            .select_related(
                "student__user",
                "teacher__user",  # For student_profile and teacher_profile serializers
            )
            .prefetch_related(
                "messages__sender__profile"  # For last_message and unread_count efficiency
            )
            .order_by("-updated_at")
        )


# Optional: View to mark messages as read explicitly if needed beyond simple fetch
class MarkMessagesAsReadView(views.APIView):
    permission_classes = [IsAuthenticated, IsConversationParticipant]

    def post(self, request, conversation_pk):
        conversation = get_object_or_404(Conversation, pk=conversation_pk)
        self.check_object_permissions(
            request, conversation
        )  # IsConversationParticipant handles this

        updated_count = (
            Message.objects.filter(conversation=conversation, is_read=False)
            .exclude(sender=request.user)
            .update(is_read=True)
        )

        return Response(
            {"detail": f"{updated_count} messages marked as read."},
            status=status.HTTP_200_OK,
        )
