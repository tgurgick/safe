"""
Safety Report Model

Comprehensive safety analysis report for content.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .safety_score import SafetyScore


class SafetyReport(BaseModel):
    """Comprehensive safety analysis report."""
    
    # Basic information
    content_id: str = Field(
        default="",
        description="Unique identifier for the content"
    )
    content_type: str = Field(
        default="text",
        description="Type of content (text, image, audio, etc.)"
    )
    
    # Safety assessment
    is_safe: bool = Field(
        default=True,
        description="Overall safety determination"
    )
    safety_score: SafetyScore = Field(
        description="Detailed safety scoring"
    )
    
    # Processing details
    processing_time_ms: float = Field(
        default=0.0,
        description="Time taken to process content (milliseconds)"
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="List of filters that were applied"
    )
    
    # Recommendations
    recommendations: List[str] = Field(
        default_factory=list,
        description="Safety recommendations"
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Suggested actions to take"
    )
    
    # Metadata
    timestamp: str = Field(
        default="",
        description="Timestamp of the safety assessment"
    )
    version: str = Field(
        default="1.0",
        description="Version of the safety layer used"
    )
    
    def get_primary_concern(self) -> Optional[str]:
        """Get the primary safety concern."""
        if self.safety_score.overall_score == 0.0:
            return None
        
        highest_risk = self.safety_score.get_highest_risk_dimension()
        risk_score = getattr(self.safety_score, f"{highest_risk}_score")
        
        if risk_score > 0.7:
            return f"High {highest_risk.replace('_', ' ')} risk"
        elif risk_score > 0.4:
            return f"Moderate {highest_risk.replace('_', ' ')} risk"
        else:
            return f"Low {highest_risk.replace('_', ' ')} risk"
    
    def get_safety_summary(self) -> Dict:
        """Get a summary of the safety assessment."""
        return {
            'is_safe': self.is_safe,
            'safety_level': self.safety_score.safety_level,
            'overall_score': self.safety_score.overall_score,
            'primary_concern': self.get_primary_concern(),
            'confidence': self.safety_score.confidence,
            'processing_time': self.processing_time_ms
        }
    
    def should_block(self, threshold: float = 0.7) -> bool:
        """Determine if content should be blocked."""
        return self.safety_score.overall_score >= threshold
    
    def should_flag(self, threshold: float = 0.4) -> bool:
        """Determine if content should be flagged for review."""
        return self.safety_score.overall_score >= threshold
    
    def get_reasoning(self) -> str:
        """Get the reasoning for the safety assessment."""
        if not self.is_safe:
            primary_concern = self.get_primary_concern()
            return f"Content flagged as unsafe due to {primary_concern}. {self.safety_score.reasoning}"
        else:
            return self.safety_score.reasoning or "Content appears safe"
    
    @classmethod
    def create_safe_report(cls, content_id: str = "", processing_time: float = 0.0) -> 'SafetyReport':
        """Create a safe report instance."""
        from datetime import datetime
        
        return cls(
            content_id=content_id,
            is_safe=True,
            safety_score=SafetyScore.create_safe_score(),
            processing_time_ms=processing_time,
            filters_applied=["basic_validation"],
            recommendations=["Content appears safe"],
            timestamp=datetime.now().isoformat()
        )
    
    @classmethod
    def create_unsafe_report(
        cls, 
        content_id: str, 
        dimension: str, 
        score: float, 
        reasoning: str,
        processing_time: float = 0.0
    ) -> 'SafetyReport':
        """Create an unsafe report instance."""
        from datetime import datetime
        
        safety_score = SafetyScore.create_unsafe_score(dimension, score, reasoning)
        
        return cls(
            content_id=content_id,
            is_safe=False,
            safety_score=safety_score,
            processing_time_ms=processing_time,
            filters_applied=["content_filtering", "safety_analysis"],
            recommendations=[f"Review content for {dimension} concerns"],
            suggested_actions=["Block content", "Flag for human review"],
            timestamp=datetime.now().isoformat()
        ) 