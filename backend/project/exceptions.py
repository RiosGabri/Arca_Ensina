from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code

        if status_code == status.HTTP_400_BAD_REQUEST:
            code = "validation_error"
            message = "Invalid request data."
            details = response.data
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            code = "authentication_error"
            original = response.data.get("detail") if isinstance(response.data, dict) else response.data
            message = str(original) if original else "Authentication credentials were not provided or are invalid."
            details = None
        elif status_code == status.HTTP_403_FORBIDDEN:
            code = "permission_denied"
            original = response.data.get("detail") if isinstance(response.data, dict) else response.data
            message = str(original) if original else "You do not have permission to perform this action."
            details = None
        elif status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
            original = response.data.get("detail") if isinstance(response.data, dict) else response.data
            message = str(original) if original else "The requested resource was not found."
            details = None
        elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = "method_not_allowed"
            original = response.data.get("detail") if isinstance(response.data, dict) else response.data
            message = str(original) if original else "The HTTP method is not allowed for this endpoint."
            details = None
        elif status_code == status.HTTP_429_THROTTLED:
            code = "throttled"
            original = response.data.get("detail") if isinstance(response.data, dict) else response.data
            message = str(original) if original else "Request was throttled. Please try again later."
            details = None
        else:
            code = "error"
            message = str(response.data.get("detail", "An error occurred."))
            details = None

        # If details is just a string, move it to message
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
