"""
Pydantic models for API request/response handling.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SafetyLevelEnum(str, Enum):
    """Safety levels for configuration."""

    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


# Request Models


class ValidateRequest(BaseModel):
    """Request model for input validation."""

    text: str = Field(..., description="Text to validate", min_length=1, max_length=10000)
    user_id: Optional[str] = Field(None, description="Optional user identifier for rate limiting")
    safety_level: Optional[SafetyLevelEnum] = Field(
        SafetyLevelEnum.MODERATE, description="Safety level to use for validation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Tell me about machine learning",
                "user_id": "user_123",
                "safety_level": "moderate",
            }
        }


class MonitorRequest(BaseModel):
    """Request model for output monitoring."""

    response: str = Field(..., description="LLM response to monitor", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {"response": "Machine learning is a subset of artificial intelligence."}
        }


class ProcessRequest(BaseModel):
    """Request model for full interaction processing."""

    user_input: str = Field(..., description="User input text", min_length=1)
    llm_response: str = Field(..., description="LLM response text", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "user_input": "What is machine learning?",
                "llm_response": "Machine learning is a subset of AI.",
                "user_id": "user_123",
            }
        }


# Response Models


class SafetyScoreResponse(BaseModel):
    """Safety score details in response."""

    violence_score: float = Field(..., description="Violence content score (0-1)")
    hate_speech_score: float = Field(..., description="Hate speech score (0-1)")
    bias_score: float = Field(..., description="Bias score (0-1)")
    privacy_score: float = Field(..., description="Privacy violation score (0-1)")
    factual_score: float = Field(..., description="Factual accuracy concern score (0-1)")
    overall_score: float = Field(..., description="Overall safety score (0-1)")
    confidence: float = Field(..., description="Confidence in the assessment")
    safety_level: str = Field(..., description="Safety level classification")
    flagged_keywords: List[str] = Field(
        default_factory=list, description="Keywords that triggered flags"
    )
    reasoning: str = Field(..., description="Reasoning for the safety assessment")


class ValidateResponse(BaseModel):
    """Response model for input validation."""

    is_valid: bool = Field(..., description="Whether input passed basic validation")
    is_safe: bool = Field(..., description="Whether input is considered safe")
    should_proceed: bool = Field(..., description="Whether to proceed with the request")
    original_text: str = Field(..., description="Original input text")
    sanitized_text: str = Field(..., description="Sanitized input text")
    safety_score: SafetyScoreResponse = Field(..., description="Detailed safety scores")
    validation_errors: List[str] = Field(
        default_factory=list, description="Validation error messages"
    )
    rate_limit_exceeded: bool = Field(..., description="Whether rate limit was exceeded")
    filters_applied: List[str] = Field(
        default_factory=list, description="Filters that were applied"
    )
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class MonitorResponse(BaseModel):
    """Response model for output monitoring."""

    content_id: str = Field(..., description="Unique identifier for this content check")
    is_safe: bool = Field(..., description="Whether output is considered safe")
    safety_score: SafetyScoreResponse = Field(..., description="Detailed safety scores")
    filters_applied: List[str] = Field(
        default_factory=list, description="Filters that were applied"
    )
    recommendations: List[str] = Field(default_factory=list, description="Safety recommendations")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class ProcessResponse(BaseModel):
    """Response model for full interaction processing."""

    input_valid: bool = Field(..., description="Whether input passed validation")
    input_safe: bool = Field(..., description="Whether input is considered safe")
    output_safe: bool = Field(..., description="Whether output is considered safe")
    should_proceed: bool = Field(..., description="Whether to proceed with the interaction")
    error_message: Optional[str] = Field(None, description="Error message if any")
    input_safety_score: Optional[SafetyScoreResponse] = Field(
        None, description="Input safety scores"
    )
    output_safety_score: Optional[SafetyScoreResponse] = Field(
        None, description="Output safety scores"
    )


class StatsResponse(BaseModel):
    """Response model for safety statistics."""

    content_filter_stats: Dict[str, Any] = Field(..., description="Content filter statistics")
    prompt_injection_stats: Dict[str, Any] = Field(
        ..., description="Prompt injection detector stats"
    )
    rate_limiter_stats: Dict[str, Any] = Field(..., description="Rate limiter statistics")
    config: Dict[str, Any] = Field(..., description="Current configuration")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    components: Dict[str, str] = Field(..., description="Component health status")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
