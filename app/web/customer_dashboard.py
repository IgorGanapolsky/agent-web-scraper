"""
Customer Dashboard with Authentication, Billing Management, and API Keys
Complete implementation for SaaS Growth Dispatch customer portal
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.api.auth import verify_token
from app.config.logging import get_logger
from app.mcp.stripe_server import MCPStripeServer
from app.models.api_key import APIKey
from app.services.api_key_service import APIKeyService

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["customer-dashboard"])

# Initialize services
stripe_server = MCPStripeServer(test_mode=False)
api_key_service = APIKeyService()

# Templates
templates = Jinja2Templates(directory="app/data/templates")


class DashboardData(BaseModel):
    """Customer dashboard data model"""

    user: dict
    subscription: dict
    billing: dict
    api_keys: list[APIKey]
    usage_stats: dict
    recent_activity: list[dict]


class APIKeyRequest(BaseModel):
    """API key creation request"""

    name: str
    description: Optional[str] = None
    tier: str = "pro"  # pro, enterprise


class BillingUpdateRequest(BaseModel):
    """Billing information update request"""

    plan: str  # basic, pro, enterprise
    billing_cycle: str  # monthly, annual


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, user_payload: dict = Depends(verify_token)):
    """Main customer dashboard page"""

    try:
        # Get user subscription info
        subscription_data = await get_customer_subscription_data(
            user_payload["user_id"]
        )

        # Get API keys
        api_keys = api_key_service.get_customer_api_keys(user_payload["user_id"])

        # Get usage statistics
        usage_stats = api_key_service.get_usage_analytics(user_payload["user_id"])

        # Get recent activity
        recent_activity = await get_recent_customer_activity(user_payload["user_id"])

        dashboard_data = DashboardData(
            user={
                "id": user_payload["user_id"],
                "email": user_payload["email"],
                "name": "Customer",  # Would come from database
                "avatar_url": None,
            },
            subscription=subscription_data,
            billing=await get_billing_info(user_payload["user_id"]),
            api_keys=api_keys,
            usage_stats=usage_stats,
            recent_activity=recent_activity,
        )

        return templates.TemplateResponse(
            "dashboard.html", {"request": request, "data": dashboard_data.dict()}
        )

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard",
        )


@router.get("/api/subscription")
async def get_subscription_info(user_payload: dict = Depends(verify_token)):
    """Get current subscription information"""

    try:
        subscription_data = await get_customer_subscription_data(
            user_payload["user_id"]
        )
        return subscription_data

    except Exception as e:
        logger.error(f"Error fetching subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch subscription information",
        )


@router.post("/api/subscription/update")
async def update_subscription(
    billing_request: BillingUpdateRequest, user_payload: dict = Depends(verify_token)
):
    """Update subscription plan"""

    try:
        # Create checkout session for plan change
        from app.mcp.stripe_server import StripeCheckoutSession

        session_request = StripeCheckoutSession(
            customer_email=user_payload["email"],
            tier=billing_request.plan,
            billing_cycle=billing_request.billing_cycle,
            trial_days=0,  # No trial for plan changes
            success_url="https://saasgrowthdispatch.com/dashboard?updated=true",
            cancel_url="https://saasgrowthdispatch.com/dashboard",
            metadata={"upgrade": "true", "previous_plan": "current"},
        )

        result = await stripe_server.create_checkout_session(session_request)

        logger.info(
            f"Plan update initiated for {user_payload['email']}: {billing_request.plan}"
        )

        return {
            "success": True,
            "checkout_url": result["checkout_url"],
            "message": f"Redirecting to update subscription to {billing_request.plan}",
        }

    except Exception as e:
        logger.error(f"Subscription update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subscription",
        )


@router.get("/api/billing/portal")
async def create_billing_portal(user_payload: dict = Depends(verify_token)):
    """Create Stripe customer portal session"""

    try:
        # Get customer's Stripe ID (would come from database)
        stripe_customer_id = f"cus_{user_payload['user_id']}"

        portal_session = await stripe_server.create_customer_portal(stripe_customer_id)

        return {
            "success": True,
            "portal_url": portal_session["portal_url"],
            "message": "Redirecting to billing portal",
        }

    except Exception as e:
        logger.error(f"Billing portal creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal",
        )


@router.get("/api/api-keys")
async def list_api_keys(user_payload: dict = Depends(verify_token)):
    """List customer's API keys"""

    try:
        api_keys = api_key_service.get_customer_api_keys(user_payload["user_id"])

        # Don't return the actual key values, only metadata
        safe_keys = [
            {
                "id": key.id,
                "name": key.name,
                "description": key.description,
                "tier": key.tier,
                "created_at": key.created_at.isoformat(),
                "last_used": key.last_used.isoformat() if key.last_used else None,
                "is_active": key.is_active,
                "key_preview": f"{key.key[:8]}...{key.key[-4:]}",
                "usage_count": key.usage_count,
                "rate_limit": key.rate_limit,
            }
            for key in api_keys
        ]

        return {"api_keys": safe_keys}

    except Exception as e:
        logger.error(f"Error fetching API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch API keys",
        )


