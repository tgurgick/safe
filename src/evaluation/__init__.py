"""
Evaluation framework for the LLM Safety Layer.

Provides tools for measuring filter accuracy and collecting human feedback.
"""

from .metrics import EvaluationMetrics, FilterEvaluator
from .datasets import EvaluationDataset, LabeledExample, create_sample_dataset
from .feedback import HumanFeedbackCollector, FeedbackSession, FeedbackType

__all__ = [
    "EvaluationMetrics",
    "FilterEvaluator",
    "EvaluationDataset",
    "LabeledExample",
    "create_sample_dataset",
    "HumanFeedbackCollector",
    "FeedbackSession",
    "FeedbackType",
]
