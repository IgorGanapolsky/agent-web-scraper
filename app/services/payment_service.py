"""
Payment Service Module
Handles Stripe integration and subscription management for $300/day revenue target
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

import stripe
from pydantic import BaseModel

from app.config.logging import get_logger
from app.config.settings import settings
from app.core.cost_tracker import CostTracker
from app.models.customer import Customer, Subscription
from app.services.api_key_service import APIKeyService

logger = get_logger(__name__)


class SubscriptionTier(BaseModel):
    """Subscription tier configuration"""

    name: str
    price_id_monthly: str
    price_id_annual: str
    amount_monthly: float
    amount_annual: float
    features: list[str]
    query_limit: int
    api_access: bool = False


class PaymentService:
    """Handles all payment and subscription operations"""

    # Pricing tiers with annual options
    TIERS = {
        "basic": SubscriptionTier(
            name="Basic",
            price_id_monthly="price_basic_monthly",
            price_id_annual="price_basic_annual",
            amount_monthly=29.00,
            amount_annual=290.00,  # 2 months free
            features=[
                "Daily market intelligence reports",
                "Niche opportunity scoring",
                "Pain point trend analysis",
                "Email delivery",
                "Basic support",
            ],
            query_limit=10000,
        ),
        "pro": SubscriptionTier(
            name="Pro",
            price_id_monthly="price_pro_monthly",
            price_id_annual="price_pro_annual",
            amount_monthly=99.00,
            amount_annual=990.00,  # 2 months free
            features=[
                "Everything in Basic",
                "API access to insights",
                "Custom niche analysis",
                "Weekly strategy calls",
                "Priority support",
                "Custom lead magnets",
            ],
            query_limit=100000,
            api_access=True,
        ),
        "enterprise": SubscriptionTier(
            name="Enterprise",
            price_id_monthly="price_enterprise_monthly",
            price_id_annual="price_enterprise_annual",
            amount_monthly=299.00,
            amount_annual=2990.00,  # 2 months free
            features=[
                "Everything in Pro",
                "Weekly 1:1 strategy calls",
                "Custom market research",
                "Competitive analysis",
                "Go-to-market planning",
                "Dedicated account manager",
            ],
            query_limit=1000000,
            api_access=True,
        ),
    }

    # Trial configuration (3 days for aggressive conversion)
    TRIAL_DAYS = 3

    def __init__(self, test_mode: bool = False):
        """Initialize payment service with live mode support"""
        self.test_mode = test_mode
        self.live_mode = settings.stripe_live_mode and not test_mode
        self.cost_tracker = CostTracker()
        self.api_key_service = APIKeyService()

        if not test_mode:
            stripe.api_key = settings.stripe_api_key or os.getenv("STRIPE_API_KEY")
            if not stripe.api_key:
                raise ValueError("STRIPE_API_KEY not configured for live payments")

            # Set webhook endpoint secret
            self.webhook_secret = settings.stripe_webhook_secret or os.getenv(
                "STRIPE_WEBHOOK_SECRET"
            )

            # Log mode for monitoring
            mode = "LIVE" if self.live_mode else "TEST"
            logger.info(f"Stripe payment service initialized in {mode} mode")

    def create_checkout_session(
        self,
        tier: str,
        interval: str = "month",
        customer_email: Optional[str] = None,
        trial: bool = True,
        require_payment_method: bool = True,
    ) -> dict:
        """Create Stripe checkout session for subscription."""
        if tier not in self.TIERS:
            raise ValueError(f"Invalid subscription tier: {tier}")

        tier_config = self.TIERS[tier]
        price_id = (
            tier_config.price_id_annual
            if interval == "year"
            else tier_config.price_id_monthly
        )

        try:
            session_params = {
                "payment_method_types": ["card"],
                "mode": "subscription",
                "line_items": [{"price": price_id, "quantity": 1}],
                "success_url": os.getenv(
                    "STRIPE_SUCCESS_URL",
                    "https://saasgrowthdispatch.com/success?session_id={CHECKOUT_SESSION_ID}",
                ),
                "cancel_url": os.getenv(
                    "STRIPE_CANCEL_URL", "https://saasgrowthdispatch.com/pricing"
                ),
                "metadata": {"tier": tier, "interval": interval},
            }

            # Add customer email if provided
            if customer_email:
                session_params["customer_email"] = customer_email

            # Add trial period with required payment method
            if trial:
                session_params["subscription_data"] = {
                    "trial_period_days": self.TRIAL_DAYS,
                    "metadata": {"tier": tier, "trial": "true"},
                }

                # Require payment method for trial (setup_future_usage)
                if require_payment_method:
                    session_params["payment_method_collection"] = "always"
                    session_params["subscription_data"]["trial_settings"] = {
                        "end_behavior": {"missing_payment_method": "cancel"}
                    }

            # Add customer portal for managing subscriptions
            session_params["billing_address_collection"] = "required"
            session_params["customer_creation"] = "always"

            if self.test_mode:
                # Return mock session for testing
                return {
                    "id": f"cs_test_{datetime.now().timestamp()}",
                    "url": "https://checkout.stripe.com/test",
                    "metadata": session_params["metadata"],
                }

            session = stripe.checkout.Session.create(**session_params)

            # Log for revenue tracking
            mode = "LIVE" if self.live_mode else "TEST"
            logger.info(f"Created {mode} checkout session for {tier} {interval} plan")

            return {
                "id": session.id,
                "url": session.url,
                "metadata": session.metadata,
                "mode": mode,
                "trial_days": self.TRIAL_DAYS if trial else 0,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error creating checkout session: {e!s}")
            raise

    def create_customer_portal_session(self, customer_id: str) -> dict:
        """Create customer portal session for subscription management."""
        try:
            if self.test_mode:
                return {"url": "https://billing.stripe.com/test"}

            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=os.getenv(
                    "STRIPE_RETURN_URL", "https://saasgrowthdispatch.com/account"
                ),
            )

            return {"url": session.url}

        except Exception as e:
            logger.error(f"Error creating portal session: {e!s}")
            raise

    def handle_webhook(self, payload: str, signature: str) -> dict:
        """Handle Stripe webhook events."""
        try:
            # Verify webhook signature
            if not self.test_mode and self.webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret
                )
            else:
                # For testing, parse the payload directly
                event = json.loads(payload)

            event_type = event.get("type")
            event_data = event.get("data", {}).get("object", {})

            logger.info(f"Processing webhook: {event_type}")

            # Route to appropriate handler
            handlers = {
                "checkout.session.completed": self._handle_checkout_completed,
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "customer.subscription.trial_will_end": self._handle_trial_ending,
                "invoice.payment_succeeded": self._handle_payment_succeeded,
                "invoice.payment_failed": self._handle_payment_failed,
                "customer.created": self._handle_customer_created,
            }

            handler = handlers.get(event_type)
            if handler:
                return handler(event_data)
            else:
                logger.warning(f"Unhandled webhook event: {event_type}")
                return {"status": "unhandled", "event": event_type}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error handling webhook: {e!s}")
            raise

    def _handle_checkout_completed(self, session_data: dict) -> dict:
        """Handle successful checkout completion."""
        customer_id = session_data.get("customer")
        subscription_id = session_data.get("subscription")

        # Customer and subscription will be created via other webhooks
        logger.info(f"Checkout completed for customer {customer_id}")

        return {
            "status": "success",
            "action": "checkout_completed",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
        }

    def _handle_customer_created(self, customer_data: dict) -> dict:
        """Handle new customer creation."""
        # Create internal customer record
        customer = Customer(
            id=f"cust_{datetime.now().timestamp()}",
            stripe_customer_id=customer_data["id"],
            email=customer_data["email"],
            name=customer_data.get("name"),
            created_at=datetime.now(),
        )

        # In production, save to database
        logger.info(f"Created customer record for {customer.email}")

        return {
            "status": "success",
            "action": "customer_created",
            "customer_id": customer.id,
        }

    def _handle_subscription_created(self, subscription_data: dict) -> dict:
        """Handle new subscription creation."""
        stripe_customer_id = subscription_data["customer"]
        items = subscription_data.get("items", {}).get("data", [])

        if not items:
            logger.error("No subscription items found")
            return {"status": "error", "message": "No subscription items"}

        price = items[0].get("price", {})
        amount = price.get("unit_amount", 0) / 100
        interval = price.get("recurring", {}).get("interval", "month")

        # Determine tier from metadata or price
        tier = subscription_data.get("metadata", {}).get("tier", "pro")

        # Create subscription record
        subscription = Subscription(
            id=f"sub_{datetime.now().timestamp()}",
            stripe_subscription_id=subscription_data["id"],
            customer_id=stripe_customer_id,
            tier=tier,
            interval=interval,
            amount=amount,
            status=subscription_data["status"],
            current_period_start=datetime.fromtimestamp(
                subscription_data["current_period_start"]
            ),
            current_period_end=datetime.fromtimestamp(
                subscription_data["current_period_end"]
            ),
        )

        # Create API key if tier includes API access
        if self.TIERS[tier].api_access:
            # In production, load customer from database
            customer = Customer(
                id="cust_temp",
                stripe_customer_id=stripe_customer_id,
                email="temp@example.com",  # Would be loaded from DB
            )

            api_key = self.api_key_service.create_api_key(customer, subscription)
            logger.info(f"Created API key for {tier} subscription")

            # Send API key to customer via email
            # TODO: Implement email sending

        # Track revenue event
        self.cost_tracker.add_revenue_event(
            {
                "customer_id": stripe_customer_id,
                "amount": amount,
                "tier": tier,
                "event_type": "subscription_created",
            }
        )

        return {
            "status": "success",
            "action": "subscription_created",
            "subscription_id": subscription.id,
            "tier": tier,
            "amount": amount,
        }

    def _handle_subscription_updated(self, subscription_data: dict) -> dict:
        """Handle subscription updates (upgrades/downgrades)."""
        old_items = (
            subscription_data.get("previous_attributes", {})
            .get("items", {})
            .get("data", [])
        )
        new_items = subscription_data.get("items", {}).get("data", [])

        if old_items and new_items:
            old_amount = old_items[0].get("price", {}).get("unit_amount", 0) / 100
            new_amount = new_items[0].get("price", {}).get("unit_amount", 0) / 100

            if new_amount > old_amount:
                action = "upgraded"
            elif new_amount < old_amount:
                action = "downgraded"
            else:
                action = "updated"

            # Update API key tier if needed
            # TODO: Update API key rate limits based on new tier

            return {
                "status": "success",
                "action": f"subscription_{action}",
                "old_amount": old_amount,
                "new_amount": new_amount,
            }

        return {"status": "success", "action": "subscription_updated"}

    def _handle_subscription_deleted(self, subscription_data: dict) -> dict:
        """Handle subscription cancellation."""
        customer_id = subscription_data["customer"]

        # Deactivate API keys
        api_keys = self.api_key_service.get_customer_api_keys(customer_id)
        for api_key in api_keys:
            self.api_key_service.deactivate_api_key(api_key.key)

        logger.info(f"Subscription cancelled for customer {customer_id}")

        return {
            "status": "success",
            "action": "subscription_cancelled",
            "customer_id": customer_id,
        }

    def _handle_trial_ending(self, subscription_data: dict) -> dict:
        """Handle trial ending notification (3 days before)."""
        customer_id = subscription_data["customer"]
        trial_end = datetime.fromtimestamp(subscription_data["trial_end"])

        # Send email reminder about trial ending
        # TODO: Implement email notification

        logger.info(f"Trial ending soon for customer {customer_id} on {trial_end}")

        return {
            "status": "success",
            "action": "trial_ending_notification",
            "customer_id": customer_id,
            "trial_end": trial_end.isoformat(),
        }

    def _handle_payment_succeeded(self, invoice_data: dict) -> dict:
        """Handle successful payment."""
        amount = invoice_data["amount_paid"] / 100
        customer_id = invoice_data["customer"]

        # Track revenue event
        self.cost_tracker.add_revenue_event(
            {
                "customer_id": customer_id,
                "amount": amount,
                "event_type": "payment_succeeded",
            }
        )

        # Reset usage counters for the new billing period
        # TODO: Reset monthly usage counters

        return {
            "status": "success",
            "action": "payment_received",
            "amount": amount,
            "customer_id": customer_id,
        }

    def _handle_payment_failed(self, invoice_data: dict) -> dict:
        """Handle failed payment."""
        amount = invoice_data["amount_due"] / 100
        attempt_count = invoice_data.get("attempt_count", 1)
        customer_id = invoice_data["customer"]

        logger.warning(
            f"Payment failed for customer {customer_id}, "
            f"amount: ${amount}, attempt: {attempt_count}"
        )

        # Send payment failure notification
        # TODO: Implement email notification

        if attempt_count < 3:
            return {
                "status": "retry_scheduled",
                "retry_attempt": attempt_count + 1,
                "next_retry": (datetime.now() + timedelta(days=3)).isoformat(),
            }
        else:
            # After 3 failed attempts, subscription will be cancelled
            return {
                "status": "subscription_at_risk",
                "action": "final_payment_failure",
                "customer_id": customer_id,
            }

    def calculate_subscription_metrics(self, customers: list[dict]) -> dict:
        """Calculate key subscription metrics."""
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

    def get_customer_subscription(self, stripe_customer_id: str) -> Optional[dict]:
        """Get customer's active subscription details."""
        try:
            if self.test_mode:
                return {
                    "id": "sub_test",
                    "status": "active",
                    "tier": "pro",
                    "current_period_end": datetime.now() + timedelta(days=30),
                }

            subscriptions = stripe.Subscription.list(
                customer=stripe_customer_id, status="active", limit=1
            )

            if subscriptions.data:
                sub = subscriptions.data[0]
                return {
                    "id": sub.id,
                    "status": sub.status,
                    "tier": sub.metadata.get("tier", "pro"),
                    "current_period_end": datetime.fromtimestamp(
                        sub.current_period_end
                    ),
                    "cancel_at_period_end": sub.cancel_at_period_end,
                }

            return None

        except Exception as e:
            logger.error(f"Error fetching subscription: {e!s}")
            return None

    def create_usage_record(
        self, subscription_id: str, quantity: int, timestamp: Optional[datetime] = None
    ):
        """Create usage record for metered billing."""
        try:
            if self.test_mode:
                return {"id": f"mbur_test_{datetime.now().timestamp()}"}

            # Get subscription item ID for usage-based pricing
            subscription = stripe.Subscription.retrieve(subscription_id)
            usage_item = None

            for item in subscription["items"]["data"]:
                if item["price"].get("recurring", {}).get("usage_type") == "metered":
                    usage_item = item
                    break

            if not usage_item:
                logger.warning(
                    f"No metered pricing item found for subscription {subscription_id}"
                )
                return None

            # Create usage record
            usage_record = stripe.SubscriptionItem.create_usage_record(
                usage_item["id"],
                quantity=quantity,
                timestamp=int((timestamp or datetime.now()).timestamp()),
            )

            return usage_record

        except Exception as e:
            logger.error(f"Error creating usage record: {e!s}")
            raise
