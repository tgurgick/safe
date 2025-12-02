"""
FastAPI application factory for the LLM Safety Layer.
"""

import logging
from typing import Optional, Set
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router, set_safety_layer
from .middleware import RequestLoggingMiddleware, APIKeyMiddleware, ErrorHandlingMiddleware
from .metrics import metrics_router, MetricsMiddleware
from ..core.safety_layer import SafetyLayer
from ..core.config import SafetyConfig, get_default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(
    config: Optional[SafetyConfig] = None,
    api_keys: Optional[Set[str]] = None,
    enable_cors: bool = True,
    enable_metrics: bool = True,
    debug: bool = False,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        config: Safety layer configuration. Uses default if not provided.
        api_keys: Set of valid API keys for authentication. Disabled if empty/None.
        enable_cors: Whether to enable CORS middleware.
        debug: Whether to enable debug mode.

    Returns:
        Configured FastAPI application.
    """
    # Create FastAPI app
    app = FastAPI(
        title="LLM Safety Layer API",
        description="""
## Educational LLM Safety Layer API

This API provides safety validation and monitoring for LLM interactions.

### Features
- **Input Validation**: Validate user inputs for safety concerns before sending to LLMs
- **Output Monitoring**: Monitor LLM responses for unsafe content
- **Full Interaction Processing**: Validate complete user-LLM interactions
- **Statistics**: Track safety metrics and filter performance

### Safety Dimensions
- Violence detection
- Hate speech detection
- Bias detection
- Privacy protection (PII)
- Prompt injection detection

### Educational Purpose
This API is designed for educational purposes to demonstrate AI safety concepts.
It is intentionally lenient and not suitable for production use.
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=debug,
    )

    # Initialize safety layer
    safety_config = config or get_default_config()
    safety_layer = SafetyLayer(safety_config)
    set_safety_layer(safety_layer)
    logger.info("Safety layer initialized")

    # Add middleware (order matters - last added runs first)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    if api_keys:
        app.add_middleware(
            APIKeyMiddleware,
            api_keys=api_keys,
            exclude_paths={"/health", "/docs", "/openapi.json", "/redoc"},
        )
        logger.info(f"API key authentication enabled with {len(api_keys)} keys")

    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS enabled")

    # Include routes
    app.include_router(router, prefix="/api/v1")

    # Include metrics
    if enable_metrics:
        app.include_router(metrics_router, prefix="/api/v1")
        app.add_middleware(MetricsMiddleware)
        logger.info("Prometheus metrics enabled at /api/v1/metrics")

    # Root endpoint
    @app.get("/", tags=["System"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "LLM Safety Layer API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/v1/health",
            "metrics": "/api/v1/metrics" if enable_metrics else None,
        }

    logger.info("Application created successfully")
    return app


# Default application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
