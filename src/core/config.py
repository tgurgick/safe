"""
Safety Layer Configuration

Defines configuration options for the safety layer.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SafetyLevel(str, Enum):
    """Safety levels for content filtering."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class SafetyConfig(BaseModel):
    """Configuration for the safety layer."""
    
    # Safety level
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.MODERATE,
        description="Safety level for content filtering"
    )
    
    # Content filters
    content_filters: List[str] = Field(
        default=["violence", "hate_speech", "illegal_activities"],
        description="List of content filter types to apply"
    )
    
    # Feature flags
    enable_content_filtering: bool = Field(
        default=True,
        description="Enable content filtering"
    )
    enable_bias_detection: bool = Field(
        default=True,
        description="Enable bias detection"
    )
    enable_fact_checking: bool = Field(
        default=False,
        description="Enable fact checking (requires external APIs)"
    )
    enable_privacy_protection: bool = Field(
        default=True,
        description="Enable privacy protection"
    )
    
    # Input validation
    max_input_length: int = Field(
        default=1000,
        description="Maximum allowed input length"
    )
    rate_limit_per_minute: int = Field(
        default=10,
        description="Rate limit per minute per user"
    )
    
    # Safety thresholds
    violence_threshold: float = Field(
        default=0.7,
        description="Threshold for violence detection (0-1)"
    )
    hate_speech_threshold: float = Field(
        default=0.6,
        description="Threshold for hate speech detection (0-1)"
    )
    bias_threshold: float = Field(
        default=0.5,
        description="Threshold for bias detection (0-1)"
    )
    
    # Model settings
    use_ml_models: bool = Field(
        default=False,
        description="Use ML models for content classification"
    )
    cache_results: bool = Field(
        default=True,
        description="Cache safety check results"
    )
    
    # Monitoring
    enable_monitoring: bool = Field(
        default=True,
        description="Enable monitoring and metrics"
    )
    log_safety_decisions: bool = Field(
        default=True,
        description="Log all safety decisions"
    )
    
    # Custom rules
    custom_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Custom safety rules"
    )
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


def get_default_config() -> SafetyConfig:
    """Get default configuration."""
    return SafetyConfig()


def get_strict_config() -> SafetyConfig:
    """Get strict safety configuration."""
    return SafetyConfig(
        safety_level=SafetyLevel.STRICT,
        violence_threshold=0.5,
        hate_speech_threshold=0.4,
        bias_threshold=0.3,
        rate_limit_per_minute=5
    )


def get_lenient_config() -> SafetyConfig:
    """Get lenient safety configuration."""
    return SafetyConfig(
        safety_level=SafetyLevel.LENIENT,
        violence_threshold=0.8,
        hate_speech_threshold=0.7,
        bias_threshold=0.6,
        rate_limit_per_minute=20
    ) 