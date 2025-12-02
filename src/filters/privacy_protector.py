"""
Privacy Protector Implementation

Protects sensitive information and personal data.
"""

import re
from typing import Dict, List, Any
from ..core.config import SafetyConfig


class PrivacyProtector:
    """Protects sensitive information and personal data."""

    def __init__(self, config: SafetyConfig):
        """Initialize privacy protector with configuration."""
        self.config = config
        self.stats = {"total_checks": 0, "privacy_violations": 0, "data_redacted": 0}

        # Initialize privacy patterns
        self._init_privacy_patterns()

    def _init_privacy_patterns(self):
        """Initialize patterns for privacy protection."""
        # Personal identification patterns
        self.pii_patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}-\d{4}-\d{4}-\d{4}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "mac_address": r"\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b",
            "date_of_birth": r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
            "driver_license": r"\b[A-Z]{1,2}\d{6,8}\b",
        }

        # Financial information patterns
        self.financial_patterns = {
            "bank_account": r"\b\d{8,17}\b",
            "routing_number": r"\b\d{9}\b",
            "credit_card_short": r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",
            "cvv": r"\b\d{3,4}\b",
        }

        # Sensitive keywords
        self.sensitive_keywords = {
            "password",
            "secret",
            "private",
            "confidential",
            "secure",
            "token",
            "key",
            "credential",
            "login",
            "username",
            "account",
            "social_security",
            "ssn",
            "credit_card",
            "bank_account",
            "address",
            "phone",
            "email",
            "birth_date",
            "passport",
        }

        # Compile patterns for efficiency
        self.compiled_pii_patterns = {
            name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.pii_patterns.items()
        }

        self.compiled_financial_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.financial_patterns.items()
        }

    def protect_privacy(self, text: str) -> Dict[str, Any]:
        """
        Protect sensitive information in text.

        Args:
            text: Text to analyze for privacy concerns

        Returns:
            Dictionary with privacy protection results
        """
        self.stats["total_checks"] += 1

        # Analyze text for privacy violations
        pii_violations = self._detect_pii_violations(text)
        financial_violations = self._detect_financial_violations(text)
        sensitive_keyword_violations = self._detect_sensitive_keywords(text)

        # Calculate overall privacy score
        total_violations = (
            len(pii_violations) + len(financial_violations) + len(sensitive_keyword_violations)
        )
        privacy_score = min(total_violations * 0.3, 1.0)

        # Redact sensitive information
        redacted_text = self._redact_sensitive_data(text)

        result = {
            "privacy_violated": privacy_score > 0.3,
            "privacy_score": privacy_score,
            "pii_violations": pii_violations,
            "financial_violations": financial_violations,
            "sensitive_keyword_violations": sensitive_keyword_violations,
            "redacted_text": redacted_text,
            "confidence": self._calculate_confidence(privacy_score),
            "recommendations": self._generate_recommendations(privacy_score),
        }

        if result["privacy_violated"]:
            self.stats["privacy_violations"] += 1

        if redacted_text != text:
            self.stats["data_redacted"] += 1

        return result

    def _detect_pii_violations(self, text: str) -> List[Dict[str, Any]]:
        """Detect personally identifiable information violations."""
        violations = []

        for pii_type, pattern in self.compiled_pii_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                violations.append(
                    {
                        "type": pii_type,
                        "value": match,
                        "severity": (
                            "high" if pii_type in ["ssn", "credit_card", "email"] else "medium"
                        ),
                    }
                )

        return violations

    def _detect_financial_violations(self, text: str) -> List[Dict[str, Any]]:
        """Detect financial information violations."""
        violations = []

        for financial_type, pattern in self.compiled_financial_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                violations.append({"type": financial_type, "value": match, "severity": "high"})

        return violations

    def _detect_sensitive_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Detect sensitive keyword violations."""
        violations = []
        normalized_text = text.lower()

        for keyword in self.sensitive_keywords:
            if keyword in normalized_text:
                violations.append(
                    {"type": "sensitive_keyword", "value": keyword, "severity": "medium"}
                )

        return violations

    def _redact_sensitive_data(self, text: str) -> str:
        """Redact sensitive data from text."""
        redacted_text = text

        # Redact PII
        for pii_type, pattern in self.compiled_pii_patterns.items():
            redacted_text = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted_text)

        # Redact financial information
        for financial_type, pattern in self.compiled_financial_patterns.items():
            redacted_text = pattern.sub(f"[REDACTED_{financial_type.upper()}]", redacted_text)

        # Redact sensitive keywords (partial redaction)
        for keyword in self.sensitive_keywords:
            # Replace with asterisks while keeping first and last character
            if len(keyword) > 2:
                replacement = keyword[0] + "*" * (len(keyword) - 2) + keyword[-1]
            else:
                replacement = "*" * len(keyword)

            # Case-insensitive replacement
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            redacted_text = pattern.sub(replacement, redacted_text)

        return redacted_text

    def _calculate_confidence(self, privacy_score: float) -> float:
        """Calculate confidence in privacy violation detection."""
        if privacy_score > 0.8:
            return 0.9
        elif privacy_score > 0.6:
            return 0.7
        elif privacy_score > 0.4:
            return 0.5
        else:
            return 0.3

    def _generate_recommendations(self, privacy_score: float) -> List[str]:
        """Generate recommendations based on privacy analysis."""
        recommendations = []

        if privacy_score > 0.7:
            recommendations.append(
                "Immediate action required - significant privacy violations detected"
            )
        elif privacy_score > 0.4:
            recommendations.append("Review content for privacy concerns")
        elif privacy_score > 0.2:
            recommendations.append("Monitor content for potential privacy issues")

        if privacy_score > 0.3:
            recommendations.append("Consider redacting sensitive information")
            recommendations.append("Review data handling practices")

        return recommendations

    def get_stats(self) -> Dict[str, int]:
        """Get protector statistics."""
        return self.stats.copy()

    def reset_stats(self):
        """Reset protector statistics."""
        self.stats = {"total_checks": 0, "privacy_violations": 0, "data_redacted": 0}
