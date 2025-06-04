"""Stripe webhook endpoint for handling payment events."""

import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.logging import get_logger
from app.services.payment_service import PaymentService

logger = get_logger(__name__)

router = APIRouter(prefix="/stripe", tags=["webhooks"])

# Initialize payment service
payment_service = PaymentService(
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
        result = payment_service.handle_webhook(
            payload.decode("utf-8"), stripe_signature or ""
        )

        return JSONResponse(content=result, status_code=200)

    except ValueError as e:
        logger.error(f"Invalid payload: {e!s}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e!s}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e!s}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/create-checkout-session")
async def create_checkout_session(
    tier: str, interval: str = "month", email: Optional[str] = None, trial: bool = True
):
    """Create a Stripe checkout session."""
    try:
        session = payment_service.create_checkout_session(
            tier=tier, interval=interval, customer_email=email, trial=trial
        )

        return JSONResponse(content=session, status_code=200)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-portal-session")
async def create_portal_session(customer_id: str):
    """Create a customer portal session for subscription management."""
    try:
        session = payment_service.create_customer_portal_session(customer_id)
        return JSONResponse(content=session, status_code=200)

    except Exception as e:
        logger.error(f"Error creating portal session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


# Import stripe for error handling
import stripe
