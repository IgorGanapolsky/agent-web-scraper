"""
Token Usage Monitoring for Claude 4 Cost Optimization
Tracks token consumption and provides budget alerts for Claude Code usage.
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from app.config.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TokenUsage:
    """Token usage record for a single API call"""

    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    session_id: Optional[str] = None
    task_type: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class BudgetAlert:
    """Budget alert configuration and status"""

    alert_id: str
    threshold_usd: float
    period_days: int
    alert_type: str  # daily, weekly, monthly, total
    is_active: bool = True
    last_triggered: Optional[datetime] = None


class TokenMonitor:
    """
    Enterprise token usage monitoring for Claude 4 optimization.
    Provides cost tracking, budget alerts, and usage optimization insights.
    """

    # Claude 4 pricing (per million tokens)
    CLAUDE_4_PRICING = {
        "claude-4": {
            "input": 15.0,  # $15 per million input tokens
            "output": 75.0,  # $75 per million output tokens
        },
        "claude-4-sonnet": {
            "input": 3.0,  # $3 per million input tokens
            "output": 15.0,  # $15 per million output tokens
        },
        "claude-3.5-sonnet": {
            "input": 3.0,  # $3 per million input tokens
            "output": 15.0,  # $15 per million output tokens
        },
        "claude-3-opus": {
            "input": 15.0,  # $15 per million input tokens
            "output": 75.0,  # $75 per million output tokens
        },
    }

    def __init__(self, data_dir: str = "./data/token_usage"):
        """
        Initialize token monitoring system.

        Args:
            data_dir: Directory for storing usage data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.usage_records: list[TokenUsage] = []
        self.budget_alerts: dict[str, BudgetAlert] = {}

        # Load existing data
        self._load_usage_data()
        self._load_budget_alerts()

        # Default budget alerts
        self._setup_default_alerts()

    def record_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: Optional[str] = None,
        task_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> float:
        """
        Record token usage and calculate cost.

        Args:
            model: Claude model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            session_id: Session identifier
            task_type: Type of task (market_research, code_generation, etc.)
            user_id: User identifier

        Returns:
            Cost in USD for this API call
        """
        # Calculate cost
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)

        # Create usage record
        usage_record = TokenUsage(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            session_id=session_id,
            task_type=task_type,
            user_id=user_id,
        )

        self.usage_records.append(usage_record)

        # Persist usage data
        self._persist_usage_data()

        # Check budget alerts
        self._check_budget_alerts()

        logger.info(
            f"Recorded token usage: {input_tokens + output_tokens} tokens, ${cost_usd:.4f} cost"
        )

        return cost_usd

    def get_usage_summary(
        self,
        period_days: int = 30,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive usage summary for specified period.

        Args:
            period_days: Number of days to analyze
            user_id: Filter by specific user
            task_type: Filter by specific task type

        Returns:
            Usage summary with costs and optimization recommendations
        """
        cutoff_date = datetime.now() - timedelta(days=period_days)

        # Filter records
        filtered_records = [
            record for record in self.usage_records if record.timestamp >= cutoff_date
        ]

        if user_id:
            filtered_records = [r for r in filtered_records if r.user_id == user_id]

        if task_type:
            filtered_records = [r for r in filtered_records if r.task_type == task_type]

        if not filtered_records:
            return {"error": "No usage data found for specified filters"}

        # Calculate metrics
        total_tokens = sum(r.total_tokens for r in filtered_records)
        total_cost = sum(r.cost_usd for r in filtered_records)
        total_calls = len(filtered_records)

        # Model breakdown
        model_usage = {}
        for record in filtered_records:
            if record.model not in model_usage:
                model_usage[record.model] = {"calls": 0, "tokens": 0, "cost": 0.0}
            model_usage[record.model]["calls"] += 1
            model_usage[record.model]["tokens"] += record.total_tokens
            model_usage[record.model]["cost"] += record.cost_usd

        # Task type breakdown
        task_usage = {}
        for record in filtered_records:
            task = record.task_type or "unknown"
            if task not in task_usage:
                task_usage[task] = {"calls": 0, "tokens": 0, "cost": 0.0}
            task_usage[task]["calls"] += 1
            task_usage[task]["tokens"] += record.total_tokens
            task_usage[task]["cost"] += record.cost_usd

        # Daily usage trend
        daily_usage = {}
        for record in filtered_records:
            date_key = record.timestamp.strftime("%Y-%m-%d")
            if date_key not in daily_usage:
                daily_usage[date_key] = {"calls": 0, "tokens": 0, "cost": 0.0}
            daily_usage[date_key]["calls"] += 1
            daily_usage[date_key]["tokens"] += record.total_tokens
            daily_usage[date_key]["cost"] += record.cost_usd

        return {
            "period_summary": {
                "period_days": period_days,
                "total_api_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "average_cost_per_call": (
                    round(total_cost / total_calls, 4) if total_calls > 0 else 0
                ),
                "average_tokens_per_call": (
                    round(total_tokens / total_calls, 0) if total_calls > 0 else 0
                ),
            },
            "model_breakdown": model_usage,
            "task_breakdown": task_usage,
            "daily_usage_trend": daily_usage,
            "cost_optimization_insights": self._generate_optimization_insights(
                filtered_records
            ),
        }

    def get_budget_status(self) -> dict[str, Any]:
        """
        Get current budget alert status and recommendations.

        Returns:
            Budget status with alerts and recommendations
        """
        budget_status = {}

        for alert_id, alert in self.budget_alerts.items():
            if not alert.is_active:
                continue

            # Calculate usage for alert period
            cutoff_date = datetime.now() - timedelta(days=alert.period_days)
            period_records = [
                record
                for record in self.usage_records
                if record.timestamp >= cutoff_date
            ]

            period_cost = sum(record.cost_usd for record in period_records)
            percentage_used = (period_cost / alert.threshold_usd) * 100

            budget_status[alert_id] = {
                "alert_type": alert.alert_type,
                "threshold_usd": alert.threshold_usd,
                "current_usage_usd": round(period_cost, 4),
                "percentage_used": round(percentage_used, 1),
                "days_remaining": alert.period_days,
                "status": self._get_alert_status(percentage_used),
                "last_triggered": (
                    alert.last_triggered.isoformat() if alert.last_triggered else None
                ),
            }

        return {
            "budget_alerts": budget_status,
            "recommendations": self._get_budget_recommendations(budget_status),
        }

    def create_budget_alert(
        self, threshold_usd: float, period_days: int, alert_type: str = "custom"
    ) -> str:
        """
        Create custom budget alert.

        Args:
            threshold_usd: Budget threshold in USD
            period_days: Period in days for the budget
            alert_type: Type of alert (custom, daily, weekly, monthly)

        Returns:
            Alert ID
        """
        alert_id = f"{alert_type}_{int(time.time())}"

        budget_alert = BudgetAlert(
            alert_id=alert_id,
            threshold_usd=threshold_usd,
            period_days=period_days,
            alert_type=alert_type,
        )

        self.budget_alerts[alert_id] = budget_alert
        self._persist_budget_alerts()

        logger.info(f"Created budget alert: {alert_id} with ${threshold_usd} threshold")

        return alert_id

    def optimize_token_usage(self, task_type: str) -> dict[str, Any]:
        """
        Provide optimization recommendations for specific task types.

        Args:
            task_type: Type of task to optimize

        Returns:
            Optimization recommendations
        """
        # Analyze usage patterns for task type
        task_records = [
            record for record in self.usage_records if record.task_type == task_type
        ]

        if not task_records:
            return {"error": f"No usage data found for task type: {task_type}"}

        # Calculate metrics
        avg_input_tokens = sum(r.input_tokens for r in task_records) / len(task_records)
        avg_output_tokens = sum(r.output_tokens for r in task_records) / len(
            task_records
        )
        avg_cost = sum(r.cost_usd for r in task_records) / len(task_records)

        # Model performance analysis
        model_performance = {}
        for record in task_records:
            if record.model not in model_performance:
                model_performance[record.model] = {
                    "count": 0,
                    "avg_cost": 0.0,
                    "avg_tokens": 0.0,
                }
            model_performance[record.model]["count"] += 1
            model_performance[record.model]["avg_cost"] += record.cost_usd
            model_performance[record.model]["avg_tokens"] += record.total_tokens

        # Finalize averages
        for perf in model_performance.values():
            perf["avg_cost"] = perf["avg_cost"] / perf["count"]
            perf["avg_tokens"] = perf["avg_tokens"] / perf["count"]

        # Generate recommendations
        recommendations = self._generate_task_recommendations(
            task_type, avg_input_tokens, avg_output_tokens, model_performance
        )

        return {
            "task_type": task_type,
            "current_metrics": {
                "average_input_tokens": round(avg_input_tokens, 0),
                "average_output_tokens": round(avg_output_tokens, 0),
                "average_cost_per_call": round(avg_cost, 4),
                "total_calls_analyzed": len(task_records),
            },
            "model_performance": model_performance,
            "optimization_recommendations": recommendations,
        }

    def _calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost for token usage"""
        if model not in self.CLAUDE_4_PRICING:
            # Default to Claude 4 pricing for unknown models
            pricing = self.CLAUDE_4_PRICING["claude-4"]
        else:
            pricing = self.CLAUDE_4_PRICING[model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _setup_default_alerts(self):
        """Setup default budget alerts"""
        default_alerts = [
            {"threshold": 50.0, "period": 30, "type": "monthly"},
            {"threshold": 10.0, "period": 7, "type": "weekly"},
            {"threshold": 2.0, "period": 1, "type": "daily"},
        ]

        for alert_config in default_alerts:
            alert_id = f"default_{alert_config['type']}"
            if alert_id not in self.budget_alerts:
                self.budget_alerts[alert_id] = BudgetAlert(
                    alert_id=alert_id,
                    threshold_usd=alert_config["threshold"],
                    period_days=alert_config["period"],
                    alert_type=alert_config["type"],
                )

    def _check_budget_alerts(self):
        """Check if any budget alerts should be triggered"""
        for alert in self.budget_alerts.values():
            if not alert.is_active:
                continue

            cutoff_date = datetime.now() - timedelta(days=alert.period_days)
            period_records = [
                record
                for record in self.usage_records
                if record.timestamp >= cutoff_date
            ]

            period_cost = sum(record.cost_usd for record in period_records)

            if period_cost >= alert.threshold_usd:
                self._trigger_budget_alert(alert, period_cost)

    def _trigger_budget_alert(self, alert: BudgetAlert, current_cost: float):
        """Trigger budget alert"""
        # Only trigger once per period
        if alert.last_triggered:
            time_since_last = datetime.now() - alert.last_triggered
            if time_since_last.days < alert.period_days:
                return

        alert.last_triggered = datetime.now()

        logger.warning(
            f"BUDGET ALERT: {alert.alert_type} spending of ${current_cost:.2f} "
            f"exceeded threshold of ${alert.threshold_usd:.2f}"
        )

        self._persist_budget_alerts()

    def _get_alert_status(self, percentage_used: float) -> str:
        """Get alert status based on usage percentage"""
        if percentage_used >= 100:
            return "EXCEEDED"
        elif percentage_used >= 80:
            return "WARNING"
        elif percentage_used >= 60:
            return "CAUTION"
        else:
            return "NORMAL"

    def _generate_optimization_insights(self, records: list[TokenUsage]) -> list[str]:
        """Generate optimization insights from usage patterns"""
        insights = []

        if not records:
            return insights

        # Model efficiency analysis
        model_costs = {}
        for record in records:
            if record.model not in model_costs:
                model_costs[record.model] = []
            model_costs[record.model].append(record.cost_usd)

        if len(model_costs) > 1:
            most_expensive_model = max(
                model_costs.keys(),
                key=lambda m: sum(model_costs[m]) / len(model_costs[m]),
            )
            least_expensive_model = min(
                model_costs.keys(),
                key=lambda m: sum(model_costs[m]) / len(model_costs[m]),
            )

            if most_expensive_model != least_expensive_model:
                insights.append(
                    f"Consider using {least_expensive_model} instead of {most_expensive_model} "
                    f"for cost optimization"
                )

        # Token usage patterns
        avg_tokens = sum(r.total_tokens for r in records) / len(records)
        if avg_tokens > 10000:
            insights.append(
                "High token usage detected. Consider breaking down complex tasks into smaller prompts"
            )

        # Output/input ratio analysis
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)

        if total_output > total_input * 2:
            insights.append(
                "High output-to-input ratio. Consider more specific prompts to reduce output tokens"
            )

        return insights

    def _generate_task_recommendations(
        self,
        task_type: str,
        avg_input: float,
        avg_output: float,
        model_performance: dict[str, Any],
    ) -> list[str]:
        """Generate task-specific optimization recommendations"""
        recommendations = []

        # Model selection recommendations
        if len(model_performance) > 1:
            best_model = min(
                model_performance.keys(), key=lambda m: model_performance[m]["avg_cost"]
            )
            recommendations.append(
                f"For {task_type} tasks, {best_model} offers the best cost efficiency"
            )

        # Token optimization recommendations
        if avg_input > 5000:
            recommendations.append(
                f"Consider using batch processing to reduce per-call overhead for {task_type}"
            )

        if avg_output > avg_input * 3:
            recommendations.append(
                f"Add output length constraints to {task_type} prompts to reduce costs"
            )

        # Task-specific optimizations
        task_optimizations = {
            "market_research": [
                "Use structured JSON output to reduce token usage",
                "Implement result caching for similar queries",
            ],
            "code_generation": [
                "Specify exact requirements to minimize iterations",
                "Use batch generation for multiple similar components",
            ],
            "data_analysis": [
                "Pre-process data to reduce input token count",
                "Use summary prompts before detailed analysis",
            ],
        }

        if task_type in task_optimizations:
            recommendations.extend(task_optimizations[task_type])

        return recommendations

    def _get_budget_recommendations(self, budget_status: dict[str, Any]) -> list[str]:
        """Generate budget management recommendations"""
        recommendations = []

        for alert_id, status in budget_status.items():
            if status["status"] in ["WARNING", "EXCEEDED"]:
                recommendations.append(
                    f"Consider optimizing {alert_id} usage - currently at {status['percentage_used']}%"
                )

            if status["percentage_used"] > 90:
                recommendations.append(
                    "Switch to more cost-effective models for non-critical tasks"
                )

        if not recommendations:
            recommendations.append("Token usage is within budget - continue monitoring")

        return recommendations

    def _persist_usage_data(self):
        """Persist usage data to disk"""
        usage_file = self.data_dir / "token_usage.json"

        try:
            serializable_records = []
            for record in self.usage_records[-1000:]:  # Keep last 1000 records
                record_dict = asdict(record)
                record_dict["timestamp"] = record.timestamp.isoformat()
                serializable_records.append(record_dict)

            with open(usage_file, "w") as f:
                json.dump(serializable_records, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to persist usage data: {e}")

    def _load_usage_data(self):
        """Load usage data from disk"""
        usage_file = self.data_dir / "token_usage.json"

        if usage_file.exists():
            try:
                with open(usage_file) as f:
                    usage_data = json.load(f)

                for record_data in usage_data:
                    record_data["timestamp"] = datetime.fromisoformat(
                        record_data["timestamp"]
                    )
                    usage_record = TokenUsage(**record_data)
                    self.usage_records.append(usage_record)

                logger.info(f"Loaded {len(self.usage_records)} usage records")

            except Exception as e:
                logger.error(f"Failed to load usage data: {e}")

    def _persist_budget_alerts(self):
        """Persist budget alerts to disk"""
        alerts_file = self.data_dir / "budget_alerts.json"

        try:
            serializable_alerts = {}
            for alert_id, alert in self.budget_alerts.items():
                alert_dict = asdict(alert)
                if alert.last_triggered:
                    alert_dict["last_triggered"] = alert.last_triggered.isoformat()
                serializable_alerts[alert_id] = alert_dict

            with open(alerts_file, "w") as f:
                json.dump(serializable_alerts, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to persist budget alerts: {e}")

    def _load_budget_alerts(self):
        """Load budget alerts from disk"""
        alerts_file = self.data_dir / "budget_alerts.json"

        if alerts_file.exists():
            try:
                with open(alerts_file) as f:
                    alerts_data = json.load(f)

                for alert_id, alert_data in alerts_data.items():
                    if alert_data.get("last_triggered"):
                        alert_data["last_triggered"] = datetime.fromisoformat(
                            alert_data["last_triggered"]
                        )
                    else:
                        alert_data["last_triggered"] = None

                    budget_alert = BudgetAlert(**alert_data)
                    self.budget_alerts[alert_id] = budget_alert

                logger.info(f"Loaded {len(self.budget_alerts)} budget alerts")

            except Exception as e:
                logger.error(f"Failed to load budget alerts: {e}")


# Global token monitor instance
_token_monitor = None


def get_token_monitor() -> TokenMonitor:
    """Get the global token monitor instance"""
    global _token_monitor
    if _token_monitor is None:
        _token_monitor = TokenMonitor()
    return _token_monitor


# Convenience functions for common monitoring scenarios
def track_api_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    task_type: str | None = None,
    session_id: str | None = None,
) -> float:
    """Quick function to track API call token usage"""
    monitor = get_token_monitor()
    return monitor.record_token_usage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        task_type=task_type,
        session_id=session_id,
    )


def get_current_budget_status() -> dict[str, Any]:
    """Quick function to get current budget status"""
    monitor = get_token_monitor()
    return monitor.get_budget_status()


def optimize_for_task(task_type: str) -> dict[str, Any]:
    """Quick function to get optimization recommendations for a task"""
    monitor = get_token_monitor()
    return monitor.optimize_token_usage(task_type)
