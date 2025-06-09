"""
Enterprise Stripe Integration with FastAPI + Supabase
Real-time subscription management with transaction storage and webhook processing.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import asyncpg
import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase import Client, create_client

from app.config.logging import get_logger

logger = get_logger(__name__)

# Initialize services
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2023-10-16"

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_ANON_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-enterprise"])


class SubscriptionRequest(BaseModel):
    """Enterprise subscription creation request"""

    customer_email: str = Field(..., description="Customer email")
    customer_name: str = Field(..., description="Customer name")
    company_name: str = Field(..., description="Company name")
    plan_id: str = Field(..., description="Subscription plan ID")
    trial_days: int = Field(default=14, description="Trial period days")
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional metadata")


class WebhookData(BaseModel):
    """Stripe webhook event data"""

    id: str
    type: str
    data: dict[str, Any]
    created: int


class StripeSupabaseService:
    """Enterprise Stripe + Supabase integration service"""

    def __init__(self):
        self.db_pool = None
        self.subscription_plans = {
            "starter": {
                "price_monthly": 9900,
                "price_yearly": 99900,
                "features": ["10K API calls", "Basic support"],
            },
            "professional": {
                "price_monthly": 19900,
                "price_yearly": 199900,
                "features": ["100K API calls", "Priority support"],
            },
            "enterprise": {
                "price_monthly": 49900,
                "price_yearly": 499900,
                "features": ["Unlimited API calls", "24/7 support"],
            },
        }

    async def init_db_pool(self):
        """Initialize database connection pool"""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                host=os.getenv("SUPABASE_DB_HOST"),
                database=os.getenv("SUPABASE_DB_NAME"),
                user=os.getenv("SUPABASE_DB_USER"),
                password=os.getenv("SUPABASE_DB_PASSWORD"),
                port=5432,
                min_size=5,
                max_size=20,
            )

    async def create_subscription(self, request: SubscriptionRequest) -> dict[str, Any]:
        """Create enterprise subscription with Supabase storage"""

        start_time = time.time()

        try:
            await self.init_db_pool()

            # Create Stripe customer
            customer = await self._create_stripe_customer(
                email=request.customer_email,
                name=request.customer_name,
                company=request.company_name,
                metadata=request.metadata or {},
            )

            # Create subscription with trial
            subscription = await self._create_stripe_subscription(
                customer_id=customer.id,
                plan_id=request.plan_id,
                trial_days=request.trial_days,
            )

            # Store in Supabase
            await self._store_subscription_data(customer, subscription, request)

            execution_time = time.time() - start_time

            logger.info(
                f"Subscription created: {subscription.id} in {execution_time:.3f}s"
            )

            return {
                "success": True,
                "subscription_id": subscription.id,
                "customer_id": customer.id,
                "trial_end": subscription.trial_end,
                "status": subscription.status,
                "execution_time": execution_time,
            }

        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _create_stripe_customer(
        self, email: str, name: str, company: str, metadata: dict
    ) -> stripe.Customer:
        """Create Stripe customer with enterprise metadata"""

        # Check for existing customer
        existing = stripe.Customer.list(email=email, limit=1)
        if existing.data:
            return existing.data[0]

        return stripe.Customer.create(
            email=email,
            name=name,
            description=f"Enterprise customer: {company}",
            metadata={
                "company": company,
                "signup_source": "fastapi_enterprise",
                "created_via": "automation_platform",
                **metadata,
            },
        )

    async def _create_stripe_subscription(
        self, customer_id: str, plan_id: str, trial_days: int
    ) -> stripe.Subscription:
        """Create Stripe subscription with trial"""

        plan = self.subscription_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Invalid plan: {plan_id}")

        # Create price if needed
        price_id = await self._ensure_price_exists(plan_id, plan["price_monthly"])

        trial_end = int((datetime.now() + timedelta(days=trial_days)).timestamp())

        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            trial_end=trial_end,
            metadata={
                "plan_id": plan_id,
                "api_limit": (
                    "unlimited"
                    if plan_id == "enterprise"
                    else f"{10 if plan_id == 'starter' else 100}K"
                ),
                "created_via": "fastapi_automation",
            },
        )

    async def _ensure_price_exists(self, plan_id: str, amount: int) -> str:
        """Ensure Stripe price exists for plan"""

        try:
            prices = stripe.Price.list(lookup_keys=[f"{plan_id}_monthly"], limit=1)
            if prices.data:
                return prices.data[0].id
        except (stripe.error.StripeError, Exception) as e:
            logger.warning(f"Failed to list prices for {plan_id}: {e!s}")
            # Continue to create a new price if lookup fails

        # Create product first
        product = stripe.Product.create(
            name=f"Enterprise {plan_id.title()} Plan",
            description=f"Enterprise automation platform - {plan_id} tier",
            metadata={"plan_id": plan_id},
        )

        # Create price
        price = stripe.Price.create(
            unit_amount=amount,
            currency="usd",
            recurring={"interval": "month"},
            product=product.id,
            lookup_key=f"{plan_id}_monthly",
        )

        return price.id

    async def _store_subscription_data(
        self,
        customer: stripe.Customer,
        subscription: stripe.Subscription,
        request: SubscriptionRequest,
    ):
        """Store subscription data in Supabase"""

        async with self.db_pool.acquire() as conn:
            # Store customer
            await conn.execute(
                """
                INSERT INTO customers (
                    stripe_customer_id, email, name, company_name,
                    created_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (stripe_customer_id) DO UPDATE SET
                    email = EXCLUDED.email,
                    name = EXCLUDED.name,
                    updated_at = NOW()
            """,
                customer.id,
                request.customer_email,
                request.customer_name,
                request.company_name,
                datetime.now(),
                json.dumps(request.metadata or {}),
            )

            # Store subscription
            await conn.execute(
                """
                INSERT INTO subscriptions (
                    stripe_subscription_id, stripe_customer_id, plan_id,
                    status, trial_end, current_period_end, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (stripe_subscription_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = NOW()
            """,
                subscription.id,
                customer.id,
                request.plan_id,
                subscription.status,
                (
                    datetime.fromtimestamp(subscription.trial_end)
                    if subscription.trial_end
                    else None
                ),
                datetime.fromtimestamp(subscription.current_period_end),
                datetime.now(),
            )

    async def process_webhook(self, webhook_data: WebhookData) -> dict[str, Any]:
        """Process Stripe webhook with Supabase storage"""

        start_time = time.time()

        try:
            await self.init_db_pool()

            event_type = webhook_data.type
            event_data = webhook_data.data["object"]

            # Store webhook event
            await self._store_webhook_event(webhook_data)

            # Process based on event type
            result = {}
            if event_type == "customer.subscription.created":
                result = await self._handle_subscription_created(event_data)
            elif event_type == "customer.subscription.updated":
                result = await self._handle_subscription_updated(event_data)
            elif event_type == "invoice.payment_succeeded":
                result = await self._handle_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                result = await self._handle_payment_failed(event_data)
            else:
                result = {"message": f"Event {event_type} logged but not processed"}

            execution_time = time.time() - start_time

            logger.info(f"Webhook {event_type} processed in {execution_time:.3f}s")

            return {
                "success": True,
                "event_type": event_type,
                "execution_time": execution_time,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _store_webhook_event(self, webhook_data: WebhookData):
        """Store webhook event in Supabase for audit trail"""

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO webhook_events (
                    stripe_event_id, event_type, event_data,
                    processed_at, created_at
                ) VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (stripe_event_id) DO NOTHING
            """,
                webhook_data.id,
                webhook_data.type,
                json.dumps(webhook_data.data),
                datetime.now(),
                datetime.fromtimestamp(webhook_data.created),
            )

    async def _handle_subscription_created(
        self, subscription_data: dict
    ) -> dict[str, Any]:
        """Handle new subscription creation"""

        subscription_id = subscription_data["id"]
        customer_id = subscription_data["customer"]

        # Update subscription status in database
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $1, updated_at = NOW()
                WHERE stripe_subscription_id = $2
            """,
                subscription_data["status"],
                subscription_id,
            )

        return {
            "action": "subscription_created",
            "subscription_id": subscription_id,
            "customer_id": customer_id,
        }

    async def _handle_subscription_updated(
        self, subscription_data: dict
    ) -> dict[str, Any]:
        """Handle subscription updates"""

        subscription_id = subscription_data["id"]

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $1,
                    current_period_end = $2,
                    updated_at = NOW()
                WHERE stripe_subscription_id = $3
            """,
                subscription_data["status"],
                datetime.fromtimestamp(subscription_data["current_period_end"]),
                subscription_id,
            )

        return {"action": "subscription_updated", "subscription_id": subscription_id}

    async def _handle_payment_succeeded(self, invoice_data: dict) -> dict[str, Any]:
        """Handle successful payment"""

        subscription_id = invoice_data.get("subscription")
        amount = invoice_data["amount_paid"] / 100  # Convert from cents

        # Store transaction
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO transactions (
                    stripe_invoice_id, stripe_subscription_id, amount_usd,
                    status, processed_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                invoice_data["id"],
                subscription_id,
                amount,
                "succeeded",
                datetime.now(),
                datetime.now(),
            )

        return {
            "action": "payment_succeeded",
            "subscription_id": subscription_id,
            "amount": amount,
        }

    async def _handle_payment_failed(self, invoice_data: dict) -> dict[str, Any]:
        """Handle failed payment"""

        subscription_id = invoice_data.get("subscription")
        amount = invoice_data["amount_due"] / 100

        # Store failed transaction
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO transactions (
                    stripe_invoice_id, stripe_subscription_id, amount_usd,
                    status, processed_at, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                invoice_data["id"],
                subscription_id,
                amount,
                "failed",
                datetime.now(),
                datetime.now(),
            )

        return {
            "action": "payment_failed",
            "subscription_id": subscription_id,
            "amount": amount,
        }

    async def simulate_transactions(self, count: int = 1000) -> dict[str, Any]:
        """Simulate transactions for testing"""

        start_time = time.time()
        successful_transactions = 0

        await self.init_db_pool()

        try:
            async with self.db_pool.acquire() as conn:
                for i in range(count):
                    # Simulate transaction data
                    amount = 99.00 + (i % 3) * 100  # Vary amounts: $99, $199, $299

                    await conn.execute(
                        """
                        INSERT INTO transactions (
                            stripe_invoice_id, stripe_subscription_id, amount_usd,
                            status, processed_at, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        f"test_inv_{i}",
                        f"test_sub_{i % 100}",
                        amount,
                        "succeeded",
                        datetime.now(),
                        datetime.now(),
                    )

                    successful_transactions += 1

            execution_time = time.time() - start_time

            return {
                "success": True,
                "transactions_created": successful_transactions,
                "execution_time": execution_time,
                "throughput": count / execution_time,
                "average_time_per_transaction": execution_time
                / count
                * 1000,  # milliseconds
            }

        except Exception as e:
            logger.error(f"Transaction simulation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "transactions_created": successful_transactions,
            }


# Global service instance
_stripe_service = None


def get_stripe_service() -> StripeSupabaseService:
    """Get global Stripe service instance"""
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeSupabaseService()
    return _stripe_service


# FastAPI endpoints
@router.post("/create-subscription")
async def create_subscription_endpoint(
    request: SubscriptionRequest,
    background_tasks: BackgroundTasks,
    service: StripeSupabaseService = Depends(get_stripe_service),
) -> JSONResponse:
    """Create enterprise subscription with Supabase storage"""

    result = await service.create_subscription(request)
    return JSONResponse(content=result)


@router.post("/webhook")
async def stripe_webhook_endpoint(
    request: Request, service: StripeSupabaseService = Depends(get_stripe_service)
) -> JSONResponse:
    """Handle Stripe webhooks with Supabase storage"""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    webhook_data = WebhookData(
        id=event["id"], type=event["type"], data=event["data"], created=event["created"]
    )

    result = await service.process_webhook(webhook_data)
    return JSONResponse(content=result)


@router.post("/simulate-transactions")
async def simulate_transactions_endpoint(
    count: int = 1000, service: StripeSupabaseService = Depends(get_stripe_service)
) -> JSONResponse:
    """Simulate transactions for testing"""

    result = await service.simulate_transactions(count)
    return JSONResponse(content=result)


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint"""

    return JSONResponse(
        content={
            "status": "healthy",
            "service": "stripe-fastapi-supabase",
            "timestamp": datetime.now().isoformat(),
        }
    )
