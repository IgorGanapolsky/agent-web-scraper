#!/usr/bin/env python3
"""
Enhanced Sentry Configuration with AI Monitoring
Business metrics tracking for $300/day revenue target
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration


class SentryAIMonitoring:
    """Enhanced Sentry monitoring with AI-powered business insights"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.release = os.getenv("RELEASE_VERSION", "1.0.0")
        self.setup_enhanced_sentry()

    def setup_enhanced_sentry(self):
        """Configure Sentry with AI monitoring and business metrics"""

        sentry_sdk.init(
            dsn=os.getenv("SENTRY_DSN"),
            # Core integrations
            integrations=[
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
                FastApiIntegration(auto_enabling_integrations=True),
                SqlalchemyIntegration(),
            ],
            # Performance monitoring
            traces_sample_rate=1.0 if self.environment == "development" else 0.1,
            profiles_sample_rate=1.0 if self.environment == "development" else 0.1,
            # Environment configuration
            environment=self.environment,
            release=self.release,
            # Business context enhancement
            before_send=self.add_business_context,
            before_send_transaction=self.add_transaction_context,
            # Custom AI monitoring options
            _experiments={
                "ai_monitoring": {
                    "track_token_usage": True,
                    "monitor_api_costs": True,
                    "detect_anomalies": True,
                    "business_metrics": True,
                }
            },
        )

    def add_business_context(
        self, event: dict[str, Any], hint: dict[str, Any]
    ) -> dict[str, Any]:
        """Add business metrics context to Sentry events"""

        try:
            from app.core.cost_tracker import CostTracker

            cost_tracker = CostTracker()

            # Add business metrics to event context
            event.setdefault("contexts", {})["business"] = {
                "daily_revenue": self._safe_get_daily_revenue(cost_tracker),
                "active_customers": self._safe_get_customer_count(cost_tracker),
                "mrr": self._safe_get_mrr(cost_tracker),
                "target_progress": self._calculate_target_progress(cost_tracker),
                "profit_margin": self._safe_get_profit_margin(cost_tracker),
                "timestamp": datetime.now().isoformat(),
            }

            # Add AI usage metrics
            event["contexts"]["ai_usage"] = {
                "daily_api_costs": self._safe_get_api_costs(cost_tracker),
                "token_usage": self._safe_get_token_usage(),
                "model_performance": self._safe_get_model_metrics(),
            }

        except Exception as e:
            # Don't break the application if business metrics fail
            event.setdefault("contexts", {})["business_error"] = {
                "error": str(e),
                "component": "business_metrics",
            }

        return event

    def add_transaction_context(
        self, event: dict[str, Any], hint: dict[str, Any]
    ) -> dict[str, Any]:
        """Add transaction-specific business context"""

        transaction_name = event.get("transaction", "")

        # Add revenue-critical transaction flags
        if any(
            revenue_endpoint in transaction_name
            for revenue_endpoint in [
                "/payment",
                "/subscription",
                "/webhook",
                "/upgrade",
            ]
        ):
            event.setdefault("tags", {})["revenue_critical"] = True
            event["tags"]["business_impact"] = "high"

        return event

    def _safe_get_daily_revenue(self, cost_tracker) -> float:
        """Safely get daily revenue with fallback"""
        try:
            return cost_tracker.get_daily_revenue()
        except Exception:
            return 0.0

    def _safe_get_customer_count(self, cost_tracker) -> int:
        """Safely get active customer count"""
        try:
            return cost_tracker.get_active_customer_count()
        except Exception:
            return 0

    def _safe_get_mrr(self, cost_tracker) -> float:
        """Safely get monthly recurring revenue"""
        try:
            return cost_tracker.calculate_mrr()
        except Exception:
            return 0.0

    def _calculate_target_progress(self, cost_tracker) -> dict[str, Any]:
        """Calculate progress toward $300/day target"""
        try:
            daily_revenue = cost_tracker.get_daily_revenue()
            target = 300.0

            return {
                "current_daily": daily_revenue,
                "target_daily": target,
                "achievement_percentage": (daily_revenue / target) * 100,
                "target_met": daily_revenue >= target,
                "gap_amount": max(0, target - daily_revenue),
            }
        except Exception:
            return {"error": "Unable to calculate target progress"}

    def _safe_get_profit_margin(self, cost_tracker) -> float:
        """Calculate profit margin safely"""
        try:
            revenue = cost_tracker.get_daily_revenue()
            costs = cost_tracker.get_daily_costs()

            if revenue > 0:
                return ((revenue - costs) / revenue) * 100
            return 0.0
        except Exception:
            return 0.0

    def _safe_get_api_costs(self, cost_tracker) -> dict[str, float]:
        """Get API costs by service"""
        try:
            return cost_tracker.get_api_costs_by_service()
        except Exception:
            return {}

    def _safe_get_token_usage(self) -> dict[str, int]:
        """Get token usage by AI model"""
        try:
            # Implement token tracking logic
            return {"openai_gpt4": 0, "openai_embeddings": 0, "anthropic_claude": 0}
        except Exception:
            return {}

    def _safe_get_model_metrics(self) -> dict[str, Any]:
        """Get AI model performance metrics"""
        try:
            return {"avg_response_time": 0.0, "success_rate": 100.0, "error_rate": 0.0}
        except Exception:
            return {}


