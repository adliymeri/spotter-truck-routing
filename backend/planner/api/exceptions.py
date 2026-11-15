import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from planner.ports import ProviderError

logger = logging.getLogger(__name__)


def api_exception_handler(exc, context):
    """Validation errors keep DRF's handling; provider and unexpected errors become JSON and are logged."""
    response = exception_handler(exc, context)
    if response is not None:
        return response

    request = context.get("request")
    path = request.path if request else "unknown"

    if isinstance(exc, ProviderError):
        logger.warning("External provider failed on %s: %s", path, exc)
        return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

    logger.error("Unhandled error on %s", path, exc_info=exc)
    return Response({"detail": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
