"""
Tests for the TextProcessor component.
"""

import pytest
from src.utils.text_processing import TextProcessor


class TestTextProcessor:
    """Test cases for the TextProcessor class."""

    def test_initialization(self):
        """Test text processor initializes correctly."""
        processor = TextProcessor()
        assert processor is not None

    def test_sanitize_empty_text(self):
        """Test sanitization of empty text."""
        processor = TextProcessor()

        result = processor.sanitize_text("")
        assert result == ""

        result = processor.sanitize_text(None)
        assert result == ""

    def test_sanitize_removes_html_tags(self):
        """Test that HTML tags are removed."""
        processor = TextProcessor()

        text = "<p>Hello <b>World</b></p>"
        result = processor.sanitize_text(text)

        assert "<p>" not in result
        assert "<b>" not in result
        assert "</p>" not in result

    def test_sanitize_decodes_html_entities(self):
        """Test that HTML entities are decoded."""
        processor = TextProcessor()

        text = "&lt;script&gt;alert('xss')&lt;/script&gt;"
        result = processor.sanitize_text(text)

        assert "&lt;" not in result
        assert "&gt;" not in result

    def test_sanitize_normalizes_whitespace(self):
        """Test whitespace normalization."""
        processor = TextProcessor()

        text = "Hello    World   with    spaces"
        result = processor.sanitize_text(text)

        assert "    " not in result
        assert result == "Hello World with spaces"

    def test_sanitize_reduces_punctuation(self):
        """Test that excessive punctuation is reduced."""
        processor = TextProcessor()

        text = "Hello!!! World??? Test..."
        result = processor.sanitize_text(text)

        assert "!!!" not in result
        assert "???" not in result
        assert "..." not in result

    def test_sanitize_trims_whitespace(self):
        """Test that leading/trailing whitespace is trimmed."""
        processor = TextProcessor()

        text = "   Hello World   "
        result = processor.sanitize_text(text)

        assert result == "Hello World"

    def test_normalize_empty_text(self):
        """Test normalization of empty text."""
        processor = TextProcessor()

        result = processor.normalize_text("")
        assert result == ""

    def test_normalize_converts_to_lowercase(self):
        """Test that text is converted to lowercase."""
        processor = TextProcessor()

        text = "HELLO World TEST"
        result = processor.normalize_text(text)

        assert result == "hello world test"

    def test_normalize_removes_extra_whitespace(self):
        """Test whitespace normalization."""
        processor = TextProcessor()

        text = "Hello    World"
        result = processor.normalize_text(text)

        assert result == "hello world"

    def test_extract_keywords_empty_text(self):
        """Test keyword extraction from empty text."""
        processor = TextProcessor()

        result = processor.extract_keywords("")
        assert result == []

    def test_extract_keywords_filters_stop_words(self):
        """Test that stop words are filtered."""
        processor = TextProcessor()

        text = "The quick brown fox jumps over the lazy dog"
        keywords = processor.extract_keywords(text)

        assert "the" not in keywords
        # 'over' may not be in stop words list - check for common ones
        assert "quick" in keywords
        assert "brown" in keywords

    def test_extract_keywords_filters_short_words(self):
        """Test that short words are filtered."""
        processor = TextProcessor()

        text = "I am a test of the system"
        keywords = processor.extract_keywords(text)

        # Words <= 2 characters should be filtered
        assert "am" not in keywords
        assert "of" not in keywords

    def test_detect_encoding_empty_text(self):
        """Test encoding detection on empty text."""
        processor = TextProcessor()

        result = processor.detect_encoding_attempts("")
        assert result == []

    def test_detect_url_encoding(self):
        """Test detection of URL encoding."""
        processor = TextProcessor()

        text = "Hello%20World%3Cscript%3E"
        patterns = processor.detect_encoding_attempts(text)

        assert len(patterns) > 0
        assert any("%20" in p for p in patterns)

    def test_detect_unicode_escapes(self):
        """Test detection of unicode escapes."""
        processor = TextProcessor()

        text = "Hello\\u0041\\u0042\\u0043"
        patterns = processor.detect_encoding_attempts(text)

        assert len(patterns) > 0

    def test_detect_hex_escapes(self):
        """Test detection of hex escapes."""
        processor = TextProcessor()

        text = "Hello\\x41\\x42\\x43"
        patterns = processor.detect_encoding_attempts(text)

        assert len(patterns) > 0

    def test_detect_html_entities(self):
        """Test detection of HTML entities."""
        processor = TextProcessor()

        text = "Hello&nbsp;World&amp;Test"
        patterns = processor.detect_encoding_attempts(text)

        assert len(patterns) > 0

    def test_calculate_complexity_empty_text(self):
        """Test complexity calculation for empty text."""
        processor = TextProcessor()

        metrics = processor.calculate_text_complexity("")

        assert metrics["length"] == 0
        assert metrics["word_count"] == 0
        assert metrics["avg_word_length"] == 0

    def test_calculate_complexity_basic(self):
        """Test basic complexity calculation."""
        processor = TextProcessor()

        text = "Hello World Test"
        metrics = processor.calculate_text_complexity(text)

        assert metrics["length"] == 16
        assert metrics["word_count"] == 3
        assert metrics["avg_word_length"] > 0

    def test_calculate_complexity_unique_words(self):
        """Test unique words ratio calculation."""
        processor = TextProcessor()

        # All unique words
        text1 = "one two three four"
        metrics1 = processor.calculate_text_complexity(text1)
        assert metrics1["unique_words_ratio"] == 1.0

        # Repeated words
        text2 = "one one one one"
        metrics2 = processor.calculate_text_complexity(text2)
        assert metrics2["unique_words_ratio"] == 0.25

    def test_calculate_complexity_special_chars(self):
        """Test special character ratio calculation."""
        processor = TextProcessor()

        # No special chars
        text1 = "Hello World"
        metrics1 = processor.calculate_text_complexity(text1)

        # With special chars
        text2 = "Hello!!! World??? @#$%"
        metrics2 = processor.calculate_text_complexity(text2)

        assert metrics2["special_char_ratio"] > metrics1["special_char_ratio"]

    def test_extract_sentences_empty_text(self):
        """Test sentence extraction from empty text."""
        processor = TextProcessor()

        result = processor.extract_sentences("")
        assert result == []

    def test_extract_sentences_basic(self):
        """Test basic sentence extraction."""
        processor = TextProcessor()

        text = "Hello world. How are you? I am fine!"
        sentences = processor.extract_sentences(text)

        assert len(sentences) == 3
        assert "Hello world" in sentences

    def test_extract_sentences_strips_whitespace(self):
        """Test that sentences are stripped of whitespace."""
        processor = TextProcessor()

        text = "  Hello world.   How are you?  "
        sentences = processor.extract_sentences(text)

        for sentence in sentences:
            assert sentence == sentence.strip()

    def test_detect_language_patterns_empty(self):
        """Test language pattern detection on empty text."""
        processor = TextProcessor()

        result = processor.detect_language_patterns("")
        assert result == {}

    def test_detect_language_patterns_uppercase(self):
        """Test detection of uppercase words."""
        processor = TextProcessor()

        text = "Hello WORLD TEST uppercase"
        patterns = processor.detect_language_patterns(text)

        assert patterns["uppercase_words"] >= 2

    def test_detect_language_patterns_repeated_chars(self):
        """Test detection of repeated characters."""
        processor = TextProcessor()

        text = "Hellooooo Worrrrrld"
        patterns = processor.detect_language_patterns(text)

        assert patterns["repeated_chars"] >= 2

    def test_detect_language_patterns_urls(self):
        """Test detection of URLs."""
        processor = TextProcessor()

        text = "Visit https://example.com or http://test.org"
        patterns = processor.detect_language_patterns(text)

        assert patterns["urls"] == 2

    def test_detect_language_patterns_emails(self):
        """Test detection of emails."""
        processor = TextProcessor()

        text = "Contact us at test@example.com or info@test.org"
        patterns = processor.detect_language_patterns(text)

        assert patterns["emails"] == 2

    def test_detect_language_patterns_punctuation(self):
        """Test detection of punctuation clusters."""
        processor = TextProcessor()

        text = "What?! Really!! Are you sure??"
        patterns = processor.detect_language_patterns(text)

        assert patterns["punctuation_clusters"] >= 2

    def test_clean_for_analysis_empty(self):
        """Test clean for analysis on empty text."""
        processor = TextProcessor()

        result = processor.clean_for_analysis("")
        assert result == ""

    def test_clean_for_analysis_combined(self):
        """Test combined cleaning for analysis."""
        processor = TextProcessor()

        text = "<p>  HELLO   World!!!  </p>"
        result = processor.clean_for_analysis(text)

        # Should be sanitized, normalized, and cleaned
        assert "<p>" not in result
        assert result == result.lower()
        assert "  " not in result


class TestTextProcessorEdgeCases:
    """Edge case tests for TextProcessor."""

    def test_very_long_text(self):
        """Test handling of very long text."""
        processor = TextProcessor()

        long_text = "word " * 10000
        result = processor.sanitize_text(long_text)

        assert len(result) > 0

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        processor = TextProcessor()

        text = "Hello 世界 مرحبا שלום"
        result = processor.sanitize_text(text)

        assert len(result) > 0

    def test_mixed_content(self):
        """Test handling of mixed content types."""
        processor = TextProcessor()

        text = """
        <html>
        Hello World!!!
        user@example.com
        https://test.com
        </html>
        """
        result = processor.clean_for_analysis(text)

        assert "<html>" not in result
        assert len(result) > 0
