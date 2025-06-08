"""FastAPI web application for SaaS Market Intelligence Platform."""

from datetime import datetime
from typing import Any, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.api.auth import router as auth_router
from app.api.batch_endpoints import router as batch_router
from app.api.stripe_webhooks import router as stripe_router
from app.core.cost_tracker import CostTracker, RevenueEvent
from app.services.payment_service import PaymentService
from app.web.customer_dashboard import router as dashboard_router
from app.web.stripe_funnel import router as funnel_router

app = FastAPI(
    title="SaaS Market Intelligence Platform",
    description="AI-powered agentic RAG system for market intelligence",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Services
payment_service = PaymentService(test_mode=True)
cost_tracker = CostTracker(test_mode=True)

# Include routers
app.include_router(auth_router, prefix="", tags=["authentication"])
app.include_router(dashboard_router, prefix="", tags=["customer-dashboard"])
app.include_router(funnel_router, prefix="", tags=["stripe-funnel"])
app.include_router(stripe_router, prefix="", tags=["stripe-webhooks"])
app.include_router(batch_router, prefix="", tags=["batch-optimization"])


@app.get("/health")
async def health_check():
    """Health check endpoint for Railway deployment"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "agent-web-scraper",
            "version": "2.0.0",
        }
    )


# Models
class SubscriptionRequest(BaseModel):
    customer_id: str
    plan_id: str
    amount: float


class QueryRequest(BaseModel):
    query: str
    sources: Optional[list[str]] = None


class DashboardResponse(BaseModel):
    current_mrr: float
    daily_revenue: float
    customer_count: int
    growth_rate: float
    days_to_target: int
    profit_margin: float
    last_updated: str


# Auth dependency (mock for now)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user."""
    # In production, validate JWT token here
    if credentials.credentials == "test_token":
        return {"user_id": "test_user", "email": "test@example.com"}
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "SaaS Market Intelligence Platform API", "version": "2.0.0"}




@app.post("/api/subscriptions", response_model=dict[str, Any])
async def create_subscription(
    request: SubscriptionRequest, current_user: dict = Depends(get_current_user)
):
    """Create a new subscription."""
    result = payment_service.create_subscription(
        customer_id=request.customer_id, plan_id=request.plan_id, amount=request.amount
    )

    if result.success:
        # Track revenue event
        revenue_event = RevenueEvent(
            customer_id=request.customer_id,
            amount=request.amount,
            tier=request.plan_id,
            event_type="subscription",
        )
        cost_tracker.add_revenue_event(revenue_event)
        cost_tracker.add_subscription(
            customer_id=request.customer_id, tier=request.plan_id, amount=request.amount
        )

        return {
            "success": True,
            "subscription_id": result.transaction_id,
            "amount": result.amount,
            "message": "Subscription created successfully",
        }
    else:
        raise HTTPException(status_code=400, detail=result.error_message)


@app.get("/api/subscriptions/{customer_id}")
async def get_customer_subscriptions(
    customer_id: str, current_user: dict = Depends(get_current_user)
):
    """Get customer subscriptions."""
    subscriptions = payment_service.list_customer_subscriptions(customer_id)
    return {"subscriptions": subscriptions}


@app.delete("/api/subscriptions/{subscription_id}")
async def cancel_subscription(
    subscription_id: str, current_user: dict = Depends(get_current_user)
):
    """Cancel a subscription."""
    result = payment_service.cancel_subscription(subscription_id)

    if result.success:
        return {"success": True, "message": "Subscription cancelled successfully"}
    else:
        raise HTTPException(status_code=404, detail=result.error_message)


@app.post("/api/query")
async def query_intelligence(
    request: QueryRequest, current_user: dict = Depends(get_current_user)
):
    """Query the agentic RAG system for market intelligence."""
    # Mock implementation - in production, integrate with RAG engine
    return {
        "query": request.query,
        "response": f"Mock intelligence response for: {request.query}",
        "sources": request.sources or ["reddit", "github", "serpapi"],
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/dashboard", response_model=DashboardResponse)
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    """Get real-time dashboard metrics."""
    metrics = cost_tracker.get_dashboard_metrics()
    return DashboardResponse(**metrics)


@app.get("/api/revenue/daily")
async def get_daily_revenue(current_user: dict = Depends(get_current_user)):
    """Get daily revenue metrics."""
    return {
        "daily_revenue": cost_tracker.get_daily_revenue(),
        "target_met": cost_tracker.is_daily_target_met(300.0),
        "target_amount": 300.0,
        "date": datetime.now().date().isoformat(),
    }


@app.get("/api/revenue/forecast")
async def get_revenue_forecast(current_user: dict = Depends(get_current_user)):
    """Get revenue forecast."""
    current_mrr = cost_tracker.calculate_mrr()
    forecast = cost_tracker.forecast_revenue(
        current_mrr=max(current_mrr, 1000),  # Minimum baseline
        growth_rate=0.15,
        months=6,
    )
    return {"current_mrr": current_mrr, "forecast": forecast, "growth_rate": 0.15}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
