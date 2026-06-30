"""Application error hierarchy + global handler (RFC-7807-like envelope).

Error responses follow `{ "error": { "code", "message", "request_id" } }`,
consistent across the whole API for downstream frontends to consume.
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class AppError(Exception):
    """Base application error with an HTTP status, machine code and message."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.message = message or self.__class__.__name__
        if code is not None:
            self.code = code
        # Optional response headers (e.g. Retry-After on 429 — set by subclasses).
        self.headers: dict[str, str] = {}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "service_unavailable"


def _error_payload(code: str, message: str, request_id: str | None) -> dict[str, object]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Render an AppError as the standard error envelope."""
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    log = logger.warning if exc.status_code < 500 else logger.error
    log("app_error", code=exc.code, status_code=exc.status_code, message=exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.message, request_id),
        headers=getattr(exc, "headers", None) or None,
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log Pydantic validation errors (422) so we can debug which field fails."""
    from fastapi.exceptions import RequestValidationError
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    errors = exc.errors() if isinstance(exc, RequestValidationError) else str(exc)  # type: ignore[union-attr]
    logger.warning("request_validation_error", errors=errors, path=request.url.path)
    return JSONResponse(
        status_code=422,
        content=_error_payload("validation_error", str(errors), request_id),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register the global AppError handler on the app."""
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
