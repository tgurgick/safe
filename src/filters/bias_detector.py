"""
Bias Detector Implementation

Detects biased language and discriminatory content.
"""

from typing import Dict, List, Set, Any
from ..core.config import SafetyConfig


class BiasDetector:
    """Detects biased language and discriminatory content."""
    
    def __init__(self, config: SafetyConfig):
        """Initialize bias detector with configuration."""
        self.config = config
        self.stats = {
            'total_checks': 0,
            'bias_detected': 0,
            'false_positives': 0
        }
        
        # Initialize bias patterns
        self._init_bias_patterns()
    
    def _init_bias_patterns(self):
        """Initialize patterns for bias detection."""
        # Absolute language patterns
        self.absolute_patterns = {
            'all', 'everyone', 'nobody', 'always', 'never', 'every', 'none',
            'completely', 'totally', 'absolutely', 'entirely', 'wholly'
        }
        
        # Stereotypical language patterns
        self.stereotype_patterns = {
            'typical', 'usual', 'normal', 'abnormal', 'weird', 'strange',
            'expected', 'unexpected', 'predictable', 'unpredictable'
        }
        
        # Discriminatory language patterns
        self.discriminatory_patterns = {
            'hate', 'dislike', 'prefer', 'avoid', 'exclude', 'include',
            'favor', 'disfavor', 'bias', 'prejudice', 'discriminate'
        }
        
        # Gender bias patterns
        self.gender_bias_patterns = {
            'he', 'she', 'his', 'her', 'him', 'hers', 'himself', 'herself',
            'man', 'woman', 'boy', 'girl', 'male', 'female'
        }
        
        # Age bias patterns
        self.age_bias_patterns = {
            'young', 'old', 'elderly', 'senior', 'junior', 'teenager',
            'adult', 'child', 'kid', 'baby', 'infant'
        }
    
    def detect_bias(self, text: str) -> Dict[str, Any]:
        """
        Detect biased language in text.
        
        Args:
            text: Text to analyze for bias
            
        Returns:
            Dictionary with bias analysis results
        """
        self.stats['total_checks'] += 1
        
        # Normalize text
        normalized_text = text.lower().strip()
        
        # Analyze different types of bias
        absolute_bias = self._detect_absolute_bias(normalized_text)
        stereotype_bias = self._detect_stereotype_bias(normalized_text)
        discriminatory_bias = self._detect_discriminatory_bias(normalized_text)
        gender_bias = self._detect_gender_bias(normalized_text)
        age_bias = self._detect_age_bias(normalized_text)
        
        # Calculate overall bias score
        bias_scores = [absolute_bias, stereotype_bias, discriminatory_bias, gender_bias, age_bias]
        overall_bias = sum(bias_scores) / len(bias_scores)
        
        # Determine bias type
        bias_type = self._classify_bias_type(absolute_bias, stereotype_bias, discriminatory_bias, gender_bias, age_bias)
        
        # Collect flagged terms
        flagged_terms = self._collect_flagged_terms(normalized_text)
        
        result = {
            'is_biased': overall_bias > self.config.bias_threshold,
            'bias_score': overall_bias,
            'bias_type': bias_type,
            'flagged_terms': flagged_terms,
            'confidence': self._calculate_confidence(overall_bias),
            'recommendations': self._generate_recommendations(overall_bias, bias_type)
        }
        
        if result['is_biased']:
            self.stats['bias_detected'] += 1
        
        return result
    
    def _detect_absolute_bias(self, text: str) -> float:
        """Detect absolute language bias."""
        absolute_count = sum(1 for pattern in self.absolute_patterns if pattern in text)
        return min(absolute_count * 0.2, 1.0)
    
    def _detect_stereotype_bias(self, text: str) -> float:
        """Detect stereotypical language bias."""
        stereotype_count = sum(1 for pattern in self.stereotype_patterns if pattern in text)
        return min(stereotype_count * 0.25, 1.0)
    
    def _detect_discriminatory_bias(self, text: str) -> float:
        """Detect discriminatory language bias."""
        discriminatory_count = sum(1 for pattern in self.discriminatory_patterns if pattern in text)
        return min(discriminatory_count * 0.3, 1.0)
    
    def _detect_gender_bias(self, text: str) -> float:
        """Detect gender bias."""
        gender_count = sum(1 for pattern in self.gender_bias_patterns if pattern in text)
        return min(gender_count * 0.15, 1.0)
    
    def _detect_age_bias(self, text: str) -> float:
        """Detect age bias."""
        age_count = sum(1 for pattern in self.age_bias_patterns if pattern in text)
        return min(age_count * 0.15, 1.0)
    
    def _classify_bias_type(self, absolute_bias: float, stereotype_bias: float,
                           discriminatory_bias: float, gender_bias: float, age_bias: float) -> str:
        """Classify the type of bias detected."""
        bias_scores = {
            'absolute': absolute_bias,
            'stereotype': stereotype_bias,
            'discriminatory': discriminatory_bias,
            'gender': gender_bias,
            'age': age_bias
        }
        
        max_bias_type = max(bias_scores, key=bias_scores.get)
        max_score = bias_scores[max_bias_type]
        
        if max_score > 0.7:
            return f"high_{max_bias_type}_bias"
        elif max_score > 0.4:
            return f"moderate_{max_bias_type}_bias"
        elif max_score > 0.2:
            return f"low_{max_bias_type}_bias"
        else:
            return "no_significant_bias"
    
    def _collect_flagged_terms(self, text: str) -> List[str]:
        """Collect terms that triggered bias flags."""
        flagged = []
        
        # Check all bias patterns
        all_patterns = {
            'absolute': self.absolute_patterns,
            'stereotype': self.stereotype_patterns,
            'discriminatory': self.discriminatory_patterns,
            'gender': self.gender_bias_patterns,
            'age': self.age_bias_patterns
        }
        
        for bias_type, patterns in all_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    flagged.append(f"{bias_type}:{pattern}")
        
        return flagged
    
    def _calculate_confidence(self, bias_score: float) -> float:
        """Calculate confidence in bias detection."""
        if bias_score > 0.8:
            return 0.9
        elif bias_score > 0.6:
            return 0.7
        elif bias_score > 0.4:
            return 0.5
        else:
            return 0.3
    
    def _generate_recommendations(self, bias_score: float, bias_type: str) -> List[str]:
        """Generate recommendations based on bias analysis."""
        recommendations = []
        
        if bias_score > 0.7:
            recommendations.append("Review content for significant bias concerns")
        elif bias_score > 0.4:
            recommendations.append("Consider reviewing content for potential bias")
        elif bias_score > 0.2:
            recommendations.append("Monitor content for bias patterns")
        
        if 'gender' in bias_type:
            recommendations.append("Consider gender-neutral language alternatives")
        elif 'age' in bias_type:
            recommendations.append("Consider age-inclusive language")
        elif 'discriminatory' in bias_type:
            recommendations.append("Review for discriminatory language")
        
        return recommendations
    
    def get_stats(self) -> Dict[str, int]:
        """Get detector statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset detector statistics."""
        self.stats = {
            'total_checks': 0,
            'bias_detected': 0,
            'false_positives': 0
        } 