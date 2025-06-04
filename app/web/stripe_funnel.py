"""
Stripe Payment Funnel Implementation
Complete checkout flow with trial management and Google Sheets integration
"""

import os
from datetime import datetime, timedelta

import stripe
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config.logging import get_logger
from app.mcp.stripe_server import MCPStripeServer, StripeCheckoutSession

logger = get_logger(__name__)
router = APIRouter(prefix="/funnel", tags=["stripe-funnel"])
templates = Jinja2Templates(directory="app/data/templates")

# Initialize Stripe and MCP server
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
mcp_stripe = MCPStripeServer(test_mode=False)


@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """Display pricing page with Stripe checkout options"""

    pricing_data = {
        "premium": {
            "name": "Premium",
            "price": "$8",
            "monthly_price": 800,  # cents
            "features": [
                "Daily SaaS market intelligence reports",
                "AI-powered pain point insights",
                "Automated opportunity discovery",
                "Email delivery + dashboard access",
                "Market trend analysis",
                "Competitive intelligence",
            ],
            "trial_days": 7,
            "popular": True,
        },
        "annual": {
            "name": "Annual Premium",
            "price": "$80",
            "yearly_price": 8000,  # cents
            "features": [
                "Everything in Premium",
                "Annual subscription (save 17%)",
                "Priority support",
                "Advanced analytics",
                "Custom report scheduling",
                "API access",
            ],
            "trial_days": 7,
            "billing_cycle": "yearly",
        },
        "founding": {
            "name": "Founding Member",
            "price": "$240",
            "yearly_price": 24000,  # cents
            "features": [
                "Everything in Annual",
                "Founding member benefits",
                "Direct access to founders",
                "Product roadmap influence",
                "Lifetime price lock",
                "Exclusive community access",
                "White-label opportunities",
            ],
            "trial_days": 14,
            "billing_cycle": "yearly",
            "badge": "Limited Time",
        },
    }

    return templates.TemplateResponse(
        "pricing.html",
        {
            "request": request,
            "pricing": pricing_data,
            "domain": os.getenv("DOMAIN", "https://saasgrowthdispatch.com"),
        },
    )


@router.post("/checkout")
async def create_checkout(
    email: str = Form(...),
    tier: str = Form(...),
    billing_cycle: str = Form(default="monthly"),
):
    """Create Stripe checkout session with trial"""

    try:
        # Validate tier
        valid_tiers = ["premium", "annual", "founding"]
        if tier not in valid_tiers:
            raise HTTPException(status_code=400, detail="Invalid pricing tier")

        # Set trial days based on tier
        trial_days = 7 if tier in ["premium", "annual"] else 14

        # Create checkout session
        checkout_request = StripeCheckoutSession(
            customer_email=email,
            tier=tier,
            billing_cycle=billing_cycle,
            trial_days=trial_days,
            success_url=f"{os.getenv('DOMAIN')}/funnel/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('DOMAIN')}/funnel/pricing?cancelled=true",
            metadata={
                "tier": tier,
                "billing_cycle": billing_cycle,
                "trial_start": datetime.now().isoformat(),
                "source": "saas_growth_dispatch_funnel",
            },
        )

        session_data = await mcp_stripe.create_checkout_session(checkout_request)

        # Log checkout creation
        logger.info(f"Checkout session created: {email} -> {tier} ({billing_cycle})")

        return RedirectResponse(url=session_data["checkout_url"], status_code=303)

    except Exception as e:
        logger.error(f"Checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/success", response_class=HTMLResponse)
async def checkout_success(request: Request, session_id: str):
    """Handle successful checkout and display confirmation"""

    try:
        # Retrieve session details from Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            customer_email = session.customer_details.email
            tier = session.metadata.get("tier", "pro")

            # Log successful conversion
            logger.info(f"Successful checkout: {customer_email} -> {tier}")

            return templates.TemplateResponse(
                "checkout_success.html",
                {
                    "request": request,
                    "customer_email": customer_email,
                    "tier": tier.title(),
                    "session": session,
                },
            )
        else:
            # Payment pending (trial period)
            return templates.TemplateResponse(
                "trial_started.html",
                {
                    "request": request,
                    "customer_email": session.customer_details.email,
                    "tier": session.metadata.get("tier", "pro").title(),
                    "trial_days": session.metadata.get("trial_days", "7"),
                },
            )

    except Exception as e:
        logger.error(f"Success page error: {e}")
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": "Unable to process checkout confirmation"},
        )


@router.get("/portal")
async def customer_portal(customer_id: str):
    """Redirect to Stripe customer portal for subscription management"""

    try:
        portal_session = await mcp_stripe.create_customer_portal(customer_id)
        return RedirectResponse(url=portal_session["portal_url"])

    except Exception as e:
        logger.error(f"Portal creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to access customer portal")


@router.post("/trial-conversion/{customer_id}")
async def convert_trial_to_paid(customer_id: str):
    """Convert trial subscription to paid (called by automation)"""

    try:
        # Get customer's subscription
        subscriptions = stripe.Subscription.list(
            customer=customer_id, status="trialing"
        )

        if not subscriptions.data:
            raise HTTPException(status_code=404, detail="No trial subscription found")

        subscription = subscriptions.data[0]

        # End trial immediately to convert to paid
        updated_subscription = stripe.Subscription.modify(
            subscription.id, trial_end="now"
        )

        logger.info(f"Trial converted to paid: {customer_id}")

        return {
            "status": "success",
            "subscription_id": updated_subscription.id,
            "customer_id": customer_id,
            "converted_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Trial conversion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to convert trial")


@router.get("/analytics")
async def funnel_analytics():
    """Get funnel conversion analytics"""

    try:
        # Get recent checkout sessions
        sessions = stripe.checkout.Session.list(
            created={"gte": int((datetime.now() - timedelta(days=30)).timestamp())},
            limit=100,
        )

        # Calculate metrics
        total_sessions = len(sessions.data)
        completed_sessions = len(
            [s for s in sessions.data if s.payment_status in ["paid", "unpaid"]]
        )
        trial_conversions = len(
            [s for s in sessions.data if s.payment_status == "paid"]
        )

        conversion_rate = (
            (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        )
        trial_conversion_rate = (
            (trial_conversions / completed_sessions * 100)
            if completed_sessions > 0
            else 0
        )

        return {
            "period": "30_days",
            "total_sessions": total_sessions,
            "completed_checkouts": completed_sessions,
            "trial_conversions": trial_conversions,
            "conversion_rate": round(conversion_rate, 2),
            "trial_conversion_rate": round(trial_conversion_rate, 2),
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Analytics generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")
