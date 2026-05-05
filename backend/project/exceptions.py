from rest_framework import status
from rest_framework.views import exception_handler

DEFAULT_MESSAGES = {
    status.HTTP_401_UNAUTHORIZED: (
        "authentication_error",
        "Authentication credentials were not provided or are invalid.",
    ),
    status.HTTP_403_FORBIDDEN: (
        "permission_denied",
        "You do not have permission to perform this action.",
    ),
    status.HTTP_404_NOT_FOUND: (
        "not_found",
        "The requested resource was not found.",
    ),
    status.HTTP_405_METHOD_NOT_ALLOWED: (
        "method_not_allowed",
        "The HTTP method is not allowed for this endpoint.",
    ),
    status.HTTP_429_TOO_MANY_REQUESTS: (
        "throttled",
        "Request was throttled. Please try again later.",
    ),
}


def _extract_detail(data):
    if isinstance(data, dict):
        return data.get("detail")
    return data


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code

        if status_code == status.HTTP_400_BAD_REQUEST:
            code = "validation_error"
            message = "Invalid request data."
            details = response.data
        elif status_code in DEFAULT_MESSAGES:
            code, default_msg = DEFAULT_MESSAGES[status_code]
            original = _extract_detail(response.data)
            message = str(original) if original else default_msg
            details = None
        else:
            code = "error"
            message = str(response.data.get("detail", "An error occurred."))
            details = None

        if isinstance(details, str):
            message = details
            details = None

        response.data = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        }

        if details is not None:
            response.data["error"]["details"] = details

    if response is None:
        from rest_framework.response import Response as DRFResponse

        return DRFResponse(
            {
                "success": False,
                "error": {
                    "code": "server_error",
                    "message": "Internal server error.",
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
