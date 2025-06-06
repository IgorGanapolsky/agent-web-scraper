#!/usr/bin/env python3
"""
Claude Squad Orchestrator - Multi-Role AI Team for Business Automation
Implements the CEO/CTO/CMO/CFO parallel execution pattern with error handling
"""

import asyncio
import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import aiohttp
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.session_memory import get_session_memory

logger = get_logger(__name__)


class ClaudeModel(Enum):
    """Available Claude models"""

    OPUS_4 = "claude-opus-4"  # Complex tasks: $15/$75 per million tokens
    SONNET_4 = "claude-sonnet-4"  # Routine tasks: $3/$15 per million tokens
    HAIKU_4 = "claude-haiku-4"  # Simple tasks: $0.25/$1.25 per million tokens


class TaskComplexity(Enum):
    """Task complexity levels for model selection"""

    SIMPLE = "simple"  # Haiku 4
    ROUTINE = "routine"  # Sonnet 4
    COMPLEX = "complex"  # Opus 4


class BusinessRole(Enum):
    """Business roles for task assignment"""

    CEO = "ceo"  # Strategic planning, synthesis
    CTO = "cto"  # Technical implementation, architecture
    CMO = "cmo"  # Marketing, content, growth
    CFO = "cfo"  # Financial analysis, metrics, forecasting


class ClaudeTask(BaseModel):
    """Individual task for Claude execution"""

    id: str
    role: BusinessRole
    complexity: TaskComplexity
    title: str
    description: str
    context: dict = {}
    dependencies: list[str] = []
    priority: int = 1  # 1=high, 2=medium, 3=low
    timeout_seconds: int = 300
    retry_count: int = 3
    model_override: Optional[ClaudeModel] = None


class TaskResult(BaseModel):
    """Result from task execution"""

    task_id: str
    role: BusinessRole
    status: str  # success, error, timeout, retry
    result: Union[dict, str, None] = None
    error: Optional[str] = None
    execution_time_seconds: float = 0
    tokens_used: dict = {}
    cost: float = 0
    timestamp: datetime
    retry_attempt: int = 0


