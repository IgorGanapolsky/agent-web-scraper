"""Customer and subscription models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """Customer model for subscription management."""

    id: str  # Internal ID
    stripe_customer_id: str
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Subscription details
    subscription: Optional["Subscription"] = None

    # Trial management
    trial_ends_at: Optional[datetime] = None
    converted_from_trial: bool = False

    # Communication preferences
    email_notifications: bool = True
    weekly_digest: bool = True

    def is_on_trial(self) -> bool:
        """Check if customer is currently on trial."""
        if not self.trial_ends_at:
            return False
        return datetime.now() < self.trial_ends_at

    def days_until_trial_ends(self) -> Optional[int]:
        """Calculate days until trial ends."""
        if not self.trial_ends_at:
            return None
        delta = self.trial_ends_at - datetime.now()
        return max(0, delta.days)


class Subscription(BaseModel):
    """Subscription model."""

    id: str  # Internal ID
    stripe_subscription_id: str
    customer_id: str

    # Pricing details
    tier: str  # basic, pro, enterprise
    interval: str = "month"  # month or year
    amount: float  # Monthly amount (even for annual)

    # Status
    status: str  # active, canceled, past_due, etc.
    current_period_start: datetime
    current_period_end: datetime

    # Billing
    stripe_payment_method_id: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None

    # Usage tracking
    queries_this_month: int = 0
    api_calls_this_month: int = 0

    # Cancellation
    canceled_at: Optional[datetime] = None
    cancel_at_period_end: bool = False

    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == "active"

    def days_until_renewal(self) -> int:
        """Calculate days until next renewal."""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.now()
        return max(0, delta.days)

    def get_monthly_amount(self) -> float:
        """Get monthly amount (accounting for annual plans)."""
        if self.interval == "year":
            return self.amount / 12
        return self.amount

    def get_query_limit(self) -> int:
        """Get monthly query limit based on tier."""
        limits = {"basic": 10000, "pro": 100000, "enterprise": 1000000}
        return limits.get(self.tier, 10000)

    def usage_percentage(self) -> float:
        """Calculate usage percentage for current period."""
        limit = self.get_query_limit()
        if limit == 0:
            return 0
        return (self.queries_this_month / limit) * 100
