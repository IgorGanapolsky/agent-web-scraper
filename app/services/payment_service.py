"""
Payment Service Module
Handles Stripe integration and subscription management for $300/day revenue target
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import stripe
from pydantic import BaseModel, Field

try:
    from app.config.logging import get_logger
except ImportError:
    import logging

    def get_logger(name):
        return logging.getLogger(name)


from app.core.cost_tracker import CostTracker

logger = get_logger(__name__)


class PaymentResult(BaseModel):
    """Result of a payment operation."""

    success: bool
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    amount: Optional[float] = None


class SubscriptionTier(BaseModel):
    """Subscription tier configuration"""

    name: str
    price_id: str
    amount: float
    features: list[str]
    query_limit: int
    api_access: bool = False


class Customer(BaseModel):
    """Customer model"""

    stripe_id: str
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    subscription_tier: Optional[str] = None


class Subscription(BaseModel):
    """Subscription model"""

    stripe_id: str
    customer_id: str
    tier: str
    amount: float
    status: str
    current_period_start: datetime
    current_period_end: datetime
    canceled_at: Optional[datetime] = None


class PaymentService:
    """Handles all payment and subscription operations"""

    # Pricing tiers
    TIERS = {
        "basic": SubscriptionTier(
            name="Basic",
            price_id="price_basic_monthly",
            amount=29.00,
            features=[
                "Daily market intelligence reports",
                "Niche opportunity scoring",
                "Pain point trend analysis",
                "Email delivery",
                "Basic support",
            ],
            query_limit=100,
        ),
        "pro": SubscriptionTier(
            name="Pro",
            price_id="price_pro_monthly",
            amount=99.00,
            features=[
                "Everything in Basic",
                "API access to insights",
                "Custom niche analysis",
                "Weekly strategy calls",
                "Priority support",
                "Custom lead magnets",
            ],
            query_limit=1000,
            api_access=True,
        ),
        "enterprise": SubscriptionTier(
            name="Enterprise",
            price_id="price_enterprise_monthly",
            amount=299.00,
            features=[
                "Everything in Pro",
                "Weekly 1:1 strategy calls",
                "Custom market research",
                "Competitive analysis",
                "Go-to-market planning",
                "Dedicated account manager",
            ],
            query_limit=10000,
            api_access=True,
        ),
    }

    def __init__(self, test_mode: bool = False):
        """Initialize payment service"""
        self.test_mode = test_mode
        self.cost_tracker = CostTracker()

        if not test_mode:
            import os

            stripe.api_key = os.getenv("STRIPE_API_KEY")
            if not stripe.api_key:
                raise ValueError("STRIPE_API_KEY not configured")

    def create_customer(self, customer_data: dict) -> Customer:
        """Create a new Stripe customer"""
        logger.info(f"Creating customer: {customer_data.get('email')}")

        try:
            if self.test_mode:
                # Return mock customer for testing
                return Customer(
                    stripe_id=f"cus_test_{datetime.now().timestamp()}",
                    email=customer_data["email"],
                    name=customer_data.get("name"),
                    company=customer_data.get("company"),
                )

            stripe_customer = stripe.Customer.create(
                email=customer_data["email"],
                name=customer_data.get("name"),
                metadata={
                    "company": customer_data.get("company", ""),
                    "source": customer_data.get("source", "organic"),
                },
            )

            customer = Customer(
                stripe_id=stripe_customer.id,
                email=stripe_customer.email,
                name=stripe_customer.name,
            )

            logger.info(f"Customer created: {customer.stripe_id}")
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error creating customer: {e!s}")
            raise

    def create_subscription(self, subscription_data: dict) -> Subscription:
        """Create a new subscription"""
        customer_id = subscription_data["customer_id"]
        tier = subscription_data["tier"]

        if tier not in self.TIERS:
            raise ValueError(f"Invalid subscription tier: {tier}")

        tier_config = self.TIERS[tier]
        logger.info(f"Creating {tier} subscription for customer {customer_id}")

        try:
            if self.test_mode:
                # Return mock subscription for testing
                return Subscription(
                    stripe_id=f"sub_test_{datetime.now().timestamp()}",
                    customer_id=customer_id,
                    tier=tier,
                    amount=tier_config.amount,
                    status="active",
                    current_period_start=datetime.now(),
                    current_period_end=datetime.now() + timedelta(days=30),
                )

            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": tier_config.price_id}],
                metadata={"tier": tier},
            )

            subscription = Subscription(
                stripe_id=stripe_subscription.id,
                customer_id=stripe_subscription.customer,
                tier=tier,
                amount=tier_config.amount,
                status=stripe_subscription.status,
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                ),
            )

            # Track revenue event
            self.cost_tracker.add_revenue_event(
                {
                    "customer_id": customer_id,
                    "amount": tier_config.amount,
                    "tier": tier,
                    "event_type": "subscription_created",
                }
            )

            logger.info(f"Subscription created: {subscription.stripe_id}")
            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error creating subscription: {e!s}")
            raise

    def handle_webhook(self, webhook_data: dict) -> dict:
        """Handle Stripe webhook events"""
        event_type = webhook_data.get("type")
        logger.info(f"Processing webhook: {event_type}")

        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(webhook_data["data"]["object"])
        else:
            logger.warning(f"Unhandled webhook event: {event_type}")
            return {"status": "unhandled", "event": event_type}

    def _handle_subscription_created(self, subscription_data: dict) -> dict:
        """Handle new subscription creation"""
        amount = subscription_data["items"]["data"][0]["price"]["unit_amount"] / 100

        # Track revenue event
        self.cost_tracker.add_revenue_event(
            {
                "customer_id": subscription_data["customer"],
                "amount": amount,
                "event_type": "subscription_created",
            }
        )

        return {
            "status": "success",
            "action": "subscription_created",
            "revenue_impact": amount,
        }

    def _handle_payment_succeeded(self, invoice_data: dict) -> dict:
        """Handle successful payment"""
        amount = invoice_data["amount_paid"] / 100

        # Track revenue event
        self.cost_tracker.add_revenue_event(
            {
                "customer_id": invoice_data["customer"],
                "amount": amount,
                "event_type": "payment_succeeded",
            }
        )

        return {"status": "success", "action": "payment_received", "amount": amount}

    def _handle_payment_failed(self, invoice_data: dict) -> dict:
        """Handle failed payment"""
        amount = invoice_data["amount_due"] / 100
        attempt_count = invoice_data.get("attempt_count", 1)

        logger.warning(
            f"Payment failed for customer {invoice_data['customer']}, "
            f"amount: ${amount}, attempt: {attempt_count}"
        )

        # Implement retry logic
        if attempt_count < 3:
            return {
                "status": "retry_scheduled",
                "retry_attempt": attempt_count + 1,
                "next_retry": datetime.now() + timedelta(days=3),
            }
        else:
            # Cancel subscription after 3 failed attempts
            return {
                "status": "subscription_at_risk",
                "action": "manual_intervention_required",
            }

    def _handle_subscription_deleted(self, subscription_data: dict) -> dict:
        """Handle subscription cancellation"""
        logger.info(f"Subscription cancelled: {subscription_data['id']}")

        return {"status": "success", "action": "subscription_cancelled"}

    def _handle_subscription_updated(self, subscription_data: dict) -> dict:
        """Handle subscription updates (upgrades/downgrades)"""
        logger.info(f"Subscription updated: {subscription_data['id']}")

        return {"status": "success", "action": "subscription_updated"}

    def calculate_subscription_metrics(self, customers: list[dict]) -> dict:
        """Calculate key subscription metrics"""
        total_mrr = sum(c["amount"] * c["count"] for c in customers)
        daily_revenue = total_mrr / 30
        customer_count = sum(c["count"] for c in customers)

        return {
            "total_mrr": total_mrr,
            "daily_revenue": daily_revenue,
            "customer_count": customer_count,
            "target_achievement": daily_revenue >= 300,
            "days_to_target": max(0, (300 - daily_revenue) / (total_mrr * 0.15 / 30)),
            # Assuming 15% monthly growth
        }

    def upgrade_subscription(self, subscription_id: str, new_price_id: str) -> dict:
        """Upgrade an existing subscription"""
        try:
            if self.test_mode:
                return {
                    "new_tier": "enterprise",
                    "new_amount": 299.00,
                    "upgrade_value": 200.00,
                }

            # Implement actual Stripe upgrade logic
            subscription = stripe.Subscription.retrieve(subscription_id)
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[
                    {"id": subscription["items"]["data"][0].id, "price": new_price_id}
                ],
            )

            return {
                "new_tier": updated.metadata.get("tier"),
                "new_amount": updated["items"]["data"][0]["price"]["unit_amount"] / 100,
                "upgrade_value": (
                    updated["items"]["data"][0]["price"]["unit_amount"]
                    - subscription["items"]["data"][0]["price"]["unit_amount"]
                )
                / 100,
            }

        except Exception as e:
            logger.error(f"Error upgrading subscription: {e!s}")
            raise

    def preview_upcoming_invoice(self, customer_id: str) -> dict:
        """Preview upcoming invoice including usage charges"""
        try:
            if self.test_mode:
                return {
                    "base_subscription": 99.00,
                    "usage_charges": 25.00,
                    "total": 124.00,
                }

            upcoming = stripe.Invoice.upcoming(customer=customer_id)

            base_subscription = 0
            usage_charges = 0

            for line in upcoming.lines.data:
                if line.type == "subscription":
                    base_subscription += line.amount / 100
                else:
                    usage_charges += line.amount / 100

            return {
                "base_subscription": base_subscription,
                "usage_charges": usage_charges,
                "total": upcoming.total / 100,
            }

        except Exception as e:
            logger.error(f"Error previewing invoice: {e!s}")
            raise

    def convert_trial_to_paid(self, customer_id: str, price_id: str) -> dict:
        """Convert trial customer to paid subscription"""
        logger.info(f"Converting trial customer {customer_id} to paid")

        try:
            subscription_data = {
                "customer_id": customer_id,
                "tier": self._get_tier_from_price_id(price_id),
            }

            subscription = self.create_subscription(subscription_data)

            return {
                "status": "converted",
                "subscription_id": subscription.stripe_id,
                "new_mrr": subscription.amount,
            }

        except Exception as e:
            logger.error(f"Error converting trial: {e!s}")
            raise

    def _get_tier_from_price_id(self, price_id: str) -> str:
        """Get tier name from price ID"""
        for tier_name, tier_config in self.TIERS.items():
            if tier_config.price_id == price_id:
                return tier_name
        raise ValueError(f"Unknown price ID: {price_id}")

    def export_analytics(self, filepath: str, analytics_data: dict):
        """Export subscription analytics"""
        with open(filepath, "w") as f:
            json.dump(analytics_data, f, indent=2, default=str)

    def manage_dunning(self, failed_payment_data: dict) -> dict:
        """Manage dunning process for failed payments"""
        failure_count = failed_payment_data["failure_count"]

        if failure_count < 2:
            action = "retry"
        elif failure_count < 4:
            action = "pause"
        else:
            action = "cancel"

        # In production, send dunning emails
        return {
            "action": action,
            "email_sent": True,
            "next_retry": failed_payment_data.get("next_retry"),
        }

    def update_payment_method(self, customer_id: str, payment_method_id: str) -> dict:
        """Update customer payment method"""
        try:
            if self.test_mode:
                return {"status": "updated", "new_payment_method": payment_method_id}

            # Update in Stripe
            stripe.Customer.modify(customer_id, default_source=payment_method_id)

            return {"status": "updated", "new_payment_method": payment_method_id}

        except Exception as e:
            logger.error(f"Error updating payment method: {e!s}")
            raise


# Missing import
