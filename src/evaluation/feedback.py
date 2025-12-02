"""
Human feedback collection for filter improvement.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import uuid


class FeedbackType(Enum):
    """Types of human feedback."""

    CORRECT = "correct"  # Filter made correct decision
    FALSE_POSITIVE = "false_positive"  # Incorrectly flagged as unsafe
    FALSE_NEGATIVE = "false_negative"  # Missed unsafe content
    UNCERTAIN = "uncertain"  # Human reviewer is unsure


@dataclass
class FeedbackItem:
    """A single piece of human feedback."""

    id: str
    text: str
    filter_prediction: bool  # What the filter predicted (True=unsafe)
    filter_score: float  # The filter's confidence score
    filter_category: str  # Category being evaluated

    # Human feedback
    human_judgment: Optional[FeedbackType] = None
    correct_label: Optional[bool] = None  # What the label should be
    severity: Optional[str] = None  # "low", "medium", "high"
    notes: Optional[str] = None
    reviewer_id: Optional[str] = None

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "text": self.text,
            "filter_prediction": self.filter_prediction,
            "filter_score": self.filter_score,
            "filter_category": self.filter_category,
            "human_judgment": self.human_judgment.value if self.human_judgment else None,
            "correct_label": self.correct_label,
            "severity": self.severity,
            "notes": self.notes,
            "reviewer_id": self.reviewer_id,
            "timestamp": self.timestamp,
        }


class FeedbackSession:
    """A session for collecting human feedback."""

    def __init__(self, session_id: Optional[str] = None, reviewer_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.reviewer_id = reviewer_id
        self.items: List[FeedbackItem] = []
        self.start_time = datetime.now().isoformat()
        self.end_time: Optional[str] = None

    def add_for_review(
        self,
        text: str,
        filter_prediction: bool,
        filter_score: float,
        filter_category: str,
    ) -> FeedbackItem:
        """Add an item for human review."""
        item = FeedbackItem(
            id=f"{self.session_id}-{len(self.items)}",
            text=text,
            filter_prediction=filter_prediction,
            filter_score=filter_score,
            filter_category=filter_category,
            reviewer_id=self.reviewer_id,
        )
        self.items.append(item)
        return item

    def submit_feedback(
        self,
        item_id: str,
        judgment: FeedbackType,
        correct_label: Optional[bool] = None,
        severity: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """Submit feedback for an item."""
        for item in self.items:
            if item.id == item_id:
                item.human_judgment = judgment
                item.correct_label = correct_label
                item.severity = severity
                item.notes = notes
                return
        raise ValueError(f"Item {item_id} not found")

    def get_pending(self) -> List[FeedbackItem]:
        """Get items pending review."""
        return [item for item in self.items if item.human_judgment is None]

    def get_completed(self) -> List[FeedbackItem]:
        """Get completed reviews."""
        return [item for item in self.items if item.human_judgment is not None]

    def complete(self):
        """Mark session as complete."""
        self.end_time = datetime.now().isoformat()

    def summary(self) -> Dict[str, Any]:
        """Get session summary."""
        completed = self.get_completed()
        judgments = {}
        for item in completed:
            if item.human_judgment:
                key = item.human_judgment.value
                judgments[key] = judgments.get(key, 0) + 1

        return {
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "total_items": len(self.items),
            "completed": len(completed),
            "pending": len(self.get_pending()),
            "judgments": judgments,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "reviewer_id": self.reviewer_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "items": [item.to_dict() for item in self.items],
        }

    def save(self, filepath: str):
        """Save session to file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "FeedbackSession":
        """Load session from file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        session = cls(
            session_id=data["session_id"],
            reviewer_id=data.get("reviewer_id"),
        )
        session.start_time = data["start_time"]
        session.end_time = data.get("end_time")

        for item_data in data.get("items", []):
            item = FeedbackItem(
                id=item_data["id"],
                text=item_data["text"],
                filter_prediction=item_data["filter_prediction"],
                filter_score=item_data["filter_score"],
                filter_category=item_data["filter_category"],
                reviewer_id=item_data.get("reviewer_id"),
                timestamp=item_data.get("timestamp", ""),
            )
            if item_data.get("human_judgment"):
                item.human_judgment = FeedbackType(item_data["human_judgment"])
            item.correct_label = item_data.get("correct_label")
            item.severity = item_data.get("severity")
            item.notes = item_data.get("notes")
            session.items.append(item)

        return session


class HumanFeedbackCollector:
    """Collects and manages human feedback across sessions."""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, FeedbackSession] = {}

    def create_session(self, reviewer_id: Optional[str] = None) -> FeedbackSession:
        """Create a new feedback session."""
        session = FeedbackSession(reviewer_id=reviewer_id)
        self.sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[FeedbackSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def aggregate_feedback(self) -> Dict[str, Any]:
        """Aggregate feedback across all sessions."""
        total_items = 0
        total_completed = 0
        all_judgments = {}
        false_positives = []
        false_negatives = []

        for session in self.sessions.values():
            for item in session.items:
                total_items += 1
                if item.human_judgment:
                    total_completed += 1
                    key = item.human_judgment.value
                    all_judgments[key] = all_judgments.get(key, 0) + 1

                    if item.human_judgment == FeedbackType.FALSE_POSITIVE:
                        false_positives.append(item.to_dict())
                    elif item.human_judgment == FeedbackType.FALSE_NEGATIVE:
                        false_negatives.append(item.to_dict())

        # Calculate inter-annotator agreement if multiple reviewers
        reviewers = set()
        for session in self.sessions.values():
            if session.reviewer_id:
                reviewers.add(session.reviewer_id)

        return {
            "total_sessions": len(self.sessions),
            "total_items": total_items,
            "total_completed": total_completed,
            "unique_reviewers": len(reviewers),
            "judgments": all_judgments,
            "false_positive_count": len(false_positives),
            "false_negative_count": len(false_negatives),
            "false_positives": false_positives[:10],  # Sample
            "false_negatives": false_negatives[:10],  # Sample
        }

    def export_training_data(self, filepath: str):
        """Export reviewed items as training data for filter improvement."""
        training_data = []

        for session in self.sessions.values():
            for item in session.get_completed():
                if item.correct_label is not None:
                    training_data.append(
                        {
                            "text": item.text,
                            "is_unsafe": item.correct_label,
                            "category": item.filter_category,
                            "severity": item.severity,
                            "source": "human_feedback",
                            "session_id": session.session_id,
                            "reviewer_id": item.reviewer_id,
                        }
                    )

        with open(filepath, "w") as f:
            json.dump(training_data, f, indent=2)

        return len(training_data)

    def generate_report(self) -> str:
        """Generate a human feedback report."""
        agg = self.aggregate_feedback()

        report = []
        report.append("=" * 60)
        report.append("HUMAN FEEDBACK REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 60)
        report.append(f"\nTotal Sessions: {agg['total_sessions']}")
        report.append(f"Unique Reviewers: {agg['unique_reviewers']}")
        report.append(f"Total Items Reviewed: {agg['total_completed']} / {agg['total_items']}")

        report.append("\nJudgment Distribution:")
        for judgment, count in agg["judgments"].items():
            pct = count / max(agg["total_completed"], 1) * 100
            report.append(f"  {judgment}: {count} ({pct:.1f}%)")

        report.append(f"\nFilter Error Summary:")
        report.append(f"  False Positives: {agg['false_positive_count']}")
        report.append(f"  False Negatives: {agg['false_negative_count']}")

        if agg["false_positives"]:
            report.append("\nSample False Positives (safe content incorrectly blocked):")
            for fp in agg["false_positives"][:3]:
                report.append(f"  - \"{fp['text'][:50]}...\" (score: {fp['filter_score']:.2f})")

        if agg["false_negatives"]:
            report.append("\nSample False Negatives (unsafe content missed):")
            for fn in agg["false_negatives"][:3]:
                report.append(f"  - \"{fn['text'][:50]}...\" (score: {fn['filter_score']:.2f})")

        return "\n".join(report)
