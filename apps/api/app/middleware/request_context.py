"""Request-context middleware: request_id, timing and structured request log.

Binds the required observability fields into structlog contextvars so every log
emitted during the request carries them, and emits one `request_completed` log
with `status_code` + `duration_ms`. Echoes `X-Request-ID` on the response.

Required log fields (config.json > observability.required_log_fields):
    request_id, user_id, endpoint, method, status_code, duration_ms

No PII is bound or logged.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger("request")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind request_id + timing context and log request completion."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        endpoint = request.url.path
        method = request.method

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=None,  # populated by auth in Phase 2; present as None now
            endpoint=endpoint,
            method=method,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            logger.error(
                "request_failed",
                status_code=500,
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        structlog.contextvars.clear_contextvars()
        return response
