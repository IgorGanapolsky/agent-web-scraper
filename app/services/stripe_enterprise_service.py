"""
Stripe Enterprise Integration for Revenue Acceleration Pipeline
Handles subscription creation, payment processing, and webhooks for the CFO-managed system.
Port: 8001
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import stripe
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config.logging import get_logger
from app.core.cfo_revenue_pipeline import get_cfo_revenue_pipeline
from app.core.token_monitor import track_api_call

logger = get_logger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2023-10-16"

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-enterprise"])


class SubscriptionPlan(BaseModel):
    """Enterprise subscription plan configuration"""

    plan_id: str = Field(..., description="Unique plan identifier")
    name: str = Field(..., description="Plan display name")
    price_monthly: int = Field(..., description="Monthly price in cents")
    price_yearly: int = Field(..., description="Yearly price in cents")
    features: list[str] = Field(..., description="Plan features")
    api_requests_limit: int = Field(..., description="Monthly API requests limit")
    users_limit: int = Field(..., description="Maximum users")
    priority_support: bool = Field(
        default=False, description="Priority support included"
    )
    sla_guarantee: Optional[str] = Field(None, description="SLA guarantee level")


class CreateSubscriptionRequest(BaseModel):
    """Request to create enterprise subscription"""

    customer_email: str = Field(..., description="Customer email address")
    customer_name: str = Field(..., description="Customer full name")
    company_name: str = Field(..., description="Company name")
    plan_id: str = Field(..., description="Selected subscription plan")
    billing_cycle: str = Field(
        default="monthly", description="Billing cycle: monthly or yearly"
    )
    trial_days: int = Field(default=14, description="Trial period in days")
    payment_method_id: Optional[str] = Field(
        None, description="Stripe payment method ID"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class WebhookEvent(BaseModel):
    """Stripe webhook event model"""

    id: str
    type: str
    data: dict[str, Any]
    created: int
    livemode: bool


class StripeEnterpriseService:
    """
    Enterprise-grade Stripe integration for revenue acceleration pipeline.

    Features:
    - Subscription management with enterprise pricing tiers
    - Automatic trial-to-paid conversion tracking
    - Usage-based billing integration
    - Revenue analytics and CFO reporting
    - Webhook handling for real-time updates
    """

    def __init__(self):
        self.cfo_pipeline = get_cfo_revenue_pipeline()
        self.subscription_plans = self._initialize_enterprise_plans()
        self.webhook_endpoints = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_cancelled,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.subscription.trial_will_end": self._handle_trial_ending,
        }

    def _initialize_enterprise_plans(self) -> dict[str, SubscriptionPlan]:
        """Initialize enterprise subscription plans for revenue acceleration"""

        plans = {
            "starter": SubscriptionPlan(
                plan_id="starter",
                name="Starter",
                price_monthly=9900,  # $99/month
                price_yearly=99900,  # $999/year (2 months free)
                features=[
                    "Up to 10,000 API requests/month",
                    "Basic automation workflows",
                    "Email support",
                    "Standard SLA (99.5% uptime)",
                    "5 team members",
                ],
                api_requests_limit=10000,
                users_limit=5,
                priority_support=False,
                sla_guarantee="99.5%",
            ),
            "professional": SubscriptionPlan(
                plan_id="professional",
                name="Professional",
                price_monthly=19900,  # $199/month
                price_yearly=199900,  # $1,999/year (2 months free)
                features=[
                    "Up to 100,000 API requests/month",
                    "Advanced automation workflows",
                    "Priority email + chat support",
                    "Enhanced SLA (99.9% uptime)",
                    "25 team members",
                    "Custom integrations",
                    "Advanced analytics",
                ],
                api_requests_limit=100000,
                users_limit=25,
                priority_support=True,
                sla_guarantee="99.9%",
            ),
            "enterprise": SubscriptionPlan(
                plan_id="enterprise",
                name="Enterprise",
                price_monthly=49900,  # $499/month
                price_yearly=499900,  # $4,999/year (2 months free)
                features=[
                    "Unlimited API requests",
                    "Enterprise automation suite",
                    "24/7 dedicated support",
                    "Enterprise SLA (99.99% uptime)",
                    "Unlimited team members",
                    "Custom development",
                    "White-label options",
                    "On-premise deployment",
                    "Advanced security features",
                ],
                api_requests_limit=-1,  # Unlimited
                users_limit=-1,  # Unlimited
                priority_support=True,
                sla_guarantee="99.99%",
            ),
        }

        return plans

    async def create_enterprise_subscription(
        self, request: CreateSubscriptionRequest, background_tasks: BackgroundTasks
    ) -> dict[str, Any]:
        """
        Create enterprise subscription with trial period and revenue tracking.
        """
        start_time = time.time()

        try:
            # Validate plan exists
            if request.plan_id not in self.subscription_plans:
                raise HTTPException(
                    status_code=400, detail=f"Invalid plan: {request.plan_id}"
                )

            plan = self.subscription_plans[request.plan_id]

            # Create or retrieve Stripe customer
            customer = await self._create_or_get_customer(
                email=request.customer_email,
                name=request.customer_name,
                company=request.company_name,
                metadata=request.metadata or {},
            )

            # Create subscription with trial
            subscription = await self._create_subscription_with_trial(
                customer_id=customer.id,
                plan=plan,
                billing_cycle=request.billing_cycle,
                trial_days=request.trial_days,
                payment_method_id=request.payment_method_id,
            )

            # Track revenue impact in CFO pipeline
            background_tasks.add_task(
                self._track_subscription_revenue,
                subscription_id=subscription.id,
                plan_id=request.plan_id,
                customer_email=request.customer_email,
            )

            execution_time = time.time() - start_time

            # Track API usage for CFO monitoring
            cost = track_api_call(
                "claude-3-sonnet-20240229", 1200, 800, "subscription_creation"
            )

            logger.info(
                f"Enterprise subscription created: {subscription.id} in {execution_time:.3f}s"
            )

            return {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "plan": plan.dict(),
                "trial_end": subscription.trial_end,
                "status": subscription.status,
                "next_payment_date": subscription.current_period_end,
                "execution_time": execution_time,
                "api_cost": cost,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating enterprise subscription: {e}")
            raise HTTPException(status_code=500, detail="Subscription creation failed")

    async def _create_or_get_customer(
        self, email: str, name: str, company: str, metadata: dict[str, Any]
    ) -> stripe.Customer:
        """Create or retrieve Stripe customer with enterprise metadata"""

        # Check if customer already exists
        existing_customers = stripe.Customer.list(email=email, limit=1)

        if existing_customers.data:
            customer = existing_customers.data[0]
            logger.info(f"Retrieved existing customer: {customer.id}")
            return customer

        # Create new enterprise customer
        customer_metadata = {
            "company": company,
            "plan_type": "enterprise",
            "signup_source": "revenue_acceleration_pipeline",
            "created_via": "cfo_optimization_system",
            **metadata,
        }

        customer = stripe.Customer.create(
            email=email,
            name=name,
            description=f"Enterprise customer from {company}",
            metadata=customer_metadata,
        )

        logger.info(f"Created new enterprise customer: {customer.id}")
        return customer

    async def _create_subscription_with_trial(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        billing_cycle: str,
        trial_days: int,
        payment_method_id: Optional[str] = None,
    ) -> stripe.Subscription:
        """Create Stripe subscription with trial period"""

        # Determine price based on billing cycle
        price = plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly

        # Create price object if it doesn't exist
        price_id = await self._ensure_price_exists(
            plan_id=plan.plan_id, amount=price, billing_cycle=billing_cycle
        )

        # Calculate trial end date
        trial_end = int((datetime.now() + timedelta(days=trial_days)).timestamp())

        subscription_params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "trial_end": trial_end,
            "metadata": {
                "plan_id": plan.plan_id,
                "billing_cycle": billing_cycle,
                "api_limit": str(plan.api_requests_limit),
                "users_limit": str(plan.users_limit),
                "created_via": "revenue_acceleration_pipeline",
            },
            "expand": ["latest_invoice.payment_intent"],
        }

        # Add payment method if provided
        if payment_method_id:
            subscription_params["default_payment_method"] = payment_method_id

        subscription = stripe.Subscription.create(**subscription_params)

        return subscription

    async def _ensure_price_exists(
        self, plan_id: str, amount: int, billing_cycle: str
    ) -> str:
        """Ensure Stripe price object exists for the plan"""

        interval = "year" if billing_cycle == "yearly" else "month"
        price_lookup_key = f"{plan_id}_{billing_cycle}"

        # Try to find existing price
        try:
            prices = stripe.Price.list(lookup_keys=[price_lookup_key], limit=1)
            if prices.data:
                return prices.data[0].id
        except stripe.error.StripeError:
            pass

        # Create new price
        product_id = await self._ensure_product_exists(plan_id)

        price = stripe.Price.create(
            unit_amount=amount,
            currency="usd",
            recurring={"interval": interval},
            product=product_id,
            lookup_key=price_lookup_key,
            metadata={"plan_id": plan_id, "billing_cycle": billing_cycle},
        )

        return price.id

    async def _ensure_product_exists(self, plan_id: str) -> str:
        """Ensure Stripe product exists for the plan"""

        plan = self.subscription_plans[plan_id]

        # Try to find existing product
        try:
            products = stripe.Product.list(metadata={"plan_id": plan_id}, limit=1)
            if products.data:
                return products.data[0].id
        except stripe.error.StripeError:
            pass

        # Create new product
        product = stripe.Product.create(
            name=f"Enterprise {plan.name} Plan",
            description=f"Enterprise automation platform - {plan.name} tier",
            metadata={"plan_id": plan_id, "features": json.dumps(plan.features)},
        )

        return product.id

    async def _track_subscription_revenue(
        self, subscription_id: str, plan_id: str, customer_email: str
    ) -> None:
        """Track subscription in CFO revenue pipeline for analytics"""

        try:
            plan = self.subscription_plans[plan_id]

            # Calculate revenue impact
            monthly_revenue = plan.price_monthly / 100  # Convert from cents
            annual_revenue = plan.price_yearly / 100

            revenue_context = {
                "subscription_id": subscription_id,
                "plan_id": plan_id,
                "customer_email": customer_email,
                "monthly_revenue": monthly_revenue,
                "annual_revenue": annual_revenue,
                "revenue_type": "subscription",
                "created_at": datetime.now().isoformat(),
            }

            # Execute CFO pipeline to update revenue projections
            result = await self.cfo_pipeline.execute_optimized_revenue_pipeline(
                revenue_context
            )

            logger.info(
                f"Revenue tracking completed for subscription {subscription_id}: {result.revenue_impact}"
            )

        except Exception as e:
            logger.error(f"Failed to track subscription revenue: {e}")

    async def handle_webhook_event(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle Stripe webhook events for real-time subscription management"""

        start_time = time.time()

        try:
            handler = self.webhook_endpoints.get(event.type)

            if not handler:
                logger.warning(f"Unhandled webhook event type: {event.type}")
                return {"success": True, "message": "Event type not handled"}

            result = await handler(event)
            execution_time = time.time() - start_time

            logger.info(f"Webhook {event.type} processed in {execution_time:.3f}s")

            return {
                "success": True,
                "event_id": event.id,
                "event_type": event.type,
                "execution_time": execution_time,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Webhook processing failed for {event.type}: {e}")
            raise HTTPException(status_code=500, detail="Webhook processing failed")

    async def _handle_subscription_created(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle new subscription creation"""

        subscription = event.data["object"]

        # Update customer records
        customer_id = subscription["customer"]
        plan_id = subscription["metadata"].get("plan_id")

        logger.info(
            f"New subscription created: {subscription['id']} for customer {customer_id}"
        )

        return {
            "action": "subscription_created",
            "subscription_id": subscription["id"],
            "customer_id": customer_id,
            "plan_id": plan_id,
        }

    async def _handle_subscription_updated(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle subscription updates"""

        subscription = event.data["object"]
        previous_attributes = event.data.get("previous_attributes", {})

        logger.info(f"Subscription updated: {subscription['id']}")

        return {
            "action": "subscription_updated",
            "subscription_id": subscription["id"],
            "changes": previous_attributes,
        }

    async def _handle_subscription_cancelled(
        self, event: WebhookEvent
    ) -> dict[str, Any]:
        """Handle subscription cancellation"""

        subscription = event.data["object"]

        logger.info(f"Subscription cancelled: {subscription['id']}")

        # Track churn in revenue pipeline
        await self._track_subscription_churn(subscription["id"])

        return {
            "action": "subscription_cancelled",
            "subscription_id": subscription["id"],
        }

    async def _handle_payment_succeeded(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle successful payment"""

        invoice = event.data["object"]
        subscription_id = invoice.get("subscription")
        amount = invoice["amount_paid"] / 100  # Convert from cents

        logger.info(f"Payment succeeded: ${amount} for subscription {subscription_id}")

        # Track revenue in CFO pipeline
        await self._track_payment_revenue(subscription_id, amount)

        return {
            "action": "payment_succeeded",
            "subscription_id": subscription_id,
            "amount": amount,
        }

    async def _handle_payment_failed(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle failed payment"""

        invoice = event.data["object"]
        subscription_id = invoice.get("subscription")

        logger.warning(f"Payment failed for subscription {subscription_id}")

        # Trigger dunning management
        await self._handle_payment_failure(subscription_id)

        return {"action": "payment_failed", "subscription_id": subscription_id}

    async def _handle_trial_ending(self, event: WebhookEvent) -> dict[str, Any]:
        """Handle trial ending notification"""

        subscription = event.data["object"]
        customer_id = subscription["customer"]

        logger.info(f"Trial ending for subscription {subscription['id']}")

        # Trigger conversion optimization
        await self._optimize_trial_conversion(subscription["id"], customer_id)

        return {
            "action": "trial_ending",
            "subscription_id": subscription["id"],
            "customer_id": customer_id,
        }

    async def _track_subscription_churn(self, subscription_id: str) -> None:
        """Track subscription churn for revenue analytics"""

        try:
            churn_context = {
                "subscription_id": subscription_id,
                "event_type": "churn",
                "timestamp": datetime.now().isoformat(),
            }

            await self.cfo_pipeline.execute_optimized_revenue_pipeline(churn_context)

        except Exception as e:
            logger.error(f"Failed to track subscription churn: {e}")

    async def _track_payment_revenue(self, subscription_id: str, amount: float) -> None:
        """Track payment revenue in CFO pipeline"""

        try:
            revenue_context = {
                "subscription_id": subscription_id,
                "payment_amount": amount,
                "event_type": "payment",
                "timestamp": datetime.now().isoformat(),
            }

            await self.cfo_pipeline.execute_optimized_revenue_pipeline(revenue_context)

        except Exception as e:
            logger.error(f"Failed to track payment revenue: {e}")

    async def _handle_payment_failure(self, subscription_id: str) -> None:
        """Handle payment failure with dunning management"""

        try:
            # Implement dunning logic here
            logger.info(
                f"Initiating dunning management for subscription {subscription_id}"
            )

            # Could trigger email campaigns, grace periods, etc.

        except Exception as e:
            logger.error(f"Dunning management failed: {e}")

    async def _optimize_trial_conversion(
        self, subscription_id: str, customer_id: str
    ) -> None:
        """Optimize trial-to-paid conversion"""

        try:
            # Trigger conversion optimization workflows
            logger.info(
                f"Optimizing trial conversion for subscription {subscription_id}"
            )

            # Could trigger personalized emails, offers, demos, etc.

        except Exception as e:
            logger.error(f"Trial conversion optimization failed: {e}")

    def get_revenue_analytics(self) -> dict[str, Any]:
        """Get revenue analytics for CFO reporting"""

        try:
            # Get subscription metrics from Stripe
            subscriptions = stripe.Subscription.list(limit=100, status="active")

            # Calculate metrics
            total_mrr = 0
            total_arr = 0
            plan_distribution = {}

            for sub in subscriptions.data:
                plan_id = sub.metadata.get("plan_id", "unknown")

                if plan_id in self.subscription_plans:
                    plan = self.subscription_plans[plan_id]
                    mrr = plan.price_monthly / 100
                    arr = plan.price_yearly / 100

                    total_mrr += mrr
                    total_arr += arr

                    if plan_id not in plan_distribution:
                        plan_distribution[plan_id] = 0
                    plan_distribution[plan_id] += 1

            return {
                "total_active_subscriptions": len(subscriptions.data),
                "total_mrr": round(total_mrr, 2),
                "total_arr": round(total_arr, 2),
                "plan_distribution": plan_distribution,
                "average_revenue_per_customer": round(
                    total_mrr / max(len(subscriptions.data), 1), 2
                ),
                "updated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get revenue analytics: {e}")
            return {"error": "Failed to retrieve analytics"}


# Global service instance
_stripe_service = None


def get_stripe_enterprise_service() -> StripeEnterpriseService:
    """Get the global Stripe enterprise service instance"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeEnterpriseService()
    return _stripe_service


# FastAPI route implementations
@router.post("/create-subscription")
async def create_enterprise_subscription_endpoint(
    request: CreateSubscriptionRequest, background_tasks: BackgroundTasks
) -> JSONResponse:
    """Create enterprise subscription with trial period"""

    service = get_stripe_enterprise_service()
    result = await service.create_enterprise_subscription(request, background_tasks)

    return JSONResponse(content=result)


@router.post("/webhook")
async def stripe_webhook_endpoint(request: Request) -> JSONResponse:
    """Handle Stripe webhooks for real-time subscription management"""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Convert to our webhook event model
    webhook_event = WebhookEvent(
        id=event["id"],
        type=event["type"],
        data=event["data"],
        created=event["created"],
        livemode=event["livemode"],
    )

    service = get_stripe_enterprise_service()
    result = await service.handle_webhook_event(webhook_event)

    return JSONResponse(content=result)


@router.get("/plans")
async def get_subscription_plans() -> JSONResponse:
    """Get available enterprise subscription plans"""

    service = get_stripe_enterprise_service()
    plans = {
        plan_id: plan.dict() for plan_id, plan in service.subscription_plans.items()
    }

    return JSONResponse(content={"plans": plans})


@router.get("/analytics")
async def get_revenue_analytics_endpoint() -> JSONResponse:
    """Get revenue analytics for CFO reporting"""

    service = get_stripe_enterprise_service()
    analytics = service.get_revenue_analytics()

    return JSONResponse(content=analytics)


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for the Stripe service"""

    return JSONResponse(
        content={
            "status": "healthy",
            "service": "stripe-enterprise",
            "port": 8001,
            "timestamp": datetime.now().isoformat(),
        }
    )
