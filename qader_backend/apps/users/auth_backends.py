import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

logger = logging.getLogger(__name__)


class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend.

    Allows users to log in using their email address or username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Overrides the default authenticate method to allow login
        with an email address or a username.
        """
        if username is None:
            # The identifier is passed in the 'username' argument by default.
            # If it's missing, we can't authenticate.
            return None

        try:
            # We perform a case-insensitive search on both the username and email fields.
            # This is more user-friendly as users don't have to worry about capitalization.
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )

        except UserModel.DoesNotExist:
            # To mitigate timing attacks, we run the password hashing function on a
            # dummy user if the user is not found. This makes the response time
            # nearly identical whether the user exists or not.
            UserModel().set_password(password)
            return None

        except UserModel.MultipleObjectsReturned:
            # This indicates a data integrity issue, for example, if one user's
            # username is the same as another user's email.
            # We should log this as a critical error and not authenticate either user.
            logger.critical(
                f"Multiple users found for the identifier '{username}'. "
                "This indicates a potential data integrity problem."
            )
            return None

        # If a user is found, check their password and ensure they are active.
        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
