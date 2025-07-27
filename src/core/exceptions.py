"""
Custom exceptions for the safety layer.
"""


class SafetyLayerError(Exception):
    """Base exception for safety layer errors."""
    pass


class ValidationError(SafetyLayerError):
    """Raised when input validation fails."""
    pass


class FilterError(SafetyLayerError):
    """Raised when content filtering fails."""
    pass


class RateLimitError(SafetyLayerError):
    """Raised when rate limit is exceeded."""
    pass


class ConfigurationError(SafetyLayerError):
    """Raised when configuration is invalid."""
    pass


class ModelError(SafetyLayerError):
    """Raised when ML model operations fail."""
    pass


class PrivacyError(SafetyLayerError):
    """Raised when privacy protection fails."""
    pass 