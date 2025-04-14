from rest_framework.views import exception_handler
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that flattens nested error structures.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Flatten the error data for ValidationError
        if response.status_code == status.HTTP_400_BAD_REQUEST and hasattr(
            exc, "detail"
        ):
            response.data = flatten_errors(response.data)  # Apply the flattening logic
        else:
            logger.warning(
                f"Exception: {exc}, context: {context}, response: {response.data}"
            )  # Log non-validation errors

    return response


def flatten_errors(data):
    """
    Recursively flattens a nested dictionary of errors into a single-level dictionary.
    """
    flat_errors = {}
    for field, errors in data.items():
        if isinstance(errors, dict):
            # If the value is a dictionary, recursively flatten it, prefixing the keys
            for inner_field, inner_errors in errors.items():
                if isinstance(inner_errors, list):  # Ensure list of errors
                    flat_errors[field] = inner_errors
                else:
                    flat_errors[field] = [
                        str(inner_errors)
                    ]  # Handle non-list error messages
        elif isinstance(errors, list):
            # If the value is already a list, use it directly
            flat_errors[field] = errors
        else:
            # If it's a single error message, convert it to a list
            flat_errors[field] = [str(errors)]  # Ensure all errors are lists
    return flat_errors
