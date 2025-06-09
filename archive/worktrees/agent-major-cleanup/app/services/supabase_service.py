"""
Supabase Integration Service
Handles persistent context storage for live payment and customer data
"""

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel
from supabase import Client, create_client

from app.config.logging import get_logger
from app.config.settings import settings

logger = get_logger(__name__)


class PersistentContext(BaseModel):
    """Persistent context model for storing payment and customer data"""

    id: str
    context_type: str  # payment, customer, subscription, trial, conversion
    stripe_id: Optional[str] = None
    customer_email: Optional[str] = None
    data: dict[str, Any]
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class SupabaseService:
    """Handles all Supabase operations for persistent context storage"""

    def __init__(self):
        """Initialize Supabase client"""
        if not settings.supabase_url or not settings.supabase_key:
            raise ValueError("Supabase URL and key must be configured")

        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_key
        )

        # Ensure table exists
        self._ensure_persistent_context_table()

    def _ensure_persistent_context_table(self):
        """Ensure the persistent_context table exists with proper schema"""
        try:
            # Check if table exists by attempting a simple query
            self.client.table("persistent_context").select("id").limit(1).execute()
            logger.info("persistent_context table verified")
        except Exception:
            logger.warning(
                "persistent_context table may not exist - ensure it's created with SQL:"
            )
            logger.warning(self._get_table_schema())

    def _get_table_schema(self) -> str:
        """Return SQL schema for persistent_context table"""
        return """
        CREATE TABLE IF NOT EXISTS persistent_context (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            context_type VARCHAR(50) NOT NULL,
            stripe_id VARCHAR(255),
            customer_email VARCHAR(255),
            data JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,

            -- Indexes for performance
            INDEX idx_context_type ON persistent_context(context_type),
            INDEX idx_stripe_id ON persistent_context(stripe_id),
            INDEX idx_customer_email ON persistent_context(customer_email),
            INDEX idx_created_at ON persistent_context(created_at)
        );

        -- Enable RLS (Row Level Security)
        ALTER TABLE persistent_context ENABLE ROW LEVEL SECURITY;

        -- Create policy for service role access
        CREATE POLICY "Enable all operations for service role" ON persistent_context
        FOR ALL USING (auth.role() = 'service_role');
        """

    def store_payment_context(
        self,
        stripe_id: str,
        customer_email: str,
        payment_data: dict[str, Any],
        context_type: str = "payment",
    ) -> str:
        """Store payment context for revenue tracking"""
        context_id = str(uuid4())

        context = {
            "id": context_id,
            "context_type": context_type,
            "stripe_id": stripe_id,
            "customer_email": customer_email,
            "data": payment_data,
            "metadata": {
                "revenue_target": settings.daily_revenue_target,
                "trial_days": settings.trial_period_days,
                "live_mode": settings.stripe_live_mode,
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            self.client.table("persistent_context").insert(context).execute()
            logger.info(f"Stored {context_type} context for {customer_email}")
            return context_id
        except Exception as e:
            logger.error(f"Failed to store payment context: {e}")
            raise

    def store_trial_context(
        self, customer_email: str, trial_data: dict[str, Any], trial_end_date: datetime
    ) -> str:
        """Store trial context with conversion tracking"""
        context_id = str(uuid4())

        context = {
            "id": context_id,
            "context_type": "trial",
            "customer_email": customer_email,
            "data": trial_data,
            "metadata": {
                "trial_length_days": settings.trial_period_days,
                "conversion_target_24h": True,
                "email_cta_scheduled": False,
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "expires_at": trial_end_date.isoformat(),
        }

        try:
            self.client.table("persistent_context").insert(context).execute()
            logger.info(
                f"Stored trial context for {customer_email}, expires: {trial_end_date}"
            )
            return context_id
        except Exception as e:
            logger.error(f"Failed to store trial context: {e}")
            raise

    def store_conversion_context(
        self,
        customer_email: str,
        conversion_data: dict[str, Any],
        stripe_subscription_id: str,
    ) -> str:
        """Store conversion context when trial converts to paid"""
        context_id = str(uuid4())

        context = {
            "id": context_id,
            "context_type": "conversion",
            "stripe_id": stripe_subscription_id,
            "customer_email": customer_email,
            "data": conversion_data,
            "metadata": {
                "converted_from_trial": True,
                "revenue_contribution": conversion_data.get("amount", 0),
                "conversion_time_hours": conversion_data.get(
                    "conversion_time_hours", 0
                ),
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        try:
            self.client.table("persistent_context").insert(context).execute()
            logger.info(f"Stored conversion context for {customer_email}")
            return context_id
        except Exception as e:
            logger.error(f"Failed to store conversion context: {e}")
            raise

    def get_trial_contexts_for_email_trigger(self) -> list[dict[str, Any]]:
        """Get trial contexts ready for 24-hour email trigger"""
        try:
            # Find trials created 24 hours ago that haven't received email CTA
            twenty_four_hours_ago = (
                datetime.utcnow().replace(hour=datetime.utcnow().hour - 24).isoformat()
            )

            result = (
                self.client.table("persistent_context")
                .select("*")
                .eq("context_type", "trial")
                .gte("created_at", twenty_four_hours_ago)
                .eq("metadata->>email_cta_scheduled", "false")
                .execute()
            )

            return result.data
        except Exception as e:
            logger.error(f"Failed to get trial contexts for email trigger: {e}")
            return []

    def mark_email_cta_sent(self, context_id: str) -> None:
        """Mark that 24-hour email CTA has been sent"""
        try:
            # Update metadata to mark email as sent
            self.client.table("persistent_context").update(
                {
                    "metadata": {
                        "email_cta_scheduled": True,
                        "email_sent_at": datetime.utcnow().isoformat(),
                    },
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", context_id).execute()

            logger.info(f"Marked email CTA as sent for context {context_id}")
        except Exception as e:
            logger.error(f"Failed to mark email CTA as sent: {e}")

    def get_revenue_metrics(self, days: int = 7) -> dict[str, Any]:
        """Get revenue metrics for the specified period"""
        try:
            start_date = (
                datetime.utcnow().replace(day=datetime.utcnow().day - days).isoformat()
            )

            # Get payment contexts
            payments = (
                self.client.table("persistent_context")
                .select("*")
                .eq("context_type", "payment")
                .gte("created_at", start_date)
                .execute()
            )

            # Get conversion contexts
            conversions = (
                self.client.table("persistent_context")
                .select("*")
                .eq("context_type", "conversion")
                .gte("created_at", start_date)
                .execute()
            )

            # Calculate metrics
            total_revenue = sum(
                ctx.get("data", {}).get("amount", 0) for ctx in payments.data
            )
            total_conversions = len(conversions.data)
            daily_average = total_revenue / days if days > 0 else 0

            return {
                "total_revenue": total_revenue,
                "total_conversions": total_conversions,
                "daily_average": daily_average,
                "target_achievement": daily_average >= settings.daily_revenue_target,
                "days_to_target": max(
                    0,
                    (settings.daily_revenue_target - daily_average)
                    / max(daily_average * 0.1, 1),
                ),
                "payment_count": len(payments.data),
                "conversion_rate": total_conversions / max(len(payments.data), 1) * 100,
            }
        except Exception as e:
            logger.error(f"Failed to get revenue metrics: {e}")
            return {}

    def get_customer_context(self, customer_email: str) -> list[dict[str, Any]]:
        """Get all context for a specific customer"""
        try:
            result = (
                self.client.table("persistent_context")
                .select("*")
                .eq("customer_email", customer_email)
                .order("created_at", desc=True)
                .execute()
            )

            return result.data
        except Exception as e:
            logger.error(f"Failed to get customer context: {e}")
            return []

    def cleanup_expired_contexts(self):
        """Clean up expired context entries"""
        try:
            current_time = datetime.utcnow().isoformat()

            result = (
                self.client.table("persistent_context")
                .delete()
                .lt("expires_at", current_time)
                .execute()
            )

            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {deleted_count} expired contexts")

        except Exception as e:
            logger.error(f"Failed to cleanup expired contexts: {e}")
