"""API Key models for authentication and usage tracking."""

import secrets
import string
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class APIKey(BaseModel):
    """API Key model for customer authentication."""

    key: str = Field(default_factory=lambda: APIKey.generate_key())
    customer_id: str
    subscription_id: str
    tier: str
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    is_active: bool = True

    # Rate limiting configuration based on tier
    rate_limits: dict = Field(default_factory=dict)

    @staticmethod
    def generate_key(prefix: str = "sk_live_") -> str:
        """Generate a secure API key."""
        # Generate 32 character random string
        alphabet = string.ascii_letters + string.digits
        random_part = "".join(secrets.choice(alphabet) for _ in range(32))
        return f"{prefix}{random_part}"

    def get_rate_limits(self) -> dict:
        """Get rate limits based on subscription tier."""
        tier_limits = {
            "basic": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "requests_per_day": 1000,
                "max_queries_per_month": 10000,
            },
            "pro": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "requests_per_day": 10000,
                "max_queries_per_month": 100000,
            },
            "enterprise": {
                "requests_per_minute": 300,
                "requests_per_hour": 10000,
                "requests_per_day": 100000,
                "max_queries_per_month": 1000000,
            },
        }
        return tier_limits.get(self.tier, tier_limits["basic"])

    def is_valid(self) -> bool:
        """Check if API key is still valid."""
        return self.is_active


class APIKeyUsage(BaseModel):
    """Track API key usage for billing and rate limiting."""

    api_key: str
    customer_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    endpoint: str
    method: str = "GET"
    status_code: int
    response_time_ms: float
    tokens_used: Optional[int] = None
    cost: Optional[float] = None

    # Rate limiting tracking
    minute_bucket: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M")
    )
    hour_bucket: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H")
    )
    day_bucket: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

    def calculate_cost(self) -> float:
        """Calculate cost based on usage."""
        if self.cost:
            return self.cost

        # Base cost per request (in dollars)
        base_cost = 0.001  # $0.001 per request

        # Additional cost for tokens if applicable
        token_cost = 0
        if self.tokens_used:
            token_cost = self.tokens_used * 0.00002  # $0.02 per 1000 tokens

        return base_cost + token_cost