class BusinessMetrics:
    """Business metrics tracking for Sentry"""

    @staticmethod
    def track_revenue_event(amount: float, customer_id: str, tier: str = "unknown"):
        """Track revenue generation events"""
        from sentry_sdk import metrics

        # Increment revenue counters
        metrics.incr("revenue.transaction.count")
        metrics.distribution("revenue.transaction.amount", amount)
        metrics.set("revenue.unique_customers", customer_id)

        # Track by tier
        metrics.incr(f"revenue.tier.{tier}.count")
        metrics.distribution(f"revenue.tier.{tier}.amount", amount)

        # Send event to Sentry with business context
        sentry_sdk.capture_message(
            f"Revenue Event: ${amount} from {tier} customer",
            level="info",
            contexts={
                "revenue": {
                    "amount": amount,
                    "customer_id": customer_id,
                    "tier": tier,
                    "timestamp": datetime.now().isoformat(),
                }
            },
            tags={
                "event_type": "revenue",
                "customer_tier": tier,
                "revenue_critical": True,
            },
        )

    @staticmethod
    def track_ai_usage(model: str, tokens: int, cost: float, operation: str = "query"):
        """Monitor AI API usage and costs"""
        from sentry_sdk import metrics

        # Track AI usage metrics
        metrics.incr(f"ai.{model}.requests")
        metrics.distribution(f"ai.{model}.tokens", tokens)
        metrics.distribution(f"ai.{model}.cost", cost)
        metrics.incr(f"ai.operation.{operation}.count")

        # Alert on high costs
        if cost > 1.0:  # Alert if single request costs > $1
            sentry_sdk.capture_message(
                f"High AI Cost Alert: ${cost} for {model}",
                level="warning",
                contexts={
                    "ai_usage": {
                        "model": model,
                        "tokens": tokens,
                        "cost": cost,
                        "operation": operation,
                    }
                },
                tags={"alert_type": "high_ai_cost", "model": model},
            )

    @staticmethod
    def track_customer_event(
        event_type: str, customer_id: str, metadata: Optional[dict] = None
    ):
        """Track customer lifecycle events"""
        from sentry_sdk import metrics

        metrics.incr(f"customer.{event_type}.count")

        sentry_sdk.capture_message(
            f"Customer Event: {event_type}",
            level="info",
            contexts={
                "customer": {
                    "customer_id": customer_id,
                    "event_type": event_type,
                    "metadata": metadata or {},
                    "timestamp": datetime.now().isoformat(),
                }
            },
            tags={"event_type": "customer_lifecycle", "customer_event": event_type},
        )

    @staticmethod
    def track_subscription_change(
        action: str, tier: str, amount: float, customer_id: str
    ):
        """Track subscription changes for revenue analysis"""
        from sentry_sdk import metrics

        metrics.incr(f"subscription.{action}.count")
        metrics.incr(f"subscription.tier.{tier}.{action}")

        if action == "upgrade":
            metrics.distribution("subscription.upgrade.amount", amount)
        elif action == "downgrade":
            metrics.distribution("subscription.downgrade.amount", amount)

        sentry_sdk.capture_message(
            f"Subscription {action}: {tier} tier (${amount})",
            level="info",
            contexts={
                "subscription": {
                    "action": action,
                    "tier": tier,
                    "amount": amount,
                    "customer_id": customer_id,
                }
            },
            tags={
                "event_type": "subscription_change",
                "subscription_action": action,
                "customer_tier": tier,
            },
        )

    @staticmethod
    def track_business_milestone(
        milestone: str, value: float, context: Optional[dict] = None
    ):
        """Track important business milestones"""
        sentry_sdk.capture_message(
            f"Business Milestone: {milestone} - ${value}",
            level="info",
            contexts={
                "milestone": {
                    "name": milestone,
                    "value": value,
                    "context": context or {},
                    "timestamp": datetime.now().isoformat(),
                }
            },
            tags={"event_type": "business_milestone", "milestone_type": milestone},
        )


def setup_sentry_monitoring():
    """Initialize Sentry AI monitoring"""
    return SentryAIMonitoring()


def get_business_metrics():
    """Get business metrics instance"""
    return BusinessMetrics()


# Initialize Sentry on module import
if os.getenv("SENTRY_DSN"):
    sentry_monitoring = setup_sentry_monitoring()
    business_metrics = get_business_metrics()
else:
    sentry_monitoring = None
    business_metrics = None
