"""
Cost Tracker Module
Tracks API costs, revenue, and business metrics for $300/day target
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.config.logging import get_logger

logger = get_logger(__name__)


class RevenueEvent(BaseModel):
    """Revenue event model"""

    customer_id: str
    amount: float
    tier: str = "pro"
    event_type: str = "subscription"
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @validator("tier")
    def validate_tier(cls, v):
        valid_tiers = ["pilot", "professional", "enterprise", "basic", "pro"]  # Updated for validation strategy
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier: {v}")
        return v

    @validator("customer_id")
    def validate_customer_id(cls, v):
        if not v:
            raise ValueError("Customer ID cannot be empty")
        return v


class CostEvent(BaseModel):
    """Cost event model"""

    service: str
    cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)


class CostTracker:
    """Tracks costs and revenue for business metrics"""

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.revenue_events: list[RevenueEvent] = []
        self.cost_events: list[CostEvent] = []
        self.subscriptions: dict[str, dict] = {}

    def add_revenue_event(self, event_data: dict):
        """Add a revenue event"""
        if isinstance(event_data, dict):
            event = RevenueEvent(**event_data)
        else:
            event = event_data

        self.revenue_events.append(event)
        logger.info(f"Revenue event tracked: ${event.amount} from {event.customer_id}")

        # Track in Sentry if not in test mode
        if not self.test_mode:
            try:
                from app.observability.sentry_config import track_revenue_event

                track_revenue_event(amount=event.amount, customer_id=event.customer_id)
            except ImportError:
                pass

    def add_cost_event(self, service: str, cost: float, metadata: dict | None = None):
        """Add a cost event"""
        event = CostEvent(service=service, cost=cost, metadata=metadata or {})
        self.cost_events.append(event)
        logger.info(f"Cost event tracked: ${cost} for {service}")

        # Special handling for Claude token costs
        if service == "claude_api" and metadata:
            self._track_token_usage(metadata)

    def add_subscription(self, customer_id: str, tier: str, amount: float):
        """Add or update a subscription"""
        self.subscriptions[customer_id] = {
            "tier": tier,
            "amount": amount,
            "created_at": datetime.now(),
        }

        # Also track as revenue event
        self.add_revenue_event(
            {
                "customer_id": customer_id,
                "amount": amount,
                "tier": tier,
                "event_type": "subscription",
            }
        )

    def get_daily_revenue(self, date: Optional[datetime] = None) -> float:
        """Get revenue for a specific day"""
        if date is None:
            date = datetime.now()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        daily_revenue = sum(
            event.amount
            for event in self.revenue_events
            if start_of_day <= event.timestamp < end_of_day
        )

        return daily_revenue

    def get_daily_costs(self, date: Optional[datetime] = None) -> float:
        """Get costs for a specific day"""
        if date is None:
            date = datetime.now()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        daily_costs = sum(
            event.cost
            for event in self.cost_events
            if start_of_day <= event.timestamp < end_of_day
        )

        return daily_costs

    def is_daily_target_met(self, target: float = 300.0) -> bool:
        """Check if daily revenue target is met"""
        return self.get_daily_revenue() >= target

    def calculate_mrr(self) -> float:
        """Calculate Monthly Recurring Revenue"""
        return sum(sub["amount"] for sub in self.subscriptions.values())

    def calculate_ltv(
        self, monthly_revenue: float, churn_rate: float, months: Optional[int] = None
    ) -> float:
        """Calculate Customer Lifetime Value"""
        if churn_rate == 0:
            return monthly_revenue * (months or 24)  # Default to 2 years if no churn

        # LTV = Monthly Revenue / Monthly Churn Rate
        ltv = monthly_revenue / churn_rate

        # Cap at reasonable maximum
        if months:
            ltv = min(ltv, monthly_revenue * months)

        return ltv

    def calculate_growth_rate(self, period_days: int = 30) -> float:
        """Calculate revenue growth rate over period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)

        # Get revenue for start and end periods
        start_revenue = sum(
            event.amount
            for event in self.revenue_events
            if start_date <= event.timestamp < start_date + timedelta(days=1)
        )

        end_revenue = sum(
            event.amount
            for event in self.revenue_events
            if end_date - timedelta(days=1) <= event.timestamp < end_date
        )

        if start_revenue == 0:
            return 100.0 if end_revenue > 0 else 0.0

        growth_rate = ((end_revenue - start_revenue) / start_revenue) * 100
        return growth_rate

    def get_tier_distribution(self) -> dict[str, dict]:
        """Get customer distribution across tiers"""
        tier_data = {}

        for sub_data in self.subscriptions.values():
            tier = sub_data["tier"]
            if tier not in tier_data:
                tier_data[tier] = {
                    "customer_count": 0,
                    "revenue": 0,
                    "average_value": 0,
                }

            tier_data[tier]["customer_count"] += 1
            tier_data[tier]["revenue"] += sub_data["amount"]

        # Calculate percentages and averages
        total_revenue = sum(data["revenue"] for data in tier_data.values())

        for data in tier_data.values():
            data["revenue_share"] = (
                (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
            )
            data["average_value"] = (
                data["revenue"] / data["customer_count"]
                if data["customer_count"] > 0
                else 0
            )

        return tier_data

    def forecast_revenue(
        self, current_mrr: float, growth_rate: float, months: int
    ) -> dict:
        """Forecast revenue based on growth rate"""
        forecast = {}

        for month in range(1, months + 1):
            projected_mrr = current_mrr * ((1 + growth_rate) ** month)
            forecast[f"month_{month}"] = projected_mrr

        return forecast

    def find_target_achievement_month(
        self, current_mrr: float, target_mrr: float, growth_rate: float
    ) -> int:
        """Find when target MRR will be achieved"""
        if current_mrr >= target_mrr:
            return 0

        months = 0
        projected_mrr = current_mrr

        while projected_mrr < target_mrr and months < 36:  # Cap at 3 years
            months += 1
            projected_mrr = current_mrr * ((1 + growth_rate) ** months)

        return months

    def calculate_cac(self, marketing_spend: float, customers_acquired: int) -> float:
        """Calculate Customer Acquisition Cost"""
        if customers_acquired == 0:
            return 0

        return marketing_spend / customers_acquired

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file"""
        metrics = {
            "daily_revenue": self.get_daily_revenue(),
            "daily_costs": self.get_daily_costs(),
            "customer_count": len(self.subscriptions),
            "mrr": self.calculate_mrr(),
            "growth_rate": self.calculate_growth_rate(),
            "tier_distribution": self.get_tier_distribution(),
            "generated_at": datetime.now().isoformat(),
        }

        with open(filepath, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")

    def get_dashboard_metrics(self) -> dict:
        """Get real-time metrics for dashboard"""
        current_mrr = self.calculate_mrr()
        daily_revenue = self.get_daily_revenue()
        daily_costs = self.get_daily_costs()

        return {
            "current_mrr": current_mrr,
            "daily_revenue": daily_revenue,
            "customer_count": len(self.subscriptions),
            "growth_rate": self.calculate_growth_rate(),
            "days_to_target": self.find_target_achievement_month(
                current_mrr,
                9000,
                0.15,  # $300/day = $9000/month, 15% growth
            ),
            "profit_margin": (
                ((daily_revenue - daily_costs) / daily_revenue * 100)
                if daily_revenue > 0
                else 0
            ),
            "ai_costs": self._get_ai_cost_breakdown(),
            "last_updated": datetime.now().isoformat(),
        }

    def _track_token_usage(self, metadata: dict):
        """Track Claude token usage patterns"""
        if hasattr(self, "token_usage"):
            self.token_usage.append(metadata)
        else:
            self.token_usage = [metadata]

    def _get_ai_cost_breakdown(self) -> dict:
        """Get AI service cost breakdown"""
        ai_costs = {"claude": 0.0, "openai": 0.0, "gemini": 0.0, "total": 0.0}

        for event in self.cost_events:
            if event.service in ["claude_api", "anthropic"]:
                ai_costs["claude"] += event.cost
            elif event.service in ["openai_api", "openai"]:
                ai_costs["openai"] += event.cost
            elif event.service in ["gemini_api", "google"]:
                ai_costs["gemini"] += event.cost

        ai_costs["total"] = sum(
            [ai_costs["claude"], ai_costs["openai"], ai_costs["gemini"]]
        )
        return ai_costs
