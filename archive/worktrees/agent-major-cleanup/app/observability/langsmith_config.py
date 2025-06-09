"""
LangSmith Configuration for LLM Observability
Control Tower: Development Black Box Instrumentation
"""

import os
import time
from datetime import datetime
from functools import wraps
from typing import Any, Optional

from langchain.callbacks import LangChainTracer
from langsmith import Client

from app.config.logging import get_logger

logger = get_logger(__name__)


class LLMObservabilityManager:
    """
    Central manager for LLM call tracking and cost monitoring
    Eliminates the "Development Black Box"
    """

    def __init__(self):
        self.langsmith_client = None
        self.tracer = None
        self.session_costs = {}
        self.daily_usage = {}

        # Initialize LangSmith if API key available
        if os.getenv("LANGCHAIN_API_KEY"):
            self._setup_langsmith()
        else:
            logger.warning("LANGCHAIN_API_KEY not set - LLM observability disabled")

    def _setup_langsmith(self):
        """Initialize LangSmith client and tracer"""
        try:
            self.langsmith_client = Client(
                api_url=os.getenv(
                    "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
                ),
                api_key=os.getenv("LANGCHAIN_API_KEY"),
            )

            self.tracer = LangChainTracer(
                project_name=os.getenv(
                    "LANGCHAIN_PROJECT", "claude-squad-observability"
                ),
                client=self.langsmith_client,
            )

            logger.info("🔍 LangSmith observability initialized")

        except Exception as e:
            logger.error(f"Failed to initialize LangSmith: {e}")
            self.langsmith_client = None
            self.tracer = None

    def track_llm_call(
        self, model: str, agent_role: str = "unknown", task_type: str = "development"
    ):
        """
        Decorator to track LLM calls with cost and performance metrics
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                # Generate unique call ID
                call_id = f"{agent_role}_{model}_{int(start_time)}"

                # Track call start
                self._log_call_start(call_id, model, agent_role, task_type)

                try:
                    # Execute LLM call
                    result = func(*args, **kwargs)

                    # Calculate execution time
                    execution_time = time.time() - start_time

                    # Track success
                    self._log_call_success(call_id, result, execution_time)

                    return result

                except Exception as e:
                    # Track failure
                    execution_time = time.time() - start_time
                    self._log_call_failure(call_id, str(e), execution_time)
                    raise

            return wrapper

        return decorator

    def _log_call_start(
        self, call_id: str, model: str, agent_role: str, task_type: str
    ):
        """Log LLM call initiation"""
        call_data = {
            "call_id": call_id,
            "model": model,
            "agent_role": agent_role,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
            "status": "started",
        }

        logger.info(f"🤖 LLM Call Started: {call_id} ({agent_role} using {model})")

        # Store in session tracking
        self.session_costs[call_id] = call_data

    def _log_call_success(self, call_id: str, result: Any, execution_time: float):
        """Log successful LLM call with metrics"""
        if call_id in self.session_costs:
            call_data = self.session_costs[call_id]
            call_data.update(
                {
                    "status": "success",
                    "execution_time": execution_time,
                    "tokens_estimated": self._estimate_tokens(result),
                    "cost_estimated": self._estimate_cost(call_data["model"], result),
                    "completed_at": datetime.now().isoformat(),
                }
            )

            # Update daily usage
            today = datetime.now().date().isoformat()
            if today not in self.daily_usage:
                self.daily_usage[today] = {"calls": 0, "total_cost": 0, "total_time": 0}

            self.daily_usage[today]["calls"] += 1
            self.daily_usage[today]["total_cost"] += call_data["cost_estimated"]
            self.daily_usage[today]["total_time"] += execution_time

            logger.info(
                f"✅ LLM Call Success: {call_id} ({execution_time:.2f}s, ~${call_data['cost_estimated']:.4f})"
            )

    def _log_call_failure(self, call_id: str, error: str, execution_time: float):
        """Log failed LLM call"""
        if call_id in self.session_costs:
            call_data = self.session_costs[call_id]
            call_data.update(
                {
                    "status": "failure",
                    "error": error,
                    "execution_time": execution_time,
                    "completed_at": datetime.now().isoformat(),
                }
            )

            logger.error(
                f"❌ LLM Call Failed: {call_id} ({execution_time:.2f}s) - {error}"
            )

    def _estimate_tokens(self, result: Any) -> int:
        """Estimate token usage from result"""
        if isinstance(result, str):
            # Rough estimation: ~4 characters per token
            return len(result) // 4
        elif hasattr(result, "content"):
            return len(str(result.content)) // 4
        return 0

    def _estimate_cost(self, model: str, result: Any) -> float:
        """Estimate cost based on model and token usage"""
        tokens = self._estimate_tokens(result)

        # Cost per token estimates (as of 2025)
        costs = {
            "claude-3-haiku": 0.00000025,  # $0.25 per million tokens
            "claude-3-sonnet": 0.000003,  # $3 per million tokens
            "claude-3-opus": 0.000015,  # $15 per million tokens
            "gpt-4": 0.00003,  # $30 per million tokens
            "gpt-3.5-turbo": 0.0000015,  # $1.5 per million tokens
        }

        return tokens * costs.get(model.lower(), 0.000003)  # Default to Sonnet

    def get_daily_summary(self, date: Optional[str] = None) -> dict[str, Any]:
        """Get daily LLM usage summary"""
        if date is None:
            date = datetime.now().date().isoformat()

        if date not in self.daily_usage:
            return {
                "date": date,
                "total_calls": 0,
                "total_cost": 0.0,
                "total_time": 0.0,
                "average_call_time": 0.0,
                "cost_per_call": 0.0,
            }

        usage = self.daily_usage[date]

        return {
            "date": date,
            "total_calls": usage["calls"],
            "total_cost": usage["total_cost"],
            "total_time": usage["total_time"],
            "average_call_time": usage["total_time"] / max(usage["calls"], 1),
            "cost_per_call": usage["total_cost"] / max(usage["calls"], 1),
            "efficiency_score": self._calculate_efficiency_score(usage),
        }

    def _calculate_efficiency_score(self, usage: dict[str, Any]) -> float:
        """Calculate efficiency score (lower cost + faster = higher score)"""
        if usage["calls"] == 0:
            return 0.0

        avg_cost = usage["total_cost"] / usage["calls"]
        avg_time = usage["total_time"] / usage["calls"]

        # Score: 100 - (cost penalty + time penalty)
        cost_penalty = min(avg_cost * 1000, 50)  # Max 50 points for cost
        time_penalty = min(avg_time, 50)  # Max 50 points for time

        return max(100 - cost_penalty - time_penalty, 0)

    def get_agent_performance(self) -> dict[str, Any]:
        """Get per-agent performance metrics"""
        agent_stats = {}

        for call_data in self.session_costs.values():
            agent = call_data["agent_role"]

            if agent not in agent_stats:
                agent_stats[agent] = {
                    "calls": 0,
                    "total_cost": 0,
                    "total_time": 0,
                    "success_rate": 0,
                    "failures": 0,
                }

            agent_stats[agent]["calls"] += 1
            agent_stats[agent]["total_cost"] += call_data.get("cost_estimated", 0)
            agent_stats[agent]["total_time"] += call_data.get("execution_time", 0)

            if call_data["status"] == "failure":
                agent_stats[agent]["failures"] += 1

        # Calculate success rates
        for agent in agent_stats:
            stats = agent_stats[agent]
            stats["success_rate"] = (stats["calls"] - stats["failures"]) / max(
                stats["calls"], 1
            )
            stats["avg_cost_per_call"] = stats["total_cost"] / max(stats["calls"], 1)
            stats["avg_time_per_call"] = stats["total_time"] / max(stats["calls"], 1)

        return agent_stats


# Global observability manager
_observability_manager = None


def get_observability_manager() -> LLMObservabilityManager:
    """Get the global observability manager instance"""
    global _observability_manager
    if _observability_manager is None:
        _observability_manager = LLMObservabilityManager()
    return _observability_manager


def track_claude_call(agent_role: str = "unknown", task_type: str = "development"):
    """Convenience decorator for tracking Claude API calls"""
    manager = get_observability_manager()
    return manager.track_llm_call("claude-3-sonnet", agent_role, task_type)


def track_gpt_call(
    model: str = "gpt-4", agent_role: str = "unknown", task_type: str = "development"
):
    """Convenience decorator for tracking OpenAI API calls"""
    manager = get_observability_manager()
    return manager.track_llm_call(model, agent_role, task_type)