class ClaudeSquadOrchestrator:
    """Orchestrate parallel Claude executions across business roles"""

    def __init__(self):
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_api_url = "https://api.anthropic.com/v1/messages"
        self.memory = get_session_memory()

        # Cost tracking per model (per million tokens)
        self.model_costs = {
            ClaudeModel.OPUS_4: {"input": 15.0, "output": 75.0},
            ClaudeModel.SONNET_4: {"input": 3.0, "output": 15.0},
            ClaudeModel.HAIKU_4: {"input": 0.25, "output": 1.25},
        }

        # Model selection based on complexity
        self.complexity_to_model = {
            TaskComplexity.SIMPLE: ClaudeModel.HAIKU_4,
            TaskComplexity.ROUTINE: ClaudeModel.SONNET_4,
            TaskComplexity.COMPLEX: ClaudeModel.OPUS_4,
        }

        logger.info("Claude Squad Orchestrator initialized")

    def create_business_automation_tasks(self) -> list[ClaudeTask]:
        """Create the standard business automation task suite"""

        business_context = self.memory.get_business_context()

        tasks = [
            # CEO: Strategic Synthesis
            ClaudeTask(
                id="ceo_strategic_plan",
                role=BusinessRole.CEO,
                complexity=TaskComplexity.COMPLEX,
                title="Generate Strategic Business Plan",
                description="Synthesize market data, financial projections, and technical capabilities into actionable strategic plan for reaching $300/day revenue target",
                context={
                    "current_revenue": business_context["current_daily_revenue"],
                    "target_revenue": business_context["target_daily_revenue"],
                    "monthly_costs": business_context["monthly_costs"],
                    "pricing_tiers": business_context["pricing_tiers"],
                },
                dependencies=[
                    "cto_api_development",
                    "cmo_market_analysis",
                    "cfo_financial_model",
                ],
                priority=1,
            ),
            # CTO: Technical Implementation
            ClaudeTask(
                id="cto_api_development",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.COMPLEX,
                title="Generate API Endpoints and Integration Code",
                description="Create FastAPI endpoints for SaaS platform, integrate with Stripe, implement authentication, set up Dagger CI/CD pipeline",
                context={
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "deployment": "Dagger CI/CD",
                    "payment_processor": "Stripe",
                    "required_endpoints": [
                        "auth",
                        "subscriptions",
                        "analytics",
                        "webhooks",
                    ],
                },
                priority=1,
            ),
            # CMO: Market Research & Content
            ClaudeTask(
                id="cmo_market_analysis",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="Comprehensive Market Analysis & Content Strategy",
                description="Use SerpAPI for market research, analyze competitor landscape, create content calendar, design customer acquisition campaigns",
                context={
                    "target_industries": ["SaaS", "FinTech", "HealthTech", "EdTech"],
                    "content_types": [
                        "blog_posts",
                        "case_studies",
                        "whitepapers",
                        "social_media",
                    ],
                    "campaign_budget": 5000,
                    "target_customer_acquisition_cost": 50,
                },
                priority=1,
            ),
            # CFO: Financial Analysis
            ClaudeTask(
                id="cfo_financial_model",
                role=BusinessRole.CFO,
                complexity=TaskComplexity.ROUTINE,
                title="Build Financial Model & Revenue Projections",
                description="Create comprehensive financial model, calculate unit economics, project revenue scenarios, optimize pricing strategy",
                context={
                    "current_mrr": 0,
                    "target_mrr": 9000,  # $300/day * 30 days
                    "pricing_tiers": business_context["pricing_tiers"],
                    "conversion_rates": business_context["conversion_rates"],
                    "customer_acquisition_cost": business_context[
                        "customer_acquisition_cost"
                    ],
                },
                priority=1,
            ),
            # Additional parallel tasks
            ClaudeTask(
                id="cmo_serpapi_research",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.SIMPLE,
                title="SerpAPI Market Data Collection",
                description="Collect real-time market data using SerpAPI for trending keywords, competitor analysis, and opportunity identification",
                context={
                    "keywords": [
                        "SaaS growth",
                        "market intelligence",
                        "business automation",
                    ],
                    "competitor_domains": [
                        "builtwith.com",
                        "similarweb.com",
                        "ahrefs.com",
                    ],
                },
                priority=2,
            ),
            ClaudeTask(
                id="cto_dagger_pipeline",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.ROUTINE,
                title="Implement Dagger CI/CD Pipeline",
                description="Set up automated testing, deployment, and monitoring pipeline using Dagger",
                context={
                    "test_frameworks": ["pytest", "jest"],
                    "deployment_target": "production",
                    "monitoring_tools": ["Sentry", "DataDog"],
                },
                dependencies=["cto_api_development"],
                priority=2,
            ),
        ]

        return tasks

    async def execute_tasks_parallel(
        self, tasks: list[ClaudeTask]
    ) -> dict[str, TaskResult]:
        """Execute tasks in parallel with dependency management and error handling"""

        start_time = datetime.now()
        results = {}

        # Organize tasks by priority and dependencies
        task_queue = self._organize_task_execution_order(tasks)

        logger.info(
            f"Executing {len(tasks)} tasks across {len(task_queue)} execution waves"
        )

        # Execute tasks in waves (respecting dependencies)
        for wave_index, wave_tasks in enumerate(task_queue):
            logger.info(f"Executing wave {wave_index + 1}: {len(wave_tasks)} tasks")

            # Execute all tasks in this wave concurrently
            wave_results = await asyncio.gather(
                *[self._execute_single_task(task, results) for task in wave_tasks],
                return_exceptions=True,
            )

            # Process wave results
            for i, result in enumerate(wave_results):
                task = wave_tasks[i]
                if isinstance(result, Exception):
                    logger.error(f"Task {task.id} failed with exception: {result}")
                    results[task.id] = TaskResult(
                        task_id=task.id,
                        role=task.role,
                        status="error",
                        error=str(result),
                        timestamp=datetime.now(),
                    )
                else:
                    results[task.id] = result

        execution_time = (datetime.now() - start_time).total_seconds()

        # Calculate total cost and tokens
        total_cost = sum(r.cost for r in results.values() if r.cost)
        total_tokens = sum(
            r.tokens_used.get("input", 0) + r.tokens_used.get("output", 0)
            for r in results.values()
            if r.tokens_used
        )

        logger.info(f"Parallel execution completed in {execution_time:.2f}s")
        logger.info(f"Total cost: ${total_cost:.2f}, Total tokens: {total_tokens}")

        return {
            "execution_summary": {
                "total_execution_time_seconds": execution_time,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "tasks_completed": len(
                    [r for r in results.values() if r.status == "success"]
                ),
                "tasks_failed": len(
                    [r for r in results.values() if r.status == "error"]
                ),
                "timestamp": datetime.now().isoformat(),
            },
            "task_results": results,
        }

    def _organize_task_execution_order(
        self, tasks: list[ClaudeTask]
    ) -> list[list[ClaudeTask]]:
        """Organize tasks into execution waves based on dependencies"""

        task_map = {task.id: task for task in tasks}
        waves = []
        remaining_tasks = set(task.id for task in tasks)

        while remaining_tasks:
            # Find tasks with no unmet dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                task = task_map[task_id]
                if all(dep not in remaining_tasks for dep in task.dependencies):
                    ready_tasks.append(task)

            if not ready_tasks:
                # Circular dependency or missing dependency
                logger.warning(
                    f"Circular dependency detected. Remaining tasks: {remaining_tasks}"
                )
                # Add remaining tasks to final wave
                ready_tasks = [task_map[tid] for tid in remaining_tasks]

            # Sort by priority
            ready_tasks.sort(key=lambda t: t.priority)
            waves.append(ready_tasks)

            # Remove from remaining
            for task in ready_tasks:
                remaining_tasks.discard(task.id)

        return waves

    async def _execute_single_task(
        self, task: ClaudeTask, completed_results: dict
    ) -> TaskResult:
        """Execute a single task with retry logic and error handling"""

        # Select model
        model = task.model_override or self.complexity_to_model[task.complexity]

        for attempt in range(task.retry_count):
            try:
                start_time = datetime.now()

                # Build context with dependency results
                enhanced_context = task.context.copy()
                for dep_id in task.dependencies:
                    if dep_id in completed_results:
                        dep_result = completed_results[dep_id]
                        if dep_result.status == "success":
                            enhanced_context[f"dependency_{dep_id}"] = dep_result.result

                # Create prompt based on role
                prompt = self._create_role_specific_prompt(task, enhanced_context)

                # Execute Claude API call
                response = await self._call_claude_api(
                    model, prompt, task.timeout_seconds
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                # Calculate cost
                input_tokens = response.get("usage", {}).get("input_tokens", 0)
                output_tokens = response.get("usage", {}).get("output_tokens", 0)
                cost = self._calculate_cost(model, input_tokens, output_tokens)

                # Track token usage
                self.memory.track_token_usage(
                    operation=f"{task.role.value}_{task.id}",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    model=model.value,
                )

                # Parse result
                result_content = response.get("content", [{}])[0].get("text", "")

                # Try to parse as JSON, fall back to text
                try:
                    parsed_result = json.loads(result_content)
                except:
                    parsed_result = result_content

                return TaskResult(
                    task_id=task.id,
                    role=task.role,
                    status="success",
                    result=parsed_result,
                    execution_time_seconds=execution_time,
                    tokens_used={"input": input_tokens, "output": output_tokens},
                    cost=cost,
                    timestamp=datetime.now(),
                    retry_attempt=attempt,
                )

            except asyncio.TimeoutError:
                logger.warning(f"Task {task.id} timed out on attempt {attempt + 1}")
                if attempt == task.retry_count - 1:
                    return TaskResult(
                        task_id=task.id,
                        role=task.role,
                        status="timeout",
                        error=f"Task timed out after {task.retry_count} attempts",
                        timestamp=datetime.now(),
                        retry_attempt=attempt,
                    )
                await asyncio.sleep(2**attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Task {task.id} failed on attempt {attempt + 1}: {e}")
                if attempt == task.retry_count - 1:
                    return TaskResult(
                        task_id=task.id,
                        role=task.role,
                        status="error",
                        error=str(e),
                        timestamp=datetime.now(),
                        retry_attempt=attempt,
                    )
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _create_role_specific_prompt(self, task: ClaudeTask, context: dict) -> str:
        """Create role-specific prompts for different business functions"""

        base_prompt = f"""
You are acting as the {task.role.value.upper()} of a SaaS company.

Task: {task.title}
Description: {task.description}

Context: {json.dumps(context, indent=2)}

Please provide a comprehensive response in JSON format with actionable insights and specific recommendations.
"""

        role_specific_additions = {
            BusinessRole.CEO: """
Focus on:
- Strategic vision and market positioning
- Resource allocation and priority setting
- Synthesis of technical, marketing, and financial insights
- Risk assessment and mitigation strategies
- Growth roadmap and key milestones

Provide JSON with: {"strategy": "", "priorities": [], "risks": [], "milestones": [], "resource_allocation": {}}
""",
            BusinessRole.CTO: """
Focus on:
- Technical architecture and implementation details
- Code examples and API specifications
- Infrastructure and deployment considerations
- Security and scalability requirements
- Integration patterns and best practices

Provide JSON with: {"architecture": "", "apis": [], "security": "", "deployment": "", "code_examples": []}
""",
            BusinessRole.CMO: """
Focus on:
- Market analysis and competitive positioning
- Customer acquisition strategies and channels
- Content and messaging frameworks
- Campaign planning and budget allocation
- Growth metrics and conversion optimization

Provide JSON with: {"market_analysis": "", "acquisition_strategy": "", "content_plan": [], "campaigns": [], "metrics": {}}
""",
            BusinessRole.CFO: """
Focus on:
- Financial modeling and revenue projections
- Unit economics and profitability analysis
- Pricing strategy and optimization
- Cash flow and funding requirements
- ROI analysis and investment priorities

Provide JSON with: {"financial_model": {}, "unit_economics": {}, "pricing": {}, "projections": {}, "recommendations": []}
""",
        }

        return base_prompt + role_specific_additions.get(task.role, "")

    async def _call_claude_api(
        self, model: ClaudeModel, prompt: str, timeout_seconds: int
    ) -> dict:
        """Make API call to Claude with timeout and error handling"""

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model.value,
            "max_tokens": 4000,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout_seconds)
        ) as session:
            async with session.post(
                self.anthropic_api_url, json=payload, headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Claude API error {response.status}: {error_text}")

    def _calculate_cost(
        self, model: ClaudeModel, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate cost based on model and token usage"""
        costs = self.model_costs[model]
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return input_cost + output_cost

    async def run_daily_business_automation(self) -> dict:
        """Run the complete daily business automation sequence"""

        logger.info("🤖 Starting Daily Business Automation with Claude Squad")

        # Create standard business tasks
        tasks = self.create_business_automation_tasks()

        # Execute all tasks in parallel
        results = await self.execute_tasks_parallel(tasks)

        # Store results in memory
        self.memory.store(
            "daily_automation_results",
            results,
            category="business_automation",
            priority=1,
            expires_in_days=7,
        )

        # Generate executive summary
        executive_summary = self._generate_executive_summary(results)

        logger.info("✅ Daily Business Automation completed")

        return {
            "status": "completed",
            "execution_summary": results["execution_summary"],
            "executive_summary": executive_summary,
            "detailed_results": results["task_results"],
            "next_actions": self._extract_next_actions(results["task_results"]),
        }

    def _generate_executive_summary(self, results: dict) -> dict:
        """Generate executive summary from task results"""

        successful_tasks = [
            r for r in results["task_results"].values() if r.status == "success"
        ]

        summary = {
            "total_tasks": len(results["task_results"]),
            "successful_tasks": len(successful_tasks),
            "total_cost": results["execution_summary"]["total_cost"],
            "execution_time": results["execution_summary"][
                "total_execution_time_seconds"
            ],
            "key_insights": [],
            "strategic_recommendations": [],
            "technical_deliverables": [],
            "financial_projections": {},
            "marketing_initiatives": [],
        }

        # Extract insights from each role
        for result in successful_tasks:
            if result.role == BusinessRole.CEO and isinstance(result.result, dict):
                summary["strategic_recommendations"] = result.result.get(
                    "priorities", []
                )
            elif result.role == BusinessRole.CTO and isinstance(result.result, dict):
                summary["technical_deliverables"] = result.result.get("apis", [])
            elif result.role == BusinessRole.CFO and isinstance(result.result, dict):
                summary["financial_projections"] = result.result.get("projections", {})
            elif result.role == BusinessRole.CMO and isinstance(result.result, dict):
                summary["marketing_initiatives"] = result.result.get("campaigns", [])

        return summary

    def _extract_next_actions(self, task_results: dict) -> list[str]:
        """Extract actionable next steps from task results"""

        actions = []

        # Add standard next actions based on results
        successful_results = [r for r in task_results.values() if r.status == "success"]

        if len(successful_results) >= 3:
            actions.append("Implement technical deliverables from CTO analysis")
            actions.append("Launch marketing campaigns identified by CMO")
            actions.append("Execute financial optimization strategies from CFO")
            actions.append("Begin strategic initiatives outlined by CEO")

        if any(r.status == "error" for r in task_results.values()):
            actions.append("Review and retry failed automation tasks")

        # Add cost optimization if needed
        total_cost = sum(r.cost for r in task_results.values() if r.cost)
        if total_cost > 25:  # $25 daily limit
            actions.append("Optimize Claude usage to reduce daily costs")

        return actions


async def main():
    """Demo the Claude Squad Orchestrator"""

    orchestrator = ClaudeSquadOrchestrator()

    print("🤖 Claude Squad Orchestrator Demo")
    print("=" * 50)

    # Run daily business automation
    results = await orchestrator.run_daily_business_automation()

    print("\n📊 Automation Results:")
    print(f"Status: {results['status']}")
    print(
        f"Execution time: {results['execution_summary']['total_execution_time_seconds']:.2f}s"
    )
    print(f"Total cost: ${results['execution_summary']['total_cost']:.2f}")
    print(f"Tasks completed: {results['execution_summary']['tasks_completed']}")

    print("\n🔄 Next Actions:")
    for action in results["next_actions"]:
        print(f"- {action}")


if __name__ == "__main__":
    asyncio.run(main())
