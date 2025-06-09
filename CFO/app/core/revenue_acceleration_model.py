"""
Revenue Acceleration Financial Model
Scales from $300 to $1,000 daily revenue with real-time AI cost optimization
"""

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.config.logging import get_logger
from app.core.claude_token_monitor import ClaudeTokenMonitor
from app.core.cost_tracker import CostTracker

logger = get_logger(__name__)


@dataclass
class AIModelCosts:
    """AI model cost structure"""

    sonnet_input_per_million: float = 3.0
    sonnet_output_per_million: float = 15.0
    opus_input_per_million: float = 15.0
    opus_output_per_million: float = 75.0
    daily_budget: float = 10.0
    optimization_savings: float = 0.7  # 70% savings target


@dataclass
class CustomerMetrics:
    """Customer acquisition and lifetime value metrics"""

    basic_tier_price: float = 29.0
    pro_tier_price: float = 99.0
    enterprise_tier_price: float = 299.0
    avg_customer_lifetime_months: int = 24
    churn_rate_monthly: float = 0.05
    trial_conversion_rate: float = 0.15
    cac_base: float = 50.0  # Base customer acquisition cost


@dataclass
class OperationalCosts:
    """Monthly operational costs"""

    infrastructure: float = 800.0
    ai_services: float = 300.0  # Claude + other AI
    marketing: float = 1500.0
    support: float = 400.0
    development: float = 600.0
    total_monthly: float = 3600.0


