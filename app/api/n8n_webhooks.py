#!/usr/bin/env python3
"""
n8n Webhook Endpoints for Claude Code Integration
Handles incoming webhooks from n8n workflows for parallel execution
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.claude_squad_orchestrator import (
    BusinessRole,
    ClaudeSquadOrchestrator,
    ClaudeTask,
    TaskComplexity,
)
from app.core.scraper import WebScraper
from app.core.session_memory import get_session_memory_manager
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)

router = APIRouter(prefix="/n8n", tags=["n8n-webhooks"])


class N8nTaskRequest(BaseModel):
    """n8n task request payload"""

    workflow_id: str
    role: str  # ceo, cto, cmo, cfo
    task_type: str
    context: dict
    priority: int = 1
    timeout_seconds: int = 300
    parallel_execution: bool = True


class N8nBatchRequest(BaseModel):
    """Batch execution request from n8n"""

    tasks: list[N8nTaskRequest]
    execution_mode: str = "parallel"  # parallel, sequential
    callback_url: Optional[str] = None
    webhook_secret: Optional[str] = None


# Initialize components
orchestrator = ClaudeSquadOrchestrator()
memory_manager = get_session_memory_manager()
scraper = WebScraper()
stripe_service = StripeCheckoutService()


@router.post("/webhook/market-research")
async def market_research_webhook(
    request: N8nTaskRequest, background_tasks: BackgroundTasks
):
    """Handle market research workflow from n8n"""

    logger.info(f"Received market research webhook: {request.workflow_id}")

    try:
        # Create market research tasks
        tasks = [
            ClaudeTask(
                id="serpapi_trends",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="SerpAPI Market Trends Analysis",
                description="Analyze current market trends using SerpAPI data",
                context={
                    **request.context,
                    "keywords": request.context.get(
                        "keywords", ["SaaS growth", "market intelligence"]
                    ),
                    "competitor_analysis": True,
                },
            ),
            ClaudeTask(
                id="reddit_sentiment",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.SIMPLE,
                title="Reddit Sentiment Analysis",
                description="Analyze Reddit discussions for market sentiment",
                context={
                    **request.context,
                    "subreddits": ["SaaS", "startups", "entrepreneur"],
                },
            ),
            ClaudeTask(
                id="github_analysis",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.ROUTINE,
                title="GitHub Trend Analysis",
                description="Analyze GitHub for technology trends and opportunities",
                context={
                    **request.context,
                    "technologies": ["FastAPI", "React", "AI", "automation"],
                },
            ),
        ]

        if request.parallel_execution:
            # Execute tasks in parallel
            background_tasks.add_task(
                execute_parallel_tasks, tasks, request.workflow_id
            )

            return {
                "status": "accepted",
                "workflow_id": request.workflow_id,
                "tasks_queued": len(tasks),
                "execution_mode": "parallel",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Execute immediately and return results
            results = await orchestrator.execute_tasks_parallel(tasks)

            return {
                "status": "completed",
                "workflow_id": request.workflow_id,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Market research webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/customer-outreach")
async def customer_outreach_webhook(
    request: N8nTaskRequest, background_tasks: BackgroundTasks
):
    """Handle customer outreach workflow from n8n"""

    logger.info(f"Received customer outreach webhook: {request.workflow_id}")

    try:
        tasks = [
            ClaudeTask(
                id="prospect_discovery",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="Prospect Discovery & Qualification",
                description="Identify and qualify potential customers",
                context={
                    **request.context,
                    "target_industries": request.context.get(
                        "industries", ["SaaS", "FinTech"]
                    ),
                    "prospect_count": request.context.get("prospect_count", 50),
                },
            ),
            ClaudeTask(
                id="email_personalization",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.SIMPLE,
                title="Personalized Email Generation",
                description="Generate personalized outreach emails",
                context={
                    **request.context,
                    "email_templates": True,
                    "personalization_level": "high",
                },
            ),
            ClaudeTask(
                id="follow_up_sequences",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="Follow-up Sequence Design",
                description="Create automated follow-up sequences",
                context={
                    **request.context,
                    "sequence_length": 5,
                    "conversion_focus": True,
                },
            ),
        ]

        if request.parallel_execution:
            background_tasks.add_task(
                execute_parallel_tasks, tasks, request.workflow_id
            )

            return {
                "status": "accepted",
                "workflow_id": request.workflow_id,
                "tasks_queued": len(tasks),
                "execution_mode": "parallel",
            }
        else:
            results = await orchestrator.execute_tasks_parallel(tasks)
            return {
                "status": "completed",
                "workflow_id": request.workflow_id,
                "results": results,
            }

    except Exception as e:
        logger.error(f"Customer outreach webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/content-generation")
async def content_generation_webhook(
    request: N8nTaskRequest, background_tasks: BackgroundTasks
):
    """Handle content generation workflow from n8n"""

    logger.info(f"Received content generation webhook: {request.workflow_id}")

    try:
        tasks = [
            ClaudeTask(
                id="gamma_presentations",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.COMPLEX,
                title="Gamma.app Presentation Creation",
                description="Create professional presentations using Gamma.app",
                context={
                    **request.context,
                    "presentation_types": ["pitch_deck", "product_demo", "case_study"],
                    "visual_style": "professional",
                },
            ),
            ClaudeTask(
                id="blog_content",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="Blog Post Generation",
                description="Generate SEO-optimized blog content",
                context={
                    **request.context,
                    "topics": request.context.get(
                        "content_topics", ["SaaS growth", "automation"]
                    ),
                    "seo_optimized": True,
                },
            ),
            ClaudeTask(
                id="social_content",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.SIMPLE,
                title="Social Media Content",
                description="Create engaging social media content",
                context={
                    **request.context,
                    "platforms": ["LinkedIn", "Twitter", "YouTube"],
                    "content_calendar": True,
                },
            ),
        ]

        if request.parallel_execution:
            background_tasks.add_task(
                execute_parallel_tasks, tasks, request.workflow_id
            )

            return {
                "status": "accepted",
                "workflow_id": request.workflow_id,
                "tasks_queued": len(tasks),
            }
        else:
            results = await orchestrator.execute_tasks_parallel(tasks)
            return {
                "status": "completed",
                "workflow_id": request.workflow_id,
                "results": results,
            }

    except Exception as e:
        logger.error(f"Content generation webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/revenue-optimization")
async def revenue_optimization_webhook(
    request: N8nTaskRequest, background_tasks: BackgroundTasks
):
    """Handle revenue optimization workflow from n8n"""

    logger.info(f"Received revenue optimization webhook: {request.workflow_id}")

    try:
        tasks = [
            ClaudeTask(
                id="pricing_analysis",
                role=BusinessRole.CFO,
                complexity=TaskComplexity.COMPLEX,
                title="Pricing Strategy Analysis",
                description="Analyze and optimize pricing strategy",
                context={
                    **request.context,
                    "current_pricing": request.context.get("pricing_tiers", {}),
                    "competitor_pricing": True,
                    "elasticity_analysis": True,
                },
            ),
            ClaudeTask(
                id="conversion_optimization",
                role=BusinessRole.CMO,
                complexity=TaskComplexity.ROUTINE,
                title="Conversion Rate Optimization",
                description="Optimize conversion funnels and user experience",
                context={
                    **request.context,
                    "funnel_analysis": True,
                    "a_b_testing": True,
                },
            ),
            ClaudeTask(
                id="churn_prevention",
                role=BusinessRole.CFO,
                complexity=TaskComplexity.ROUTINE,
                title="Churn Prevention Analysis",
                description="Identify and prevent customer churn",
                context={
                    **request.context,
                    "retention_strategies": True,
                    "early_warning_signals": True,
                },
            ),
        ]

        if request.parallel_execution:
            background_tasks.add_task(
                execute_parallel_tasks, tasks, request.workflow_id
            )

            return {
                "status": "accepted",
                "workflow_id": request.workflow_id,
                "tasks_queued": len(tasks),
            }
        else:
            results = await orchestrator.execute_tasks_parallel(tasks)
            return {
                "status": "completed",
                "workflow_id": request.workflow_id,
                "results": results,
            }

    except Exception as e:
        logger.error(f"Revenue optimization webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/deployment")
async def deployment_webhook(
    request: N8nTaskRequest, background_tasks: BackgroundTasks
):
    """Handle deployment pipeline webhook from n8n"""

    logger.info(f"Received deployment webhook: {request.workflow_id}")

    try:
        tasks = [
            ClaudeTask(
                id="code_quality_check",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.ROUTINE,
                title="Code Quality Analysis",
                description="Analyze code quality and suggest improvements",
                context={
                    **request.context,
                    "quality_gates": True,
                    "security_scan": True,
                },
            ),
            ClaudeTask(
                id="performance_test",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.ROUTINE,
                title="Performance Testing",
                description="Run performance tests and optimization",
                context={
                    **request.context,
                    "load_testing": True,
                    "bottleneck_analysis": True,
                },
            ),
            ClaudeTask(
                id="deployment_strategy",
                role=BusinessRole.CTO,
                complexity=TaskComplexity.COMPLEX,
                title="Deployment Strategy Optimization",
                description="Optimize deployment pipeline with Dagger CI",
                context={
                    **request.context,
                    "dagger_pipeline": True,
                    "rollback_strategy": True,
                },
            ),
        ]

        if request.parallel_execution:
            background_tasks.add_task(
                execute_parallel_tasks, tasks, request.workflow_id
            )

            return {
                "status": "accepted",
                "workflow_id": request.workflow_id,
                "tasks_queued": len(tasks),
            }
        else:
            results = await orchestrator.execute_tasks_parallel(tasks)
            return {
                "status": "completed",
                "workflow_id": request.workflow_id,
                "results": results,
            }

    except Exception as e:
        logger.error(f"Deployment webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/batch-execution")
async def batch_execution_webhook(
    request: N8nBatchRequest, background_tasks: BackgroundTasks
):
    """Handle batch execution of multiple workflows from n8n"""

    logger.info(f"Received batch execution request with {len(request.tasks)} tasks")

    try:
        # Convert n8n tasks to Claude tasks
        claude_tasks = []

        for n8n_task in request.tasks:
            # Map role string to BusinessRole enum
            role_mapping = {
                "ceo": BusinessRole.CEO,
                "cto": BusinessRole.CTO,
                "cmo": BusinessRole.CMO,
                "cfo": BusinessRole.CFO,
            }

            role = role_mapping.get(n8n_task.role.lower(), BusinessRole.CEO)

            # Determine complexity based on task type
            complexity = TaskComplexity.ROUTINE
            if (
                "complex" in n8n_task.task_type.lower()
                or "strategic" in n8n_task.task_type.lower()
            ):
                complexity = TaskComplexity.COMPLEX
            elif "simple" in n8n_task.task_type.lower():
                complexity = TaskComplexity.SIMPLE

            claude_task = ClaudeTask(
                id=f"{n8n_task.workflow_id}_{n8n_task.role}_{n8n_task.task_type}",
                role=role,
                complexity=complexity,
                title=n8n_task.task_type.replace("_", " ").title(),
                description=f"Execute {n8n_task.task_type} for {n8n_task.role}",
                context=n8n_task.context,
                priority=n8n_task.priority,
                timeout_seconds=n8n_task.timeout_seconds,
            )

            claude_tasks.append(claude_task)

        if request.execution_mode == "parallel":
            # Execute all tasks in parallel
            background_tasks.add_task(
                execute_batch_tasks_with_callback, claude_tasks, request.callback_url
            )

            return {
                "status": "accepted",
                "tasks_queued": len(claude_tasks),
                "execution_mode": "parallel",
                "estimated_completion_time": "5-10 minutes",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Execute sequentially and return results
            results = await execute_sequential_tasks(claude_tasks)

            return {
                "status": "completed",
                "results": results,
                "execution_mode": "sequential",
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Batch execution webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a specific workflow execution"""

    try:
        # Check memory for workflow status
        memory = get_session_memory_manager()
        workflow_status = memory.memory_nodes.get(f"workflow_status_{workflow_id}")

        if workflow_status:
            return {
                "workflow_id": workflow_id,
                "status": workflow_status.content.get("status", "unknown"),
                "progress": workflow_status.content.get("progress", 0),
                "results": workflow_status.content.get("results"),
                "last_updated": workflow_status.updated_at.isoformat(),
            }
        else:
            return {
                "workflow_id": workflow_id,
                "status": "not_found",
                "message": "Workflow not found or expired",
            }

    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions


