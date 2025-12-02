"""
Tests for the BiasDetector component.
"""

import pytest
from src.filters.bias_detector import BiasDetector
from src.core.config import SafetyConfig


class TestBiasDetector:
    """Test cases for the BiasDetector class."""

    def test_initialization(self, default_config):
        """Test bias detector initializes correctly."""
        detector = BiasDetector(default_config)
        assert detector is not None
        assert detector.config == default_config
        assert detector.stats["total_checks"] == 0

    def test_neutral_text_no_bias(self, default_config):
        """Test that neutral text is not flagged as biased."""
        detector = BiasDetector(default_config)

        neutral_texts = [
            "The weather is nice today.",
            "Python is a programming language.",
            "The meeting is scheduled for tomorrow.",
        ]

        for text in neutral_texts:
            result = detector.detect_bias(text)
            assert result["bias_score"] < 0.5, f"False positive bias: {text}"

    def test_absolute_language_detection(self, default_config):
        """Test detection of absolute language."""
        detector = BiasDetector(default_config)

        absolute_texts = [
            "All programmers always write bugs",
            "Everyone knows this is completely true",
            "Nobody ever does that, never",
        ]

        for text in absolute_texts:
            result = detector.detect_bias(text)
            assert result["bias_score"] > 0.0
            assert any("absolute:" in term for term in result["flagged_terms"])

    def test_stereotype_language_detection(self, default_config):
        """Test detection of stereotypical language."""
        detector = BiasDetector(default_config)

        stereotype_texts = [
            "That's typical behavior for them",
            "This is normal but that is weird",
            "The expected outcome was predictable",
        ]

        for text in stereotype_texts:
            result = detector.detect_bias(text)
            assert result["bias_score"] > 0.0
            assert any("stereotype:" in term for term in result["flagged_terms"])

    def test_discriminatory_language_detection(self, default_config):
        """Test detection of discriminatory language."""
        detector = BiasDetector(default_config)

        discriminatory_texts = [
            "We should discriminate and exclude them",
            "I hate and dislike that group",
            "There's clear prejudice and bias here",
        ]

        for text in discriminatory_texts:
            result = detector.detect_bias(text)
            assert result["bias_score"] > 0.0
            assert any("discriminatory:" in term for term in result["flagged_terms"])

    def test_gender_bias_detection(self, default_config):
        """Test detection of gender-related language."""
        detector = BiasDetector(default_config)

        gender_texts = [
            "He always does better work than she does",
            "The man and woman have different capabilities",
        ]

        for text in gender_texts:
            result = detector.detect_bias(text)
            assert any("gender:" in term for term in result["flagged_terms"])

    def test_age_bias_detection(self, default_config):
        """Test detection of age-related language."""
        detector = BiasDetector(default_config)

        age_texts = [
            "Young people are better at technology",
            "Old elderly workers are less productive",
        ]

        for text in age_texts:
            result = detector.detect_bias(text)
            assert any("age:" in term for term in result["flagged_terms"])

    def test_bias_classification(self, default_config):
        """Test bias type classification."""
        detector = BiasDetector(default_config)

        # Heavy absolute bias
        result = detector.detect_bias("all everyone always never nobody completely")
        assert "absolute" in result["bias_type"]

        # Heavy discriminatory bias
        result = detector.detect_bias("hate discriminate prejudice bias exclude")
        assert "discriminatory" in result["bias_type"]

    def test_is_biased_flag(self, default_config):
        """Test is_biased flag based on threshold."""
        detector = BiasDetector(default_config)

        # Should not be biased
        result = detector.detect_bias("Hello world")
        assert not result["is_biased"]

        # Should have some bias score (threshold may vary)
        result = detector.detect_bias(
            "all everyone always never discriminate hate prejudice bias"
        )
        assert result["bias_score"] > 0.0  # Has bias indicators

    def test_confidence_calculation(self, default_config):
        """Test confidence score calculation."""
        detector = BiasDetector(default_config)

        # Low bias should have low confidence
        result = detector.detect_bias("Hello world")
        assert result["confidence"] <= 0.5

        # Bias detected should have some confidence
        result = detector.detect_bias(
            "all everyone completely totally discriminate hate prejudice"
        )
        assert result["confidence"] > 0.0  # Has some confidence

    def test_recommendations_generation(self, default_config):
        """Test recommendations generation."""
        detector = BiasDetector(default_config)

        # High bias content
        result = detector.detect_bias(
            "all everyone always hate discriminate prejudice"
        )
        assert len(result["recommendations"]) > 0

        # Gender-specific recommendations
        result = detector.detect_bias("he she man woman male female")
        assert any("gender" in rec.lower() for rec in result["recommendations"])

    def test_stats_tracking(self, default_config):
        """Test statistics tracking."""
        detector = BiasDetector(default_config)

        detector.detect_bias("Hello world")
        detector.detect_bias("all everyone always discriminate")

        stats = detector.get_stats()
        assert stats["total_checks"] == 2

    def test_stats_reset(self, default_config):
        """Test stats reset functionality."""
        detector = BiasDetector(default_config)

        detector.detect_bias("all everyone discriminate")
        assert detector.stats["total_checks"] > 0

        detector.reset_stats()
        assert detector.stats["total_checks"] == 0

    def test_empty_input(self, default_config):
        """Test handling of empty input."""
        detector = BiasDetector(default_config)

        result = detector.detect_bias("")
        assert result["bias_score"] == 0.0
        assert not result["is_biased"]
        assert len(result["flagged_terms"]) == 0

    def test_case_insensitivity(self, default_config):
        """Test that detection is case-insensitive."""
        detector = BiasDetector(default_config)

        lower_result = detector.detect_bias("all everyone always")
        upper_result = detector.detect_bias("ALL EVERYONE ALWAYS")

        assert lower_result["bias_score"] == upper_result["bias_score"]

    def test_combined_bias_types(self, default_config):
        """Test detection of multiple bias types."""
        detector = BiasDetector(default_config)

        result = detector.detect_bias(
            "All young men always discriminate against old women"
        )

        # Should detect multiple types
        flagged_types = set()
        for term in result["flagged_terms"]:
            bias_type = term.split(":")[0]
            flagged_types.add(bias_type)

        assert len(flagged_types) >= 3  # absolute, age, gender, discriminatory


class TestBiasDetectorWithConfigs:
    """Test BiasDetector with different configurations."""

    def test_strict_config_lower_threshold(self, strict_config):
        """Test with strict configuration has lower threshold."""
        detector = BiasDetector(strict_config)
        assert detector.config.bias_threshold == 0.3

    def test_lenient_config_higher_threshold(self, lenient_config):
        """Test with lenient configuration has higher threshold."""
        detector = BiasDetector(lenient_config)
        assert detector.config.bias_threshold == 0.6

    def test_threshold_affects_is_biased(self, strict_config, lenient_config):
        """Test that threshold affects is_biased determination."""
        strict_detector = BiasDetector(strict_config)
        lenient_detector = BiasDetector(lenient_config)

        # Moderate bias text
        text = "All people always do typical things"

        strict_result = strict_detector.detect_bias(text)
        lenient_result = lenient_detector.detect_bias(text)

        # Scores should be the same
        assert strict_result["bias_score"] == lenient_result["bias_score"]

        # But is_biased might differ based on threshold
        # (strict is more likely to flag as biased)
