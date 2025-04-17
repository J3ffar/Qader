from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _


import logging

logger = logging.getLogger(__name__)


class IsSubscribed(BasePermission):
    """
    Custom permission to only allow access to users with an active subscription.
    Relies on IsAuthenticated running first or checks authentication itself.
    """

    message = _("An active subscription is required to access this resource.")

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Crucial: Ensure the user is authenticated before checking profile/subscription
        if not request.user or not request.user.is_authenticated:
            return False  # Rely on IsAuthenticated to send 401, but block here too

        # Check for the subscription status on the user's profile.
        try:
            # Access the related profile directly via the user object
            profile = request.user.profile
            # Use the efficient `is_subscribed` property defined in the model
            return profile.is_subscribed
        except AttributeError:
            # This means user is authenticated but has no 'profile' attribute (MAJOR PROBLEM)
            # Or profile exists but has no 'is_subscribed' property.
            logger.error(
                f"AttributeError accessing profile or is_subscribed for authenticated user ID: {request.user.id}. Check profile existence and model property."
            )
            return False
        # Removed UserProfile.DoesNotExist as AttributeError on user.profile handles it
