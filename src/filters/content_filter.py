"""
Content Filter Implementation

Analyzes content for safety concerns and provides scoring.
"""

import re
from typing import Dict, List, Set
from ..core.config import SafetyConfig
from ..models.safety_score import SafetyScore


class ContentFilter:
    """Filters content for safety concerns."""

    def __init__(self, config: SafetyConfig):
        """Initialize content filter with configuration."""
        self.config = config
        self.stats = {
            "total_checks": 0,
            "violence_flags": 0,
            "hate_speech_flags": 0,
            "bias_flags": 0,
            "privacy_flags": 0,
        }

        # Initialize keyword lists
        self._init_keywords()

    def _init_keywords(self):
        """Initialize keyword lists for different safety dimensions."""
        # Violence-related keywords
        self.violence_keywords = {
            "kill",
            "murder",
            "assassinate",
            "bomb",
            "explode",
            "shoot",
            "gun",
            "weapon",
            "attack",
            "fight",
            "violence",
            "blood",
            "death",
            "die",
            "suicide",
            "terrorism",
            "hack",
            "cyberattack",
            "destroy",
            "harm",
        }

        # Hate speech keywords
        self.hate_speech_keywords = {
            "hate",
            "racist",
            "bigot",
            "discriminate",
            "slur",
            "offensive",
            "insult",
            "derogatory",
            "prejudice",
            "bias",
            "stereotype",
        }

        # Bias-related keywords
        self.bias_keywords = {
            "all",
            "everyone",
            "nobody",
            "always",
            "never",
            "typical",
            "usual",
            "normal",
            "abnormal",
            "weird",
            "strange",
        }

        # Privacy-related patterns
        self.privacy_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",  # Credit card
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
            r"\b\d{3}-\d{3}-\d{4}\b",  # Phone number
        ]

    def analyze_content(self, text: str) -> SafetyScore:
        """
        Analyze content for safety concerns.

        Args:
            text: Text to analyze

        Returns:
            SafetyScore with detailed analysis
        """
        self.stats["total_checks"] += 1

        # Normalize text
        normalized_text = text.lower().strip()

        # Analyze different dimensions
        violence_score = self._analyze_violence(normalized_text)
        hate_speech_score = self._analyze_hate_speech(normalized_text)
        bias_score = self._analyze_bias(normalized_text)
        privacy_score = self._analyze_privacy(normalized_text)
        factual_score = self._analyze_factual_accuracy(normalized_text)

        # Collect flagged keywords
        flagged_keywords = self._collect_flagged_keywords(normalized_text)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            violence_score,
            hate_speech_score,
            bias_score,
            privacy_score,
            factual_score,
            flagged_keywords,
        )

        # Create safety score
        safety_score = SafetyScore(
            violence_score=violence_score,
            hate_speech_score=hate_speech_score,
            bias_score=bias_score,
            privacy_score=privacy_score,
            factual_score=factual_score,
            flagged_keywords=flagged_keywords,
            reasoning=reasoning,
            confidence=self._calculate_confidence(
                violence_score, hate_speech_score, bias_score, privacy_score, factual_score
            ),
        )

        return safety_score

    def _analyze_violence(self, text: str) -> float:
        """Analyze text for violent content."""
        violence_count = sum(1 for keyword in self.violence_keywords if keyword in text)

        if violence_count == 0:
            return 0.0

        # Calculate score based on keyword density and context
        score = min(violence_count * 0.2, 1.0)

        # Check for context that might reduce violence score
        if any(word in text for word in ["game", "movie", "fiction", "story"]):
            score *= 0.5

        if score > 0.3:
            self.stats["violence_flags"] += 1

        return score

    def _analyze_hate_speech(self, text: str) -> float:
        """Analyze text for hate speech."""
        hate_count = sum(1 for keyword in self.hate_speech_keywords if keyword in text)

        if hate_count == 0:
            return 0.0

        # Calculate score based on keyword density
        score = min(hate_count * 0.3, 1.0)

        # Check for context that might reduce hate speech score
        if any(word in text for word in ["discuss", "debate", "analysis", "study"]):
            score *= 0.6

        if score > 0.3:
            self.stats["hate_speech_flags"] += 1

        return score

    def _analyze_bias(self, text: str) -> float:
        """Analyze text for biased language."""
        bias_count = sum(1 for keyword in self.bias_keywords if keyword in text)

        if bias_count == 0:
            return 0.0

        # Calculate score based on keyword density
        score = min(bias_count * 0.15, 1.0)

        # Check for context that might reduce bias score
        if any(word in text for word in ["research", "study", "analysis", "data"]):
            score *= 0.7

        if score > 0.3:
            self.stats["bias_flags"] += 1

        return score

    def _analyze_privacy(self, text: str) -> float:
        """Analyze text for privacy violations."""
        privacy_score = 0.0

        # Check for privacy patterns
        for pattern in self.privacy_patterns:
            matches = re.findall(pattern, text)
            if matches:
                privacy_score += len(matches) * 0.4

        # Check for other privacy indicators
        privacy_indicators = ["password", "secret", "private", "confidential"]
        privacy_count = sum(1 for indicator in privacy_indicators if indicator in text)
        privacy_score += privacy_count * 0.1

        privacy_score = min(privacy_score, 1.0)

        if privacy_score > 0.3:
            self.stats["privacy_flags"] += 1

        return privacy_score

    def _analyze_factual_accuracy(self, text: str) -> float:
        """Analyze text for factual accuracy concerns."""
        # This is a simplified implementation
        # In a real system, this would integrate with fact-checking APIs

        factual_indicators = [
            "fact",
            "true",
            "accurate",
            "verified",
            "confirmed",
            "false",
            "fake",
            "hoax",
            "conspiracy",
            "rumor",
        ]

        factual_count = sum(1 for indicator in factual_indicators if indicator in text)

        if factual_count == 0:
            return 0.0

        # Simple heuristic: more factual indicators might indicate uncertainty
        return min(factual_count * 0.1, 1.0)

    def _collect_flagged_keywords(self, text: str) -> List[str]:
        """Collect keywords that triggered safety flags."""
        flagged = []

        # Check violence keywords
        for keyword in self.violence_keywords:
            if keyword in text:
                flagged.append(f"violence:{keyword}")

        # Check hate speech keywords
        for keyword in self.hate_speech_keywords:
            if keyword in text:
                flagged.append(f"hate_speech:{keyword}")

        # Check bias keywords
        for keyword in self.bias_keywords:
            if keyword in text:
                flagged.append(f"bias:{keyword}")

        return flagged

    def _generate_reasoning(
        self,
        violence_score: float,
        hate_speech_score: float,
        bias_score: float,
        privacy_score: float,
        factual_score: float,
        flagged_keywords: List[str],
    ) -> str:
        """Generate reasoning for the safety assessment."""
        concerns = []

        if violence_score > 0.5:
            concerns.append("violent content")

        if hate_speech_score > 0.5:
            concerns.append("hate speech")

        if bias_score > 0.5:
            concerns.append("biased language")

        if privacy_score > 0.5:
            concerns.append("privacy violations")

        if factual_score > 0.5:
            concerns.append("factual accuracy concerns")

        if concerns:
            return f"Content flagged for: {', '.join(concerns)}"
        else:
            return "Content appears safe"

    def _calculate_confidence(
        self,
        violence_score: float,
        hate_speech_score: float,
        bias_score: float,
        privacy_score: float,
        factual_score: float,
    ) -> float:
        """Calculate confidence in the safety assessment."""
        # Higher scores generally indicate higher confidence
        max_score = max(violence_score, hate_speech_score, bias_score, privacy_score, factual_score)

        if max_score > 0.7:
            return 0.9
        elif max_score > 0.4:
            return 0.7
        elif max_score > 0.2:
            return 0.5
        else:
            return 0.3

    def get_stats(self) -> Dict[str, int]:
        """Get filter statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset filter statistics."""
        self.stats = {
            "total_checks": 0,
            "violence_flags": 0,
            "hate_speech_flags": 0,
            "bias_flags": 0,
            "privacy_flags": 0,
        }
