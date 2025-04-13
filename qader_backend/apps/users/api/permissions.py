from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView
from django.utils import timezone
from ..models import UserProfile  # Adjust import if needed


class IsSubscribed(BasePermission):
    """
    Allows access only to authenticated users with an active subscription.
    Assumes a related UserProfile model exists with an 'is_subscribed' property or method.
    """

    message = "User does not have an active subscription."

    def has_permission(self, request: Request, view: APIView) -> bool:
        # First, ensure the user is authenticated at all.
        if not request.user or not request.user.is_authenticated:
            return False

        # Then, check for the subscription status on their profile.
        try:
            profile = request.user.profile
            # Rely on the is_subscribed property in the UserProfile model
            return profile.is_subscribed
        except UserProfile.DoesNotExist:
            # Handle cases where profile might not exist (data integrity issue)
            return False
        except AttributeError:
            # Handle cases where 'is_subscribed' is not defined on the profile
            # (should not happen with the current model definition)
            # You might want to log this error.
            print(
                f"Error: User {request.user.id} profile missing 'is_subscribed' property."
            )  # Use proper logging
            return False


# Example Usage (in a view):
# from rest_framework.permissions import IsAuthenticated
# from .permissions import IsSubscribed
#
# class SubscriberOnlyView(APIView):
#     permission_classes = [IsAuthenticated, IsSubscribed]
#
#     def get(self, request):
#         # ... view logic for subscribed users ...
#         return Response(...)
