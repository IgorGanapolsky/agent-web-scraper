"""
Stripe Checkout Service
Handles checkout sessions, trials, and subscription management
"""

import json
import os
from datetime import datetime
from typing import ClassVar, Optional

import stripe
from pydantic import BaseModel

from app.config.logging import get_logger
from app.models.customer import Customer, Subscription
from app.services.api_key_service import APIKeyService
from app.services.payment_service import PaymentService

logger = get_logger(__name__)


class CheckoutSession(BaseModel):
    """Checkout session model"""

    session_id: str
    customer_email: str
    subscription_type: str  # monthly or annual
    tier: str
    trial_days: int = 0
    success_url: str
    cancel_url: str
    metadata: dict = {}


class StripeCheckoutService:
    """Handles Stripe checkout and subscription flows"""

    # Pricing configuration
    PRICES: ClassVar[dict] = {
        "starter": {
            "monthly": "price_starter_monthly",  # $19/month
            "annual": "price_starter_annual",  # $182/year (20% off)
            "monthly_amount": 19.00,
            "annual_amount": 182.00,
        },
        "basic": {
            "monthly": "price_basic_monthly",  # $29/month
            "annual": "price_basic_annual",  # $278/year (20% off)
            "monthly_amount": 29.00,
            "annual_amount": 278.00,
        },
        "pro": {
            "monthly": "price_pro_monthly",  # $99/month
            "annual": "price_pro_annual",  # $950/year (20% off)
            "monthly_amount": 99.00,
            "annual_amount": 950.00,
        },
        "enterprise": {
            "monthly": "price_enterprise_monthly",  # $299/month
            "annual": "price_enterprise_annual",  # $2870/year (20% off)
            "monthly_amount": 299.00,
            "annual_amount": 2870.00,
        },
    }

    def __init__(self, test_mode: bool = False):
        """Initialize checkout service"""
        self.test_mode = test_mode
        self.payment_service = PaymentService(test_mode=test_mode)
        self.api_key_service = APIKeyService()

        if not test_mode:
            stripe.api_key = os.getenv("STRIPE_API_KEY")
            self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    def create_checkout_session(
        self,
        email: str,
        tier: str,
        billing_cycle: str = "monthly",
        trial_days: int = 14,
        success_url: str = "https://saasgrowthdispatch.com/success",
        cancel_url: str = "https://saasgrowthdispatch.com/pricing",
        metadata: Optional[dict] = None,
    ) -> str:
        """Create a Stripe checkout session"""

        if tier not in self.PRICES:
            raise ValueError(f"Invalid tier: {tier}")

        if billing_cycle not in ["monthly", "annual"]:
            raise ValueError(f"Invalid billing cycle: {billing_cycle}")

        price_id = self.PRICES[tier][billing_cycle]

        logger.info(
            f"Creating checkout session for {email} - "
            f"{tier} {billing_cycle} with {trial_days} day trial"
        )

        try:
            if self.test_mode:
                # Return mock session for testing
                return f"cs_test_{datetime.now().timestamp()}"

            # Create Stripe checkout session
            session_data = {
                "payment_method_types": ["card"],
                "line_items": [
                    {
                        "price": price_id,
                        "quantity": 1,
                    }
                ],
                "mode": "subscription",
                "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
                "cancel_url": cancel_url,
                "customer_email": email,
                "metadata": {
                    "tier": tier,
                    "billing_cycle": billing_cycle,
                    **(metadata or {}),
                },
            }

            # Add trial period if specified
            if trial_days > 0:
                session_data["subscription_data"] = {
                    "trial_period_days": trial_days,
                    "metadata": {
                        "tier": tier,
                        "billing_cycle": billing_cycle,
                    },
                }

            # Allow promotion codes
            session_data["allow_promotion_codes"] = True

            session = stripe.checkout.Session.create(**session_data)

            logger.info(f"Checkout session created: {session.id}")
            return session.url

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error creating checkout session: {e!s}")
            raise

    def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """Handle Stripe webhooks"""
        try:
            # Verify webhook signature
            if not self.test_mode:
                event = stripe.Webhook.construct_event(
                    payload, signature, self.webhook_secret
                )
            else:
                # For testing, parse the payload directly
                event = json.loads(payload)

            logger.info(f"Processing webhook event: {event['type']}")

            # Route to appropriate handler
            handlers = {
                "checkout.session.completed": self._handle_checkout_completed,
                "customer.subscription.created": self._handle_subscription_created,
                "customer.subscription.updated": self._handle_subscription_updated,
                "customer.subscription.deleted": self._handle_subscription_deleted,
                "customer.subscription.trial_will_end": self._handle_trial_ending,
                "invoice.payment_succeeded": self._handle_payment_succeeded,
                "invoice.payment_failed": self._handle_payment_failed,
            }

            handler = handlers.get(event["type"])
            if handler:
                return handler(event["data"]["object"])
            else:
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {"status": "unhandled", "event": event["type"]}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e!s}")
            raise
        except Exception as e:
            logger.error(f"Error processing webhook: {e!s}")
            raise

    def _handle_checkout_completed(self, session: dict) -> dict:
        """Handle successful checkout completion"""
        customer_email = session["customer_email"]
        customer_id = session["customer"]
        subscription_id = session["subscription"]

        logger.info(
            f"Checkout completed for {customer_email} - "
            f"Customer: {customer_id}, Subscription: {subscription_id}"
        )

        # Create customer record if needed
        customer = Customer(
            stripe_id=customer_id,
            email=customer_email,
            subscription_tier=session["metadata"].get("tier", "pro"),
        )

        # Issue API key for the customer
        subscription = Subscription(
            stripe_id=subscription_id,
            customer_id=customer_id,
            tier=session["metadata"].get("tier", "pro"),
            status="active",
        )

        api_key = self.api_key_service.create_api_key(customer, subscription)

        # Send welcome email with API key
        self._send_welcome_email(customer, api_key)

        return {
            "status": "success",
            "customer_id": customer_id,
            "subscription_id": subscription_id,
            "api_key_issued": True,
        }

    def _handle_subscription_created(self, subscription: dict) -> dict:
        """Handle new subscription creation"""
        tier = subscription["metadata"].get("tier", "pro")
        billing_cycle = subscription["metadata"].get("billing_cycle", "monthly")

        # Track in analytics
        amount = self._get_subscription_amount(subscription)

        self.payment_service.cost_tracker.add_revenue_event(
            {
                "customer_id": subscription["customer"],
                "amount": amount,
                "tier": tier,
                "event_type": "subscription_created",
                "metadata": {
                    "billing_cycle": billing_cycle,
                    "trial": subscription.get("trial_end") is not None,
                },
            }
        )

        return {
            "status": "success",
            "action": "subscription_created",
            "tier": tier,
            "billing_cycle": billing_cycle,
        }

    def _handle_trial_ending(self, subscription: dict) -> dict:
        """Handle trial ending (3 days before end)"""
        customer_id = subscription["customer"]
        trial_end = datetime.fromtimestamp(subscription["trial_end"])

        logger.info(f"Trial ending for customer {customer_id} on {trial_end}")

        # Send trial ending email with conversion incentive
        self._send_trial_ending_email(customer_id, trial_end)

        return {
            "status": "success",
            "action": "trial_ending_notification_sent",
            "trial_end": trial_end.isoformat(),
        }

    def _handle_subscription_updated(self, subscription: dict) -> dict:
        """Handle subscription updates (upgrades/downgrades)"""
        old_tier = subscription["metadata"].get("previous_tier")
        new_tier = subscription["metadata"].get("tier")

        if old_tier and new_tier and old_tier != new_tier:
            logger.info(
                f"Subscription tier changed from {old_tier} to {new_tier} "
                f"for customer {subscription['customer']}"
            )

            # Update API key rate limits
            api_keys = self.api_key_service.get_customer_api_keys(
                subscription["customer"]
            )
            for api_key in api_keys:
                api_key.tier = new_tier
                self.api_key_service._store_api_key(api_key)

        return {
            "status": "success",
            "action": "subscription_updated",
            "old_tier": old_tier,
            "new_tier": new_tier,
        }

    def _handle_subscription_deleted(self, subscription: dict) -> dict:
        """Handle subscription cancellation"""
        customer_id = subscription["customer"]

        logger.info(f"Subscription cancelled for customer {customer_id}")

        # Deactivate API keys
        api_keys = self.api_key_service.get_customer_api_keys(customer_id)
        for api_key in api_keys:
            self.api_key_service.deactivate_api_key(api_key.key)

        # Send cancellation survey
        self._send_cancellation_survey(customer_id)

        return {
            "status": "success",
            "action": "subscription_cancelled",
            "api_keys_deactivated": len(api_keys),
        }

    def _handle_payment_succeeded(self, invoice: dict) -> dict:
        """Handle successful payment"""
        return self.payment_service._handle_payment_succeeded(invoice)

    def _handle_payment_failed(self, invoice: dict) -> dict:
        """Handle failed payment"""
        return self.payment_service._handle_payment_failed(invoice)

    def create_portal_session(self, customer_id: str) -> str:
        """Create customer portal session for subscription management"""
        try:
            if self.test_mode:
                return f"https://billing.stripe.com/test/session/{customer_id}"

            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url="https://saasgrowthdispatch.com/account",
            )

            return session.url

        except Exception as e:
            logger.error(f"Error creating portal session: {e!s}")
            raise

    def _get_subscription_amount(self, subscription: dict) -> float:
        """Extract subscription amount from Stripe object"""
        items = subscription.get("items", {}).get("data", [])
        if items:
            amount = items[0]["price"]["unit_amount"] / 100

            # Adjust for annual billing
            billing_interval = items[0]["price"]["recurring"]["interval"]
            if billing_interval == "year":
                amount = amount / 12  # Convert to monthly for MRR tracking

            return amount
        return 0.0

    def _send_welcome_email(self, customer: Customer, api_key):
        """Send welcome email with API key and getting started guide"""
        # In production, integrate with email service
        logger.info(f"Sending welcome email to {customer.email} with API key")

        # Email would include:
        # - API key and how to use it
        # - Getting started guide
        # - Link to documentation
        # - Support contact

    def _send_trial_ending_email(self, customer_id: str, trial_end: datetime):
        """Send trial ending reminder with conversion incentive"""
        logger.info(f"Sending trial ending email to customer {customer_id}")

        # Email would include:
        # - Trial ending date
        # - 20% off first month if they convert now
        # - Feature comparison
        # - Testimonials

    def _send_cancellation_survey(self, customer_id: str):
        """Send cancellation survey to understand churn"""
        logger.info(f"Sending cancellation survey to customer {customer_id}")

        # Survey would ask:
        # - Reason for cancellation
        # - What could we improve
        # - Would they consider returning
        # - Offer win-back discount
