"""
API route handlers for the LLM Safety Layer.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional

from .models import (
    ValidateRequest,
    ValidateResponse,
    MonitorRequest,
    MonitorResponse,
    ProcessRequest,
    ProcessResponse,
    StatsResponse,
    HealthResponse,
    SafetyScoreResponse,
    SafetyLevelEnum,
)
from ..core.safety_layer import SafetyLayer
from ..core.config import SafetyConfig, get_strict_config, get_lenient_config


# Create router
router = APIRouter()

# Global safety layer instance (will be set during app creation)
_safety_layer: Optional[SafetyLayer] = None


def get_safety_layer() -> SafetyLayer:
    """Dependency to get the safety layer instance."""
    if _safety_layer is None:
        raise HTTPException(status_code=500, detail="Safety layer not initialized")
    return _safety_layer


def set_safety_layer(safety_layer: SafetyLayer) -> None:
    """Set the global safety layer instance."""
    global _safety_layer
    _safety_layer = safety_layer


def _safety_score_to_response(score) -> SafetyScoreResponse:
    """Convert internal SafetyScore to API response model."""
    return SafetyScoreResponse(
        violence_score=score.violence_score,
        hate_speech_score=score.hate_speech_score,
        bias_score=score.bias_score,
        privacy_score=score.privacy_score,
        factual_score=score.factual_score,
        overall_score=score.overall_score,
        confidence=score.confidence,
        safety_level=(
            score.safety_level.value
            if hasattr(score.safety_level, "value")
            else str(score.safety_level)
        ),
        flagged_keywords=score.flagged_keywords,
        reasoning=score.reasoning,
    )


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate user input",
    description="Validates user input for safety concerns before sending to an LLM.",
    tags=["Safety"],
)
async def validate_input(
    request: ValidateRequest,
    safety_layer: SafetyLayer = Depends(get_safety_layer),
) -> ValidateResponse:
    """
    Validate user input for safety concerns.

    This endpoint performs multiple safety checks including:
    - Content filtering (violence, hate speech, bias)
    - Prompt injection detection
    - Privacy protection (PII detection)
    - Rate limiting (if user_id provided)
    """
    try:
        result = safety_layer.validate_input(
            text=request.text,
            user_id=request.user_id or "anonymous",
        )

        return ValidateResponse(
            is_valid=result.is_valid,
            is_safe=result.is_safe,
            should_proceed=result.should_proceed(),
            original_text=result.original_text,
            sanitized_text=result.sanitized_text,
            safety_score=_safety_score_to_response(result.safety_score),
            validation_errors=result.validation_errors,
            rate_limit_exceeded=result.rate_limit_exceeded,
            filters_applied=result.filters_applied,
            processing_time_ms=result.processing_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/monitor",
    response_model=MonitorResponse,
    summary="Monitor LLM output",
    description="Monitors LLM output for safety concerns before returning to user.",
    tags=["Safety"],
)
async def monitor_output(
    request: MonitorRequest,
    safety_layer: SafetyLayer = Depends(get_safety_layer),
) -> MonitorResponse:
    """
    Monitor LLM output for safety concerns.

    This endpoint analyzes LLM responses to ensure they don't contain:
    - Violent or harmful content
    - Hate speech or discriminatory language
    - Privacy violations (leaked PII)
    - Factually inaccurate information
    """
    try:
        report = safety_layer.monitor_output(request.response)

        return MonitorResponse(
            content_id=report.content_id,
            is_safe=report.is_safe,
            safety_score=_safety_score_to_response(report.safety_score),
            filters_applied=report.filters_applied,
            recommendations=report.recommendations,
            processing_time_ms=report.processing_time_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/process",
    response_model=ProcessResponse,
    summary="Process full interaction",
    description="Processes a complete user-LLM interaction, validating both input and output.",
    tags=["Safety"],
)
async def process_interaction(
    request: ProcessRequest,
    safety_layer: SafetyLayer = Depends(get_safety_layer),
) -> ProcessResponse:
    """
    Process a complete user-LLM interaction.

    This endpoint validates both the user input and the LLM response,
    providing a comprehensive safety assessment of the entire interaction.
    """
    try:
        result = safety_layer.process_interaction(
            user_input=request.user_input,
            llm_response=request.llm_response,
            user_id=request.user_id or "anonymous",
        )

        input_score = None
        output_score = None

        if result.get("input_validation"):
            input_score = _safety_score_to_response(result["input_validation"].safety_score)

        if result.get("output_report"):
            output_score = _safety_score_to_response(result["output_report"].safety_score)

        return ProcessResponse(
            input_valid=result.get("input_valid", False),
            input_safe=result.get("input_safe", False),
            output_safe=result.get("output_safe", False),
            should_proceed=result.get("should_proceed", False),
            error_message=result.get("error_message"),
            input_safety_score=input_score,
            output_safety_score=output_score,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get safety statistics",
    description="Returns statistics about safety checks performed.",
    tags=["Monitoring"],
)
async def get_stats(
    safety_layer: SafetyLayer = Depends(get_safety_layer),
) -> StatsResponse:
    """
    Get safety statistics.

    Returns aggregated statistics about:
    - Content filter hits (violence, hate speech, bias, privacy)
    - Prompt injection attempts detected
    - Rate limiting statistics
    - Current configuration
    """
    try:
        stats = safety_layer.get_safety_stats()

        return StatsResponse(
            content_filter_stats=stats.get("content_filter_stats", {}),
            prompt_injection_stats=stats.get("prompt_injection_stats", {}),
            rate_limiter_stats=stats.get("rate_limiter_stats", {}),
            config=stats.get("config", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the health status of the API.",
    tags=["System"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the health status of all API components.
    Used for monitoring and load balancer health checks.
    """
    components = {
        "api": "healthy",
        "safety_layer": "healthy" if _safety_layer is not None else "not_initialized",
    }

    overall_status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="0.1.0",
        components=components,
    )