async def execute_parallel_tasks(tasks: list[ClaudeTask], workflow_id: str):
    """Execute tasks in parallel and store results"""

    try:
        logger.info(f"Starting parallel execution for workflow {workflow_id}")

        # Store initial status
        memory = get_session_memory_manager()
        memory.store_memory_node(
            category="workflow_status",
            content={
                "workflow_id": workflow_id,
                "status": "running",
                "progress": 0,
                "started_at": datetime.now().isoformat(),
            },
        )

        # Execute tasks
        results = await orchestrator.execute_tasks_parallel(tasks)

        # Store final results
        memory.store_memory_node(
            category="workflow_results",
            content={
                "workflow_id": workflow_id,
                "status": "completed",
                "progress": 100,
                "results": results,
                "completed_at": datetime.now().isoformat(),
            },
        )

        logger.info(f"Parallel execution completed for workflow {workflow_id}")

    except Exception as e:
        logger.error(f"Parallel execution failed for workflow {workflow_id}: {e}")

        # Store error status
        memory = get_session_memory_manager()
        memory.store_memory_node(
            category="workflow_status",
            content={
                "workflow_id": workflow_id,
                "status": "error",
                "error": str(e),
                "failed_at": datetime.now().isoformat(),
            },
        )


async def execute_batch_tasks_with_callback(
    tasks: list[ClaudeTask], callback_url: Optional[str]
):
    """Execute batch tasks and send results to callback URL"""

    try:
        results = await orchestrator.execute_tasks_parallel(tasks)

        # Send results to callback URL if provided
        if callback_url:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                await session.post(
                    callback_url,
                    json={
                        "status": "completed",
                        "results": results,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        logger.info("Batch execution completed and results sent to callback")

    except Exception as e:
        logger.error(f"Batch execution with callback failed: {e}")

        # Send error to callback URL if provided
        if callback_url:
            try:
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    await session.post(
                        callback_url,
                        json={
                            "status": "error",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
            except Exception:
                pass  # Don't fail on callback errors


async def execute_sequential_tasks(tasks: list[ClaudeTask]) -> dict:
    """Execute tasks sequentially with dependency handling"""

    results = {}

    for task in tasks:
        try:
            # Execute single task
            task_results = await orchestrator.execute_tasks_parallel([task])
            results[task.id] = task_results

            logger.info(f"Sequential task {task.id} completed")

        except Exception as e:
            logger.error(f"Sequential task {task.id} failed: {e}")
            results[task.id] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    return results
