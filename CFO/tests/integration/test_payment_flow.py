#!/usr/bin/env python3
"""
Critical Integration Tests: Stripe Payment Flow
100% coverage required for revenue-critical paths
"""

import json
from unittest.mock import patch

import pytest

from app.services.payment_service import PaymentService


class TestStripePaymentFlow:
    """Integration tests for Stripe payment processing"""

    @pytest.fixture
    def payment_service(self):
        """Mock payment service for testing"""
        with patch("stripe.api_key", "sk_test_fake"):
            service = PaymentService(test_mode=True)
            return service

    @pytest.fixture
    def mock_stripe_customer(self):
        """Mock Stripe customer object"""
        return {
            "id": "cus_test123",
            "email": "test@saasgrowthdispatch.com",
            "name": "Test Customer",
            "created": 1640995200,
            "subscriptions": {"data": []},
        }

    @pytest.fixture
    def mock_stripe_subscription(self):
        """Mock Stripe subscription object"""
        return {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "active",
            "current_period_start": 1640995200,
            "current_period_end": 1643673600,
            "items": {
                "data": [
                    {
                        "price": {
                            "id": "price_pro_monthly",
                            "unit_amount": 9900,  # $99.00
                            "currency": "usd",
                        }
                    }
                ]
            },
        }

    @patch("stripe.Customer.create")
    def test_customer_creation_flow(
        self, mock_create, payment_service, mock_stripe_customer
    ):
        """Test customer creation with Stripe integration"""
        mock_create.return_value = mock_stripe_customer

        customer_data = {
            "email": "test@saasgrowthdispatch.com",
            "name": "Test Customer",
            "company": "Test SaaS Inc",
        }

        customer = payment_service.create_customer(customer_data)

        assert customer.stripe_id == "cus_test123"
        assert customer.email == "test@saasgrowthdispatch.com"
        mock_create.assert_called_once()

    @patch("stripe.Subscription.create")
    @patch("stripe.Customer.retrieve")
    def test_pro_subscription_creation(
        self,
        mock_retrieve,
        mock_create,
        payment_service,
        mock_stripe_customer,
        mock_stripe_subscription,
    ):
        """Test Pro tier subscription ($99/month) creation"""
        mock_retrieve.return_value = mock_stripe_customer
        mock_create.return_value = mock_stripe_subscription

        subscription_data = {
            "customer_id": "cus_test123",
            "price_id": "price_pro_monthly",
            "tier": "pro",
        }

        subscription = payment_service.create_subscription(subscription_data)

        assert subscription.stripe_id == "sub_test123"
        assert subscription.tier == "pro"
        assert subscription.amount == 99.00
        assert subscription.status == "active"

    @patch("stripe.Subscription.create")
    def test_enterprise_subscription_creation(self, mock_create, payment_service):
        """Test Enterprise tier subscription ($299/month) creation"""
        enterprise_subscription = {
            "id": "sub_enterprise123",
            "customer": "cus_test123",
            "status": "active",
            "items": {
                "data": [
                    {
                        "price": {
                            "id": "price_enterprise_monthly",
                            "unit_amount": 29900,  # $299.00
                            "currency": "usd",
                        }
                    }
                ]
            },
        }

        mock_create.return_value = enterprise_subscription

        subscription_data = {
            "customer_id": "cus_test123",
            "price_id": "price_enterprise_monthly",
            "tier": "enterprise",
        }

        subscription = payment_service.create_subscription(subscription_data)

        assert subscription.tier == "enterprise"
        assert subscription.amount == 299.00

    def test_webhook_subscription_created(self, payment_service):
        """Test webhook handling for subscription.created events"""
        webhook_payload = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_webhook123",
                    "customer": "cus_test123",
                    "status": "active",
                    "items": {
                        "data": [
                            {"price": {"id": "price_pro_monthly", "unit_amount": 9900}}
                        ]
                    },
                }
            },
        }

        result = payment_service.handle_webhook(webhook_payload)

        assert result["status"] == "success"
        assert result["revenue_impact"] == 99.00

    def test_webhook_subscription_cancelled(self, payment_service):
        """Test webhook handling for subscription cancellation"""
        webhook_payload = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_cancelled123",
                    "customer": "cus_test123",
                    "status": "cancelled",
                }
            },
        }

        result = payment_service.handle_webhook(webhook_payload)

        assert result["status"] == "success"
        assert result["action"] == "subscription_cancelled"

    @patch("stripe.Invoice.upcoming")
    def test_usage_based_billing(self, mock_upcoming, payment_service):
        """Test usage-based billing for query overages"""
        # Mock upcoming invoice with usage charges
        mock_upcoming.return_value = {
            "lines": {
                "data": [
                    {
                        "description": "Query overage",
                        "amount": 2500,  # $25.00 for 50 extra queries
                        "quantity": 50,
                    }
                ]
            },
            "total": 12400,  # $99 + $25 overage
        }

        invoice_preview = payment_service.preview_upcoming_invoice("cus_test123")

        assert invoice_preview["base_subscription"] == 99.00
        assert invoice_preview["usage_charges"] == 25.00
        assert invoice_preview["total"] == 124.00

    def test_subscription_upgrade_flow(self, payment_service):
        """Test Pro → Enterprise upgrade flow"""
        with patch("stripe.Subscription.modify") as mock_modify:
            mock_modify.return_value = {
                "id": "sub_upgraded123",
                "items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_enterprise_monthly",
                                "unit_amount": 29900,
                            }
                        }
                    ]
                },
            }

            upgrade_result = payment_service.upgrade_subscription(
                subscription_id="sub_test123", new_price_id="price_enterprise_monthly"
            )

            assert upgrade_result["new_tier"] == "enterprise"
            assert upgrade_result["new_amount"] == 299.00
            assert upgrade_result["upgrade_value"] == 200.00  # $299 - $99

    def test_failed_payment_handling(self, payment_service):
        """Test failed payment retry logic"""
        webhook_payload = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "in_failed123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "amount_due": 9900,
                    "attempt_count": 1,
                }
            },
        }

        result = payment_service.handle_webhook(webhook_payload)

        assert result["status"] == "retry_scheduled"
        assert result["retry_attempt"] == 2

    @patch("app.core.cost_tracker.CostTracker.add_revenue_event")
    def test_revenue_tracking_integration(self, mock_revenue_tracker, payment_service):
        """Test integration with cost tracker for revenue metrics"""
        webhook_payload = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "in_success123",
                    "customer": "cus_test123",
                    "subscription": "sub_test123",
                    "amount_paid": 9900,
                    "paid": True,
                }
            },
        }

        payment_service.handle_webhook(webhook_payload)

        mock_revenue_tracker.assert_called_once()
        call_args = mock_revenue_tracker.call_args[1]
        assert call_args["amount"] == 99.00
        assert call_args["customer_id"] == "cus_test123"

    def test_subscription_metrics_calculation(self, payment_service):
        """Test subscription metrics for $300/day target"""
        # Simulate current customer base
        customers = [
            {"tier": "pro", "amount": 99.00, "count": 60},
            {"tier": "enterprise", "amount": 299.00, "count": 15},
        ]

        metrics = payment_service.calculate_subscription_metrics(customers)

        assert metrics["total_mrr"] == 10425.00  # (60 * 99) + (15 * 299)
        assert metrics["daily_revenue"] == 347.50  # MRR / 30
        assert metrics["target_achievement"] is True  # Above $300/day
        assert metrics["customer_count"] == 75

    def test_trial_to_paid_conversion(self, payment_service):
        """Test trial customer conversion to paid subscription"""
        with patch("stripe.Subscription.create") as mock_create:
            mock_create.return_value = {
                "id": "sub_converted123",
                "status": "active",
                "trial_end": None,  # Trial ended
                "items": {
                    "data": [
                        {"price": {"id": "price_pro_monthly", "unit_amount": 9900}}
                    ]
                },
            }

            conversion_result = payment_service.convert_trial_to_paid(
                customer_id="cus_trial123", price_id="price_pro_monthly"
            )

            assert conversion_result["status"] == "converted"
            assert conversion_result["new_mrr"] == 99.00

    def test_subscription_analytics_export(self, payment_service, tmp_path):
        """Test subscription analytics export for business reporting"""
        analytics_data = {
            "total_customers": 75,
            "mrr": 10425.00,
            "arr": 125100.00,
            "churn_rate": 0.05,
            "conversion_rate": 0.15,
            "tier_distribution": {
                "pro": {"count": 60, "revenue": 5940.00},
                "enterprise": {"count": 15, "revenue": 4485.00},
            },
        }

        export_file = tmp_path / "subscription_analytics.json"
        payment_service.export_analytics(str(export_file), analytics_data)

        assert export_file.exists()

        with open(export_file) as f:
            exported_data = json.load(f)

        assert exported_data["mrr"] == 10425.00
        assert exported_data["total_customers"] == 75

    def test_dunning_management(self, payment_service):
        """Test dunning management for failed payments"""
        failed_payment_data = {
            "customer_id": "cus_dunning123",
            "subscription_id": "sub_dunning123",
            "amount": 99.00,
            "failure_count": 2,
            "next_retry": "2025-06-05T10:00:00Z",
        }

        dunning_result = payment_service.manage_dunning(failed_payment_data)

        assert dunning_result["action"] in ["retry", "cancel", "pause"]
        assert dunning_result["email_sent"] is True

    def test_payment_method_update(self, payment_service):
        """Test payment method update flow"""
        with patch("stripe.Customer.modify") as mock_modify:
            mock_modify.return_value = {
                "id": "cus_test123",
                "default_source": "card_new123",
            }

            update_result = payment_service.update_payment_method(
                customer_id="cus_test123", payment_method_id="pm_new123"
            )

            assert update_result["status"] == "updated"
            assert update_result["new_payment_method"] == "pm_new123"
