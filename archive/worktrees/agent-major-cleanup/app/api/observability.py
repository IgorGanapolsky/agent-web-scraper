"""
Observability API endpoints for Control Tower dashboard
"""

from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.config.logging import get_logger
from app.observability.langsmith_config import get_observability_manager

logger = get_logger(__name__)
router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/llm/daily-summary")
async def get_daily_llm_summary(date: Optional[str] = Query(None)) -> dict[str, Any]:
    """
    Get daily LLM usage summary for cost tracking
    """
    manager = get_observability_manager()
    return manager.get_daily_summary(date)


@router.get("/llm/agent-performance")
async def get_agent_performance() -> dict[str, Any]:
    """
    Get per-agent LLM performance metrics
    """
    manager = get_observability_manager()
    return manager.get_agent_performance()


@router.get("/llm/cost-breakdown")
async def get_cost_breakdown(days: int = Query(7)) -> dict[str, Any]:
    """
    Get cost breakdown over the last N days
    """
    manager = get_observability_manager()

    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days - 1)

    daily_costs = []
    total_cost = 0
    total_calls = 0

    # Collect daily summaries
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.isoformat()
        summary = manager.get_daily_summary(date_str)
        daily_costs.append(summary)
        total_cost += summary["total_cost"]
        total_calls += summary["total_calls"]
        current_date += timedelta(days=1)

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
        },
        "totals": {
            "total_cost": total_cost,
            "total_calls": total_calls,
            "average_cost_per_day": total_cost / days,
            "average_calls_per_day": total_calls / days,
        },
        "daily_breakdown": daily_costs,
        "cost_trends": {
            "yesterday_cost": (
                daily_costs[-2]["total_cost"] if len(daily_costs) > 1 else 0
            ),
            "today_cost": daily_costs[-1]["total_cost"],
            "trend": (
                "increasing"
                if len(daily_costs) > 1
                and daily_costs[-1]["total_cost"] > daily_costs[-2]["total_cost"]
                else "stable"
            ),
        },
    }


@router.get("/llm/efficiency-metrics")
async def get_efficiency_metrics() -> dict[str, Any]:
    """
    Get LLM efficiency and optimization recommendations
    """
    manager = get_observability_manager()

    # Get current performance
    today_summary = manager.get_daily_summary()
    agent_performance = manager.get_agent_performance()

    # Calculate efficiency insights
    recommendations = []

    if today_summary["cost_per_call"] > 0.01:  # $0.01 per call threshold
        recommendations.append(
            {
                "type": "cost_optimization",
                "priority": "high",
                "message": "High cost per call detected. Consider using Haiku for simpler tasks.",
                "estimated_savings": (today_summary["cost_per_call"] - 0.005)
                * today_summary["total_calls"],
            }
        )

    if today_summary["average_call_time"] > 30:  # 30 second threshold
        recommendations.append(
            {
                "type": "performance_optimization",
                "priority": "medium",
                "message": "Slow LLM response times detected. Review prompt complexity.",
                "current_avg_time": today_summary["average_call_time"],
            }
        )

    # Check agent efficiency
    for agent, stats in agent_performance.items():
        if stats["success_rate"] < 0.9:  # 90% success rate threshold
            recommendations.append(
                {
                    "type": "reliability_improvement",
                    "priority": "high",
                    "message": f"Agent {agent} has low success rate ({stats['success_rate']:.1%})",
                    "agent": agent,
                    "success_rate": stats["success_rate"],
                }
            )

    return {
        "current_efficiency": {
            "efficiency_score": today_summary["efficiency_score"],
            "cost_per_call": today_summary["cost_per_call"],
            "average_response_time": today_summary["average_call_time"],
        },
        "agent_rankings": sorted(
            [{"agent": agent, **stats} for agent, stats in agent_performance.items()],
            key=lambda x: x["avg_cost_per_call"],
        ),
        "recommendations": recommendations,
        "optimization_potential": {
            "daily_savings_possible": sum(
                r.get("estimated_savings", 0) for r in recommendations
            ),
            "performance_improvement_possible": any(
                r["type"] == "performance_optimization" for r in recommendations
            ),
        },
    }


@router.get("/system/health")
async def get_system_health() -> dict[str, Any]:
    """
    Overall system health combining LLM and infrastructure metrics
    """
    manager = get_observability_manager()

    # LLM health
    today_summary = manager.get_daily_summary()
    agent_performance = manager.get_agent_performance()

    # Calculate health scores
    llm_health_score = min(today_summary["efficiency_score"], 100)

    agent_health_scores = {
        agent: stats["success_rate"] * 100 for agent, stats in agent_performance.items()
    }

    overall_health = (
        llm_health_score
        + (sum(agent_health_scores.values()) / max(len(agent_health_scores), 1))
    ) / 2

    return {
        "overall_health_score": overall_health,
        "status": (
            "healthy"
            if overall_health > 80
            else "warning" if overall_health > 60 else "critical"
        ),
        "components": {
            "llm_efficiency": {
                "score": llm_health_score,
                "status": "healthy" if llm_health_score > 80 else "warning",
            },
            "agent_performance": {
                "scores": agent_health_scores,
                "average": sum(agent_health_scores.values())
                / max(len(agent_health_scores), 1),
                "status": (
                    "healthy"
                    if all(score > 80 for score in agent_health_scores.values())
                    else "warning"
                ),
            },
        },
        "metrics": {
            "daily_calls": today_summary["total_calls"],
            "daily_cost": today_summary["total_cost"],
            "active_agents": len(agent_performance),
        },
        "last_updated": datetime.now().isoformat(),
    }
