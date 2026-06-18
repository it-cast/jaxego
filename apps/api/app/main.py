"""Application entrypoint — `create_app()` factory.

The factory wires logging, conditional Sentry, the request-context middleware,
the global error handler, the versioned `/v1` router and the root `/health`
probe. It contains no business logic.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.observability import init_sentry
from app.middleware.request_context import RequestContextMiddleware


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    configure_logging()
    init_sentry()  # no-op when SENTRY_DSN is absent

    app = FastAPI(
        title="Jaxego API",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    # Health/readiness probe at the root (Docker/Nginx/k8s convention).
    app.include_router(health.router)
    # Versioned domain endpoints under /v1 (DRV-003).
    app.include_router(api_router, prefix="/v1")

    # Upload proxy — frontend uploads here, API forwards to storage (B2 or stub).
    from app.dev_upload import router as upload_router
    app.include_router(upload_router, prefix="/v1")

    return app


app = create_app()
