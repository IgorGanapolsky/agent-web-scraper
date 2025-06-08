"""
BMAD AI Framework Integration for Dynamic Model Orchestration
Routes tasks to Claude Opus 4 or Sonnet 4 based on complexity analysis.
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from app.config.logging import get_logger

logger = get_logger(__name__)


class ModelType(Enum):
    """Available Claude models"""

    OPUS_4 = "claude-opus-4"
    SONNET_4 = "claude-sonnet-4"
    HAIKU_3 = "claude-haiku-3"


class TaskComplexity(Enum):
    """Task complexity levels"""

    SIMPLE = "simple"  # Facts, basic queries
    MODERATE = "moderate"  # Analysis, summaries
    COMPLEX = "complex"  # Strategic thinking, deep reasoning
    ENTERPRISE = "enterprise"  # Multi-step business decisions


@dataclass
class TaskProfile:
    """Profile of a task for model selection"""

    content_length: int
    reasoning_depth: str
    domain_complexity: str
    time_sensitivity: str
    business_impact: str
    required_accuracy: float
    cost_sensitivity: str


@dataclass
class ModelCapability:
    """Capability profile of a Claude model"""

    model_type: ModelType
    cost_per_token: float
    max_tokens: int
    reasoning_strength: float
    speed_rating: float
    accuracy_rating: float
    best_use_cases: list[str]


class BMADAIOrchestrator:
    """
    Business-oriented AI framework for dynamic model orchestration.

    BMAD (Business Model AI Decision) Framework Features:
    - Automatic task complexity analysis
    - Dynamic model routing (Opus 4 vs Sonnet 4)
    - Cost optimization and budget management
    - Performance monitoring and learning
    - Enterprise decision support
    """

    def __init__(self, cost_budget: float = 100.0):
        self.cost_budget = cost_budget
        self.daily_spending = 0.0
        self.model_performance_stats = {}
        self.routing_history = []

        # Model configurations
        self.model_configs = {
            ModelType.OPUS_4: ModelCapability(
                model_type=ModelType.OPUS_4,
                cost_per_token=0.000075,  # $75 per million tokens
                max_tokens=200000,
                reasoning_strength=0.95,
                speed_rating=0.7,
                accuracy_rating=0.98,
                best_use_cases=[
                    "strategic_planning",
                    "complex_analysis",
                    "enterprise_decisions",
                    "technical_architecture",
                    "financial_modeling",
                ],
            ),
            ModelType.SONNET_4: ModelCapability(
                model_type=ModelType.SONNET_4,
                cost_per_token=0.000015,  # $15 per million tokens
                max_tokens=200000,
                reasoning_strength=0.85,
                speed_rating=0.9,
                accuracy_rating=0.92,
                best_use_cases=[
                    "code_generation",
                    "content_creation",
                    "data_analysis",
                    "quick_insights",
                    "operational_tasks",
                ],
            ),
            ModelType.HAIKU_3: ModelCapability(
                model_type=ModelType.HAIKU_3,
                cost_per_token=0.0000003,  # $0.25 per million tokens
                max_tokens=200000,
                reasoning_strength=0.7,
                speed_rating=0.95,
                accuracy_rating=0.85,
                best_use_cases=[
                    "simple_queries",
                    "basic_formatting",
                    "data_extraction",
                    "quick_responses",
                ],
            ),
        }

    def analyze_task_complexity(
        self, prompt: str, context: dict[str, Any] | None = None
    ) -> TaskProfile:
        """
        Analyze task complexity to determine optimal model routing.

        Args:
            prompt: The task prompt to analyze
            context: Additional context about the task

        Returns:
            TaskProfile with complexity analysis
        """
        context = context or {}

        # Analyze content length
        content_length = len(prompt.split())

        # Analyze reasoning requirements
        reasoning_indicators = [
            "strategy",
            "plan",
            "analyze",
            "evaluate",
            "decide",
            "recommend",
            "optimize",
            "design",
            "architecture",
            "framework",
            "model",
            "business case",
            "roi",
            "investment",
            "forecast",
            "projection",
        ]

        reasoning_depth = "simple"
        reasoning_score = sum(
            1 for indicator in reasoning_indicators if indicator in prompt.lower()
        )

        if reasoning_score >= 5:
            reasoning_depth = "complex"
        elif reasoning_score >= 2:
            reasoning_depth = "moderate"

        # Analyze domain complexity
        enterprise_domains = [
            "enterprise",
            "saas",
            "revenue",
            "business",
            "strategic",
            "financial",
            "investment",
            "market",
            "competitive",
            "growth",
        ]

        domain_complexity = "basic"
        domain_score = sum(
            1 for domain in enterprise_domains if domain in prompt.lower()
        )

        if domain_score >= 3:
            domain_complexity = "enterprise"
        elif domain_score >= 1:
            domain_complexity = "business"

        # Analyze time sensitivity
        urgency_indicators = ["urgent", "immediate", "asap", "quick", "fast", "now"]
        time_sensitivity = "normal"
        if any(indicator in prompt.lower() for indicator in urgency_indicators):
            time_sensitivity = "urgent"

        # Analyze business impact
        impact_indicators = [
            "revenue",
            "customer",
            "critical",
            "mission",
            "enterprise",
            "strategic",
        ]
        business_impact = "low"
        impact_score = sum(
            1 for indicator in impact_indicators if indicator in prompt.lower()
        )

        if impact_score >= 3:
            business_impact = "high"
        elif impact_score >= 1:
            business_impact = "medium"

        # Determine required accuracy
        accuracy_indicators = ["accurate", "precise", "exact", "critical", "important"]
        required_accuracy = 0.85  # Default
        if any(indicator in prompt.lower() for indicator in accuracy_indicators):
            required_accuracy = 0.95

        # Cost sensitivity
        cost_sensitivity = "medium"
        if self.daily_spending > self.cost_budget * 0.8:
            cost_sensitivity = "high"
        elif self.daily_spending < self.cost_budget * 0.2:
            cost_sensitivity = "low"

        return TaskProfile(
            content_length=content_length,
            reasoning_depth=reasoning_depth,
            domain_complexity=domain_complexity,
            time_sensitivity=time_sensitivity,
            business_impact=business_impact,
            required_accuracy=required_accuracy,
            cost_sensitivity=cost_sensitivity,
        )

    def select_optimal_model(
        self, task_profile: TaskProfile, context: dict[str, Any] | None = None
    ) -> ModelType:
        """
        Select the optimal Claude model based on task profile and BMAD analysis.

        Business logic:
        - Opus 4: Complex strategic decisions, high business impact
        - Sonnet 4: Standard business operations, balanced performance
        - Haiku 3: Simple tasks, cost optimization
        """
        context = context or {}

        # Score each model for this task
        model_scores = {}

        for model_type, capability in self.model_configs.items():
            score = 0.0

            # Reasoning requirement scoring
            if task_profile.reasoning_depth == "complex":
                score += capability.reasoning_strength * 0.4
            elif task_profile.reasoning_depth == "moderate":
                score += capability.reasoning_strength * 0.3
            else:
                score += capability.speed_rating * 0.3

            # Domain complexity scoring
            if task_profile.domain_complexity == "enterprise":
                score += capability.reasoning_strength * 0.3
                score += capability.accuracy_rating * 0.2
            elif task_profile.domain_complexity == "business":
                score += capability.reasoning_strength * 0.2
                score += capability.accuracy_rating * 0.15

            # Time sensitivity scoring
            if task_profile.time_sensitivity == "urgent":
                score += capability.speed_rating * 0.3
            else:
                score += capability.accuracy_rating * 0.2

            # Business impact scoring
            if task_profile.business_impact == "high":
                score += capability.accuracy_rating * 0.4
                score += capability.reasoning_strength * 0.3
            elif task_profile.business_impact == "medium":
                score += capability.accuracy_rating * 0.2

            # Cost sensitivity adjustment
            if task_profile.cost_sensitivity == "high":
                # Penalize expensive models
                cost_penalty = capability.cost_per_token * 10000  # Normalize cost
                score -= cost_penalty * 0.3
            elif task_profile.cost_sensitivity == "low":
                # Reward accuracy for low cost sensitivity
                score += capability.accuracy_rating * 0.1

            # Required accuracy threshold
            if capability.accuracy_rating < task_profile.required_accuracy:
                score *= 0.5  # Significant penalty for insufficient accuracy

            model_scores[model_type] = score

        # Select model with highest score
        selected_model = max(model_scores.items(), key=lambda x: x[1])[0]

        # Business rules override
        # CEO-level strategic queries always use Opus 4
        if any(
            term in context.get("role", "").lower()
            for term in ["ceo", "cto", "strategic"]
        ):
            selected_model = ModelType.OPUS_4

        # High-revenue activities use Opus 4
        if context.get("revenue_impact", 0) > 10000:
            selected_model = ModelType.OPUS_4

        # Budget protection - force cheaper model if near budget limit
        if self.daily_spending > self.cost_budget * 0.9:
            if selected_model == ModelType.OPUS_4:
                selected_model = ModelType.SONNET_4
                logger.warning("Downgraded to Sonnet 4 due to budget constraints")

        return selected_model

    async def route_task(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
        force_model: Optional[ModelType] = None,
    ) -> dict[str, Any]:
        """
        Route a task to the optimal Claude model using BMAD framework.

        Args:
            prompt: The task prompt
            context: Additional context for routing decision
            force_model: Override automatic model selection

        Returns:
            Task routing result with model selection and reasoning
        """
        time.time()
        context = context or {}

        # Analyze task if no model is forced
        if force_model is None:
            task_profile = self.analyze_task_complexity(prompt, context)
            selected_model = self.select_optimal_model(task_profile, context)
        else:
            selected_model = force_model
            task_profile = None

        # Calculate estimated cost
        estimated_tokens = len(prompt.split()) * 1.3  # Rough estimation
        estimated_cost = (
            estimated_tokens * self.model_configs[selected_model].cost_per_token
        )

        # Execute task (mock implementation)
        execution_result = await self._execute_with_model(
            prompt, selected_model, context
        )

        # Update spending tracking
        actual_cost = execution_result.get("cost", estimated_cost)
        self.daily_spending += actual_cost

        # Record routing decision
        routing_record = {
            "timestamp": time.time(),
            "prompt_length": len(prompt),
            "selected_model": selected_model.value,
            "task_profile": task_profile.__dict__ if task_profile else None,
            "estimated_cost": estimated_cost,
            "actual_cost": actual_cost,
            "execution_time": execution_result.get("execution_time", 0),
            "context": context,
        }

        self.routing_history.append(routing_record)

        # Update performance stats
        if selected_model.value not in self.model_performance_stats:
            self.model_performance_stats[selected_model.value] = {
                "total_tasks": 0,
                "total_cost": 0.0,
                "avg_execution_time": 0.0,
                "success_rate": 0.0,
            }

        stats = self.model_performance_stats[selected_model.value]
        stats["total_tasks"] += 1
        stats["total_cost"] += actual_cost
        stats["avg_execution_time"] = (
            stats["avg_execution_time"] * (stats["total_tasks"] - 1)
            + execution_result.get("execution_time", 0)
        ) / stats["total_tasks"]

        return {
            "success": True,
            "selected_model": selected_model.value,
            "routing_reasoning": self._explain_routing_decision(
                task_profile, selected_model, context
            ),
            "estimated_cost": estimated_cost,
            "actual_cost": actual_cost,
            "result": execution_result.get("result", "Task completed"),
            "performance_metrics": {
                "execution_time": execution_result.get("execution_time", 0),
                "token_usage": execution_result.get("token_usage", {}),
                "model_efficiency": execution_result.get("efficiency_score", 0.85),
            },
            "budget_status": {
                "daily_spending": self.daily_spending,
                "budget_remaining": self.cost_budget - self.daily_spending,
                "budget_utilization": self.daily_spending / self.cost_budget,
            },
        }

    async def _execute_with_model(
        self, prompt: str, model: ModelType, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute task with selected model (mock implementation).
        In production, this would call the actual Anthropic API.
        """
        capability = self.model_configs[model]

        # Simulate execution time based on model speed
        base_time = len(prompt.split()) * 0.01  # Base processing time
        model_speed_factor = 1.0 / capability.speed_rating
        execution_time = base_time * model_speed_factor

        await asyncio.sleep(min(execution_time, 0.5))  # Cap simulation time

        # Simulate token usage
        input_tokens = len(prompt.split())
        output_tokens = int(input_tokens * 0.7)  # Rough estimation
        total_tokens = input_tokens + output_tokens

        cost = total_tokens * capability.cost_per_token

        return {
            "result": f"Enterprise response generated by {model.value}",
            "execution_time": execution_time,
            "cost": cost,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
            "efficiency_score": capability.reasoning_strength * capability.speed_rating,
        }

    def _explain_routing_decision(
        self,
        task_profile: Optional[TaskProfile],
        selected_model: ModelType,
        context: dict[str, Any],
    ) -> str:
        """Generate human-readable explanation of routing decision"""
        if task_profile is None:
            return f"Model {selected_model.value} was manually selected"

        self.model_configs[selected_model]

        reasons = []

        # Reasoning depth
        if task_profile.reasoning_depth == "complex":
            reasons.append(
                f"Complex reasoning required (selected {selected_model.value} for high reasoning strength)"
            )
        elif task_profile.reasoning_depth == "simple":
            reasons.append(
                f"Simple task (optimized for speed with {selected_model.value})"
            )

        # Business impact
        if task_profile.business_impact == "high":
            reasons.append("High business impact requires maximum accuracy")
        elif task_profile.business_impact == "low":
            reasons.append("Low business impact allows cost optimization")

        # Time sensitivity
        if task_profile.time_sensitivity == "urgent":
            reasons.append("Urgent request prioritizes speed")

        # Cost considerations
        if task_profile.cost_sensitivity == "high":
            reasons.append("Budget constraints favor cost-effective model")

        # Domain complexity
        if task_profile.domain_complexity == "enterprise":
            reasons.append("Enterprise domain requires sophisticated reasoning")

        return f"Selected {selected_model.value}: " + "; ".join(reasons)

    def get_performance_analytics(self) -> dict[str, Any]:
        """Get comprehensive performance analytics"""
        return {
            "budget_status": {
                "daily_spending": self.daily_spending,
                "budget_remaining": self.cost_budget - self.daily_spending,
                "utilization_percentage": (self.daily_spending / self.cost_budget)
                * 100,
            },
            "model_performance": self.model_performance_stats,
            "routing_efficiency": {
                "total_tasks": len(self.routing_history),
                "avg_cost_per_task": (
                    sum(r["actual_cost"] for r in self.routing_history)
                    / len(self.routing_history)
                    if self.routing_history
                    else 0
                ),
                "model_distribution": self._calculate_model_distribution(),
            },
            "optimization_opportunities": self._identify_optimization_opportunities(),
        }

    def _calculate_model_distribution(self) -> dict[str, float]:
        """Calculate how tasks are distributed across models"""
        if not self.routing_history:
            return {}

        total_tasks = len(self.routing_history)
        distribution = {}

        for record in self.routing_history:
            model = record["selected_model"]
            distribution[model] = distribution.get(model, 0) + 1

        # Convert to percentages
        return {
            model: (count / total_tasks) * 100 for model, count in distribution.items()
        }

    def _identify_optimization_opportunities(self) -> list[str]:
        """Identify potential cost and performance optimizations"""
        opportunities = []

        if self.daily_spending > self.cost_budget * 0.8:
            opportunities.append("Consider using Sonnet 4 for more routine tasks")

        opus_usage = sum(
            1
            for r in self.routing_history
            if r["selected_model"] == ModelType.OPUS_4.value
        )
        if opus_usage > len(self.routing_history) * 0.3:
            opportunities.append(
                "High Opus 4 usage - review task complexity requirements"
            )

        if self.daily_spending < self.cost_budget * 0.3:
            opportunities.append(
                "Budget underutilized - consider upgrading model selection for better accuracy"
            )

        return opportunities


