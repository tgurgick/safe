"""
FastAPI REST API for the LLM Safety Layer.

This module provides HTTP endpoints for safety validation and monitoring.
"""

from .app import create_app

__all__ = ["create_app"]
