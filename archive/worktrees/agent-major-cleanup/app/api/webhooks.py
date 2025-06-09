"""
Stripe webhook endpoints for payment processing
"""

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config.logging import get_logger
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize services
checkout_service = StripeCheckoutService()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Handle Stripe webhooks"""
    try:
        # Get raw body
        payload = await request.body()

        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")

        # Process webhook
        result = checkout_service.handle_webhook(payload, stripe_signature)

        return JSONResponse(content=result, status_code=200)

    except ValueError as e:
        logger.error(f"Invalid payload: {e!s}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        logger.error(f"Webhook error: {e!s}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/stripe/test")
async def test_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {"status": "ok", "message": "Stripe webhook endpoint is working"}
