"""
Tests for Stripe Revenue Engine
Tests for $1,074.86/day revenue generation system
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.revenue_dashboard import RevenueMetrics
from app.revenue.stripe_revenue_engine import StripeRevenueEngine
from app.services.payment_service import SubscriptionTier


class TestSubscriptionTier:
    """Test subscription tier enumeration"""

    def test_subscription_tiers(self):
        """Test subscription tier values"""
        assert SubscriptionTier.PROFESSIONAL.value == "professional"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"
        assert SubscriptionTier.STRATEGIC.value == "strategic"


class TestRevenueMetrics:
    """Test revenue metrics data class"""

    def test_revenue_metrics_creation(self):
        """Test creating revenue metrics"""
        metrics = RevenueMetrics(
            daily_revenue=1074.86,
            monthly_revenue=32246.00,
            customer_count=76,
            average_revenue_per_customer=79.00,
            target_achievement_rate=179.14,
            growth_rate=15.5,
        )

        assert metrics.daily_revenue == 1074.86
        assert metrics.monthly_revenue == 32246.00
        assert metrics.customer_count == 76
        assert metrics.average_revenue_per_customer == 79.00
        assert metrics.target_achievement_rate == 179.14
        assert metrics.growth_rate == 15.5


class TestStripeRevenueEngine:
    """Test Stripe revenue engine operations"""

    @pytest.fixture
    def engine(self):
        """Create revenue engine instance"""
        return StripeRevenueEngine()

    @pytest.fixture
    def mock_stripe_customer(self):
        """Mock Stripe customer"""
        customer = MagicMock()
        customer.id = "cus_test123"
        customer.email = "test@example.com"
        customer.created = 1234567890
        customer.metadata = {"source": "meta_ads", "discount": "REVENUE20"}
        return customer

    @pytest.fixture
    def mock_stripe_subscription(self):
        """Mock Stripe subscription"""
        subscription = MagicMock()
        subscription.id = "sub_test456"
        subscription.customer = "cus_test123"
        subscription.status = "active"
        subscription.current_period_start = 1234567890
        subscription.current_period_end = 1237159890
        subscription.items.data = [
            MagicMock(price=MagicMock(unit_amount=7900, currency="usd"))
        ]
        return subscription

    def test_initialization(self, engine):
        """Test engine initialization"""
        assert engine.daily_target == 600.0
        assert engine.pricing_tiers[SubscriptionTier.PROFESSIONAL] == 79.0
        assert engine.pricing_tiers[SubscriptionTier.ENTERPRISE] == 199.0
        assert engine.pricing_tiers[SubscriptionTier.STRATEGIC] == 499.0

    @patch("stripe.Customer.list")
    def test_get_customer_metrics_success(
        self, mock_customer_list, engine, mock_stripe_customer
    ):
        """Test successful customer metrics retrieval"""
        mock_customer_list.return_value.data = [mock_stripe_customer]

        metrics = engine.get_customer_metrics()

        assert metrics["total_customers"] == 1
        assert metrics["revenue_per_customer"] == 79.0
        assert "customers_by_source" in metrics
        assert "discount_usage" in metrics

    @patch("stripe.Customer.list")
    def test_get_customer_metrics_error(self, mock_customer_list, engine):
        """Test customer metrics error handling"""
        mock_customer_list.side_effect = Exception("API Error")

        metrics = engine.get_customer_metrics()

        assert metrics["total_customers"] == 0
        assert metrics["revenue_per_customer"] == 0.0
        assert metrics["error"] == "Failed to fetch customer metrics: API Error"

    @patch("stripe.Subscription.list")
    def test_get_subscription_metrics_success(
        self, mock_sub_list, engine, mock_stripe_subscription
    ):
        """Test successful subscription metrics retrieval"""
        mock_sub_list.return_value.data = [mock_stripe_subscription]

        metrics = engine.get_subscription_metrics()

        assert metrics["active_subscriptions"] == 1
        assert metrics["total_mrr"] == 79.0
        assert metrics["average_subscription_value"] == 79.0
        assert "subscriptions_by_tier" in metrics

    @patch("stripe.Subscription.list")
    def test_get_subscription_metrics_error(self, mock_sub_list, engine):
        """Test subscription metrics error handling"""
        mock_sub_list.side_effect = Exception("API Error")

        metrics = engine.get_subscription_metrics()

        assert metrics["active_subscriptions"] == 0
        assert metrics["total_mrr"] == 0.0
        assert metrics["error"] == "Failed to fetch subscription metrics: API Error"

    @patch("stripe.Charge.list")
    def test_get_daily_revenue_success(self, mock_charge_list, engine):
        """Test successful daily revenue calculation"""
        # Mock successful charges
        mock_charges = [
            MagicMock(amount=7900, paid=True, created=1234567890),  # $79
            MagicMock(amount=7900, paid=True, created=1234567900),  # $79
            MagicMock(amount=7900, paid=True, created=1234567910),  # $79
        ]
        mock_charge_list.return_value.data = mock_charges

        revenue = engine.get_daily_revenue()

        assert revenue == 237.0  # 3 * $79

    @patch("stripe.Charge.list")
    def test_get_daily_revenue_with_failed_charges(self, mock_charge_list, engine):
        """Test daily revenue calculation excluding failed charges"""
        mock_charges = [
            MagicMock(amount=7900, paid=True, created=1234567890),  # $79 - counted
            MagicMock(amount=7900, paid=False, created=1234567900),  # $79 - not counted
            MagicMock(amount=7900, paid=True, created=1234567910),  # $79 - counted
        ]
        mock_charge_list.return_value.data = mock_charges

        revenue = engine.get_daily_revenue()

        assert revenue == 158.0  # 2 * $79

    @patch("stripe.Charge.list")
    def test_get_daily_revenue_error(self, mock_charge_list, engine):
        """Test daily revenue error handling"""
        mock_charge_list.side_effect = Exception("API Error")

        revenue = engine.get_daily_revenue()

        assert revenue == 0.0

    def test_calculate_target_achievement_on_target(self, engine):
        """Test target achievement calculation at target"""
        achievement = engine.calculate_target_achievement(600.0)
        assert achievement == 100.0

    def test_calculate_target_achievement_above_target(self, engine):
        """Test target achievement calculation above target"""
        achievement = engine.calculate_target_achievement(1074.86)
        assert achievement == 179.14  # (1074.86 / 600) * 100

    def test_calculate_target_achievement_below_target(self, engine):
        """Test target achievement calculation below target"""
        achievement = engine.calculate_target_achievement(300.0)
        assert achievement == 50.0

    def test_calculate_target_achievement_zero(self, engine):
        """Test target achievement calculation with zero revenue"""
        achievement = engine.calculate_target_achievement(0.0)
        assert achievement == 0.0

    def test_estimate_monthly_revenue(self, engine):
        """Test monthly revenue estimation"""
        # Test with $79/day
        monthly = engine.estimate_monthly_revenue(79.0)
        assert monthly == 2449.0  # 79 * 31

        # Test with $1074.86/day
        monthly = engine.estimate_monthly_revenue(1074.86)
        assert monthly == 33320.66  # 1074.86 * 31

    def test_get_tier_for_amount_professional(self, engine):
        """Test tier classification for professional tier"""
        tier = engine.get_tier_for_amount(79.0)
        assert tier == SubscriptionTier.PROFESSIONAL

    def test_get_tier_for_amount_enterprise(self, engine):
        """Test tier classification for enterprise tier"""
        tier = engine.get_tier_for_amount(199.0)
        assert tier == SubscriptionTier.ENTERPRISE

    def test_get_tier_for_amount_strategic(self, engine):
        """Test tier classification for strategic tier"""
        tier = engine.get_tier_for_amount(499.0)
        assert tier == SubscriptionTier.STRATEGIC

    def test_get_tier_for_amount_unknown(self, engine):
        """Test tier classification for unknown amount"""
        tier = engine.get_tier_for_amount(999.0)
        assert tier is None

    @patch.object(StripeRevenueEngine, "get_daily_revenue")
    @patch.object(StripeRevenueEngine, "get_customer_metrics")
    @patch.object(StripeRevenueEngine, "get_subscription_metrics")
    def test_generate_comprehensive_report(
        self, mock_sub_metrics, mock_customer_metrics, mock_daily_revenue, engine
    ):
        """Test comprehensive revenue report generation"""
        # Mock return values
        mock_daily_revenue.return_value = 1074.86
        mock_customer_metrics.return_value = {
            "total_customers": 76,
            "revenue_per_customer": 79.0,
            "customers_by_source": {"meta_ads": 60, "organic": 16},
            "discount_usage": {"REVENUE20": 76},
        }
        mock_sub_metrics.return_value = {
            "active_subscriptions": 76,
            "total_mrr": 6004.0,
            "average_subscription_value": 79.0,
            "subscriptions_by_tier": {"professional": 76},
        }

        report = engine.generate_comprehensive_report()

        # Verify report structure
        assert "revenue_summary" in report
        assert "customer_analysis" in report
        assert "subscription_analysis" in report
        assert "performance_metrics" in report

        # Verify calculations
        revenue_summary = report["revenue_summary"]
        assert revenue_summary["daily_revenue"] == 1074.86
        assert revenue_summary["target_achievement"] == 179.14
        assert revenue_summary["monthly_projection"] == 33320.66

        performance_metrics = report["performance_metrics"]
        assert performance_metrics["revenue_per_customer"] == 79.0
        assert performance_metrics["target_exceeded"] is True

    @patch.object(StripeRevenueEngine, "get_daily_revenue")
    def test_generate_comprehensive_report_below_target(
        self, mock_daily_revenue, engine
    ):
        """Test comprehensive report when below target"""
        mock_daily_revenue.return_value = 300.0

        with (
            patch.object(engine, "get_customer_metrics", return_value={}),
            patch.object(engine, "get_subscription_metrics", return_value={}),
        ):
            report = engine.generate_comprehensive_report()

        performance_metrics = report["performance_metrics"]
        assert performance_metrics["target_exceeded"] is False
        assert performance_metrics["revenue_gap"] == 300.0  # 600 - 300

    def test_format_currency(self, engine):
        """Test currency formatting"""
        assert engine.format_currency(1074.86) == "$1,074.86"
        assert engine.format_currency(79.0) == "$79.00"
        assert engine.format_currency(0) == "$0.00"

    def test_calculate_growth_rate(self, engine):
        """Test growth rate calculation"""
        # 100% growth
        growth = engine.calculate_growth_rate(current=200.0, previous=100.0)
        assert growth == 100.0

        # 50% growth
        growth = engine.calculate_growth_rate(current=150.0, previous=100.0)
        assert growth == 50.0

        # Negative growth
        growth = engine.calculate_growth_rate(current=80.0, previous=100.0)
        assert growth == -20.0

        # Zero previous (avoid division by zero)
        growth = engine.calculate_growth_rate(current=100.0, previous=0.0)
        assert growth == 0.0


# Integration tests for revenue scenarios
class TestStripeRevenueEngineScenarios:
    """Test real-world revenue generation scenarios"""

    @pytest.fixture
    def engine(self):
        """Create revenue engine"""
        return StripeRevenueEngine()

    def test_revenue_target_exceeded_scenario(self, engine):
        """Test scenario where daily target is exceeded"""
        daily_revenue = 1074.86
        target_achievement = engine.calculate_target_achievement(daily_revenue)

        assert target_achievement > 100.0
        assert target_achievement == 179.14

        monthly_projection = engine.estimate_monthly_revenue(daily_revenue)
        assert monthly_projection > 30000.0  # Well above $30k/month

    def test_revenue_scaling_scenario(self, engine):
        """Test revenue scaling from 8 to 76 customers"""
        # Week 1: 8 customers * $79 = $632/day
        week1_revenue = 8 * 79.0
        week1_achievement = engine.calculate_target_achievement(week1_revenue)
        assert week1_achievement > 100.0  # Already exceeds $600 target

        # Current: 76 customers * $79 = $6,004/day (theoretical max)
        current_theoretical = 76 * 79.0
        current_achievement = engine.calculate_target_achievement(current_theoretical)
        assert current_achievement > 1000.0  # Massively exceeds target

        # Realistic current: $1,074.86/day from usage report
        current_actual = 1074.86
        actual_achievement = engine.calculate_target_achievement(current_actual)
        assert actual_achievement == 179.14

    def test_discount_impact_analysis(self, engine):
        """Test REVENUE20 discount impact on revenue"""
        # Original price: $99/month
        original_price = 99.0
        discount_percentage = 20.0
        discounted_price = original_price * (1 - discount_percentage / 100)

        assert discounted_price == 79.0  # Matches our pricing

        # Revenue comparison: 76 customers
        revenue_without_discount = 76 * original_price  # $7,524/day
        revenue_with_discount = 76 * discounted_price  # $6,004/day
        revenue_impact = revenue_without_discount - revenue_with_discount  # $1,520/day

        assert revenue_impact == 1520.0
        assert revenue_with_discount > engine.daily_target  # Still exceeds target

    @patch("stripe.Customer.list")
    @patch("stripe.Subscription.list")
    @patch("stripe.Charge.list")
    def test_full_revenue_analysis_scenario(
        self, mock_charge_list, mock_sub_list, mock_customer_list, engine
    ):
        """Test complete revenue analysis scenario"""
        # Mock 76 customers with REVENUE20 discount
        mock_customers = []
        for i in range(76):
            customer = MagicMock()
            customer.id = f"cus_customer_{i}"
            customer.email = f"customer{i}@example.com"
            customer.metadata = {"source": "meta_ads", "discount": "REVENUE20"}
            mock_customers.append(customer)
        mock_customer_list.return_value.data = mock_customers

        # Mock 76 active subscriptions
        mock_subscriptions = []
        for i in range(76):
            subscription = MagicMock()
            subscription.id = f"sub_subscription_{i}"
            subscription.customer = f"cus_customer_{i}"
            subscription.status = "active"
            subscription.items.data = [
                MagicMock(price=MagicMock(unit_amount=7900, currency="usd"))  # $79
            ]
            mock_subscriptions.append(subscription)
        mock_sub_list.return_value.data = mock_subscriptions

        # Mock daily charges totaling $1,074.86
        daily_total_cents = int(1074.86 * 100)  # 107486 cents
        charges_per_customer = daily_total_cents // 76  # ~1414 cents per customer
        mock_charges = []
<<<<<<< HEAD
        for _ in range(76):
=======
        for _i in range(76):
>>>>>>> f93f027 (Push changes from the CTO)
            charge = MagicMock()
            charge.amount = charges_per_customer
            charge.paid = True
            charge.created = 1234567890
            mock_charges.append(charge)

        # Add remainder to first charge to get exact total
        remainder = daily_total_cents - (charges_per_customer * 76)
        mock_charges[0].amount += remainder

        mock_charge_list.return_value.data = mock_charges

        # Generate comprehensive report
        report = engine.generate_comprehensive_report()

        # Verify revenue analysis
        assert report["customer_analysis"]["total_customers"] == 76
        assert report["subscription_analysis"]["active_subscriptions"] == 76
        assert (
            abs(report["revenue_summary"]["daily_revenue"] - 1074.86) < 1.0
        )  # Allow small rounding
        assert report["performance_metrics"]["target_exceeded"] is True
        assert (
            report["revenue_summary"]["target_achievement"] > 170.0
        )  # Significantly above target
