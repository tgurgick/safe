"""
Rate Limiter Implementation

Manages rate limiting for user requests.
"""

import time
from typing import Dict, Any
from collections import defaultdict


class RateLimiter:
    """Simple rate limiter for user requests."""
    
    def __init__(self, requests_per_minute: int = 10):
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.user_requests = defaultdict(list)
        self.stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'active_users': 0
        }
    
    def check_rate_limit(self, user_id: str) -> Dict[str, Any]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with rate limit status
        """
        current_time = time.time()
        
        # Clean old requests (older than 1 minute)
        self._clean_old_requests(user_id, current_time)
        
        # Get user's recent requests
        user_requests = self.user_requests[user_id]
        
        # Check if user has exceeded rate limit
        if len(user_requests) >= self.requests_per_minute:
            # Calculate time until next allowed request
            oldest_request = min(user_requests)
            reset_time = int(60 - (current_time - oldest_request))
            
            self.stats['rate_limited_requests'] += 1
            
            return {
                'allowed': False,
                'reset_time': max(0, reset_time),
                'requests_remaining': 0,
                'limit': self.requests_per_minute
            }
        
        # Add current request
        user_requests.append(current_time)
        self.stats['total_requests'] += 1
        
        # Update active users count
        self.stats['active_users'] = len(self.user_requests)
        
        return {
            'allowed': True,
            'reset_time': 0,
            'requests_remaining': self.requests_per_minute - len(user_requests),
            'limit': self.requests_per_minute
        }
    
    def _clean_old_requests(self, user_id: str, current_time: float):
        """Remove requests older than 1 minute."""
        if user_id in self.user_requests:
            # Keep only requests from the last minute
            cutoff_time = current_time - 60
            self.user_requests[user_id] = [
                req_time for req_time in self.user_requests[user_id]
                if req_time > cutoff_time
            ]
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit statistics for a specific user."""
        current_time = time.time()
        self._clean_old_requests(user_id, current_time)
        
        user_requests = self.user_requests[user_id]
        
        return {
            'requests_in_window': len(user_requests),
            'requests_remaining': max(0, self.requests_per_minute - len(user_requests)),
            'limit': self.requests_per_minute,
            'window_seconds': 60,
            'oldest_request': min(user_requests) if user_requests else None,
            'newest_request': max(user_requests) if user_requests else None
        }
    
    def reset_user_limit(self, user_id: str):
        """Reset rate limit for a specific user."""
        if user_id in self.user_requests:
            del self.user_requests[user_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall rate limiter statistics."""
        current_time = time.time()
        
        # Clean all old requests
        for user_id in list(self.user_requests.keys()):
            self._clean_old_requests(user_id, current_time)
        
        # Remove empty user entries
        self.user_requests = {
            user_id: requests for user_id, requests in self.user_requests.items()
            if requests
        }
        
        return {
            'total_requests': self.stats['total_requests'],
            'rate_limited_requests': self.stats['rate_limited_requests'],
            'active_users': len(self.user_requests),
            'requests_per_minute': self.requests_per_minute,
            'rate_limit_hit_rate': (
                self.stats['rate_limited_requests'] / max(1, self.stats['total_requests'])
            )
        }
    
    def reset_stats(self):
        """Reset rate limiter statistics."""
        self.stats = {
            'total_requests': 0,
            'rate_limited_requests': 0,
            'active_users': 0
        }
        self.user_requests.clear() 