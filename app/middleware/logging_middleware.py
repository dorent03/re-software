"""Request/response logging middleware."""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs each incoming request and its response status + duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "%s %s -> %s (%sms)",
            method,
            path,
            response.status_code,
            duration_ms,
        )
        return response
