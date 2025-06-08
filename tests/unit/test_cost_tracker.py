#!/usr/bin/env python3
"""
Critical Business Logic Tests: Cost Tracker
Revenue tracking and business metrics testing
"""

import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.core.cost_tracker import CostTracker, RevenueEvent


class TestCostTracker:
    """Test cost tracking for $300/day revenue target"""

    @pytest.fixture
    def cost_tracker(self):
        """Initialize cost tracker with test config"""
        return CostTracker(test_mode=True)

    @pytest.fixture
    def sample_revenue_event(self):
        """Sample revenue event for testing"""
        return RevenueEvent(
            customer_id="test_customer_001",
            amount=99.00,
            tier="pro",
            event_type="subscription",
            timestamp=datetime.now(),
        )

    def test_daily_revenue_tracking(self, cost_tracker, sample_revenue_event):
        """Test daily revenue accumulation toward $300 target"""
        # Add multiple revenue events
        cost_tracker.add_revenue_event(sample_revenue_event)
        cost_tracker.add_revenue_event(
            RevenueEvent(
                customer_id="test_customer_002",
                amount=299.00,
                tier="enterprise",
                event_type="subscription",
            )
        )

        daily_revenue = cost_tracker.get_daily_revenue()
        assert daily_revenue >= 398.00
        assert cost_tracker.is_daily_target_met(target=300.00) is True

    def test_monthly_recurring_revenue(self, cost_tracker):
        """Test MRR calculation for business projections"""
        # Add subscription customers
        customers = [
            {"tier": "pro", "amount": 99.00, "customers": 60},
            {"tier": "enterprise", "amount": 299.00, "customers": 15},
        ]

        for customer_tier in customers:
            for i in range(customer_tier["customers"]):
                cost_tracker.add_subscription(
                    customer_id=f"{customer_tier['tier']}_customer_{i}",
                    tier=customer_tier["tier"],
                    amount=customer_tier["amount"],
                )

        mrr = cost_tracker.calculate_mrr()
        expected_mrr = (60 * 99.00) + (15 * 299.00)  # $10,425
        assert mrr == expected_mrr
        assert mrr > 9000  # Above $300/day target

    def test_customer_lifetime_value(self, cost_tracker):
        """Test LTV calculation for business metrics"""
        customer_data = {
            "tier": "pro",
            "monthly_amount": 99.00,
            "months_active": 18,
            "churn_probability": 0.05,
        }

        ltv = cost_tracker.calculate_ltv(
            monthly_revenue=customer_data["monthly_amount"],
            churn_rate=customer_data["churn_probability"],
            months=customer_data["months_active"],
        )

        99.00 * (1 / 0.05)  # ~$1,980
        assert ltv >= 1500  # Minimum viable LTV
        assert ltv <= 2500  # Realistic maximum

    def test_revenue_growth_rate(self, cost_tracker):
        """Test revenue growth tracking"""
        # Add historical revenue data
        base_date = datetime.now() - timedelta(days=30)

        for day in range(30):
            revenue_date = base_date + timedelta(days=day)
            daily_amount = 100 + (day * 5)  # Growing revenue

            cost_tracker.add_revenue_event(
                RevenueEvent(
                    customer_id=f"customer_{day}",
                    amount=daily_amount,
                    event_type="subscription",
                    timestamp=revenue_date,
                )
            )

        growth_rate = cost_tracker.calculate_growth_rate(period_days=30)
        assert growth_rate > 0  # Positive growth
        assert growth_rate < 100  # Realistic growth rate

    @patch("app.observability.sentry_config.track_revenue_event")
    def test_sentry_integration(self, mock_sentry, cost_tracker, sample_revenue_event):
        """Test Sentry business metrics integration"""
        cost_tracker.add_revenue_event(sample_revenue_event)

        # Verify Sentry tracking was called
        mock_sentry.assert_called_once_with(
            amount=99.00, customer_id="test_customer_001"
        )

    def test_subscription_tier_distribution(self, cost_tracker):
        """Test customer distribution across pricing tiers"""
        # Add customers across tiers
        tiers = {
            "basic": {"price": 29, "count": 100},
            "pro": {"price": 99, "count": 60},
            "enterprise": {"price": 299, "count": 15},
        }

        for tier_name, tier_data in tiers.items():
            for i in range(tier_data["count"]):
                cost_tracker.add_subscription(
                    customer_id=f"{tier_name}_{i}",
                    tier=tier_name,
                    amount=tier_data["price"],
                )

        distribution = cost_tracker.get_tier_distribution()
        assert distribution["pro"]["revenue_share"] > 40  # Pro tier dominance
        assert distribution["enterprise"]["customer_count"] == 15

    def test_revenue_forecasting(self, cost_tracker):
        """Test revenue projections for business planning"""
        current_mrr = 8500  # Current monthly recurring revenue
        growth_rate = 0.15  # 15% monthly growth

        forecast = cost_tracker.forecast_revenue(
            current_mrr=current_mrr, growth_rate=growth_rate, months=6
        )

        # Should project revenue growth over 6 months
        assert forecast["month_6"] > current_mrr
        assert forecast["month_6"] > 15000  # Significant growth expected

        # Verify $300/day target achievement timeline
        daily_target = 300 * 30  # $9,000/month
        target_month = cost_tracker.find_target_achievement_month(
            current_mrr=current_mrr, target_mrr=daily_target, growth_rate=growth_rate
        )
        assert target_month <= 3  # Should achieve within 3 months

    def test_cost_tracking_accuracy(self, cost_tracker):
        """Test API cost tracking for profitability analysis"""
        api_costs = [
            {"service": "openai", "cost": 0.02, "tokens": 1000},
            {"service": "serpapi", "cost": 0.005, "queries": 100},
            {"service": "anthropic", "cost": 0.015, "tokens": 750},
        ]

        for cost_event in api_costs:
            cost_tracker.add_cost_event(
                service=cost_event["service"],
                cost=cost_event["cost"],
                metadata=cost_event,
            )

        total_costs = cost_tracker.get_daily_costs()
        assert total_costs < 0.05  # Keep costs under $0.05/day

        # Ensure profitability margins
        daily_revenue = 300.00
        profit_margin = (daily_revenue - total_costs) / daily_revenue
        assert profit_margin > 0.95  # >95% profit margin

    def test_customer_acquisition_cost(self, cost_tracker):
        """Test CAC tracking for marketing ROI"""
        marketing_spend = 500.00  # Monthly marketing budget
        new_customers = 10  # Customers acquired this month

        cac = cost_tracker.calculate_cac(
            marketing_spend=marketing_spend, customers_acquired=new_customers
        )

        assert cac == 50.00  # $50 CAC

        # Verify LTV:CAC ratio
        avg_ltv = 1800.00  # Average customer LTV
        ltv_cac_ratio = avg_ltv / cac
        assert ltv_cac_ratio > 20  # Target >20:1 ratio

    def test_revenue_event_validation(self, cost_tracker):
        """Test revenue event data validation"""
        invalid_events = [
            {"amount": -100},  # Negative amount
            {"amount": 0},  # Zero amount
            {"tier": "invalid"},  # Invalid tier
            {"customer_id": ""},  # Empty customer ID
        ]

        for invalid_data in invalid_events:
            with pytest.raises(ValueError):
                cost_tracker.add_revenue_event(RevenueEvent(**invalid_data))

    def test_business_metrics_export(self, cost_tracker, tmp_path):
        """Test business metrics export for reporting"""
        # Add sample data
        cost_tracker.add_revenue_event(
            RevenueEvent(customer_id="export_test_001", amount=199.00, tier="pro")
        )

        # Export metrics
        export_file = tmp_path / "business_metrics.json"
        cost_tracker.export_metrics(str(export_file))

        assert export_file.exists()

        with open(export_file) as f:
            metrics = json.load(f)

        assert "daily_revenue" in metrics
        assert "customer_count" in metrics
        assert metrics["daily_revenue"] > 0

    def test_real_time_dashboard_data(self, cost_tracker):
        """Test real-time data for revenue dashboard"""
        dashboard_data = cost_tracker.get_dashboard_metrics()

        required_metrics = [
            "current_mrr",
            "daily_revenue",
            "customer_count",
            "growth_rate",
            "days_to_target",
            "profit_margin",
        ]

        for metric in required_metrics:
            assert metric in dashboard_data

        # Verify data freshness (updated within last minute)
        assert dashboard_data["last_updated"]
        update_time = datetime.fromisoformat(dashboard_data["last_updated"])
        assert (datetime.now() - update_time).seconds < 60
