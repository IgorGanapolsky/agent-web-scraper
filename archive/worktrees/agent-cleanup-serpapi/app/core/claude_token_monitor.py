"""
Claude Token Usage Monitor
Tracks and optimizes Claude 4 API costs for budget management
"""

import json
import os
from datetime import datetime, timedelta
from typing import ClassVar, Optional

from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.cost_tracker import CostTracker

logger = get_logger(__name__)


class TokenUsage(BaseModel):
    """Token usage tracking model"""

    timestamp: datetime
    model: str  # sonnet-4, opus-4
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    session_id: str
    task_type: str


class ClaudeTokenMonitor:
    """Monitor and optimize Claude token usage"""

    # Claude 4 pricing (per million tokens)
    PRICING: ClassVar[dict[str, dict[str, float]]] = {
        "claude-4-opus": {"input": 15.0, "output": 75.0},
        "claude-4-sonnet": {"input": 3.0, "output": 15.0},
    }

    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker or CostTracker()
        self.usage_log: list[TokenUsage] = []
        self.daily_budget = float(os.getenv("CLAUDE_DAILY_BUDGET", "10.0"))
        self.session_memory_file = "data/claude_sessions.json"

    def track_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        session_id: str,
        task_type: str = "general",
    ) -> float:
        """Track token usage and calculate cost"""

        total_tokens = input_tokens + output_tokens

        # Calculate cost
        if model in self.PRICING:
            input_cost = (input_tokens / 1_000_000) * self.PRICING[model]["input"]
            output_cost = (output_tokens / 1_000_000) * self.PRICING[model]["output"]
            total_cost = input_cost + output_cost
        else:
            # Default to Sonnet pricing
            input_cost = (input_tokens / 1_000_000) * self.PRICING["claude-4-sonnet"][
                "input"
            ]
            output_cost = (output_tokens / 1_000_000) * self.PRICING["claude-4-sonnet"][
                "output"
            ]
            total_cost = input_cost + output_cost

        # Log usage
        usage = TokenUsage(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost=total_cost,
            session_id=session_id,
            task_type=task_type,
        )

        self.usage_log.append(usage)

        # Track in cost tracker
        self.cost_tracker.add_cost_event(
            service="claude_api",
            cost=total_cost,
            metadata={
                "model": model,
                "tokens": total_tokens,
                "task_type": task_type,
                "session_id": session_id,
            },
        )

        logger.info(
            f"Claude usage: {total_tokens} tokens, ${total_cost:.4f} for {task_type}"
        )

        # Check budget limits
        self._check_budget_alerts(total_cost)

        return total_cost

    def _check_budget_alerts(self, current_cost: float):
        """Check if approaching budget limits"""
        daily_spent = self.get_daily_spend()

        if daily_spent > self.daily_budget * 0.8:  # 80% threshold
            logger.warning(
                f"Claude budget warning: ${daily_spent:.2f} / ${self.daily_budget}"
            )

        if daily_spent > self.daily_budget:
            logger.error(
                f"Claude budget exceeded: ${daily_spent:.2f} / ${self.daily_budget}"
            )
            # Could pause non-critical operations here

    def get_daily_spend(self) -> float:
        """Get total Claude spending for today"""
        today = datetime.now().date()
        return sum(
            usage.cost for usage in self.usage_log if usage.timestamp.date() == today
        )

    def get_session_context(self, session_id: str) -> dict:
        """Retrieve session context for memory continuity"""
        try:
            if os.path.exists(self.session_memory_file):
                with open(self.session_memory_file) as f:
                    sessions = json.load(f)
                return sessions.get(session_id, {})
        except Exception as e:
            logger.error(f"Error loading session context: {e}")
        return {}

    def save_session_context(self, session_id: str, context: dict):
        """Save session context for future use"""
        try:
            sessions = {}
            if os.path.exists(self.session_memory_file):
                with open(self.session_memory_file) as f:
                    sessions = json.load(f)

            sessions[session_id] = {
                **context,
                "last_updated": datetime.now().isoformat(),
                "token_usage": sum(
                    u.total_tokens for u in self.usage_log if u.session_id == session_id
                ),
            }

            os.makedirs(os.path.dirname(self.session_memory_file), exist_ok=True)
            with open(self.session_memory_file, "w") as f:
                json.dump(sessions, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving session context: {e}")

    def optimize_prompt_length(self, prompt: str, max_tokens: int = 4000) -> str:
        """Optimize prompt length to reduce token usage"""
        # Simple token estimation (roughly 4 chars per token)
        estimated_tokens = len(prompt) // 4

        if estimated_tokens <= max_tokens:
            return prompt

        # Truncate while preserving important parts
        lines = prompt.split("\n")
        optimized_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = len(line) // 4
            if current_tokens + line_tokens <= max_tokens:
                optimized_lines.append(line)
                current_tokens += line_tokens
            else:
                break

        optimized_prompt = "\n".join(optimized_lines)
        logger.info(f"Prompt optimized: {estimated_tokens} → {current_tokens} tokens")

        return optimized_prompt

    def get_usage_analytics(self, days: int = 7) -> dict:
        """Get usage analytics for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_usage = [u for u in self.usage_log if u.timestamp >= cutoff_date]

        if not recent_usage:
            return {"error": "No usage data available"}

        total_cost = sum(u.cost for u in recent_usage)
        total_tokens = sum(u.total_tokens for u in recent_usage)

        # Usage by model
        model_breakdown = {}
        for usage in recent_usage:
            if usage.model not in model_breakdown:
                model_breakdown[usage.model] = {"tokens": 0, "cost": 0, "requests": 0}
            model_breakdown[usage.model]["tokens"] += usage.total_tokens
            model_breakdown[usage.model]["cost"] += usage.cost
            model_breakdown[usage.model]["requests"] += 1

        # Usage by task type
        task_breakdown = {}
        for usage in recent_usage:
            if usage.task_type not in task_breakdown:
                task_breakdown[usage.task_type] = {
                    "tokens": 0,
                    "cost": 0,
                    "requests": 0,
                }
            task_breakdown[usage.task_type]["tokens"] += usage.total_tokens
            task_breakdown[usage.task_type]["cost"] += usage.cost
            task_breakdown[usage.task_type]["requests"] += 1

        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_requests": len(recent_usage),
            "avg_cost_per_request": total_cost / len(recent_usage),
            "avg_tokens_per_request": total_tokens / len(recent_usage),
            "model_breakdown": model_breakdown,
            "task_breakdown": task_breakdown,
            "daily_average": total_cost / days,
            "monthly_projection": (total_cost / days) * 30,
        }

    def get_optimization_recommendations(self) -> list[str]:
        """Get recommendations for reducing token usage"""
        analytics = self.get_usage_analytics()
        recommendations = []

        if analytics.get("avg_tokens_per_request", 0) > 5000:
            recommendations.append(
                "Consider breaking large prompts into smaller chunks"
            )

        if analytics.get("monthly_projection", 0) > 100:
            recommendations.append(
                "Switch to Claude 4 Sonnet for routine tasks (5x cheaper)"
            )

        # Check for high-usage task types
        task_breakdown = analytics.get("task_breakdown", {})
        high_usage_tasks = [
            task
            for task, data in task_breakdown.items()
            if data["cost"] > analytics["total_cost"] * 0.3
        ]

        if high_usage_tasks:
            recommendations.append(
                f"Optimize high-cost tasks: {', '.join(high_usage_tasks)}"
            )

        if analytics.get("daily_average", 0) > self.daily_budget:
            recommendations.append(
                f"Daily usage exceeds budget by ${analytics['daily_average'] - self.daily_budget:.2f}"
            )

        return recommendations

    def export_usage_report(self, filepath: str):
        """Export detailed usage report"""
        analytics = self.get_usage_analytics(30)  # Last 30 days
        recommendations = self.get_optimization_recommendations()

        report = {
            "generated_at": datetime.now().isoformat(),
            "claude_usage_summary": analytics,
            "optimization_recommendations": recommendations,
            "budget_status": {
                "daily_budget": self.daily_budget,
                "daily_average": analytics.get("daily_average", 0),
                "monthly_projection": analytics.get("monthly_projection", 0),
                "budget_utilization": (
                    analytics.get("daily_average", 0) / self.daily_budget
                )
                * 100,
            },
            "detailed_usage": [
                {
                    "timestamp": usage.timestamp.isoformat(),
                    "model": usage.model,
                    "tokens": usage.total_tokens,
                    "cost": usage.cost,
                    "task_type": usage.task_type,
                }
                for usage in self.usage_log[-100:]  # Last 100 requests
            ],
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Claude usage report exported to {filepath}")


# Decorator for automatic token tracking
def track_claude_usage(model: str, task_type: str, session_id: str = "default"):
    """Decorator to automatically track Claude API usage"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = ClaudeTokenMonitor()

            # Execute function and capture usage
            result = func(*args, **kwargs)

            # Extract token usage from result (implementation depends on Claude client)
            if hasattr(result, "usage"):
                monitor.track_usage(
                    model=model,
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                    session_id=session_id,
                    task_type=task_type,
                )

            return result

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage
    monitor = ClaudeTokenMonitor()

    # Simulate some usage
    monitor.track_usage(
        "claude-4-sonnet", 1000, 500, "test_session", "financial_analysis"
    )
    monitor.track_usage("claude-4-opus", 2000, 1000, "test_session", "code_generation")

    # Get analytics
    analytics = monitor.get_usage_analytics()
    print(f"Total cost last 7 days: ${analytics['total_cost']:.4f}")

    # Get recommendations
    recommendations = monitor.get_optimization_recommendations()
    for rec in recommendations:
        print(f"💡 {rec}")
