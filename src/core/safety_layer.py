"""
Main Safety Layer Implementation

Orchestrates all safety checks and filtering for LLM interactions.
"""

import time
import uuid
from typing import Optional, Dict, Any
from .config import SafetyConfig
from .exceptions import SafetyLayerError, ValidationError
from ..models.safety_report import SafetyReport
from ..models.validation_result import ValidationResult
from ..models.safety_score import SafetyScore
from ..filters.content_filter import ContentFilter
from ..filters.prompt_injection import PromptInjectionDetector
from ..utils.rate_limiter import RateLimiter
from ..utils.text_processing import TextProcessor


class SafetyLayer:
    """Main safety layer for LLM interactions."""
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """Initialize the safety layer."""
        self.config = config or SafetyConfig()
        self.content_filter = ContentFilter(self.config)
        self.prompt_injection_detector = PromptInjectionDetector(self.config)
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_minute)
        self.text_processor = TextProcessor()
        
        # Initialize monitoring if enabled
        if self.config.enable_monitoring:
            self._setup_monitoring()
    
    def validate_input(self, text: str, user_id: Optional[str] = None) -> ValidationResult:
        """
        Validate and check safety of input text.
        
        Args:
            text: Input text to validate
            user_id: Optional user identifier for rate limiting
            
        Returns:
            ValidationResult with validation and safety assessment
        """
        start_time = time.time()
        
        try:
            # Generate content ID
            content_id = str(uuid.uuid4())
            
            # Basic input validation
            if not text or not text.strip():
                return ValidationResult.create_invalid_result(
                    text, 
                    ["Input text cannot be empty"],
                    (time.time() - start_time) * 1000
                )
            
            # Check input length
            if len(text) > self.config.max_input_length:
                return ValidationResult.create_invalid_result(
                    text,
                    [f"Input exceeds maximum length of {self.config.max_input_length} characters"],
                    (time.time() - start_time) * 1000
                )
            
            # Rate limiting
            if user_id:
                rate_limit_result = self.rate_limiter.check_rate_limit(user_id)
                if not rate_limit_result['allowed']:
                    return ValidationResult.create_rate_limited_result(
                        text,
                        rate_limit_result['reset_time'],
                        (time.time() - start_time) * 1000
                    )
            
            # Sanitize input
            sanitized_text = self.text_processor.sanitize_text(text)
            
            # Detect prompt injection
            if self.prompt_injection_detector.detect_injection(sanitized_text):
                return ValidationResult.create_unsafe_result(
                    text,
                    "prompt_injection",
                    0.8,
                    "Potential prompt injection detected",
                    (time.time() - start_time) * 1000
                )
            
            # Content filtering
            if self.config.enable_content_filtering:
                safety_score = self.content_filter.analyze_content(sanitized_text)
                
                # Check if content is unsafe based on thresholds
                if safety_score.violence_score > self.config.violence_threshold:
                    return ValidationResult.create_unsafe_result(
                        text,
                        "violence",
                        safety_score.violence_score,
                        "Content contains potentially violent content",
                        (time.time() - start_time) * 1000
                    )
                
                if safety_score.hate_speech_score > self.config.hate_speech_threshold:
                    return ValidationResult.create_unsafe_result(
                        text,
                        "hate_speech",
                        safety_score.hate_speech_score,
                        "Content contains potentially harmful speech",
                        (time.time() - start_time) * 1000
                    )
                
                if safety_score.bias_score > self.config.bias_threshold:
                    return ValidationResult.create_unsafe_result(
                        text,
                        "bias",
                        safety_score.bias_score,
                        "Content contains potentially biased language",
                        (time.time() - start_time) * 1000
                    )
                
                # If any dimension is high risk, mark as unsafe
                if safety_score.overall_score > 0.7:
                    highest_risk = safety_score.get_highest_risk_dimension()
                    return ValidationResult.create_unsafe_result(
                        text,
                        highest_risk,
                        safety_score.overall_score,
                        f"Content flagged for {highest_risk} concerns",
                        (time.time() - start_time) * 1000
                    )
                
                # Create valid result with safety score
                result = ValidationResult.create_valid_result(
                    text,
                    sanitized_text,
                    (time.time() - start_time) * 1000
                )
                result.safety_score = safety_score
                result.filters_applied = ["basic_validation", "prompt_injection", "content_filtering"]
                return result
            
            # If content filtering is disabled, return valid result
            return ValidationResult.create_valid_result(
                text,
                sanitized_text,
                (time.time() - start_time) * 1000
            )
            
        except Exception as e:
            # Log error and return safe result to avoid blocking legitimate requests
            if self.config.log_safety_decisions:
                print(f"Safety layer error: {e}")
            
            return ValidationResult.create_valid_result(
                text,
                text,
                (time.time() - start_time) * 1000
            )
    
    def monitor_output(self, response: str, content_id: Optional[str] = None) -> SafetyReport:
        """
        Monitor and analyze LLM output for safety concerns.
        
        Args:
            response: LLM response to analyze
            content_id: Optional content identifier for tracking
            
        Returns:
            SafetyReport with safety analysis
        """
        start_time = time.time()
        
        try:
            if not content_id:
                content_id = str(uuid.uuid4())
            
            # Basic response validation
            if not response or not response.strip():
                return SafetyReport.create_safe_report(
                    content_id,
                    (time.time() - start_time) * 1000
                )
            
            # Content filtering for output
            if self.config.enable_content_filtering:
                safety_score = self.content_filter.analyze_content(response)
                
                # Determine if response should be blocked
                if safety_score.overall_score >= 0.8:
                    return SafetyReport.create_unsafe_report(
                        content_id,
                        safety_score.get_highest_risk_dimension(),
                        safety_score.overall_score,
                        f"Response contains unsafe content: {safety_score.reasoning}",
                        (time.time() - start_time) * 1000
                    )
                
                # Create report with safety analysis
                report = SafetyReport(
                    content_id=content_id,
                    is_safe=safety_score.overall_score < 0.6,
                    safety_score=safety_score,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    filters_applied=["output_monitoring", "content_filtering"],
                    recommendations=self._generate_recommendations(safety_score),
                    suggested_actions=self._generate_actions(safety_score)
                )
                
                return report
            
            # If content filtering is disabled, return safe report
            return SafetyReport.create_safe_report(
                content_id,
                (time.time() - start_time) * 1000
            )
            
        except Exception as e:
            # Log error and return safe report
            if self.config.log_safety_decisions:
                print(f"Output monitoring error: {e}")
            
            return SafetyReport.create_safe_report(
                content_id,
                (time.time() - start_time) * 1000
            )
    
    def process_interaction(self, user_input: str, llm_response: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a complete user-LLM interaction.
        
        Args:
            user_input: User's input text
            llm_response: LLM's response text
            user_id: Optional user identifier
            
        Returns:
            Dictionary with processing results
        """
        # Validate input
        input_result = self.validate_input(user_input, user_id)
        
        if not input_result.should_proceed():
            return {
                'input_valid': False,
                'input_result': input_result,
                'output_result': None,
                'should_proceed': False,
                'error_message': input_result.get_error_message()
            }
        
        # Monitor output
        output_result = self.monitor_output(llm_response)
        
        return {
            'input_valid': True,
            'input_result': input_result,
            'output_result': output_result,
            'should_proceed': output_result.is_safe,
            'error_message': None if output_result.is_safe else output_result.get_reasoning()
        }
    
    def _generate_recommendations(self, safety_score: SafetyScore) -> list[str]:
        """Generate safety recommendations based on score."""
        recommendations = []
        
        if safety_score.violence_score > 0.5:
            recommendations.append("Review content for violent language")
        
        if safety_score.hate_speech_score > 0.5:
            recommendations.append("Review content for harmful speech")
        
        if safety_score.bias_score > 0.5:
            recommendations.append("Review content for biased language")
        
        if safety_score.privacy_score > 0.5:
            recommendations.append("Review content for privacy concerns")
        
        if not recommendations:
            recommendations.append("Content appears safe")
        
        return recommendations
    
    def _generate_actions(self, safety_score: SafetyScore) -> list[str]:
        """Generate suggested actions based on safety score."""
        if safety_score.overall_score >= 0.8:
            return ["Block content", "Flag for human review"]
        elif safety_score.overall_score >= 0.6:
            return ["Flag for human review", "Add warning"]
        elif safety_score.overall_score >= 0.4:
            return ["Monitor closely", "Consider review"]
        else:
            return ["Allow content"]
    
    def _setup_monitoring(self):
        """Setup monitoring and metrics collection."""
        # This would integrate with Prometheus, logging, etc.
        # For now, just a placeholder
        pass
    
    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety layer statistics."""
        return {
            'config': self.config.dict(),
            'rate_limiter_stats': self.rate_limiter.get_stats(),
            'content_filter_stats': self.content_filter.get_stats(),
            'prompt_injection_stats': self.prompt_injection_detector.get_stats()
        } 