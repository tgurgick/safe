"""
Validation Result Model

Represents the result of input validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from .safety_score import SafetyScore


class ValidationResult(BaseModel):
    """Result of input validation."""
    
    # Basic validation
    is_valid: bool = Field(
        default=True,
        description="Whether the input passed basic validation"
    )
    is_safe: bool = Field(
        default=True,
        description="Whether the input is safe for processing"
    )
    
    # Input details
    original_text: str = Field(
        default="",
        description="Original input text"
    )
    sanitized_text: str = Field(
        default="",
        description="Sanitized input text"
    )
    
    # Validation details
    validation_errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    safety_score: SafetyScore = Field(
        description="Safety assessment of the input"
    )
    
    # Rate limiting
    rate_limit_exceeded: bool = Field(
        default=False,
        description="Whether rate limit was exceeded"
    )
    rate_limit_reset_time: Optional[int] = Field(
        default=None,
        description="Time until rate limit resets (seconds)"
    )
    
    # Processing metadata
    processing_time_ms: float = Field(
        default=0.0,
        description="Time taken to validate input (milliseconds)"
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="List of validation filters applied"
    )
    
    def get_primary_error(self) -> Optional[str]:
        """Get the primary validation error."""
        if not self.is_valid and self.validation_errors:
            return self.validation_errors[0]
        return None
    
    def get_safety_concern(self) -> Optional[str]:
        """Get the primary safety concern."""
        if not self.is_safe:
            return self.safety_score.get_highest_risk_dimension()
        return None
    
    def should_proceed(self) -> bool:
        """Determine if processing should proceed."""
        return self.is_valid and self.is_safe and not self.rate_limit_exceeded
    
    def get_error_message(self) -> str:
        """Get a user-friendly error message."""
        if self.rate_limit_exceeded:
            return f"Rate limit exceeded. Please wait {self.rate_limit_reset_time} seconds."
        
        if not self.is_valid:
            return f"Invalid input: {self.get_primary_error()}"
        
        if not self.is_safe:
            concern = self.get_safety_concern()
            return f"Input contains unsafe content: {concern}"
        
        return "Input is valid and safe"
    
    @classmethod
    def create_valid_result(cls, text: str, sanitized: str = "", processing_time: float = 0.0) -> 'ValidationResult':
        """Create a valid validation result."""
        from .safety_score import SafetyScore
        
        return cls(
            is_valid=True,
            is_safe=True,
            original_text=text,
            sanitized_text=sanitized or text,
            safety_score=SafetyScore.create_safe_score(),
            processing_time_ms=processing_time,
            filters_applied=["basic_validation"]
        )
    
    @classmethod
    def create_invalid_result(cls, text: str, errors: List[str], processing_time: float = 0.0) -> 'ValidationResult':
        """Create an invalid validation result."""
        from .safety_score import SafetyScore
        
        return cls(
            is_valid=False,
            is_safe=False,
            original_text=text,
            sanitized_text=text,
            validation_errors=errors,
            safety_score=SafetyScore.create_safe_score(),
            processing_time_ms=processing_time,
            filters_applied=["validation"]
        )
    
    @classmethod
    def create_unsafe_result(cls, text: str, dimension: str, score: float, reasoning: str, processing_time: float = 0.0) -> 'ValidationResult':
        """Create an unsafe validation result."""
        from .safety_score import SafetyScore
        
        return cls(
            is_valid=True,
            is_safe=False,
            original_text=text,
            sanitized_text=text,
            safety_score=SafetyScore.create_unsafe_score(dimension, score, reasoning),
            processing_time_ms=processing_time,
            filters_applied=["content_filtering"]
        )
    
    @classmethod
    def create_rate_limited_result(cls, text: str, reset_time: int, processing_time: float = 0.0) -> 'ValidationResult':
        """Create a rate-limited validation result."""
        from .safety_score import SafetyScore
        
        return cls(
            is_valid=True,
            is_safe=True,
            original_text=text,
            sanitized_text=text,
            safety_score=SafetyScore.create_safe_score(),
            rate_limit_exceeded=True,
            rate_limit_reset_time=reset_time,
            processing_time_ms=processing_time,
            filters_applied=["rate_limiting"]
        ) 