#!/usr/bin/env python3
"""
Revenue Dashboard - Track progress to $300/day profit goal
Real-time monitoring of customer acquisition and revenue metrics
"""

import json
import os
from datetime import datetime, timedelta

import stripe


class RevenueDashboard:
    """Track and display revenue metrics and progress to $300/day goal"""

    def __init__(self):
        self.target_daily_profit = 300.00
        self.target_monthly_revenue = 9000.00  # $300/day * 30 days
        self.monthly_costs = 2000.00  # Infrastructure costs

        # Initialize Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        self.metrics_file = "data/metrics/revenue_metrics.json"

    def get_current_metrics(self) -> dict:
        """Get current revenue and customer metrics"""
        try:
            # Get Stripe data for last 30 days
            thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())

            # Get customers
            customers = stripe.Customer.list(
                created={"gte": thirty_days_ago}, limit=100
            )

            # Get subscriptions
            subscriptions = stripe.Subscription.list(
                created={"gte": thirty_days_ago}, status="all", limit=100
            )

            # Get checkout sessions
            sessions = stripe.checkout.Session.list(
                created={"gte": thirty_days_ago}, limit=100
            )

            # Calculate metrics
            active_subscriptions = [
                s for s in subscriptions.data if s.status == "active"
            ]
            trial_subscriptions = [
                s for s in subscriptions.data if s.status == "trialing"
            ]

            # Calculate MRR
            monthly_revenue = 0
            tier_breakdown = {"starter": 0, "basic": 0, "pro": 0, "enterprise": 0}

            for sub in active_subscriptions:
                if sub.items.data:
                    amount = sub.items.data[0].price.unit_amount / 100
                    interval = sub.items.data[0].price.recurring.interval

                    # Convert to monthly
                    monthly_amount = amount / 12 if interval == "year" else amount

                    monthly_revenue += monthly_amount

                    # Determine tier
                    tier = self.determine_tier(monthly_amount)
                    tier_breakdown[tier] += 1

            # Calculate conversion rates
            total_sessions = len(sessions.data)
            completed_sessions = len(
                [s for s in sessions.data if s.payment_status in ["paid", "unpaid"]]
            )
            paid_sessions = len(
                [s for s in sessions.data if s.payment_status == "paid"]
            )

            session_conversion = (
                (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            )
            trial_conversion = (
                (paid_sessions / completed_sessions * 100)
                if completed_sessions > 0
                else 0
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "revenue": {
                    "monthly_revenue": monthly_revenue,
                    "daily_revenue": monthly_revenue / 30,
                    "profit": monthly_revenue - self.monthly_costs,
                    "daily_profit": (monthly_revenue - self.monthly_costs) / 30,
                    "target_progress": (monthly_revenue / self.target_monthly_revenue)
                    * 100,
                },
                "customers": {
                    "total_active": len(active_subscriptions),
                    "total_trials": len(trial_subscriptions),
                    "new_customers_30d": len(customers.data),
                    "tier_breakdown": tier_breakdown,
                },
                "conversion": {
                    "checkout_sessions_30d": total_sessions,
                    "session_conversion_rate": round(session_conversion, 2),
                    "trial_conversion_rate": round(trial_conversion, 2),
                },
                "projections": {
                    "days_to_goal": self.calculate_days_to_goal(monthly_revenue),
                    "customers_needed": self.calculate_customers_needed(
                        monthly_revenue
                    ),
                    "revenue_gap": self.target_monthly_revenue - monthly_revenue,
                },
            }

        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return self.get_mock_metrics()

    def determine_tier(self, monthly_amount: float) -> str:
        """Determine subscription tier based on amount"""
        if monthly_amount <= 19:
            return "starter"
        elif monthly_amount <= 29:
            return "basic"
        elif monthly_amount <= 99:
            return "pro"
        else:
            return "enterprise"

    def calculate_days_to_goal(self, current_revenue: float) -> int:
        """Calculate days to reach $300/day goal at current growth rate"""
        if current_revenue == 0:
            return "∞"

        # Assume 20% monthly growth rate
        growth_rate = 0.20
        months_needed = 0
        revenue = current_revenue

        while revenue < self.target_monthly_revenue and months_needed < 24:
            revenue *= 1 + growth_rate
            months_needed += 1

        return months_needed * 30 if months_needed < 24 else "24+ months"

    def calculate_customers_needed(self, current_revenue: float) -> dict:
        """Calculate how many customers needed per tier"""
        revenue_gap = self.target_monthly_revenue - current_revenue

        return {
            "starter_only": int(revenue_gap / 19) + 1,
            "basic_only": int(revenue_gap / 29) + 1,
            "pro_only": int(revenue_gap / 99) + 1,
            "enterprise_only": int(revenue_gap / 299) + 1,
            "mixed_scenario": {
                "starter": 100,
                "basic": 100,
                "pro": 50,
                "enterprise": 10,
            },
        }

    def get_mock_metrics(self) -> dict:
        """Return mock metrics for testing"""
        return {
            "timestamp": datetime.now().isoformat(),
            "revenue": {
                "monthly_revenue": 0.00,
                "daily_revenue": 0.00,
                "profit": -2000.00,
                "daily_profit": -66.67,
                "target_progress": 0.0,
            },
            "customers": {
                "total_active": 0,
                "total_trials": 0,
                "new_customers_30d": 0,
                "tier_breakdown": {"starter": 0, "basic": 0, "pro": 0, "enterprise": 0},
            },
            "conversion": {
                "checkout_sessions_30d": 0,
                "session_conversion_rate": 0.0,
                "trial_conversion_rate": 0.0,
            },
            "projections": {
                "days_to_goal": "Execute customer validation first",
                "customers_needed": {
                    "starter_only": 474,
                    "basic_only": 311,
                    "pro_only": 91,
                    "enterprise_only": 31,
                },
                "revenue_gap": 9000.00,
            },
        }

    def save_metrics(self, metrics: dict):
        """Save metrics to file for historical tracking"""
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)

        # Load existing metrics
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file) as f:
                historical_data = json.load(f)
        else:
            historical_data = []

        historical_data.append(metrics)

        # Keep only last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        historical_data = [
            m
            for m in historical_data
            if datetime.fromisoformat(m["timestamp"]) > cutoff_date
        ]

        with open(self.metrics_file, "w") as f:
            json.dump(historical_data, f, indent=2)

    def display_dashboard(self):
        """Display revenue dashboard in terminal"""
        metrics = self.get_current_metrics()
        self.save_metrics(metrics)

        print("=" * 60)
        print("🎯 REVENUE DASHBOARD - Path to $300/Day Profit")
        print("=" * 60)

        # Revenue Section
        print("\n💰 REVENUE METRICS")
        print(f"Monthly Revenue:     ${metrics['revenue']['monthly_revenue']:,.2f}")
        print(f"Daily Revenue:       ${metrics['revenue']['daily_revenue']:,.2f}")
        print(f"Monthly Profit:      ${metrics['revenue']['profit']:,.2f}")
        print(f"Daily Profit:        ${metrics['revenue']['daily_profit']:,.2f}")
        print(f"Target Progress:     {metrics['revenue']['target_progress']:.1f}%")

        # Goal Progress Bar
        progress = min(metrics["revenue"]["target_progress"], 100)
        bar_length = 30
        filled_length = int(bar_length * progress / 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"Progress: [{bar}] {progress:.1f}%")

        # Customer Section
        print("\n👥 CUSTOMER METRICS")
        print(f"Active Customers:    {metrics['customers']['total_active']}")
        print(f"Trial Customers:     {metrics['customers']['total_trials']}")
        print(f"New Customers (30d): {metrics['customers']['new_customers_30d']}")

        # Tier Breakdown
        print("\n📊 TIER BREAKDOWN")
        for tier, count in metrics["customers"]["tier_breakdown"].items():
            print(f"{tier.capitalize():12}: {count:3d} customers")

        # Conversion Metrics
        print("\n🔄 CONVERSION METRICS")
        print(f"Sessions (30d):      {metrics['conversion']['checkout_sessions_30d']}")
        print(
            f"Session Conversion:  {metrics['conversion']['session_conversion_rate']}%"
        )
        print(f"Trial Conversion:    {metrics['conversion']['trial_conversion_rate']}%")

        # Projections
        print("\n🎯 PROJECTIONS TO GOAL")
        print(f"Revenue Gap:         ${metrics['projections']['revenue_gap']:,.2f}")
        print(f"Time to Goal:        {metrics['projections']['days_to_goal']}")

        print("\n📈 CUSTOMERS NEEDED:")
        needed = metrics["projections"]["customers_needed"]
        print(f"Starter ($19):       {needed['starter_only']} customers")
        print(f"Basic ($29):         {needed['basic_only']} customers")
        print(f"Pro ($99):           {needed['pro_only']} customers")
        print(f"Enterprise ($299):   {needed['enterprise_only']} customers")

        # Current Status
        if metrics["revenue"]["monthly_revenue"] == 0:
            print("\n🚨 CRITICAL: NO REVENUE")
            print("Action Required: Execute customer validation campaign")
            print("Priority: Contact prospects immediately")
        elif metrics["revenue"]["daily_profit"] < 0:
            print("\n⚠️  OPERATING AT LOSS")
            print(f"Monthly Loss: ${abs(metrics['revenue']['profit']):,.2f}")
            print("Focus: Customer acquisition and retention")
        else:
            print("\n✅ PROFITABLE")
            print("Keep growing at current rate")

        print("=" * 60)

        return metrics

    def generate_weekly_report(self) -> str:
        """Generate weekly revenue report for stakeholders"""
        metrics = self.get_current_metrics()

        report = f"""
# Weekly Revenue Report - {datetime.now().strftime('%B %d, %Y')}

## Executive Summary
- **Monthly Revenue:** ${metrics['revenue']['monthly_revenue']:,.2f}
- **Target Progress:** {metrics['revenue']['target_progress']:.1f}%
- **Active Customers:** {metrics['customers']['total_active']}
- **Monthly Profit:** ${metrics['revenue']['profit']:,.2f}

## Key Metrics
- Daily Revenue: ${metrics['revenue']['daily_revenue']:,.2f}
- Daily Profit: ${metrics['revenue']['daily_profit']:,.2f}
- Trial Customers: {metrics['customers']['total_trials']}
- Revenue Gap: ${metrics['projections']['revenue_gap']:,.2f}

## Customer Breakdown
- Starter ($19): {metrics['customers']['tier_breakdown']['starter']} customers
- Basic ($29): {metrics['customers']['tier_breakdown']['basic']} customers
- Pro ($99): {metrics['customers']['tier_breakdown']['pro']} customers
- Enterprise ($299): {metrics['customers']['tier_breakdown']['enterprise']} customers

## Action Items
{'- Execute customer validation campaign (0 revenue)' if metrics['revenue']['monthly_revenue'] == 0 else '- Continue customer acquisition efforts'}
- {'Focus on trial conversion' if metrics['customers']['total_trials'] > 0 else 'Generate more trial signups'}
- Target {metrics['projections']['customers_needed']['enterprise_only']} enterprise customers for fastest path to goal

## Projected Timeline
Time to $300/day goal: {metrics['projections']['days_to_goal']}
"""
        return report


if __name__ == "__main__":
    dashboard = RevenueDashboard()
    dashboard.display_dashboard()
