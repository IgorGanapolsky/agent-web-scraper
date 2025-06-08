"""
MCP Customer Dashboard Server
Handles authentication, billing management, and usage analytics
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config.logging import get_logger
from app.mcp.stripe_server import MCPStripeServer

logger = get_logger(__name__)
security = HTTPBearer()


class CustomerAuth(BaseModel):
    """Customer authentication model"""

    email: str
    password: str


class CustomerProfile(BaseModel):
    """Customer profile model"""

    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    tier: str
    subscription_status: str
    trial_end: Optional[datetime] = None
    created_at: datetime


class UsageMetrics(BaseModel):
    """Customer usage metrics"""

    api_calls_current_month: int
    api_calls_limit: int
    reports_generated: int
    insights_accessed: int
    last_activity: datetime


class BillingInfo(BaseModel):
    """Customer billing information"""

    tier: str
    amount: float
    billing_cycle: str
    next_billing_date: datetime
    payment_method: Optional[str] = None
    subscription_status: str


class MCPDashboardServer:
    """MCP Server for Customer Dashboard Operations"""

    def __init__(self, test_mode: bool = False):
        """Initialize dashboard server"""
        self.test_mode = test_mode
        self.stripe_server = MCPStripeServer(test_mode=test_mode)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        # JWT configuration
        self.jwt_secret = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(days=7)

    def create_access_token(self, customer_id: str) -> str:
        """Create JWT access token for customer"""

        expires = datetime.utcnow() + self.jwt_expiration
        payload = {"customer_id": customer_id, "exp": expires, "iat": datetime.utcnow()}

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> str:
        """Verify JWT token and return customer ID"""

        try:
            payload = jwt.decode(
                credentials.credentials,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
            customer_id = payload.get("customer_id")
            if not customer_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            return customer_id

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def authenticate_customer(self, auth: CustomerAuth) -> dict:
        """Authenticate customer and return access token"""

        if self.test_mode:
            # Mock authentication for testing
            return {
                "access_token": self.create_access_token("test_customer"),
                "token_type": "bearer",
                "customer_id": "test_customer",
            }

        # In production, verify against database
        # customer = await self.customer_service.get_customer_by_email(auth.email)
        # if not customer or not self.pwd_context.verify(auth.password, customer.password_hash):
        #     raise HTTPException(status_code=401, detail="Invalid credentials")

        # For now, mock successful authentication
        customer_id = f"cust_{hash(auth.email)}"
        access_token = self.create_access_token(customer_id)

        logger.info(f"Customer authenticated: {auth.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "customer_id": customer_id,
        }

    async def get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Get customer profile information"""

        if self.test_mode:
            return CustomerProfile(
                email="test@example.com",
                name="Test Customer",
                company="Test Company",
                tier="pro",
                subscription_status="active",
                trial_end=None,
                created_at=datetime.now() - timedelta(days=30),
            )

        # In production, fetch from database
        # customer = await self.customer_service.get_customer(customer_id)
        # subscriptions = await self.stripe_server.get_customer_subscriptions(customer.stripe_id)

        # Mock profile for now
        return CustomerProfile(
            email="customer@example.com",
            name="John Doe",
            company="Acme Corp",
            tier="pro",
            subscription_status="active",
            created_at=datetime.now() - timedelta(days=60),
        )

    async def get_usage_metrics(self, customer_id: str) -> UsageMetrics:
        """Get customer usage analytics"""

        if self.test_mode:
            return UsageMetrics(
                api_calls_current_month=1250,
                api_calls_limit=100000,
                reports_generated=15,
                insights_accessed=47,
                last_activity=datetime.now() - timedelta(hours=2),
            )

        # In production, fetch from usage tracking system
        # usage = await self.usage_service.get_customer_usage(customer_id)

        # Mock usage for now
        return UsageMetrics(
            api_calls_current_month=2100,
            api_calls_limit=100000,
            reports_generated=8,
            insights_accessed=23,
            last_activity=datetime.now() - timedelta(minutes=30),
        )

    async def get_billing_info(self, customer_id: str) -> BillingInfo:
        """Get customer billing information"""

        if self.test_mode:
            return BillingInfo(
                tier="pro",
                amount=99.00,
                billing_cycle="monthly",
                next_billing_date=datetime.now() + timedelta(days=15),
                payment_method="**** **** **** 4242",
                subscription_status="active",
            )

        # In production, fetch from Stripe and database
        # customer = await self.customer_service.get_customer(customer_id)
        # subscriptions = await self.stripe_server.get_customer_subscriptions(customer.stripe_id)

        return BillingInfo(
            tier="pro",
            amount=99.00,
            billing_cycle="monthly",
            next_billing_date=datetime.now() + timedelta(days=20),
            payment_method="**** **** **** 1234",
            subscription_status="active",
        )

    async def get_revenue_dashboard(self, customer_id: str) -> dict:
        """Get revenue analytics dashboard data"""

        # Verify customer has access to revenue data (admin/enterprise only)
        profile = await self.get_customer_profile(customer_id)

        if profile.tier not in ["enterprise", "admin"]:
            raise HTTPException(
                status_code=403, detail="Revenue dashboard requires Enterprise tier"
            )

        # Get comprehensive revenue metrics
        metrics = await self.stripe_server.get_revenue_metrics()

        return {
            "current_metrics": metrics,
            "growth_trends": {
                "mrr_growth": 15.0,  # 15% monthly growth
                "customer_growth": 12.0,  # 12% customer growth
                "ltv_trend": 8.5,  # 8.5% LTV improvement
                "churn_improvement": -2.1,  # 2.1% churn reduction
            },
            "forecasts": {
                "next_month_mrr": metrics["monthly_revenue"] * 1.15,
                "next_quarter_arr": metrics["arr"] * 1.45,
                "year_end_projection": 504000.0,  # $504K ARR target
            },
            "automation_stats": {
                "automation_rate": metrics["automation_rate"],
                "ai_agents_active": 5,
                "workflows_running": 12,
                "uptime": 99.95,
            },
        }

    async def update_customer_profile(
        self, customer_id: str, updates: dict
    ) -> CustomerProfile:
        """Update customer profile information"""

        # In production, validate and update database
        # await self.customer_service.update_customer(customer_id, updates)

        logger.info(f"Profile updated for customer {customer_id}")

        return await self.get_customer_profile(customer_id)

    async def generate_api_key(self, customer_id: str) -> dict:
        """Generate new API key for customer"""

        profile = await self.get_customer_profile(customer_id)

        if profile.tier == "basic":
            raise HTTPException(
                status_code=403, detail="API access requires Pro or Enterprise tier"
            )

        # Generate secure API key
        import secrets

        api_key = f"sgd_{secrets.token_urlsafe(32)}"

        # In production, store in database with proper scoping
        # await self.api_key_service.create_api_key(customer_id, api_key, profile.tier)

        logger.info(f"API key generated for customer {customer_id}")

        return {
            "api_key": api_key,
            "tier": profile.tier,
            "rate_limits": {
                "basic": "10,000 requests/month",
                "pro": "100,000 requests/month",
                "enterprise": "Unlimited",
            }[profile.tier],
            "created_at": datetime.now().isoformat(),
        }

    async def get_subscription_analytics(self, customer_id: str) -> dict:
        """Get detailed subscription analytics"""

        usage = await self.get_usage_metrics(customer_id)
        billing = await self.get_billing_info(customer_id)

        return {
            "subscription_health": {
                "status": billing.subscription_status,
                "tier": billing.tier,
                "usage_percentage": (
                    usage.api_calls_current_month / usage.api_calls_limit
                )
                * 100,
                "engagement_score": min(
                    100, (usage.insights_accessed / 30) * 100
                ),  # Based on monthly access
            },
            "usage_trends": {
                "api_calls_trend": "+12% vs last month",
                "reports_trend": "+8% vs last month",
                "insights_trend": "+15% vs last month",
            },
            "recommendations": self._get_usage_recommendations(usage, billing),
            "upgrade_opportunities": self._get_upgrade_opportunities(usage, billing),
        }

    def _get_usage_recommendations(
        self, usage: UsageMetrics, billing: BillingInfo
    ) -> list[str]:
        """Generate usage recommendations"""

        recommendations = []

        usage_percentage = (usage.api_calls_current_month / usage.api_calls_limit) * 100

        if usage_percentage > 80:
            recommendations.append("Consider upgrading to avoid hitting API limits")
        elif usage_percentage < 20:
            recommendations.append(
                "You're using only a small portion of your plan - consider downgrading"
            )

        if usage.last_activity < datetime.now() - timedelta(days=7):
            recommendations.append(
                "You haven't been active recently - check out our latest features"
            )

        if usage.reports_generated == 0:
            recommendations.append(
                "Generate your first automated report to see the platform's power"
            )

        return recommendations

    def _get_upgrade_opportunities(
        self, usage: UsageMetrics, billing: BillingInfo
    ) -> list[dict]:
        """Identify upgrade opportunities"""

        opportunities = []

        if billing.tier == "basic" and usage.api_calls_current_month > 5000:
            opportunities.append(
                {
                    "type": "tier_upgrade",
                    "from_tier": "basic",
                    "to_tier": "pro",
                    "benefit": "10x more API calls + Advanced analytics",
                    "savings": "Better value at higher usage",
                }
            )

        if billing.tier == "pro" and usage.api_calls_current_month > 50000:
            opportunities.append(
                {
                    "type": "tier_upgrade",
                    "from_tier": "pro",
                    "to_tier": "enterprise",
                    "benefit": "Unlimited API calls + Dedicated support",
                    "savings": "No usage limits + premium features",
                }
            )

        if billing.billing_cycle == "monthly":
            opportunities.append(
                {
                    "type": "billing_upgrade",
                    "from_cycle": "monthly",
                    "to_cycle": "annual",
                    "benefit": "Save 2 months per year",
                    "savings": f"${billing.amount * 2:.0f} annual savings",
                }
            )

        return opportunities