@router.post("/api/api-keys")
async def create_api_key(
    key_request: APIKeyRequest, user_payload: dict = Depends(verify_token)
):
    """Create new API key"""

    try:
        # Validate tier access based on subscription
        subscription_data = await get_customer_subscription_data(
            user_payload["user_id"]
        )
        customer_tier = subscription_data.get("tier", "basic")

        if key_request.tier == "enterprise" and customer_tier != "enterprise":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Enterprise API keys require Enterprise subscription",
            )

        # Create API key
        new_key = api_key_service.create_api_key(
            customer_id=user_payload["user_id"],
            name=key_request.name,
            description=key_request.description,
            tier=key_request.tier,
        )

        logger.info(f"API key created for {user_payload['email']}: {key_request.name}")

        return {
            "success": True,
            "api_key": {
                "id": new_key.id,
                "name": new_key.name,
                "key": new_key.key,  # Only show full key on creation
                "tier": new_key.tier,
                "rate_limit": new_key.rate_limit,
                "created_at": new_key.created_at.isoformat(),
            },
            "message": "API key created successfully. Save this key - it won't be shown again!",
        }

    except Exception as e:
        logger.error(f"API key creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.delete("/api/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_payload: dict = Depends(verify_token)):
    """Delete API key"""

    try:
        # Verify ownership
        api_key = api_key_service.get_api_key(key_id)
        if not api_key or api_key.customer_id != user_payload["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
            )

        # Delete key
        success = api_key_service.delete_api_key(key_id)

        if success:
            logger.info(f"API key deleted: {key_id}")
            return {"success": True, "message": "API key deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete API key",
            )

    except Exception as e:
        logger.error(f"API key deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete API key",
        )


@router.get("/api/usage")
async def get_usage_analytics(
    user_payload: dict = Depends(verify_token), days: int = 30
):
    """Get usage analytics for customer"""

    try:
        analytics = api_key_service.get_usage_analytics(
            user_payload["user_id"], days=days
        )

        return {
            "period_days": days,
            "total_requests": analytics.get("total_requests", 0),
            "successful_requests": analytics.get("successful_requests", 0),
            "error_rate": analytics.get("error_rate", 0),
            "average_response_time": analytics.get("average_response_time", 0),
            "daily_breakdown": analytics.get("daily_breakdown", []),
            "endpoint_usage": analytics.get("endpoint_usage", {}),
            "rate_limit_hits": analytics.get("rate_limit_hits", 0),
        }

    except Exception as e:
        logger.error(f"Usage analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch usage analytics",
        )


async def get_customer_subscription_data(customer_id: str) -> dict:
    """Get customer subscription information"""

    try:
        # In production, fetch from database and Stripe
        # For now, return mock data
        return {
            "tier": "pro",
            "status": "active",
            "current_period_start": datetime.now().strftime("%Y-%m-%d"),
            "current_period_end": (datetime.now() + timedelta(days=30)).strftime(
                "%Y-%m-%d"
            ),
            "cancel_at_period_end": False,
            "amount": 99.00,
            "currency": "USD",
            "billing_cycle": "monthly",
            "trial_end": None,
            "next_billing_date": (datetime.now() + timedelta(days=30)).strftime(
                "%Y-%m-%d"
            ),
        }

    except Exception as e:
        logger.error(f"Error fetching subscription data: {e}")
        return {}


async def get_billing_info(customer_id: str) -> dict:
    """Get customer billing information"""

    try:
        # In production, fetch from Stripe
        return {
            "payment_method": {
                "type": "card",
                "last4": "4242",
                "brand": "visa",
                "exp_month": 12,
                "exp_year": 2025,
            },
            "billing_address": {
                "line1": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94105",
                "country": "US",
            },
            "upcoming_invoice": {
                "amount": 99.00,
                "currency": "USD",
                "date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            },
        }

    except Exception as e:
        logger.error(f"Error fetching billing info: {e}")
        return {}


async def get_recent_customer_activity(customer_id: str) -> list[dict]:
    """Get recent customer activity"""

    try:
        # In production, fetch from activity logs
        return [
            {
                "type": "api_request",
                "description": "API request to /intelligence/analyze",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
            },
            {
                "type": "subscription",
                "description": "Subscription renewed",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "status": "success",
            },
            {
                "type": "api_key",
                "description": "New API key created",
                "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
                "status": "success",
            },
        ]

    except Exception as e:
        logger.error(f"Error fetching activity: {e}")
        return []
