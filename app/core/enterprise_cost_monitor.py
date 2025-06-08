#!/usr/bin/env python3
"""
Enterprise Claude Code Cost Monitoring System
Activates CEO's strategy for optimal AI spend management
"""

import json
import os
from datetime import datetime, timedelta

from app.config.logging import get_logger
from app.core.session_memory import get_session_memory_manager

logger = get_logger(__name__)


class EnterpriseCostMonitor:
    """Enterprise-grade cost monitoring for Claude Code optimization"""

    def __init__(self):
        self.memory = get_session_memory_manager()
        self.cost_data_file = "data/memory/enterprise_cost_tracking.json"

        # CEO Strategy Parameters
        self.target_monthly_spend = 100.00  # $100/month target
        self.current_baseline_spend = 250.00  # $250/month baseline
        self.target_cost_reduction = 0.6  # 60% minimum savings target

        # Model Usage Strategy (CEO's directive)
        self.target_model_distribution = {
            "sonnet_4": 0.80,  # 80% of operations
            "opus_4": 0.10,  # 10% of operations
            "haiku_4": 0.10,  # 10% of operations
        }

        # Model costs per million tokens
        self.model_costs = {
            "sonnet_4": {"input": 3.0, "output": 15.0},
            "opus_4": {"input": 15.0, "output": 75.0},
            "haiku_4": {"input": 0.25, "output": 1.25},
        }

        # Week 1 Revenue Targets
        self.week1_revenue_target = 400.00  # $400/day
        self.week1_cost_reduction_target = 0.30  # 30% cost reduction

        # Initialize tracking
        self.week1_start_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.week1_end_date = self.week1_start_date + timedelta(days=7)

        logger.info("Enterprise Cost Monitor activated with CEO strategy")

    def activate_cost_monitoring(self) -> dict:
        """Activate the enterprise cost monitoring system"""

        logger.info("🎯 Activating Enterprise Cost Monitoring System")

        # Initialize cost tracking structure
        cost_tracking = {
            "activation_timestamp": datetime.now().isoformat(),
            "strategy_parameters": {
                "target_monthly_spend": self.target_monthly_spend,
                "baseline_monthly_spend": self.current_baseline_spend,
                "target_cost_reduction": f"{self.target_cost_reduction*100}%",
                "model_distribution_strategy": self.target_model_distribution,
            },
            "week1_targets": {
                "revenue_target": f"${self.week1_revenue_target}/day",
                "cost_reduction_target": f"{self.week1_cost_reduction_target*100}%",
                "tracking_period": {
                    "start": self.week1_start_date.isoformat(),
                    "end": self.week1_end_date.isoformat(),
                },
            },
            "daily_tracking": {},
            "alerts": [],
            "optimization_recommendations": [],
        }

        # Store activation in persistent memory
        self.memory.store_memory_node(
            category="enterprise_cost_monitoring",
            content=cost_tracking,
            tags=["ceo_strategy", "cost_optimization", "week1_activation"],
            importance_score=1.0,
        )

        # Create initial cost tracking file
        os.makedirs(os.path.dirname(self.cost_data_file), exist_ok=True)
        with open(self.cost_data_file, "w") as f:
            json.dump(cost_tracking, f, indent=2)

        logger.info(
            "✅ Cost monitoring system activated and stored in persistent memory"
        )

        return {
            "status": "activated",
            "monitoring_active": True,
            "cost_tracking_file": self.cost_data_file,
            "week1_monitoring": "enabled",
            "ceo_strategy_compliance": "active",
        }

    def track_token_usage(
        self,
        operation: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> dict:
        """Track individual token usage with enterprise monitoring"""

        usage_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "model": model,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "cost": cost,
            "model_efficiency_score": self._calculate_model_efficiency(model, cost),
        }

        # Load current tracking data
        tracking_data = self._load_cost_tracking_data()

        # Add to daily tracking
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in tracking_data["daily_tracking"]:
            tracking_data["daily_tracking"][today] = {
                "operations": [],
                "daily_totals": {
                    "total_cost": 0,
                    "total_tokens": 0,
                    "model_breakdown": {"sonnet_4": 0, "opus_4": 0, "haiku_4": 0},
                },
            }

        # Add usage entry
        tracking_data["daily_tracking"][today]["operations"].append(usage_entry)

        # Update daily totals
        daily_totals = tracking_data["daily_tracking"][today]["daily_totals"]
        daily_totals["total_cost"] += cost
        daily_totals["total_tokens"] += input_tokens + output_tokens
        daily_totals["model_breakdown"][model] += cost

        # Check for cost alerts
        self._check_cost_alerts(tracking_data, daily_totals["total_cost"])

        # Save updated tracking data
        self._save_cost_tracking_data(tracking_data)

        logger.info(f"Token usage tracked: {operation} - {model} - ${cost:.2f}")

        return usage_entry

    def generate_week1_progress_report(self) -> dict:
        """Generate comprehensive Week 1 progress report"""

        logger.info("📊 Generating Week 1 Progress Report")

        tracking_data = self._load_cost_tracking_data()

        # Calculate Week 1 metrics
        week1_metrics = self._calculate_week1_metrics(tracking_data)

        # Generate cost report
        cost_report = {
            "report_period": "Week 1",
            "generated_at": datetime.now().isoformat(),
            "targets_vs_actual": {
                "revenue_target": f"${self.week1_revenue_target}/day",
                "cost_reduction_target": f"{self.week1_cost_reduction_target*100}%",
                "ai_spend_target": f"${self.target_monthly_spend/4:.2f}/week",
                "actual_ai_spend": f"${week1_metrics['total_week_cost']:.2f}",
                "cost_reduction_achieved": f"{week1_metrics['cost_reduction_achieved']*100:.1f}%",
            },
            "model_usage_analysis": {
                "target_distribution": self.target_model_distribution,
                "actual_distribution": week1_metrics["actual_model_distribution"],
                "compliance_score": week1_metrics["distribution_compliance_score"],
            },
            "cost_breakdown": {
                "total_spend": week1_metrics["total_week_cost"],
                "daily_average": week1_metrics["daily_average_cost"],
                "model_breakdown": week1_metrics["model_cost_breakdown"],
                "savings_achieved": week1_metrics["savings_vs_baseline"],
            },
            "efficiency_metrics": {
                "cost_per_operation": week1_metrics["cost_per_operation"],
                "tokens_per_dollar": week1_metrics["tokens_per_dollar"],
                "model_efficiency_scores": week1_metrics["model_efficiency_scores"],
            },
            "alerts_and_recommendations": tracking_data.get("alerts", []),
            "week1_grade": self._calculate_week1_grade(week1_metrics),
        }

        # Generate token usage report
        token_usage_report = {
            "report_type": "Week 1 Token Usage Analysis",
            "tracking_period": {
                "start": self.week1_start_date.isoformat(),
                "end": datetime.now().isoformat(),
                "days_tracked": len(week1_metrics["daily_data"]),
            },
            "token_summary": {
                "total_tokens_used": week1_metrics["total_tokens"],
                "input_tokens": week1_metrics["total_input_tokens"],
                "output_tokens": week1_metrics["total_output_tokens"],
                "average_tokens_per_day": week1_metrics["average_tokens_per_day"],
            },
            "model_performance": {
                "sonnet_4": {
                    "usage_percentage": f"{week1_metrics['actual_model_distribution']['sonnet_4']*100:.1f}%",
                    "target_percentage": "80%",
                    "compliance": (
                        "✅"
                        if week1_metrics["actual_model_distribution"]["sonnet_4"]
                        >= 0.75
                        else "⚠️"
                    ),
                    "cost_efficiency": week1_metrics["model_efficiency_scores"].get(
                        "sonnet_4", 0
                    ),
                },
                "opus_4": {
                    "usage_percentage": f"{week1_metrics['actual_model_distribution']['opus_4']*100:.1f}%",
                    "target_percentage": "10%",
                    "compliance": (
                        "✅"
                        if week1_metrics["actual_model_distribution"]["opus_4"] <= 0.15
                        else "⚠️"
                    ),
                    "cost_efficiency": week1_metrics["model_efficiency_scores"].get(
                        "opus_4", 0
                    ),
                },
                "haiku_4": {
                    "usage_percentage": f"{week1_metrics['actual_model_distribution']['haiku_4']*100:.1f}%",
                    "target_percentage": "10%",
                    "compliance": (
                        "✅"
                        if week1_metrics["actual_model_distribution"]["haiku_4"] >= 0.05
                        else "⚠️"
                    ),
                    "cost_efficiency": week1_metrics["model_efficiency_scores"].get(
                        "haiku_4", 0
                    ),
                },
            },
            "cost_optimization_status": {
                "target_savings": "60-80%",
                "achieved_savings": f"{week1_metrics['cost_reduction_achieved']*100:.1f}%",
                "monthly_projection": f"${week1_metrics['total_week_cost']*4:.2f}",
                "on_track_for_target": week1_metrics["total_week_cost"] * 4
                <= self.target_monthly_spend,
            },
        }

        # Store reports in persistent memory
        self.memory.store_memory_node(
            category="week1_cost_report",
            content={
                "cost_report": cost_report,
                "token_usage_report": token_usage_report,
            },
            tags=["week1_progress", "cost_analysis", "ceo_strategy"],
            importance_score=1.0,
        )

        # Save to files
        reports_dir = "data/memory/week1_reports"
        os.makedirs(reports_dir, exist_ok=True)

        with open(f"{reports_dir}/week1_cost_report.json", "w") as f:
            json.dump(cost_report, f, indent=2)

        with open(f"{reports_dir}/week1_token_usage_report.json", "w") as f:
            json.dump(token_usage_report, f, indent=2)

        logger.info("✅ Week 1 reports generated and stored in persistent memory")

        return {
            "cost_report": cost_report,
            "token_usage_report": token_usage_report,
            "reports_stored": True,
            "memory_persistence": True,
        }

    def _calculate_week1_metrics(self, tracking_data: dict) -> dict:
        """Calculate comprehensive Week 1 metrics"""

        daily_data = tracking_data.get("daily_tracking", {})

        total_cost = 0
        total_tokens = 0
        total_input_tokens = 0
        total_output_tokens = 0
        model_costs = {"sonnet_4": 0, "opus_4": 0, "haiku_4": 0}
        total_operations = 0

        for data in daily_data.values():
            daily_totals = data.get("daily_totals", {})
            total_cost += daily_totals.get("total_cost", 0)
            total_tokens += daily_totals.get("total_tokens", 0)

            for operation in data.get("operations", []):
                total_input_tokens += operation["tokens"]["input"]
                total_output_tokens += operation["tokens"]["output"]
                model_costs[operation["model"]] += operation["cost"]
                total_operations += 1

        # Calculate model distribution
        total_model_cost = sum(model_costs.values())
        actual_distribution = {
            model: (cost / total_model_cost if total_model_cost > 0 else 0)
            for model, cost in model_costs.items()
        }

        # Calculate compliance score
        compliance_score = 1.0
        for model, target_pct in self.target_model_distribution.items():
            actual_pct = actual_distribution.get(model, 0)
            deviation = abs(target_pct - actual_pct)
            compliance_score -= deviation * 0.5  # Penalty for deviation

        compliance_score = max(0, compliance_score)

        # Calculate savings
        baseline_week_cost = self.current_baseline_spend / 4  # Weekly baseline
        cost_reduction_achieved = max(
            0, (baseline_week_cost - total_cost) / baseline_week_cost
        )
        savings_vs_baseline = baseline_week_cost - total_cost

        return {
            "total_week_cost": total_cost,
            "daily_average_cost": total_cost / max(1, len(daily_data)),
            "total_tokens": total_tokens,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "average_tokens_per_day": total_tokens / max(1, len(daily_data)),
            "model_cost_breakdown": model_costs,
            "actual_model_distribution": actual_distribution,
            "distribution_compliance_score": compliance_score,
            "cost_reduction_achieved": cost_reduction_achieved,
            "savings_vs_baseline": savings_vs_baseline,
            "cost_per_operation": total_cost / max(1, total_operations),
            "tokens_per_dollar": total_tokens / max(0.01, total_cost),
            "model_efficiency_scores": self._calculate_all_model_efficiency_scores(
                daily_data
            ),
            "daily_data": daily_data,
        }

    def _calculate_model_efficiency(self, model: str, cost: float) -> float:
        """Calculate efficiency score for model usage"""

        # Efficiency is based on cost-effectiveness vs target usage
        target_usage = self.target_model_distribution.get(model, 0)

        if model == "sonnet_4":  # Should be used most (80%)
            return min(1.0, target_usage / max(0.01, cost * 10))
        elif model == "haiku_4":  # Should be used for simple tasks (10%)
            return min(1.0, 1 / max(0.01, cost * 100))  # Reward low cost
        else:  # opus_4 - should be used sparingly (10%)
            return min(1.0, 0.1 / max(0.01, cost))  # Penalize high cost

    def _calculate_all_model_efficiency_scores(self, daily_data: dict) -> dict:
        """Calculate efficiency scores for all models"""

        model_efficiency = {"sonnet_4": 0, "opus_4": 0, "haiku_4": 0}
        model_usage_count = {"sonnet_4": 0, "opus_4": 0, "haiku_4": 0}

        for day_data in daily_data.values():
            for operation in day_data.get("operations", []):
                model = operation["model"]
                efficiency = operation.get("model_efficiency_score", 0)
                model_efficiency[model] += efficiency
                model_usage_count[model] += 1

        # Average efficiency per model
        return {
            model: (total / max(1, model_usage_count[model]))
            for model, total in model_efficiency.items()
        }

    def _calculate_week1_grade(self, metrics: dict) -> dict:
        """Calculate overall Week 1 performance grade"""

        grade_components = {
            "cost_reduction": min(
                100,
                metrics["cost_reduction_achieved"]
                * 100
                / self.week1_cost_reduction_target,
            ),
            "model_compliance": metrics["distribution_compliance_score"] * 100,
            "efficiency": min(
                100, metrics["tokens_per_dollar"] / 1000 * 100
            ),  # Normalize
            "budget_adherence": min(
                100,
                (self.target_monthly_spend / 4)
                / max(0.01, metrics["total_week_cost"])
                * 100,
            ),
        }

        overall_score = sum(grade_components.values()) / len(grade_components)

        if overall_score >= 90:
            letter_grade = "A"
            assessment = "Excellent - exceeding CEO strategy targets"
        elif overall_score >= 80:
            letter_grade = "B"
            assessment = "Good - meeting most CEO strategy targets"
        elif overall_score >= 70:
            letter_grade = "C"
            assessment = "Satisfactory - some optimization needed"
        else:
            letter_grade = "D"
            assessment = "Needs improvement - strategy adjustments required"

        return {
            "overall_score": round(overall_score, 1),
            "letter_grade": letter_grade,
            "assessment": assessment,
            "component_scores": grade_components,
        }

    def _check_cost_alerts(self, tracking_data: dict, daily_cost: float):
        """Check for cost alerts and add to tracking"""

        alerts = tracking_data.get("alerts", [])

        # Daily cost threshold alert
        daily_threshold = self.target_monthly_spend / 30  # Daily target
        if daily_cost > daily_threshold * 1.5:  # 50% over daily target
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": "DAILY_COST_EXCEEDED",
                "severity": "HIGH",
                "message": f"Daily cost ${daily_cost:.2f} exceeds target ${daily_threshold:.2f}",
                "recommendation": "Switch to more cost-effective models (Sonnet 4 or Haiku 4)",
            }
            alerts.append(alert)

        tracking_data["alerts"] = alerts

    def _load_cost_tracking_data(self) -> dict:
        """Load cost tracking data from file"""
        if os.path.exists(self.cost_data_file):
            with open(self.cost_data_file) as f:
                return json.load(f)
        return {"daily_tracking": {}, "alerts": []}

    def _save_cost_tracking_data(self, data: dict):
        """Save cost tracking data to file"""
        with open(self.cost_data_file, "w") as f:
            json.dump(data, f, indent=2)


