"""
Safety Score Model

Represents multi-dimensional safety scoring for content.
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator


class SafetyLevel(str, Enum):
    """Safety levels based on overall score."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SAFE = "safe"


class SafetyScore(BaseModel):
    """Multi-dimensional safety score for content."""
    
    # Individual dimension scores (0-1, where 1 is most unsafe)
    violence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Violence detection score"
    )
    hate_speech_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Hate speech detection score"
    )
    bias_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Bias detection score"
    )
    privacy_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Privacy violation score"
    )
    factual_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Factual accuracy score (lower is better)"
    )
    
    # Overall safety score
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall safety score"
    )
    
    # Confidence in the assessment
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the safety assessment"
    )
    
    # Safety level classification
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.SAFE,
        description="Safety level classification"
    )
    
    # Additional metadata
    flagged_keywords: list[str] = Field(
        default_factory=list,
        description="Keywords that triggered safety flags"
    )
    reasoning: str = Field(
        default="",
        description="Reasoning for the safety assessment"
    )
    
    @validator('overall_score', pre=True, always=True)
    def calculate_overall_score(cls, v, values):
        """Calculate overall score from individual dimensions."""
        if v != 0.0:  # If explicitly set, use it
            return v
        
        # Weighted average of individual scores
        weights = {
            'violence_score': 0.3,
            'hate_speech_score': 0.25,
            'bias_score': 0.2,
            'privacy_score': 0.15,
            'factual_score': 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for dimension, weight in weights.items():
            if dimension in values:
                total_score += values[dimension] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    @validator('safety_level', pre=True, always=True)
    def determine_safety_level(cls, v, values):
        """Determine safety level based on overall score."""
        if v != SafetyLevel.SAFE:  # If explicitly set, use it
            return v
        
        overall_score = values.get('overall_score', 0.0)
        
        if overall_score >= 0.8:
            return SafetyLevel.CRITICAL
        elif overall_score >= 0.6:
            return SafetyLevel.HIGH
        elif overall_score >= 0.4:
            return SafetyLevel.MEDIUM
        elif overall_score >= 0.2:
            return SafetyLevel.LOW
        else:
            return SafetyLevel.SAFE
    
    def is_safe(self, threshold: float = 0.5) -> bool:
        """Check if content is safe based on threshold."""
        return self.overall_score < threshold
    
    def get_highest_risk_dimension(self) -> str:
        """Get the dimension with the highest risk score."""
        scores = {
            'violence': self.violence_score,
            'hate_speech': self.hate_speech_score,
            'bias': self.bias_score,
            'privacy': self.privacy_score,
            'factual': self.factual_score
        }
        return max(scores, key=scores.get)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            'overall_score': self.overall_score,
            'safety_level': self.safety_level,
            'confidence': self.confidence,
            'dimensions': {
                'violence': self.violence_score,
                'hate_speech': self.hate_speech_score,
                'bias': self.bias_score,
                'privacy': self.privacy_score,
                'factual': self.factual_score
            },
            'flagged_keywords': self.flagged_keywords,
            'reasoning': self.reasoning
        }
    
    @classmethod
    def create_safe_score(cls) -> 'SafetyScore':
        """Create a safe score instance."""
        return cls(
            violence_score=0.0,
            hate_speech_score=0.0,
            bias_score=0.0,
            privacy_score=0.0,
            factual_score=0.0,
            overall_score=0.0,
            confidence=1.0,
            safety_level=SafetyLevel.SAFE,
            reasoning="Content appears safe"
        )
    
    @classmethod
    def create_unsafe_score(cls, dimension: str, score: float, reasoning: str = "") -> 'SafetyScore':
        """Create an unsafe score instance."""
        scores = {
            'violence': {'violence_score': score},
            'hate_speech': {'hate_speech_score': score},
            'bias': {'bias_score': score},
            'privacy': {'privacy_score': score},
            'factual': {'factual_score': score}
        }
        
        return cls(
            **scores.get(dimension, {}),
            reasoning=reasoning
        ) 