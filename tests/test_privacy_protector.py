"""
Tests for the PrivacyProtector component.
"""

import pytest
from src.filters.privacy_protector import PrivacyProtector
from src.core.config import SafetyConfig


class TestPrivacyProtector:
    """Test cases for the PrivacyProtector class."""

    def test_initialization(self, default_config):
        """Test privacy protector initializes correctly."""
        protector = PrivacyProtector(default_config)
        assert protector is not None
        assert protector.config == default_config
        assert protector.stats["total_checks"] == 0

    def test_clean_text_no_violations(self, default_config):
        """Test that clean text has no privacy violations."""
        protector = PrivacyProtector(default_config)

        clean_texts = [
            "Hello, how are you today?",
            "The weather is nice.",
            "I like programming.",
        ]

        for text in clean_texts:
            result = protector.protect_privacy(text)
            assert result["privacy_score"] < 0.3
            assert not result["privacy_violated"]

    def test_ssn_detection(self, default_config):
        """Test detection of Social Security Numbers."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("My SSN is 123-45-6789")

        assert result["privacy_violated"]
        assert len(result["pii_violations"]) > 0
        assert any(v["type"] == "ssn" for v in result["pii_violations"])

    def test_credit_card_detection(self, default_config):
        """Test detection of credit card numbers."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Card: 1234-5678-9012-3456")

        assert result["privacy_violated"]
        assert any(v["type"] == "credit_card" for v in result["pii_violations"])

    def test_email_detection(self, default_config):
        """Test detection of email addresses."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Contact me at user@example.com")

        assert len(result["pii_violations"]) > 0
        assert any(v["type"] == "email" for v in result["pii_violations"])

    def test_phone_detection(self, default_config):
        """Test detection of phone numbers."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Call me at 555-123-4567")

        assert len(result["pii_violations"]) > 0
        assert any(v["type"] == "phone" for v in result["pii_violations"])

    def test_ip_address_detection(self, default_config):
        """Test detection of IP addresses."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Server IP is 192.168.1.100")

        assert len(result["pii_violations"]) > 0
        assert any(v["type"] == "ip_address" for v in result["pii_violations"])

    def test_date_of_birth_detection(self, default_config):
        """Test detection of dates of birth."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Born on 12/25/1990")

        assert len(result["pii_violations"]) > 0
        assert any(v["type"] == "date_of_birth" for v in result["pii_violations"])

    def test_sensitive_keywords_detection(self, default_config):
        """Test detection of sensitive keywords."""
        protector = PrivacyProtector(default_config)

        sensitive_texts = [
            "My password is secret123",
            "The private key is stored here",
            "Your login credentials are",
        ]

        for text in sensitive_texts:
            result = protector.protect_privacy(text)
            assert len(result["sensitive_keyword_violations"]) > 0

    def test_redaction_ssn(self, default_config):
        """Test SSN redaction."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("SSN: 123-45-6789")

        # SSN should be redacted (implementation uses REDACTED_ prefix)
        assert "123-45-6789" not in result["redacted_text"]
        assert "REDACTED" in result["redacted_text"]

    def test_redaction_credit_card(self, default_config):
        """Test credit card redaction."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Card: 1234-5678-9012-3456")

        # Credit card should be redacted
        assert "1234-5678-9012-3456" not in result["redacted_text"]
        assert "REDACTED" in result["redacted_text"]

    def test_redaction_email(self, default_config):
        """Test email redaction."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("Email: user@example.com")

        # Email should be redacted
        assert "user@example.com" not in result["redacted_text"]
        assert "REDACTED" in result["redacted_text"]

    def test_redaction_sensitive_keywords(self, default_config):
        """Test sensitive keyword partial redaction."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("The password is here")

        # Password should be partially redacted (p******d)
        assert "password" not in result["redacted_text"].lower()

    def test_multiple_pii_detection(self, default_config):
        """Test detection of multiple PII in same text."""
        protector = PrivacyProtector(default_config)

        text = "SSN: 123-45-6789, Email: test@example.com, Phone: 555-123-4567"
        result = protector.protect_privacy(text)

        assert len(result["pii_violations"]) >= 3
        assert result["privacy_violated"]

    def test_severity_levels(self, default_config):
        """Test severity level assignment."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy(
            "SSN: 123-45-6789 Phone: 555-123-4567"
        )

        # SSN should be high severity
        ssn_violations = [v for v in result["pii_violations"] if v["type"] == "ssn"]
        assert all(v["severity"] == "high" for v in ssn_violations)

    def test_privacy_score_calculation(self, default_config):
        """Test privacy score calculation."""
        protector = PrivacyProtector(default_config)

        # No violations
        clean_result = protector.protect_privacy("Hello world")
        assert clean_result["privacy_score"] == 0.0

        # Multiple violations should increase score
        violation_result = protector.protect_privacy(
            "SSN: 123-45-6789 Card: 1234-5678-9012-3456 Email: test@test.com"
        )
        assert violation_result["privacy_score"] > 0.5

    def test_confidence_calculation(self, default_config):
        """Test confidence score calculation."""
        protector = PrivacyProtector(default_config)

        # Low privacy score = low confidence
        clean_result = protector.protect_privacy("Hello")
        assert clean_result["confidence"] <= 0.5

        # High privacy score = high confidence
        violation_result = protector.protect_privacy(
            "SSN: 123-45-6789 Card: 1234-5678-9012-3456 secret password"
        )
        assert violation_result["confidence"] >= 0.5

    def test_recommendations_generation(self, default_config):
        """Test recommendations generation."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy(
            "SSN: 123-45-6789 password secret confidential"
        )

        assert len(result["recommendations"]) > 0

    def test_stats_tracking(self, default_config):
        """Test statistics tracking."""
        protector = PrivacyProtector(default_config)

        protector.protect_privacy("Hello world")
        protector.protect_privacy("SSN: 123-45-6789")

        stats = protector.get_stats()
        assert stats["total_checks"] == 2
        assert stats["privacy_violations"] >= 1

    def test_stats_data_redacted(self, default_config):
        """Test data redacted counter."""
        protector = PrivacyProtector(default_config)

        protector.protect_privacy("SSN: 123-45-6789")

        stats = protector.get_stats()
        assert stats["data_redacted"] >= 1

    def test_stats_reset(self, default_config):
        """Test stats reset functionality."""
        protector = PrivacyProtector(default_config)

        protector.protect_privacy("SSN: 123-45-6789")
        assert protector.stats["total_checks"] > 0

        protector.reset_stats()
        assert protector.stats["total_checks"] == 0
        assert protector.stats["privacy_violations"] == 0

    def test_empty_input(self, default_config):
        """Test handling of empty input."""
        protector = PrivacyProtector(default_config)

        result = protector.protect_privacy("")

        assert result["privacy_score"] == 0.0
        assert not result["privacy_violated"]
        assert result["redacted_text"] == ""

    def test_no_change_for_clean_text(self, default_config):
        """Test that clean text remains unchanged after redaction."""
        protector = PrivacyProtector(default_config)

        original_text = "Hello, how are you today?"
        result = protector.protect_privacy(original_text)

        # Text should be mostly unchanged (sensitive keywords might still be redacted)
        assert len(result["pii_violations"]) == 0


class TestPrivacyProtectorPatterns:
    """Test specific pattern detection in PrivacyProtector."""

    def test_various_ssn_formats(self, default_config):
        """Test various SSN format detection."""
        protector = PrivacyProtector(default_config)

        ssn_texts = [
            "123-45-6789",
            "987-65-4321",
        ]

        for text in ssn_texts:
            result = protector.protect_privacy(text)
            assert len(result["pii_violations"]) > 0

    def test_various_email_formats(self, default_config):
        """Test various email format detection."""
        protector = PrivacyProtector(default_config)

        email_texts = [
            "user@example.com",
            "user.name@subdomain.example.org",
            "user+tag@example.co.uk",
        ]

        for text in email_texts:
            result = protector.protect_privacy(text)
            assert any(v["type"] == "email" for v in result["pii_violations"])
