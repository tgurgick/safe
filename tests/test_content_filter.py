"""
Tests for the ContentFilter component.
"""

import pytest
from src.filters.content_filter import ContentFilter
from src.core.config import SafetyConfig


class TestContentFilter:
    """Test cases for the ContentFilter class."""

    def test_initialization(self, default_config):
        """Test content filter initializes correctly."""
        filter = ContentFilter(default_config)
        assert filter is not None
        assert filter.config == default_config
        assert filter.stats["total_checks"] == 0

    def test_safe_content_analysis(self, default_config):
        """Test analysis of safe content."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("Hello, how are you today?")

        assert score.violence_score == 0.0
        assert score.hate_speech_score == 0.0
        assert score.is_safe()

    def test_violent_content_detection(self, default_config):
        """Test detection of violent content."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("I want to kill and murder everyone")

        assert score.violence_score > 0.0
        assert "violence:kill" in score.flagged_keywords
        assert "violence:murder" in score.flagged_keywords

    def test_hate_speech_detection(self, default_config):
        """Test detection of hate speech."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("I hate everyone and they are all racist bigots")

        assert score.hate_speech_score > 0.0
        assert any("hate_speech:" in kw for kw in score.flagged_keywords)

    def test_bias_detection(self, default_config):
        """Test detection of biased language."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("All people from that group are always weird")

        assert score.bias_score > 0.0
        assert any("bias:" in kw for kw in score.flagged_keywords)

    def test_privacy_violation_ssn(self, default_config):
        """Test detection of SSN in content."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("My social security number is 123-45-6789")

        assert score.privacy_score > 0.0

    def test_privacy_violation_credit_card(self, default_config):
        """Test detection of credit card in content."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("My credit card is 1234-5678-9012-3456")

        assert score.privacy_score > 0.0

    def test_privacy_violation_email(self, default_config):
        """Test detection of email address in content."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("Contact me at test@example.com")

        assert score.privacy_score > 0.0

    def test_context_reduces_violence_score(self, default_config):
        """Test that fictional context reduces violence scores."""
        filter = ContentFilter(default_config)

        # Direct violence
        direct_score = filter.analyze_content("someone gets killed")

        # Fictional context
        fiction_score = filter.analyze_content("in the movie, someone gets killed")

        assert fiction_score.violence_score < direct_score.violence_score

    def test_context_reduces_hate_speech_score(self, default_config):
        """Test that academic context reduces hate speech scores."""
        filter = ContentFilter(default_config)

        # Direct hate speech
        direct_score = filter.analyze_content("racist prejudice hate")

        # Academic context
        academic_score = filter.analyze_content("study analysis of racist prejudice")

        assert academic_score.hate_speech_score < direct_score.hate_speech_score

    def test_stats_tracking(self, default_config):
        """Test that statistics are tracked correctly."""
        filter = ContentFilter(default_config)

        # Run several checks
        filter.analyze_content("Hello world")
        filter.analyze_content("Kill someone violently")
        filter.analyze_content("I hate everyone")

        stats = filter.get_stats()
        assert stats["total_checks"] == 3
        # Note: flags only increment when score > 0.3 (implementation detail)

    def test_stats_reset(self, default_config):
        """Test stats reset functionality."""
        filter = ContentFilter(default_config)

        filter.analyze_content("Kill someone")
        assert filter.stats["total_checks"] > 0

        filter.reset_stats()
        assert filter.stats["total_checks"] == 0
        assert filter.stats["violence_flags"] == 0

    def test_multiple_categories(self, default_config):
        """Test content with multiple safety issues."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content(
            "I hate them all and want to kill them, email me at bad@evil.com"
        )

        assert score.violence_score > 0.0
        assert score.hate_speech_score > 0.0
        assert score.privacy_score > 0.0
        assert len(score.flagged_keywords) > 2

    def test_empty_input(self, default_config):
        """Test handling of empty input."""
        filter = ContentFilter(default_config)
        score = filter.analyze_content("")

        assert score.is_safe()
        assert score.overall_score == 0.0

    def test_reasoning_generation(self, default_config):
        """Test that reasoning is generated correctly."""
        filter = ContentFilter(default_config)

        safe_score = filter.analyze_content("Hello world")
        assert "safe" in safe_score.reasoning.lower()

        unsafe_score = filter.analyze_content("Kill murder bomb attack destroy")
        assert "violent" in unsafe_score.reasoning.lower() or "flagged" in unsafe_score.reasoning.lower()

    def test_confidence_calculation(self, default_config):
        """Test confidence score calculation."""
        filter = ContentFilter(default_config)

        # Low-risk content should have lower confidence
        safe_score = filter.analyze_content("Hello")
        assert safe_score.confidence <= 0.5

        # High-risk content should have higher confidence
        unsafe_score = filter.analyze_content("kill murder bomb attack weapon")
        assert unsafe_score.confidence >= 0.5


class TestContentFilterWithConfigs:
    """Test ContentFilter with different configurations."""

    def test_strict_config(self, strict_config):
        """Test content filter with strict configuration."""
        filter = ContentFilter(strict_config)
        assert filter.config.violence_threshold == 0.5

    def test_lenient_config(self, lenient_config):
        """Test content filter with lenient configuration."""
        filter = ContentFilter(lenient_config)
        assert filter.config.violence_threshold == 0.8
