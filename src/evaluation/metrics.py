"""
Evaluation metrics for measuring filter performance.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime


class PredictionResult(Enum):
    """Classification of a prediction outcome."""
    TRUE_POSITIVE = "tp"   # Correctly identified unsafe
    TRUE_NEGATIVE = "tn"   # Correctly identified safe
    FALSE_POSITIVE = "fp"  # Incorrectly flagged as unsafe
    FALSE_NEGATIVE = "fn"  # Missed unsafe content


@dataclass
class EvaluationMetrics:
    """Metrics for evaluating filter performance."""

    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # Detailed tracking
    fp_examples: List[Dict[str, Any]] = field(default_factory=list)
    fn_examples: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Total number of predictions."""
        return self.true_positives + self.true_negatives + self.false_positives + self.false_negatives

    @property
    def accuracy(self) -> float:
        """Overall accuracy."""
        if self.total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / self.total

    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP) - How many flagged items were actually unsafe."""
        denominator = self.true_positives + self.false_positives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator

    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN) - How many unsafe items were caught."""
        denominator = self.true_positives + self.false_negatives
        if denominator == 0:
            return 0.0
        return self.true_positives / denominator

    @property
    def f1_score(self) -> float:
        """F1 Score: Harmonic mean of precision and recall."""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)

    @property
    def false_positive_rate(self) -> float:
        """FPR: FP / (FP + TN) - Rate of safe content incorrectly flagged."""
        denominator = self.false_positives + self.true_negatives
        if denominator == 0:
            return 0.0
        return self.false_positives / denominator

    @property
    def false_negative_rate(self) -> float:
        """FNR: FN / (FN + TP) - Rate of unsafe content missed."""
        denominator = self.false_negatives + self.true_positives
        if denominator == 0:
            return 0.0
        return self.false_negatives / denominator

    def record(self, result: PredictionResult, example: Optional[Dict[str, Any]] = None):
        """Record a prediction result."""
        if result == PredictionResult.TRUE_POSITIVE:
            self.true_positives += 1
        elif result == PredictionResult.TRUE_NEGATIVE:
            self.true_negatives += 1
        elif result == PredictionResult.FALSE_POSITIVE:
            self.false_positives += 1
            if example:
                self.fp_examples.append(example)
        elif result == PredictionResult.FALSE_NEGATIVE:
            self.false_negatives += 1
            if example:
                self.fn_examples.append(example)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_samples": self.total,
            "true_positives": self.true_positives,
            "true_negatives": self.true_negatives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
        }

    def summary(self) -> str:
        """Generate a human-readable summary."""
        return f"""
Evaluation Results ({self.total} samples)
{'='*50}
Confusion Matrix:
  Predicted Unsafe | Predicted Safe
  TP: {self.true_positives:4d}         | FN: {self.false_negatives:4d}    (Actual Unsafe)
  FP: {self.false_positives:4d}         | TN: {self.true_negatives:4d}    (Actual Safe)

Performance Metrics:
  Accuracy:  {self.accuracy:.2%}
  Precision: {self.precision:.2%}  (of flagged, how many were truly unsafe)
  Recall:    {self.recall:.2%}  (of unsafe, how many were caught)
  F1 Score:  {self.f1_score:.2%}

Error Rates:
  False Positive Rate: {self.false_positive_rate:.2%} (safe content incorrectly blocked)
  False Negative Rate: {self.false_negative_rate:.2%} (unsafe content missed)
"""


class FilterEvaluator:
    """Evaluates filter performance against labeled datasets."""

    def __init__(self, filter_component, threshold: float = 0.5):
        """
        Initialize evaluator.

        Args:
            filter_component: The filter to evaluate (ContentFilter, BiasDetector, etc.)
            threshold: Score threshold for classifying as "unsafe"
        """
        self.filter = filter_component
        self.threshold = threshold
        self.metrics: Dict[str, EvaluationMetrics] = {}

    def evaluate(
        self,
        dataset: "EvaluationDataset",
        category: Optional[str] = None,
    ) -> EvaluationMetrics:
        """
        Evaluate filter against a labeled dataset.

        Args:
            dataset: Labeled evaluation dataset
            category: Optional category to evaluate (e.g., "violence", "hate_speech")

        Returns:
            EvaluationMetrics with results
        """
        metrics = EvaluationMetrics()

        for example in dataset.examples:
            # Skip if category specified and doesn't match
            if category and example.category != category:
                continue

            # Get filter prediction
            prediction = self._get_prediction(example.text, category)
            predicted_unsafe = prediction > self.threshold

            # Compare to ground truth
            actual_unsafe = example.is_unsafe

            # Record result
            if predicted_unsafe and actual_unsafe:
                result = PredictionResult.TRUE_POSITIVE
            elif not predicted_unsafe and not actual_unsafe:
                result = PredictionResult.TRUE_NEGATIVE
            elif predicted_unsafe and not actual_unsafe:
                result = PredictionResult.FALSE_POSITIVE
            else:
                result = PredictionResult.FALSE_NEGATIVE

            metrics.record(result, {
                "text": example.text,
                "category": example.category,
                "expected": actual_unsafe,
                "predicted": predicted_unsafe,
                "score": prediction,
            })

        # Store metrics by category
        key = category or "overall"
        self.metrics[key] = metrics

        return metrics

    def _get_prediction(self, text: str, category: Optional[str] = None) -> float:
        """Get prediction score from filter."""
        # Handle different filter types
        if hasattr(self.filter, 'analyze_content'):
            # ContentFilter
            score = self.filter.analyze_content(text)
            if category == "violence":
                return score.violence_score
            elif category == "hate_speech":
                return score.hate_speech_score
            elif category == "bias":
                return score.bias_score
            elif category == "privacy":
                return score.privacy_score
            else:
                return score.overall_score
        elif hasattr(self.filter, 'detect_injection'):
            # PromptInjectionDetector
            analysis = self.filter.analyze_injection_attempt(text)
            return analysis["injection_score"]
        elif hasattr(self.filter, 'detect_bias'):
            # BiasDetector
            result = self.filter.detect_bias(text)
            return result["bias_score"]
        elif hasattr(self.filter, 'protect_privacy'):
            # PrivacyProtector
            result = self.filter.protect_privacy(text)
            return result["privacy_score"]
        else:
            raise ValueError(f"Unknown filter type: {type(self.filter)}")

    def evaluate_all_categories(self, dataset: "EvaluationDataset") -> Dict[str, EvaluationMetrics]:
        """Evaluate all categories in the dataset."""
        categories = dataset.get_categories()

        for category in categories:
            self.evaluate(dataset, category)

        # Also compute overall
        self.evaluate(dataset, None)

        return self.metrics

    def generate_report(self) -> str:
        """Generate a full evaluation report."""
        report = []
        report.append("=" * 60)
        report.append("FILTER EVALUATION REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 60)

        for category, metrics in self.metrics.items():
            report.append(f"\n--- {category.upper()} ---")
            report.append(metrics.summary())

        return "\n".join(report)

    def export_errors(self, filepath: str):
        """Export false positives and false negatives for review."""
        errors = {
            "false_positives": [],
            "false_negatives": [],
        }

        for category, metrics in self.metrics.items():
            for fp in metrics.fp_examples:
                fp["evaluation_category"] = category
                errors["false_positives"].append(fp)
            for fn in metrics.fn_examples:
                fn["evaluation_category"] = category
                errors["false_negatives"].append(fn)

        with open(filepath, "w") as f:
            json.dump(errors, f, indent=2)
