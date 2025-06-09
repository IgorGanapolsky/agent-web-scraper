"""Stripe webhook endpoint for handling payment events."""

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.logging import get_logger
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)

router = APIRouter(prefix="/stripe", tags=["webhooks"])

# Initialize checkout service
checkout_service = StripeCheckoutService(
    test_mode=os.getenv("STRIPE_TEST_MODE", "false").lower() == "true"
)


@router.post("/webhook")
async def stripe_webhook(
    request: Request, stripe_signature: Optional[str] = Header(None)
):
    """Handle Stripe webhook events."""
    try:
        # Get raw body
        payload = await request.body()

        # Handle webhook
        result = checkout_service.handle_webhook(payload, stripe_signature or "")

        return JSONResponse(content=result, status_code=200)

    except ValueError as e:
        logger.error(f"Invalid payload: {e!s}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error(f"Webhook error: {e!s}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/create-checkout-session")
async def create_checkout_session(
    tier: str,
    billing_cycle: str = "monthly",
    email: Optional[str] = None,
    trial_days: int = 14,
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
):
    """Create a Stripe checkout session."""
    try:
        # Use default URLs if not provided
        if not success_url:
            success_url = os.getenv(
                "STRIPE_SUCCESS_URL", "https://saasgrowthdispatch.com/success"
            )
        if not cancel_url:
            cancel_url = os.getenv(
                "STRIPE_CANCEL_URL", "https://saasgrowthdispatch.com/pricing"
            )

        session_url = checkout_service.create_checkout_session(
            email=email,
            tier=tier,
            billing_cycle=billing_cycle,
            trial_days=trial_days,
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return JSONResponse(content={"checkout_url": session_url}, status_code=200)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-portal-session")
async def create_portal_session(customer_id: str):
    """Create a customer portal session for subscription management."""
    try:
        portal_url = checkout_service.create_portal_session(customer_id)
        return JSONResponse(content={"portal_url": portal_url}, status_code=200)

    except Exception as e:
        logger.error(f"Error creating portal session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.get("/subscription/{customer_id}")
async def get_subscription_status(customer_id: str):
    """Get subscription status for a customer."""
    try:
        # In production, this would query the database
        # For now, return a mock response
        return JSONResponse(
            content={
                "customer_id": customer_id,
                "status": "active",
                "tier": "pro",
                "billing_cycle": "monthly",
                "next_billing_date": "2025-07-04",
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error getting subscription status: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")