class RevenueAccelerationModel:
    """Advanced financial model for scaling SaaS revenue with AI cost optimization"""

    def __init__(self):
        self.ai_costs = AIModelCosts()
        self.customer_metrics = CustomerMetrics()
        self.operational_costs = OperationalCosts()
        self.token_monitor = ClaudeTokenMonitor()
        self.cost_tracker = CostTracker()
        self.memory_file = "data/revenue_acceleration_memory.json"

        # Revenue targets
        self.current_daily_target = 300.0
        self.scale_daily_target = 1000.0
        self.scale_timeline_days = 30

    def calculate_ai_cost_optimization(self) -> dict:
        """Calculate AI cost optimization impact"""
        current_ai_spend = self.ai_costs.daily_budget * 30  # Monthly
        optimized_ai_spend = current_ai_spend * (1 - self.ai_costs.optimization_savings)

        # Task distribution optimization
        routine_tasks_pct = 0.80  # 80% of tasks are routine (use Sonnet)
        complex_tasks_pct = 0.20  # 20% require Opus

        # Cost per task estimation
        avg_tokens_per_task = 2000  # input + output
        sonnet_cost_per_task = (
            avg_tokens_per_task / 1_000_000
        ) * self.ai_costs.sonnet_output_per_million
        opus_cost_per_task = (
            avg_tokens_per_task / 1_000_000
        ) * self.ai_costs.opus_output_per_million

        blended_cost_per_task = (routine_tasks_pct * sonnet_cost_per_task) + (
            complex_tasks_pct * opus_cost_per_task
        )

        return {
            "current_monthly_ai_cost": current_ai_spend,
            "optimized_monthly_ai_cost": optimized_ai_spend,
            "monthly_savings": current_ai_spend - optimized_ai_spend,
            "cost_per_task": blended_cost_per_task,
            "sonnet_usage_pct": routine_tasks_pct * 100,
            "opus_usage_pct": complex_tasks_pct * 100,
            "tasks_per_dollar": 1 / blended_cost_per_task,
        }

    def calculate_customer_acquisition_model(self) -> dict:
        """Calculate customer acquisition metrics for scaling"""
        # Current state (assuming $300/day = $9,000/month)
        current_monthly_revenue = self.current_daily_target * 30
        target_monthly_revenue = self.scale_daily_target * 30
        revenue_gap = target_monthly_revenue - current_monthly_revenue

        # Customer mix optimization for faster scaling
        customer_mix = {
            "basic": {
                "price": self.customer_metrics.basic_tier_price,
                "target_pct": 0.20,
            },
            "pro": {"price": self.customer_metrics.pro_tier_price, "target_pct": 0.60},
            "enterprise": {
                "price": self.customer_metrics.enterprise_tier_price,
                "target_pct": 0.20,
            },
        }

        # Calculate weighted average revenue per customer
        avg_revenue_per_customer = sum(
            tier["price"] * tier["target_pct"] for tier in customer_mix.values()
        )

        # Calculate customers needed
        additional_customers_needed = revenue_gap / avg_revenue_per_customer

        # Calculate CAC with AI optimization (lower costs = lower CAC)
        ai_optimization = self.calculate_ai_cost_optimization()
        ai_savings_monthly = ai_optimization["monthly_savings"]

        # Reinvest AI savings into marketing for lower CAC
        optimized_cac = self.customer_metrics.cac_base * (
            1 - (ai_savings_monthly / 1000)
        )  # $1 saved = $1 less CAC

        # LTV calculation
        avg_ltv = (
            avg_revenue_per_customer
            * self.customer_metrics.avg_customer_lifetime_months
        )
        ltv_cac_ratio = avg_ltv / optimized_cac

        return {
            "revenue_gap": revenue_gap,
            "avg_revenue_per_customer": avg_revenue_per_customer,
            "additional_customers_needed": math.ceil(additional_customers_needed),
            "optimized_cac": optimized_cac,
            "avg_ltv": avg_ltv,
            "ltv_cac_ratio": ltv_cac_ratio,
            "customer_mix": customer_mix,
            "payback_period_months": optimized_cac / avg_revenue_per_customer,
        }

    def calculate_scaling_timeline(self) -> dict:
        """Calculate week-by-week scaling plan"""
        acquisition_model = self.calculate_customer_acquisition_model()
        customers_needed = acquisition_model["additional_customers_needed"]

        # Weekly scaling plan (30 days = ~4.3 weeks)
        weeks = 4.3
        customers_per_week = customers_needed / weeks

        timeline = []
        cumulative_customers = 0
        cumulative_revenue = self.current_daily_target * 30  # Start from current

        for week in range(1, 5):
            week_customers = customers_per_week
            cumulative_customers += week_customers
            week_revenue = (
                week_customers * acquisition_model["avg_revenue_per_customer"]
            )
            cumulative_revenue += week_revenue

            timeline.append(
                {
                    "week": week,
                    "new_customers": round(week_customers),
                    "cumulative_customers": round(cumulative_customers),
                    "weekly_revenue_added": round(week_revenue),
                    "cumulative_monthly_revenue": round(cumulative_revenue),
                    "daily_revenue": round(cumulative_revenue / 30, 2),
                }
            )

        return {
            "scaling_timeline": timeline,
            "total_weeks": weeks,
            "customers_per_week": round(customers_per_week),
            "final_daily_revenue": timeline[-1]["daily_revenue"] if timeline else 0,
        }

    def calculate_roi_metrics(self) -> dict:
        """Calculate ROI and break-even metrics"""
        acquisition_model = self.calculate_customer_acquisition_model()
        ai_optimization = self.calculate_ai_cost_optimization()

        # Investment calculation
        total_cac_investment = (
            acquisition_model["additional_customers_needed"]
            * acquisition_model["optimized_cac"]
        )
        operational_costs_monthly = self.operational_costs.total_monthly

        # Revenue calculation
        additional_monthly_revenue = acquisition_model["revenue_gap"]

        # Break-even calculation
        monthly_profit = additional_monthly_revenue - operational_costs_monthly
        break_even_months = (
            total_cac_investment / monthly_profit
            if monthly_profit > 0
            else float("inf")
        )

        # ROI calculation (12-month horizon)
        roi_period_months = 12
        total_revenue_12m = additional_monthly_revenue * roi_period_months
        total_costs_12m = total_cac_investment + (
            operational_costs_monthly * roi_period_months
        )
        roi_12m = (
            ((total_revenue_12m - total_costs_12m) / total_costs_12m) * 100
            if total_costs_12m > 0
            else 0
        )

        return {
            "total_cac_investment": total_cac_investment,
            "additional_monthly_revenue": additional_monthly_revenue,
            "monthly_profit": monthly_profit,
            "break_even_months": round(break_even_months, 1),
            "roi_12_months_pct": round(roi_12m, 1),
            "ai_cost_savings_monthly": ai_optimization["monthly_savings"],
            "payback_period_months": acquisition_model["payback_period_months"],
        }

    def generate_comprehensive_model(self) -> dict:
        """Generate the complete financial model"""
        ai_optimization = self.calculate_ai_cost_optimization()
        acquisition_model = self.calculate_customer_acquisition_model()
        scaling_timeline = self.calculate_scaling_timeline()
        roi_metrics = self.calculate_roi_metrics()

        model = {
            "model_metadata": {
                "generated_at": datetime.now().isoformat(),
                "model_version": "2.0",
                "current_daily_target": self.current_daily_target,
                "scale_daily_target": self.scale_daily_target,
                "timeline_days": self.scale_timeline_days,
            },
            "ai_cost_optimization": ai_optimization,
            "customer_acquisition": acquisition_model,
            "scaling_timeline": scaling_timeline,
            "roi_metrics": roi_metrics,
            "key_assumptions": {
                "trial_conversion_rate": self.customer_metrics.trial_conversion_rate,
                "churn_rate_monthly": self.customer_metrics.churn_rate_monthly,
                "ai_optimization_savings": self.ai_costs.optimization_savings,
                "operational_costs_monthly": self.operational_costs.total_monthly,
            },
            "risk_factors": [
                "Market saturation affecting conversion rates",
                "Increased competition driving up CAC",
                "AI model pricing changes affecting cost structure",
                "Economic downturn reducing enterprise spending",
            ],
            "success_metrics": {
                "target_ltv_cac_ratio": 3.0,
                "target_payback_period_months": 6.0,
                "target_monthly_churn_rate": 0.03,
                "target_roi_12m_pct": 200.0,
            },
        }

        # Save to memory file
        self.save_to_memory(model)

        return model

    def save_to_memory(self, model: dict):
        """Save model to local memory file for continuity"""
        try:
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)

            # Load existing memory
            memory = {}
            if os.path.exists(self.memory_file):
                with open(self.memory_file) as f:
                    memory = json.load(f)

            # Update with new model
            memory["revenue_acceleration_model"] = model
            memory["last_updated"] = datetime.now().isoformat()

            # Save updated memory
            with open(self.memory_file, "w") as f:
                json.dump(memory, f, indent=2)

            logger.info(f"Revenue model saved to memory: {self.memory_file}")

        except Exception as e:
            logger.error(f"Error saving model to memory: {e}")

    def load_from_memory(self) -> Optional[dict]:
        """Load model from memory file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file) as f:
                    memory = json.load(f)
                return memory.get("revenue_acceleration_model")
        except Exception as e:
            logger.error(f"Error loading model from memory: {e}")
        return None

    def update_with_real_time_data(self):
        """Update model with real-time cost tracker data"""
        # Get current AI costs from cost tracker
        dashboard_metrics = self.cost_tracker.get_dashboard_metrics()
        ai_costs = dashboard_metrics.get("ai_costs", {})

        # Update AI cost structure based on actual usage
        total_ai_cost = ai_costs.get("total", 0)
        if total_ai_cost > 0:
            daily_ai_cost = total_ai_cost / 30  # Convert to daily
            self.ai_costs.daily_budget = max(daily_ai_cost, self.ai_costs.daily_budget)

        # Update operational costs based on current spending
        daily_costs = dashboard_metrics.get("daily_costs", 0)
        if daily_costs > 0:
            monthly_costs = daily_costs * 30
            self.operational_costs.total_monthly = monthly_costs

        logger.info("Model updated with real-time cost data")


if __name__ == "__main__":
    # Generate comprehensive revenue acceleration model
    model = RevenueAccelerationModel()
    model.update_with_real_time_data()

    financial_model = model.generate_comprehensive_model()

    # Display key metrics
    print("🚀 REVENUE ACCELERATION MODEL: $300 → $1,000/day")
    print("=" * 60)

    roi = financial_model["roi_metrics"]
    print(f"💰 Investment Required: ${roi['total_cac_investment']:,.0f}")
    print(f"📈 Additional Monthly Revenue: ${roi['additional_monthly_revenue']:,.0f}")
    print(f"⏱️  Break-even Time: {roi['break_even_months']} months")
    print(f"📊 12-Month ROI: {roi['roi_12_months_pct']}%")

    ai_opt = financial_model["ai_cost_optimization"]
    print(f"🤖 AI Cost Savings: ${ai_opt['monthly_savings']:.0f}/month")
    print(
        f"🎯 Optimized Task Distribution: {ai_opt['sonnet_usage_pct']:.0f}% Sonnet, {ai_opt['opus_usage_pct']:.0f}% Opus"
    )

    # Export detailed model
    with open("data/revenue_acceleration_model.json", "w") as f:
        json.dump(financial_model, f, indent=2)

    print("\n📄 Detailed model exported to: data/revenue_acceleration_model.json")
