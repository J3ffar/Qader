from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def flatten_errors(data):
    """
    Flattens DRF error data (dict, list, or string) into a standardized
    single-level dictionary format, typically using 'detail' for non-field errors.
    """
    flat_errors = {}

    if isinstance(data, dict):
        # Handle dictionary errors (usually field-specific)
        for field, errors in data.items():
            # Ensure errors is always a list for processing
            error_list = errors if isinstance(errors, list) else [errors]
            # Take the first error message for simplicity or join them
            # Use str() to handle potential ErrorDetail objects
            flat_errors[field] = str(error_list[0])
            # Example alternative: Join all messages
            # flat_errors[field] = ' '.join(map(str, error_list))

    elif isinstance(data, list):
        # Handle list of errors (often non_field_errors or direct raises)
        # Combine them into a single 'detail' key
        # Use str() to handle potential ErrorDetail objects
        flat_errors["detail"] = " ".join(map(str, data))

    elif data:
        # Handle single string error (wrap it in 'detail')
        flat_errors["detail"] = str(data)

    else:
        # Handle empty or unexpected data
        flat_errors["detail"] = "An unknown error occurred."

    return flat_errors


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    - Calls the default handler first.
    - Flattens validation errors (400) into a simpler structure.
    - Logs other types of errors.
    - Ensures a consistent error response format.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None:
        # Check if it's a standard APIException (like ValidationError, PermissionDenied, etc.)
        # And if the data needs flattening (typically for 400 Bad Request / Validation Errors)
        if isinstance(exc, APIException) and hasattr(response, "data"):
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                # Flatten specifically for validation errors
                response.data = flatten_errors(response.data)
            # Optionally, you could simplify other error responses too:
            # elif 'detail' in response.data:
            #      # If detail exists, ensure it's the primary message
            #      response.data = {'detail': str(response.data['detail'])}
            else:
                # For other API exceptions (401, 403, 404), ensure a 'detail' key exists
                if "detail" not in response.data:
                    # Attempt to create a detail message from the data
                    response.data = {"detail": str(response.data)}
                else:
                    # Ensure the existing detail is a string
                    response.data["detail"] = str(response.data["detail"])

        # If it's not an APIException handled by DRF, but still resulted in a response
        elif hasattr(response, "data"):
            logger.warning(
                f"Non-APIException resulted in response. Exc: {exc}, Status: {response.status_code}, Data: {response.data}"
            )
            # Ensure a basic structure
            response.data = flatten_errors(response.data)

    # If response is None (DRF didn't handle it, likely a server error)
    elif isinstance(exc, Exception):  # Catch broader Python exceptions
        logger.exception(
            f"Unhandled exception occurred: {exc}", exc_info=True
        )  # Log the full traceback
        response = Response(
            {"detail": "A server error occurred. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
