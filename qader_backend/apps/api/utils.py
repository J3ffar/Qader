# qader_backend/apps/api/utils.py
import logging
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def get_user_from_context(context):
    """
    Safely retrieves the authenticated user from the serializer context.
    Raises PermissionDenied if user is not found or not authenticated.
    """
    request = context.get("request")
    if request and hasattr(request, "user") and request.user.is_authenticated:
        return request.user
    logger.error("Authenticated user could not be retrieved from serializer context.")
    raise PermissionDenied(
        _("User not found or not authenticated in serializer context.")
    )
