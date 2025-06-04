"""
Customer and Subscription models
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Customer(BaseModel):
    """Customer model"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    stripe_id: str
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    subscription_tier: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Subscription(BaseModel):
    """Subscription model"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    stripe_id: str
    customer_id: str
    tier: str  # basic, pro, enterprise
    status: str  # active, trialing, past_due, cancelled
    billing_cycle: str = "monthly"  # monthly or annual
    current_period_start: datetime = Field(default_factory=datetime.now)
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)

    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in ["active", "trialing"]

    def is_trial(self) -> bool:
        """Check if subscription is in trial"""
        return (
            self.status == "trialing"
            and self.trial_end
            and self.trial_end > datetime.now()
        )

    def days_until_trial_end(self) -> Optional[int]:
        """Get days until trial ends"""
        if self.is_trial() and self.trial_end:
            delta = self.trial_end - datetime.now()
            return delta.days
        return None
