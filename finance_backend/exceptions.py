from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    # wraps all errors into a consistent shape so frontend always knows what to expect
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            "success": False,
            "error": {
                "code": _get_error_code(response.status_code),
                "message": _extract_message(response.data),
                "details": response.data if isinstance(response.data, dict) else None,
            }
        }
        response.data = error_data

    return response


def _get_error_code(status_code):
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
    }
    return codes.get(status_code, "ERROR")


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # pick first field error if there are multiple
        for key, value in data.items():
            if isinstance(value, list) and value:
                return f"{key}: {value[0]}"
            return str(value)
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
