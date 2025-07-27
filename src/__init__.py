"""
LLM Safety Layer - Educational Implementation

This package provides a basic safety layer for LLM interactions.
For educational purposes only.
"""

from .core.safety_layer import SafetyLayer
from .core.config import SafetyConfig
from .models.safety_score import SafetyScore
from .models.safety_report import SafetyReport

__version__ = "0.1.0"
__all__ = ["SafetyLayer", "SafetyConfig", "SafetyScore", "SafetyReport"] 