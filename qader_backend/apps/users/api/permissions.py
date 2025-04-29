from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from typing import Any


class IsCurrentlySubscribed(permissions.BasePermission):
    """
    Custom permission to only allow users with an active subscription.
    Assumes user is already authenticated.
    """

    message = _("You must have an active subscription to perform this action.")

    def has_permission(self, request: Request, view: APIView) -> bool:
        # relies on IsAuthenticated running first
        if not request.user or not request.user.is_authenticated:
            return False

        # Check if the user has a profile and the profile indicates subscription
        try:
            # Access the profile safely
            profile = request.user.profile
            return profile.is_subscribed
        except AttributeError:
            # Handle cases where profile might not exist (though signal should prevent this)
            # Or if profile doesn't have is_subscribed (shouldn't happen)
            return False
        except Exception:
            # Catch any other unexpected errors during profile access
            return False
