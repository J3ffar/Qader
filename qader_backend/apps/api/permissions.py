from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from ..users.models import UserProfile

import logging  # Use standard logging

logger = logging.getLogger(__name__)


class IsSubscribed(BasePermission):
    """
    Custom permission to only allow access to users with an active subscription.

    Assumes:
    - User is authenticated (should be checked before this permission).
    - A related UserProfile model exists via `request.user.profile`.
    - The UserProfile model has an `is_subscribed` property or method.
    """

    message = _("An active subscription is required to access this resource.")

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check for the subscription status on the user's profile.
        try:
            # Access the related profile directly
            profile = request.user.profile
            # Use the efficient `is_subscribed` property defined in the model
            return profile.is_subscribed
        except UserProfile.DoesNotExist:
            # This indicates a data integrity issue - a logged-in user should have a profile.
            logger.error(
                f"UserProfile.DoesNotExist for authenticated user ID: {request.user.id}"
            )
            return False
        except AttributeError:
            # This would mean `is_subscribed` is not defined on the profile model.
            logger.error(
                f"AttributeError: UserProfile for user ID {request.user.id} is missing 'is_subscribed' property."
            )
            return False


# --- Example Usage in a View ---
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from .permissions import IsSubscribed
#
# class PremiumFeatureView(APIView):
#     """
#     An example view that requires both authentication and an active subscription.
#     """
#     permission_classes = [IsAuthenticated, IsSubscribed] # Order matters
#
#     def get(self, request):
#         content = {"message": "Welcome to the premium feature!"}
#         return Response(content)
