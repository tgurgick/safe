"""
Text Processing Utilities

Handles text sanitization and processing for safety checks.
"""

import re
import html
from typing import List, Set, Dict


class TextProcessor:
    """Text processing utilities for safety layer."""

    def __init__(self):
        """Initialize text processor."""
        # Patterns for text cleaning
        self.html_patterns = [
            r"<[^>]+>",  # HTML tags
            r"&[a-zA-Z]+;",  # HTML entities
            r"&#[0-9]+;",  # Numeric HTML entities
        ]

        # Compile patterns for efficiency
        self.compiled_html_patterns = [re.compile(pattern) for pattern in self.html_patterns]

        # Common encoding patterns
        self.encoding_patterns = [
            r"%[0-9A-Fa-f]{2}",  # URL encoding
            r"\\u[0-9A-Fa-f]{4}",  # Unicode escape
            r"\\x[0-9A-Fa-f]{2}",  # Hex escape
        ]

        self.compiled_encoding_patterns = [
            re.compile(pattern) for pattern in self.encoding_patterns
        ]

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing potentially harmful content.

        Args:
            text: Raw text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Decode HTML entities
        sanitized = html.unescape(text)

        # Remove HTML tags
        for pattern in self.compiled_html_patterns:
            sanitized = pattern.sub("", sanitized)

        # Normalize whitespace
        sanitized = re.sub(r"\s+", " ", sanitized)

        # Remove excessive punctuation
        sanitized = re.sub(r"[!]{2,}", "!", sanitized)
        sanitized = re.sub(r"[?]{2,}", "?", sanitized)
        sanitized = re.sub(r"[.]{2,}", ".", sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        return sanitized

    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent processing.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        if not text:
            return ""

        # Convert to lowercase
        normalized = text.lower()

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        if not text:
            return []

        # Normalize text
        normalized = self.normalize_text(text)

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        # Split into words and filter
        words = re.findall(r"\b[a-zA-Z]+\b", normalized)
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords

    def detect_encoding_attempts(self, text: str) -> List[str]:
        """
        Detect potential encoding attempts in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected encoding patterns
        """
        if not text:
            return []

        detected_patterns = []

        # Check for URL encoding
        url_encoded = re.findall(r"%[0-9A-Fa-f]{2}", text)
        if url_encoded:
            detected_patterns.extend(url_encoded)

        # Check for Unicode escapes
        unicode_escapes = re.findall(r"\\u[0-9A-Fa-f]{4}", text)
        if unicode_escapes:
            detected_patterns.extend(unicode_escapes)

        # Check for hex escapes
        hex_escapes = re.findall(r"\\x[0-9A-Fa-f]{2}", text)
        if hex_escapes:
            detected_patterns.extend(hex_escapes)

        # Check for HTML entities
        html_entities = re.findall(r"&[a-zA-Z]+;", text)
        if html_entities:
            detected_patterns.extend(html_entities)

        return detected_patterns

    def calculate_text_complexity(self, text: str) -> Dict[str, float]:
        """
        Calculate various complexity metrics for text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with complexity metrics
        """
        if not text:
            return {
                "length": 0,
                "word_count": 0,
                "avg_word_length": 0,
                "unique_words_ratio": 0,
                "special_char_ratio": 0,
            }

        # Basic metrics
        length = len(text)
        words = text.split()
        word_count = len(words)

        # Average word length
        if word_count > 0:
            total_word_length = sum(len(word) for word in words)
            avg_word_length = total_word_length / word_count
        else:
            avg_word_length = 0

        # Unique words ratio
        unique_words = set(words)
        unique_words_ratio = len(unique_words) / max(1, word_count)

        # Special character ratio
        special_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
        special_char_ratio = special_chars / max(1, length)

        return {
            "length": length,
            "word_count": word_count,
            "avg_word_length": avg_word_length,
            "unique_words_ratio": unique_words_ratio,
            "special_char_ratio": special_char_ratio,
        }

    def extract_sentences(self, text: str) -> List[str]:
        """
        Extract sentences from text.

        Args:
            text: Text to extract sentences from

        Returns:
            List of sentences
        """
        if not text:
            return []

        # Simple sentence splitting (can be improved with NLP)
        sentences = re.split(r"[.!?]+", text)

        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)

        return cleaned_sentences

    def detect_language_patterns(self, text: str) -> Dict[str, int]:
        """
        Detect various language patterns in text.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with pattern counts
        """
        if not text:
            return {}

        patterns = {
            "uppercase_words": len(re.findall(r"\b[A-Z]{2,}\b", text)),
            "repeated_chars": len(re.findall(r"(.)\1{2,}", text)),
            "numbers": len(re.findall(r"\d+", text)),
            "urls": len(re.findall(r"https?://\S+", text)),
            "emails": len(re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text)),
            "punctuation_clusters": len(re.findall(r"[!?]{2,}", text)),
        }

        return patterns

    def clean_for_analysis(self, text: str) -> str:
        """
        Clean text specifically for safety analysis.

        Args:
            text: Text to clean

        Returns:
            Cleaned text suitable for analysis
        """
        if not text:
            return ""

        # Basic sanitization
        cleaned = self.sanitize_text(text)

        # Normalize
        cleaned = self.normalize_text(cleaned)

        # Remove excessive whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip()
