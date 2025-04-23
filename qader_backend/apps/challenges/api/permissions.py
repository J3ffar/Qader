from rest_framework import permissions
from ..models import Challenge, ChallengeAttempt, ChallengeStatus


class IsParticipant(permissions.BasePermission):
    """
    Allows access only to participants (challenger or opponent) of the challenge.
    """

    message = "You are not a participant in this challenge."

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Challenge):
            return obj.is_participant(request.user)
        elif isinstance(obj, ChallengeAttempt):
            return obj.user == request.user
        return False  # Should not happen if used correctly


class IsInvitedOpponent(permissions.BasePermission):
    """
    Allows access only to the opponent of a challenge invitation that is pending.
    """

    message = "You are not the invited opponent or the challenge is not pending."

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Challenge):
            return (
                obj.opponent == request.user
                and obj.status == ChallengeStatus.PENDING_INVITE
            )
        return False


class IsChallengeOwner(permissions.BasePermission):
    """
    Allows access only to the challenger (owner) of the challenge,
    e.g., for cancelling before acceptance.
    """

    message = "Only the challenger can perform this action."

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Challenge):
            return obj.challenger == request.user
        return False
