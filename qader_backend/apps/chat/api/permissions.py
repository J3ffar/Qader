from rest_framework.permissions import BasePermission
from ..models import Conversation


class IsConversationParticipant(BasePermission):
    """
    Allows access only to users who are participants in the conversation object.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Conversation):
            return (
                request.user.profile == obj.student
                or request.user.profile == obj.teacher
            )
        # For messages, check participation in obj.conversation
        if hasattr(obj, "conversation"):  # Assuming obj is a Message instance
            return (
                request.user.profile == obj.conversation.student
                or request.user.profile == obj.conversation.teacher
            )
        return False
