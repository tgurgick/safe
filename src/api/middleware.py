"""
Middleware components for the FastAPI application.
"""

import time
import uuid
import logging
from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())[:8]

        # Record start time
        start_time = time.time()

        # Log request
        logger.info(f"[{request_id}] {request.method} {request.url.path} - Started")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Completed {response.status_code} in {duration_ms:.2f}ms"
        )

        # Add request ID header
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"

        return response


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware for API key authentication."""

    def __init__(self, app, api_keys: Optional[set] = None, exclude_paths: Optional[set] = None):
        super().__init__(app)
        self.api_keys = api_keys or set()
        self.exclude_paths = exclude_paths or {"/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Skip if no API keys configured (disabled)
        if not self.api_keys:
            return await call_next(request)

        # Check for API key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return Response(
                content='{"error": "Missing API key", "message": "X-API-Key header is required"}',
                status_code=401,
                media_type="application/json",
            )

        if api_key not in self.api_keys:
            return Response(
                content='{"error": "Invalid API key", "message": "The provided API key is not valid"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


class CORSMiddleware(BaseHTTPMiddleware):
    """Simple CORS middleware for development."""

    def __init__(
        self,
        app,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response(status_code=200)
        else:
            response = await call_next(request)

        # Add CORS headers
        origin = request.headers.get("origin", "*")
        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
        response.headers["Access-Control-Max-Age"] = "600"

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled error: {str(e)}")
            return Response(
                content=f'{{"error": "Internal server error", "message": "{str(e)}"}}',
                status_code=500,
                media_type="application/json",
            )