# Global orchestrator instance
_bmad_orchestrator = None


def get_bmad_orchestrator(cost_budget: float = 100.0) -> BMADAIOrchestrator:
    """Get the global BMAD AI orchestrator instance"""
    global _bmad_orchestrator
    if _bmad_orchestrator is None:
        _bmad_orchestrator = BMADAIOrchestrator(cost_budget=cost_budget)
    return _bmad_orchestrator


# Convenience functions for common enterprise scenarios
async def route_ceo_query(query: str) -> dict[str, Any]:
    """Route CEO-level strategic query (always uses Opus 4)"""
    orchestrator = get_bmad_orchestrator()
    return await orchestrator.route_task(
        query,
        context={"role": "CEO", "business_impact": "high", "revenue_impact": 50000},
    )


async def route_operational_task(task: str) -> dict[str, Any]:
    """Route operational task (optimized for speed and cost)"""
    orchestrator = get_bmad_orchestrator()
    return await orchestrator.route_task(
        task, context={"role": "operations", "time_sensitivity": "urgent"}
    )


async def route_enterprise_analysis(analysis_request: str) -> dict[str, Any]:
    """Route enterprise analysis (balanced approach)"""
    orchestrator = get_bmad_orchestrator()
    return await orchestrator.route_task(
        analysis_request, context={"domain": "enterprise", "accuracy_required": True}
    )
