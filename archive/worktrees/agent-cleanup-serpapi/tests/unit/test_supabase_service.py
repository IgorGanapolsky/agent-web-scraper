"""
Tests for Supabase Service - Persistent Context Storage
Tests for revenue tracking and customer data persistence
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.services.supabase_service import PersistentContext, SupabaseService


class TestPersistentContext:
    """Test persistent context model"""

    def test_persistent_context_creation(self):
        """Test creating persistent context"""
        context_id = str(uuid4())
        now = datetime.utcnow()

        context = PersistentContext(
            id=context_id,
            context_type="payment",
            stripe_id="cus_test123",
            customer_email="test@example.com",
            data={"amount": 79.0, "currency": "usd"},
            metadata={"trial": True},
            created_at=now,
            updated_at=now,
        )

        assert context.id == context_id
        assert context.context_type == "payment"
        assert context.stripe_id == "cus_test123"
        assert context.customer_email == "test@example.com"
        assert context.data["amount"] == 79.0
        assert context.metadata["trial"] is True


class TestSupabaseService:
    """Test Supabase service operations"""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch("app.services.supabase_service.settings") as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_key = "test_key"
            mock_settings.daily_revenue_target = 600
            mock_settings.trial_period_days = 3
            mock_settings.stripe_live_mode = True
            yield mock_settings

    @pytest.fixture
    def mock_client(self):
        """Mock Supabase client"""
        with patch("app.services.supabase_service.create_client") as mock_create:
            client = MagicMock()
            mock_create.return_value = client
            yield client

    @pytest.fixture
    def service(self, mock_settings, mock_client):
        """Create Supabase service instance"""
        with patch.object(SupabaseService, "_ensure_persistent_context_table"):
            return SupabaseService()

    def test_initialization_success(self, mock_settings, mock_client):
        """Test successful service initialization"""
        with patch.object(SupabaseService, "_ensure_persistent_context_table"):
            service = SupabaseService()
            assert service.client == mock_client

    def test_initialization_missing_config(self):
        """Test initialization with missing configuration"""
        with patch("app.services.supabase_service.settings") as mock_settings:
            mock_settings.supabase_url = None
            mock_settings.supabase_key = "test_key"

            with pytest.raises(
                ValueError, match="Supabase URL and key must be configured"
            ):
                SupabaseService()

    def test_ensure_persistent_context_table_success(self, service):
        """Test table verification success"""
        service.client.table.return_value.select.return_value.limit.return_value.execute.return_value = (
            True
        )

        # Should not raise exception
        service._ensure_persistent_context_table()

    def test_ensure_persistent_context_table_missing(self, service):
        """Test handling missing table"""
        service.client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Table not found"
        )

        with patch("app.services.supabase_service.logger") as mock_logger:
            service._ensure_persistent_context_table()
            mock_logger.warning.assert_called()

    def test_get_table_schema(self, service):
        """Test table schema generation"""
        schema = service._get_table_schema()

        assert "CREATE TABLE IF NOT EXISTS persistent_context" in schema
        assert "id UUID PRIMARY KEY" in schema
        assert "context_type VARCHAR(50)" in schema
        assert "stripe_id VARCHAR(255)" in schema
        assert "customer_email VARCHAR(255)" in schema
        assert "data JSONB NOT NULL" in schema

    def test_store_payment_context_success(self, service):
        """Test successful payment context storage"""
        service.client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        context_id = service.store_payment_context(
            stripe_id="cus_test123",
            customer_email="test@example.com",
            payment_data={"amount": 79.0, "currency": "usd"},
        )

        assert context_id is not None
        service.client.table.assert_called_with("persistent_context")

    def test_store_payment_context_error(self, service):
        """Test payment context storage error"""
        service.client.table.return_value.insert.return_value.execute.side_effect = (
            Exception("DB Error")
        )

        with pytest.raises(Exception, match="DB Error"):
            service.store_payment_context(
                stripe_id="cus_test123",
                customer_email="test@example.com",
                payment_data={"amount": 79.0},
            )

    def test_store_trial_context_success(self, service):
        """Test successful trial context storage"""
        service.client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )
        trial_end = datetime.utcnow() + timedelta(days=3)

        context_id = service.store_trial_context(
            customer_email="trial@example.com",
            trial_data={"trial_days": 3, "conversion_target": "24h"},
            trial_end_date=trial_end,
        )

        assert context_id is not None

    def test_store_conversion_context_success(self, service):
        """Test successful conversion context storage"""
        service.client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        context_id = service.store_conversion_context(
            customer_email="convert@example.com",
            conversion_data={"amount": 79.0, "conversion_time_hours": 18},
            stripe_subscription_id="sub_test123",
        )

        assert context_id is not None

    def test_get_trial_contexts_for_email_trigger(self, service):
        """Test getting trial contexts for email trigger"""
        mock_data = [
            {
                "id": "ctx_123",
                "customer_email": "trial1@example.com",
                "data": {"trial_days": 3},
                "metadata": {"email_cta_scheduled": False},
            }
        ]
        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.eq.return_value.execute.return_value.data = (
            mock_data
        )

        contexts = service.get_trial_contexts_for_email_trigger()

        assert len(contexts) == 1
        assert contexts[0]["customer_email"] == "trial1@example.com"

    def test_get_trial_contexts_error(self, service):
        """Test error handling in getting trial contexts"""
        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.eq.return_value.execute.side_effect = Exception(
            "Query error"
        )

        contexts = service.get_trial_contexts_for_email_trigger()
        assert contexts == []

    def test_mark_email_cta_sent_success(self, service):
        """Test marking email CTA as sent"""
        service.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )

        # Should not raise exception
        service.mark_email_cta_sent("ctx_123")

        service.client.table.assert_called_with("persistent_context")

    def test_mark_email_cta_sent_error(self, service):
        """Test error handling when marking email CTA"""
        service.client.table.return_value.update.return_value.eq.return_value.execute.side_effect = Exception(
            "Update error"
        )

        with patch("app.services.supabase_service.logger") as mock_logger:
            service.mark_email_cta_sent("ctx_123")
            mock_logger.error.assert_called()

    def test_get_revenue_metrics_success(self, service):
        """Test getting revenue metrics"""
        # Mock payment data
        payment_data = [
            {"data": {"amount": 79.0}},
            {"data": {"amount": 50.0}},
        ]
        # Mock conversion data
        conversion_data = [
            {"data": {"amount": 79.0}},
        ]

        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value.data = (
            payment_data
        )

        def mock_execute_side_effect(*args, **kwargs):
            # Return different data based on the eq call (payment vs conversion)
            call_stack = str(
                service.client.table.return_value.select.return_value.eq.call_args_list
            )
            if "payment" in call_stack:
                return MagicMock(data=payment_data)
            else:
                return MagicMock(data=conversion_data)

        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.side_effect = (
            mock_execute_side_effect
        )

        metrics = service.get_revenue_metrics(days=7)

        assert "total_revenue" in metrics
        assert "total_conversions" in metrics
        assert "daily_average" in metrics
        assert "target_achievement" in metrics

    def test_get_revenue_metrics_error(self, service):
        """Test error handling in revenue metrics"""
        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.side_effect = Exception(
            "Query error"
        )

        metrics = service.get_revenue_metrics()
        assert metrics == {}

    def test_get_customer_context_success(self, service):
        """Test getting customer context"""
        mock_data = [
            {
                "id": "ctx_123",
                "context_type": "payment",
                "customer_email": "customer@example.com",
                "data": {"amount": 79.0},
            }
        ]
        service.client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
            mock_data
        )

        contexts = service.get_customer_context("customer@example.com")

        assert len(contexts) == 1
        assert contexts[0]["customer_email"] == "customer@example.com"

    def test_get_customer_context_error(self, service):
        """Test error handling in getting customer context"""
        service.client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception(
            "Query error"
        )

        contexts = service.get_customer_context("customer@example.com")
        assert contexts == []

    def test_cleanup_expired_contexts_success(self, service):
        """Test cleaning up expired contexts"""
        service.client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [
            {"id": "expired_1"},
            {"id": "expired_2"},
        ]

        with patch("app.services.supabase_service.logger") as mock_logger:
            service.cleanup_expired_contexts()
            mock_logger.info.assert_called_with("Cleaned up 2 expired contexts")

    def test_cleanup_expired_contexts_no_data(self, service):
        """Test cleanup when no data returned"""
        service.client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = (
            None
        )

        with patch("app.services.supabase_service.logger") as mock_logger:
            service.cleanup_expired_contexts()
            mock_logger.info.assert_called_with("Cleaned up 0 expired contexts")

    def test_cleanup_expired_contexts_error(self, service):
        """Test error handling in cleanup"""
        service.client.table.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception(
            "Delete error"
        )

        with patch("app.services.supabase_service.logger") as mock_logger:
            service.cleanup_expired_contexts()
            mock_logger.error.assert_called()


# Integration tests for revenue scenarios
class TestSupabaseServiceIntegration:
    """Test complete revenue tracking scenarios"""

    @pytest.fixture
    def service(self):
        """Create service with mocked client"""
        with (
            patch("app.services.supabase_service.settings") as mock_settings,
            patch("app.services.supabase_service.create_client") as mock_create,
            patch.object(SupabaseService, "_ensure_persistent_context_table"),
        ):
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_key = "test_key"
            mock_settings.daily_revenue_target = 600
            mock_settings.trial_period_days = 3
            mock_settings.stripe_live_mode = True

            client = MagicMock()
            mock_create.return_value = client

            service = SupabaseService()
            service.client = client
            return service

    def test_complete_customer_journey(self, service):
        """Test complete customer journey from trial to payment"""
        service.client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock()
        )

        # Step 1: Store trial context
        trial_end = datetime.utcnow() + timedelta(days=3)
        trial_id = service.store_trial_context(
            customer_email="journey@example.com",
            trial_data={"trial_type": "3_day", "source": "meta_ads"},
            trial_end_date=trial_end,
        )
        assert trial_id is not None

        # Step 2: Store payment context
        payment_id = service.store_payment_context(
            stripe_id="cus_journey123",
            customer_email="journey@example.com",
            payment_data={"amount": 79.0, "currency": "usd", "discount": "REVENUE20"},
        )
        assert payment_id is not None

        # Step 3: Store conversion context
        conversion_id = service.store_conversion_context(
            customer_email="journey@example.com",
            conversion_data={"amount": 79.0, "conversion_time_hours": 18},
            stripe_subscription_id="sub_journey456",
        )
        assert conversion_id is not None

    def test_revenue_tracking_scenario(self, service):
        """Test revenue tracking for $600/day target"""
        # Mock multiple payment contexts
        payment_contexts = [
            {"data": {"amount": 79.0}},  # Customer 1
            {"data": {"amount": 79.0}},  # Customer 2
            {"data": {"amount": 79.0}},  # Customer 3
            {"data": {"amount": 79.0}},  # Customer 4
            {"data": {"amount": 79.0}},  # Customer 5
            {"data": {"amount": 79.0}},  # Customer 6
            {"data": {"amount": 79.0}},  # Customer 7
            {"data": {"amount": 79.0}},  # Customer 8 = $632 total
        ]

        conversion_contexts = [
            {"data": {"amount": 79.0}},  # 8 conversions
        ] * 8

        def mock_execute_for_metrics(*args, **kwargs):
            # Check which query is being executed
            call_str = str(service.client.table.call_args_list)
            if "payment" in call_str:
                return MagicMock(data=payment_contexts)
            else:
                return MagicMock(data=conversion_contexts)

        service.client.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.side_effect = (
            mock_execute_for_metrics
        )

        metrics = service.get_revenue_metrics(days=1)

        # Check calculations
        total_revenue = 8 * 79.0  # $632
        daily_average = total_revenue / 1  # $632/day

        assert metrics["total_revenue"] == total_revenue
        assert metrics["daily_average"] == daily_average
        assert metrics["target_achievement"] is True  # $632 > $600
        assert metrics["total_conversions"] == 8
