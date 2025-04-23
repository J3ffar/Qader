from rest_framework.permissions import BasePermission, SAFE_METHODS
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
        if request.user and request.user.is_authenticated and request.user.is_staff:
            return True

        if not request.user or not request.user.is_authenticated:
            return False  # Rely on IsAuthenticated to send 401, but block here too

        # Check for the subscription status on the user's profile.
        try:
            # Access the related profile directly via the user object
            profile = request.user.profile
            if profile:
                return getattr(profile, "is_subscribed", False)
            return False
        except AttributeError:
            # This means user is authenticated but has no 'profile' attribute (MAJOR PROBLEM)
            # Or profile exists but has no 'is_subscribed' property.
            logger.error(
                f"AttributeError accessing profile or is_subscribed for authenticated user ID: {request.user.id}. Check profile existence and model property."
            )
            return False
        # Removed UserProfile.DoesNotExist as AttributeError on user.profile handles it


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to edit it.
    Assumes the model instance has an `author` attribute. Allows read-only otherwise.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of the post or staff users.
        return obj.author == request.user or request.user.is_staff
