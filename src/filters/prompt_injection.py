"""
Prompt Injection Detector

Detects attempts to manipulate or bypass the LLM's safety measures.
"""

import re
from typing import List, Dict
from ..core.config import SafetyConfig


class PromptInjectionDetector:
    """Detects prompt injection attempts."""
    
    def __init__(self, config: SafetyConfig):
        """Initialize prompt injection detector."""
        self.config = config
        self.stats = {
            'total_checks': 0,
            'injection_detected': 0,
            'false_positives': 0
        }
        
        # Initialize detection patterns
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize patterns for prompt injection detection."""
        # Common prompt injection patterns
        self.injection_patterns = [
            # System prompt manipulation
            r'system:\s*[^\n]*',
            r'you are now\s+[^\n]*',
            r'ignore previous instructions',
            r'forget everything',
            r'new instructions:',
            r'act as if',
            r'pretend to be',
            
            # Role manipulation
            r'you are a\s+[^\n]*',
            r'your role is\s+[^\n]*',
            r'your job is\s+[^\n]*',
            
            # Safety bypass attempts
            r'ignore safety',
            r'bypass safety',
            r'disable safety',
            r'ignore rules',
            r'break rules',
            
            # Output manipulation
            r'output format:',
            r'respond with:',
            r'answer only:',
            r'start your response with',
            r'end your response with',
            
            # Context manipulation
            r'context:\s*[^\n]*',
            r'background:\s*[^\n]*',
            r'scenario:\s*[^\n]*',
            
            # Conditional instructions
            r'if\s+[^\n]*\s+then\s+[^\n]*',
            r'when\s+[^\n]*\s+do\s+[^\n]*',
            
            # Repetition attempts
            r'repeat\s+[^\n]*',
            r'say\s+[^\n]*\s+exactly',
            r'copy\s+[^\n]*',
            
            # Code injection
            r'```[^\n]*```',
            r'<script[^>]*>',
            r'javascript:',
            
            # Special characters and encoding
            r'%[0-9A-Fa-f]{2}',
            r'\\u[0-9A-Fa-f]{4}',
            r'&#[0-9]+;',
        ]
        
        # Whitelist patterns (legitimate uses that might trigger false positives)
        self.whitelist_patterns = [
            r'please\s+[^\n]*',  # Polite requests
            r'can you\s+[^\n]*',  # Questions
            r'how to\s+[^\n]*',   # How-to questions
            r'what is\s+[^\n]*',  # Definition questions
            r'explain\s+[^\n]*',  # Explanation requests
            r'tell me\s+[^\n]*',  # Information requests
        ]
        
        # Compile patterns for efficiency
        self.compiled_injection_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.injection_patterns]
        self.compiled_whitelist_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.whitelist_patterns]
    
    def detect_injection(self, text: str) -> bool:
        """
        Detect prompt injection attempts in text.
        
        Args:
            text: Text to analyze for injection attempts
            
        Returns:
            True if injection is detected, False otherwise
        """
        self.stats['total_checks'] += 1
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Check for injection patterns
        injection_matches = []
        for pattern in self.compiled_injection_patterns:
            matches = pattern.findall(normalized_text)
            injection_matches.extend(matches)
        
        # Check for whitelist patterns (legitimate uses)
        whitelist_matches = []
        for pattern in self.compiled_whitelist_patterns:
            matches = pattern.findall(normalized_text)
            whitelist_matches.extend(matches)
        
        # Calculate injection score
        injection_score = self._calculate_injection_score(
            normalized_text, injection_matches, whitelist_matches
        )
        
        # Determine if injection is detected
        is_injection = injection_score > 0.6
        
        if is_injection:
            self.stats['injection_detected'] += 1
        
        return is_injection
    
    def _calculate_injection_score(self, text: str, injection_matches: List[str], 
                                 whitelist_matches: List[str]) -> float:
        """Calculate injection score based on matches and context."""
        if not injection_matches:
            return 0.0
        
        # Base score from injection matches
        base_score = min(len(injection_matches) * 0.3, 1.0)
        
        # Reduce score for whitelist matches (legitimate uses)
        whitelist_reduction = min(len(whitelist_matches) * 0.1, 0.3)
        base_score = max(0.0, base_score - whitelist_reduction)
        
        # Additional scoring based on suspicious patterns
        suspicious_patterns = [
            # Multiple injection attempts
            (len(injection_matches) > 2, 0.2),
            # Long text with injection attempts
            (len(text) > 500 and len(injection_matches) > 0, 0.1),
            # Repeated patterns
            (any(text.count(match) > 1 for match in injection_matches), 0.15),
            # Special character density
            (self._calculate_special_char_density(text) > 0.1, 0.1),
        ]
        
        for condition, score_increase in suspicious_patterns:
            if condition:
                base_score = min(1.0, base_score + score_increase)
        
        return base_score
    
    def _calculate_special_char_density(self, text: str) -> float:
        """Calculate density of special characters that might indicate encoding attempts."""
        special_chars = ['%', '\\', '&', '#', '<', '>', '{', '}', '[', ']']
        special_char_count = sum(1 for char in text if char in special_chars)
        return special_char_count / len(text) if text else 0.0
    
    def analyze_injection_attempt(self, text: str) -> Dict:
        """
        Analyze text for injection attempts and provide detailed analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with detailed analysis
        """
        normalized_text = text.lower().strip()
        
        # Find all matches
        injection_matches = []
        for pattern in self.compiled_injection_patterns:
            matches = pattern.findall(normalized_text)
            injection_matches.extend(matches)
        
        whitelist_matches = []
        for pattern in self.compiled_whitelist_patterns:
            matches = pattern.findall(normalized_text)
            whitelist_matches.extend(matches)
        
        # Calculate score
        injection_score = self._calculate_injection_score(
            normalized_text, injection_matches, whitelist_matches
        )
        
        # Determine injection type
        injection_type = self._classify_injection_type(injection_matches)
        
        return {
            'is_injection': injection_score > 0.6,
            'injection_score': injection_score,
            'injection_type': injection_type,
            'injection_matches': injection_matches,
            'whitelist_matches': whitelist_matches,
            'confidence': self._calculate_confidence(injection_score, len(injection_matches)),
            'recommendations': self._generate_recommendations(injection_score, injection_type)
        }
    
    def _classify_injection_type(self, matches: List[str]) -> str:
        """Classify the type of injection attempt."""
        if not matches:
            return "none"
        
        # Count different types of patterns
        system_manipulation = sum(1 for match in matches if any(word in match.lower() for word in ['system', 'ignore', 'forget']))
        role_manipulation = sum(1 for match in matches if any(word in match.lower() for word in ['role', 'job', 'act as']))
        safety_bypass = sum(1 for match in matches if any(word in match.lower() for word in ['safety', 'bypass', 'disable']))
        output_manipulation = sum(1 for match in matches if any(word in match.lower() for word in ['output', 'respond', 'answer']))
        
        # Determine primary type
        if system_manipulation > 0:
            return "system_manipulation"
        elif role_manipulation > 0:
            return "role_manipulation"
        elif safety_bypass > 0:
            return "safety_bypass"
        elif output_manipulation > 0:
            return "output_manipulation"
        else:
            return "general_injection"
    
    def _calculate_confidence(self, injection_score: float, match_count: int) -> float:
        """Calculate confidence in the injection detection."""
        if injection_score > 0.8:
            return 0.9
        elif injection_score > 0.6:
            return 0.7
        elif injection_score > 0.4:
            return 0.5
        else:
            return 0.3
    
    def _generate_recommendations(self, injection_score: float, injection_type: str) -> List[str]:
        """Generate recommendations based on injection analysis."""
        recommendations = []
        
        if injection_score > 0.8:
            recommendations.append("Block request - high confidence injection attempt")
        elif injection_score > 0.6:
            recommendations.append("Flag for human review - potential injection attempt")
        elif injection_score > 0.4:
            recommendations.append("Monitor closely - suspicious patterns detected")
        
        if injection_type == "safety_bypass":
            recommendations.append("Pay special attention to safety bypass attempts")
        elif injection_type == "system_manipulation":
            recommendations.append("Watch for system prompt manipulation")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, int]:
        """Get detector statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset detector statistics."""
        self.stats = {
            'total_checks': 0,
            'injection_detected': 0,
            'false_positives': 0
        } 