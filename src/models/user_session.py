"""
User Session Model

Represents user session information for safety layer tracking.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class UserSession(BaseModel):
    """User session information for safety tracking."""

    # Basic session info
    user_id: str = Field(description="Unique user identifier")
    session_id: str = Field(description="Unique session identifier")

    # Session metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Session creation timestamp"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )

    # Safety tracking
    total_requests: int = Field(default=0, description="Total number of requests in this session")
    flagged_requests: int = Field(
        default=0, description="Number of requests flagged for safety concerns"
    )
    blocked_requests: int = Field(default=0, description="Number of requests blocked")

    # Rate limiting
    rate_limit_exceeded: bool = Field(
        default=False, description="Whether user has exceeded rate limits"
    )
    rate_limit_reset_time: Optional[int] = Field(
        default=None, description="Time until rate limit resets (seconds)"
    )

    # Safety preferences
    safety_level: str = Field(default="moderate", description="User's preferred safety level")
    custom_rules: Dict[str, Any] = Field(
        default_factory=dict, description="User-specific safety rules"
    )

    # Session state
    is_active: bool = Field(default=True, description="Whether session is currently active")

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def increment_requests(self):
        """Increment request counter."""
        self.total_requests += 1
        self.update_activity()

    def flag_request(self):
        """Flag a request for safety concerns."""
        self.flagged_requests += 1
        self.update_activity()

    def block_request(self):
        """Block a request."""
        self.blocked_requests += 1
        self.update_activity()

    def get_safety_stats(self) -> Dict[str, Any]:
        """Get safety statistics for this session."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "total_requests": self.total_requests,
            "flagged_requests": self.flagged_requests,
            "blocked_requests": self.blocked_requests,
            "flag_rate": self.flagged_requests / max(1, self.total_requests),
            "block_rate": self.blocked_requests / max(1, self.total_requests),
            "session_duration": (self.last_activity - self.created_at).total_seconds(),
            "is_active": self.is_active,
            "rate_limit_exceeded": self.rate_limit_exceeded,
        }

    def is_expired(self, max_duration_hours: int = 24) -> bool:
        """Check if session has expired."""
        duration = (datetime.now() - self.last_activity).total_seconds()
        return duration > (max_duration_hours * 3600)

    @classmethod
    def create_session(cls, user_id: str, safety_level: str = "moderate") -> "UserSession":
        """Create a new user session."""
        import uuid

        return cls(user_id=user_id, session_id=str(uuid.uuid4()), safety_level=safety_level)
