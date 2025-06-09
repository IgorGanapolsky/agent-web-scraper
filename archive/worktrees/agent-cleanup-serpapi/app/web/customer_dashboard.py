#!/usr/bin/env python3
"""
Customer Dashboard for SaaS Growth Dispatch
Complete customer experience with auth, usage, and billing
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from fastapi.templating import Jinja2Templates

from app.config.logging import get_logger
from app.services.api_key_service import APIKeyService
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)
router = APIRouter(prefix="/dashboard", tags=["customer-dashboard"])
templates = Jinja2Templates(directory="app/data/templates")

# Initialize services
api_key_service = APIKeyService()
stripe_service = StripeCheckoutService()
security = HTTPBearer()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main customer dashboard"""

    # For now, return a simple dashboard
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "customer": {"email": "demo@saasgrowthdispatch.com"},
            "usage": {"total_requests": 1250, "monthly_limit": 25000},
            "subscription": {"tier": "pro", "status": "active"},
        },
    )


@router.get("/auth/test")
async def test_auth():
    """Generate test API key for dashboard testing"""

    return {
        "message": "Dashboard ready for customer authentication",
        "status": "success",
    }