def simulate_week1_operations():
    """Simulate Week 1 operations for demonstration"""

    monitor = EnterpriseCostMonitor()

    # Activate monitoring
    activation_result = monitor.activate_cost_monitoring()
    print("🎯 Cost Monitoring Activated:")
    print(json.dumps(activation_result, indent=2))
    print()

    # Simulate various operations throughout Week 1
    operations = [
        # Day 1 - Foundation setup (heavy Sonnet 4 usage)
        ("market_research_analysis", "sonnet_4", 2500, 1200, 0.75),
        ("customer_segmentation", "sonnet_4", 1800, 900, 0.54),
        ("competitive_analysis", "sonnet_4", 2200, 1100, 0.66),
        ("content_strategy_planning", "sonnet_4", 1500, 800, 0.48),
        # Day 2 - Strategic synthesis (Opus 4 for complex tasks)
        ("strategic_plan_synthesis", "opus_4", 3000, 2000, 4.50),
        ("financial_model_analysis", "sonnet_4", 2000, 1000, 0.60),
        ("risk_assessment", "sonnet_4", 1200, 600, 0.36),
        # Day 3 - Implementation planning (Mixed usage)
        ("technical_architecture", "sonnet_4", 2800, 1400, 0.84),
        ("api_endpoint_generation", "sonnet_4", 1600, 800, 0.48),
        ("simple_data_processing", "haiku_4", 800, 400, 0.03),
        ("email_template_creation", "haiku_4", 600, 300, 0.02),
        # Day 4 - Content creation and optimization
        ("blog_content_generation", "sonnet_4", 2200, 1100, 0.66),
        ("social_media_content", "haiku_4", 1000, 500, 0.04),
        ("presentation_creation", "opus_4", 2500, 1500, 3.00),
        # Day 5 - Analysis and reporting
        ("performance_analytics", "sonnet_4", 1800, 900, 0.54),
        ("cost_optimization_analysis", "sonnet_4", 2000, 1000, 0.60),
        ("simple_report_formatting", "haiku_4", 500, 250, 0.02),
        # Day 6 - Customer outreach
        ("prospect_qualification", "sonnet_4", 1500, 750, 0.45),
        ("email_personalization", "sonnet_4", 1200, 600, 0.36),
        ("follow_up_sequences", "haiku_4", 800, 400, 0.03),
        # Day 7 - Week 1 completion and planning
        ("week1_strategy_review", "opus_4", 2000, 1200, 2.40),
        ("next_week_planning", "sonnet_4", 1500, 800, 0.48),
        ("simple_task_automation", "haiku_4", 400, 200, 0.02),
    ]

    print("📊 Tracking Week 1 Operations:")
    total_tracked_cost = 0

    for operation, model, input_tokens, output_tokens, cost in operations:
        monitor.track_token_usage(operation, model, input_tokens, output_tokens, cost)
        total_tracked_cost += cost
        print(f"• {operation}: {model} - ${cost:.2f}")

    print(f"\nTotal simulated cost: ${total_tracked_cost:.2f}")
    print()

    # Generate Week 1 report
    reports = monitor.generate_week1_progress_report()

    return reports


if __name__ == "__main__":
    reports = simulate_week1_operations()

    print("📋 WEEK 1 COST REPORT:")
    print(json.dumps(reports["cost_report"], indent=2))

    print("\n📊 WEEK 1 TOKEN USAGE REPORT:")
    print(json.dumps(reports["token_usage_report"], indent=2))
