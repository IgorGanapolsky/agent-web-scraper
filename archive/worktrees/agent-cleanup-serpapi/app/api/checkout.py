"""
Checkout API endpoints for Stripe integration
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.config.logging import get_logger
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)

router = APIRouter(prefix="/checkout", tags=["checkout"])

# Initialize services
checkout_service = StripeCheckoutService()


class CreateCheckoutRequest(BaseModel):
    """Request model for creating checkout session"""

    email: EmailStr
    tier: str  # basic, pro, enterprise
    billing_cycle: str = "monthly"  # monthly or annual
    trial_days: int = 14
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    metadata: Optional[dict] = None


class CreateCheckoutResponse(BaseModel):
    """Response model for checkout session"""

    checkout_url: str
    session_id: Optional[str] = None


class CreatePortalRequest(BaseModel):
    """Request model for customer portal"""

    customer_id: str


class CreatePortalResponse(BaseModel):
    """Response model for customer portal"""

    portal_url: str


@router.post("/session", response_model=CreateCheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest):
    """Create a new Stripe checkout session"""
    try:
        # Validate tier
        valid_tiers = ["basic", "pro", "enterprise"]
        if request.tier not in valid_tiers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
            )

        # Create checkout session
        checkout_url = checkout_service.create_checkout_session(
            email=request.email,
            tier=request.tier,
            billing_cycle=request.billing_cycle,
            trial_days=request.trial_days,
            success_url=request.success_url or "https://saasgrowthdispatch.com/success",
            cancel_url=request.cancel_url or "https://saasgrowthdispatch.com/pricing",
            metadata=request.metadata,
        )

        # Extract session ID if it's a full URL
        session_id = None
        if checkout_url.startswith("https://checkout.stripe.com"):
            parts = checkout_url.split("/")
            if len(parts) > 0:
                session_id = parts[-1]

        return CreateCheckoutResponse(checkout_url=checkout_url, session_id=session_id)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal", response_model=CreatePortalResponse)
async def create_customer_portal(request: CreatePortalRequest):
    """Create a customer portal session for subscription management"""
    try:
        portal_url = checkout_service.create_portal_session(request.customer_id)

        return CreatePortalResponse(portal_url=portal_url)

    except Exception as e:
        logger.error(f"Error creating portal session: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.get("/prices")
async def get_prices():
    """Get current pricing information"""
    return {
        "tiers": {
            "basic": {
                "name": "Basic",
                "monthly_price": 29,
                "annual_price": 290,
                "annual_savings": 58,
                "features": [
                    "Daily market intelligence reports",
                    "Niche opportunity scoring",
                    "Pain point trend analysis",
                    "Email delivery",
                    "Basic support",
                    "100 API requests/day",
                ],
            },
            "pro": {
                "name": "Pro",
                "monthly_price": 99,
                "annual_price": 990,
                "annual_savings": 198,
                "features": [
                    "Everything in Basic",
                    "API access to insights",
                    "Custom niche analysis",
                    "Weekly strategy calls",
                    "Priority support",
                    "Custom lead magnets",
                    "10,000 API requests/day",
                ],
            },
            "enterprise": {
                "name": "Enterprise",
                "monthly_price": 299,
                "annual_price": 2990,
                "annual_savings": 598,
                "features": [
                    "Everything in Pro",
                    "Weekly 1:1 strategy calls",
                    "Custom market research",
                    "Competitive analysis",
                    "Go-to-market planning",
                    "Dedicated account manager",
                    "100,000 API requests/day",
                ],
            },
        },
        "trial_days": 14,
        "currency": "USD",
    }
