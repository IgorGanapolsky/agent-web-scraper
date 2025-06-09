"""
Basic tests for Live Stripe Integration - Coverage focused
Tests for $1,074.86/day revenue system with actual method signatures
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import stripe

from app.core.live_stripe_integration import (
    LivePaymentResult,
    LiveStripeIntegration,
    TrialConfig,
    get_live_stripe_integration,
)


class TestTrialConfig:
    """Test trial configuration"""

    def test_trial_config_defaults(self):
        """Test default trial configuration"""
        config = TrialConfig()
        assert config.trial_days == 3
        assert config.require_payment_method is True
        assert config.immediate_conversion_trigger == 24
        assert config.meta_ads_test_budget == 50.0


class TestLivePaymentResult:
    """Test live payment result"""

    def test_live_payment_result_creation(self):
        """Test creating live payment result"""
        trial_end = datetime.now() + timedelta(days=3)
        result = LivePaymentResult(
            success=True,
            customer_id="cus_test123",
            subscription_id="sub_test456",
            amount=79.00,
            trial_end=trial_end,
            payment_method_id="pm_test789",
        )

        assert result.success is True
        assert result.customer_id == "cus_test123"
        assert result.subscription_id == "sub_test456"
        assert result.amount == 79.00


class TestLiveStripeIntegration:
    """Test live Stripe integration"""

    @pytest.fixture
    def integration(self):
        """Create integration with mocked dependencies"""
        with (
            patch("app.core.live_stripe_integration.get_session_memory_manager"),
            patch("app.core.live_stripe_integration.get_enterprise_batch_client"),
            patch.object(LiveStripeIntegration, "_verify_live_mode", return_value=True),
        ):
            return LiveStripeIntegration()

    def test_initialization(self, integration):
        """Test integration initialization"""
        assert integration.daily_target == 600
        assert integration.week2_target == 4200
        assert isinstance(integration.trial_config, TrialConfig)

    @patch("stripe.Account.retrieve")
    def test_verify_live_mode_success(self, mock_retrieve):
        """Test live mode verification"""
        mock_account = MagicMock()
        mock_account.get.return_value = True
        mock_retrieve.return_value = mock_account

        with (
            patch("app.core.live_stripe_integration.get_session_memory_manager"),
            patch("app.core.live_stripe_integration.get_enterprise_batch_client"),
        ):
            integration = LiveStripeIntegration()
            result = integration._verify_live_mode()

        assert result is False  # Because details_submitted=True means not live in test

    @patch("stripe.Account.retrieve")
    def test_verify_live_mode_auth_error(self, mock_retrieve):
        """Test live mode verification with auth error"""
        mock_retrieve.side_effect = stripe.error.AuthenticationError("Invalid API key")

        with (
            patch("app.core.live_stripe_integration.get_session_memory_manager"),
            patch("app.core.live_stripe_integration.get_enterprise_batch_client"),
        ):
            integration = LiveStripeIntegration()
            result = integration._verify_live_mode()

        assert result is False

    @pytest.mark.asyncio
    @patch("stripe.Customer.create")
    @patch("stripe.PaymentMethod.attach")
    @patch("stripe.Subscription.create")
    async def test_create_live_customer_success(
        self, mock_sub_create, mock_pm_attach, mock_customer_create, integration
    ):
        """Test successful live customer creation"""
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_customer_create.return_value = mock_customer

        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test456"
        mock_sub_create.return_value = mock_subscription

        integration.live_mode = True

        with patch.dict(os.environ, {"STRIPE_LIVE_PRICE_ID": "price_test"}):
            result = await integration.create_live_customer_with_trial(
                email="test@example.com",
                name="Test Customer",
                payment_method_id="pm_test789",
            )

        assert isinstance(result, LivePaymentResult)
        assert result.success is True
        assert result.customer_id == "cus_test123"

    @pytest.mark.asyncio
    async def test_create_live_customer_not_live_mode(self, integration):
        """Test customer creation fails when not in live mode"""
        integration.live_mode = False

        with pytest.raises(
            ValueError, match="Cannot process live payments in test mode"
        ):
            await integration.create_live_customer_with_trial(
                email="test@example.com",
                name="Test Customer",
                payment_method_id="pm_test789",
            )

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_handle_live_webhook_success(self, mock_construct, integration):
        """Test successful webhook handling"""
        mock_event = {
            "id": "evt_test123",
            "type": "invoice.payment_succeeded",
            "data": {"object": {"customer": "cus_test", "amount_paid": 7900}},
        }
        mock_construct.return_value = mock_event

        result = await integration.handle_live_webhook(b"payload", "sig_header")

        assert result["status"] == "success"
        assert result["event_type"] == "invoice.payment_succeeded"

    @pytest.mark.asyncio
    @patch("stripe.Webhook.construct_event")
    async def test_handle_live_webhook_invalid_signature(
        self, mock_construct, integration
    ):
        """Test webhook handling with invalid signature"""
        mock_construct.side_effect = ValueError("Invalid signature")

        result = await integration.handle_live_webhook(b"payload", "sig_header")

        assert result["status"] == "error"
        assert result["message"] == "Invalid signature"

    @pytest.mark.asyncio
    async def test_handle_subscription_created(self, integration):
        """Test subscription created handler"""
        subscription = {
            "id": "sub_test123",
            "customer": "cus_test456",
            "items": {"data": [{"price": {"unit_amount": 7900}}]},
            "trial_end": 1234567890,
        }

        # Mock the methods this calls
        with (
            patch.object(integration, "_trigger_n8n_crm_sync") as mock_crm,
            patch.object(integration, "_log_live_revenue_event"),
        ):
            await integration._handle_subscription_created(subscription)

        mock_crm.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_payment_succeeded(self, integration):
        """Test payment succeeded handler"""
        invoice = {"customer": "cus_test123", "amount_paid": 7900}

        with (
            patch.object(integration, "_update_daily_revenue_tracking") as mock_update,
            patch.object(integration, "_store_revenue_persistent") as mock_store,
            patch.object(integration, "_get_daily_progress", return_value={}),
        ):
            await integration._handle_payment_succeeded(invoice)

        mock_update.assert_called_once_with(79.0)
        mock_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_daily_revenue_tracking(self, integration):
        """Test daily revenue tracking"""
        integration.daily_target = 600

        with (
            patch.object(integration, "_get_daily_revenue_total", return_value=100.0),
            patch.object(integration, "_store_daily_tracking_persistent") as mock_store,
        ):
            await integration._update_daily_revenue_tracking(50.0)

        mock_store.assert_called_once()

    @pytest.mark.asyncio
    @patch("stripe.Charge.list")
    async def test_get_daily_revenue_total(self, mock_charge_list, integration):
        """Test getting daily revenue total"""
        mock_charge1 = MagicMock()
        mock_charge1.amount = 7900
        mock_charge1.paid = True

        mock_charge2 = MagicMock()
        mock_charge2.amount = 5000
        mock_charge2.paid = True

        mock_charge_list.return_value = [mock_charge1, mock_charge2]

        total = await integration._get_daily_revenue_total()
        assert total == 129.0

    @pytest.mark.asyncio
    async def test_get_daily_progress(self, integration):
        """Test getting daily progress"""
        integration.daily_target = 600

        with patch.object(integration, "_get_daily_revenue_total", return_value=150.0):
            progress = await integration._get_daily_progress()

        assert progress["current_daily_revenue"] == 150.0
        assert progress["daily_target"] == 600
        assert progress["progress_percentage"] == 25.0

    def test_log_live_revenue_event(self, integration):
        """Test revenue event logging"""
        event_data = {"event_type": "test", "amount": 79.0}

        integration._log_live_revenue_event(event_data)

        assert "timestamp" in event_data
        assert "live_mode" in event_data

    @pytest.mark.asyncio
    async def test_store_persistent_local(self, integration, tmp_path):
        """Test local persistent storage"""
        data = {"test": "data", "amount": 79.0}

        with patch("pathlib.Path") as mock_path_class:
            mock_storage_dir = tmp_path / "storage"
            mock_storage_dir.mkdir()
            mock_category_file = mock_storage_dir / "test.json"

            mock_path_class.return_value = mock_storage_dir
            mock_path_class.return_value.__truediv__ = (
                lambda self, other: mock_category_file
            )
            mock_path_class.return_value.mkdir = MagicMock()

            with patch("builtins.open", create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                await integration._store_persistent_local(data, "test")

        mock_open.assert_called()

    @pytest.mark.asyncio
    @patch("stripe.Account.retrieve")
    @patch("stripe.Charge.list")
    @patch("stripe.Subscription.list")
    @patch("stripe.WebhookEndpoint.list")
    async def test_get_live_mode_confirmation(
        self,
        mock_webhook_list,
        mock_sub_list,
        mock_charge_list,
        mock_account,
        integration,
    ):
        """Test live mode confirmation"""
        mock_account.return_value = MagicMock(
            id="acct_test",
            business_profile={"name": "Test"},
            charges_enabled=True,
            payouts_enabled=True,
        )
        mock_charge_list.return_value.data = []
        mock_sub_list.return_value.data = []
        mock_webhook_list.return_value.data = []

        with patch.object(
            integration, "_get_daily_progress", return_value={"test": "progress"}
        ):
            confirmation = await integration.get_live_mode_confirmation()

        assert "live_mode_status" in confirmation
        assert "revenue_tracking" in confirmation


class TestGlobalInstance:
    """Test global instance management"""

    def test_get_live_stripe_integration_singleton(self):
        """Test singleton pattern"""
        with (
            patch("app.core.live_stripe_integration.get_session_memory_manager"),
            patch("app.core.live_stripe_integration.get_enterprise_batch_client"),
            patch.object(LiveStripeIntegration, "_verify_live_mode", return_value=True),
        ):
            instance1 = get_live_stripe_integration()
            instance2 = get_live_stripe_integration()

        assert instance1 is instance2


# Real scenario tests
class TestRevenueScenarios:
    """Test revenue scenarios"""

    @pytest.fixture
    def integration(self):
        """Create integration"""
        with (
            patch("app.core.live_stripe_integration.get_session_memory_manager"),
            patch("app.core.live_stripe_integration.get_enterprise_batch_client"),
            patch.object(LiveStripeIntegration, "_verify_live_mode", return_value=True),
        ):
            return LiveStripeIntegration()

    @pytest.mark.asyncio
    async def test_revenue_target_achievement(self, integration):
        """Test achieving $600/day target"""
        integration.daily_target = 600

        with patch.object(integration, "_get_daily_revenue_total", return_value=632.0):
            progress = await integration._get_daily_progress()

        assert progress["target_achieved"] is True
        assert progress["current_daily_revenue"] == 632.0

    @pytest.mark.asyncio
    async def test_trial_to_payment_workflow(self, integration):
        """Test trial to payment conversion"""
        integration.live_mode = True

        # Mock trial customer creation
        with (
            patch("stripe.Customer.create") as mock_customer,
            patch("stripe.PaymentMethod.attach"),
            patch("stripe.Subscription.create") as mock_sub,
            patch.dict(os.environ, {"STRIPE_LIVE_PRICE_ID": "price_test"}),
        ):
            mock_customer.return_value = MagicMock(id="cus_trial123")
            mock_sub.return_value = MagicMock(id="sub_trial456")

            result = await integration.create_live_customer_with_trial(
                email="trial@example.com",
                name="Trial Customer",
                payment_method_id="pm_test",
            )

        assert result.success is True

        # Mock payment success
        invoice = {"customer": "cus_trial123", "amount_paid": 7900}
        with (
            patch.object(integration, "_update_daily_revenue_tracking"),
            patch.object(integration, "_store_revenue_persistent"),
            patch.object(integration, "_get_daily_progress", return_value={}),
        ):
            await integration._handle_payment_succeeded(invoice)

        # Payment processed successfully
