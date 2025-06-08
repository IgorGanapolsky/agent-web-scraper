#!/usr/bin/env python3
"""
n8n Workflow Orchestrator for Parallel Business Automation
Integrates Claude Code with n8n for maximum parallelization
"""

import asyncio
import os
from datetime import datetime

import aiohttp
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.cost_tracker import CostTracker
from app.core.scraper import WebScraper
from app.services.stripe_checkout_service import StripeCheckoutService

logger = get_logger(__name__)


class N8nWorkflow(BaseModel):
    """n8n workflow configuration"""

    id: str
    name: str
    webhook_url: str
    enabled: bool = True
    parallel_nodes: list[str] = []
    dependencies: list[str] = []
    priority: int = 1  # 1=high, 2=medium, 3=low


class N8nOrchestrator:
    """Orchestrate parallel workflows with n8n for business automation"""

    def __init__(self):
        self.n8n_base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.n8n_api_key = os.getenv("N8N_API_KEY")
        self.webhook_secret = os.getenv("N8N_WEBHOOK_SECRET")

        # Initialize components
        self.cost_tracker = CostTracker()
        self.scraper = WebScraper()
        self.stripe_service = StripeCheckoutService()

        # Define parallel workflows
        self.workflows = {
            "market_research": N8nWorkflow(
                id="wf_market_research",
                name="Parallel Market Research",
                webhook_url=f"{self.n8n_base_url}/webhook/market-research",
                parallel_nodes=[
                    "serpapi_trends",
                    "reddit_scraping",
                    "github_analysis",
                    "competitor_intel",
                ],
                priority=1,
            ),
            "customer_outreach": N8nWorkflow(
                id="wf_customer_outreach",
                name="Customer Acquisition Pipeline",
                webhook_url=f"{self.n8n_base_url}/webhook/customer-outreach",
                parallel_nodes=[
                    "prospect_discovery",
                    "email_personalization",
                    "social_media_outreach",
                    "follow_up_sequences",
                ],
                priority=1,
            ),
            "content_generation": N8nWorkflow(
                id="wf_content_generation",
                name="AI Content Creation",
                webhook_url=f"{self.n8n_base_url}/webhook/content-generation",
                parallel_nodes=[
                    "gamma_presentations",
                    "blog_posts",
                    "social_content",
                    "email_templates",
                ],
                priority=2,
            ),
            "revenue_optimization": N8nWorkflow(
                id="wf_revenue_optimization",
                name="Revenue & Performance Optimization",
                webhook_url=f"{self.n8n_base_url}/webhook/revenue-optimization",
                parallel_nodes=[
                    "pricing_analysis",
                    "conversion_optimization",
                    "churn_prevention",
                    "upsell_automation",
                ],
                priority=1,
            ),
            "deployment_pipeline": N8nWorkflow(
                id="wf_deployment",
                name="Dagger CI/CD Pipeline",
                webhook_url=f"{self.n8n_base_url}/webhook/deployment",
                parallel_nodes=[
                    "code_quality_check",
                    "security_scan",
                    "performance_test",
                    "deployment_staging",
                ],
                dependencies=["market_research", "customer_outreach"],
                priority=2,
            ),
        }

        logger.info(
            f"n8n Orchestrator initialized with {len(self.workflows)} workflows"
        )

    async def trigger_parallel_workflows(
        self, workflows: list[str], context: dict
    ) -> dict:
        """Trigger multiple n8n workflows in parallel"""

        start_time = datetime.now()
        tasks = []

        # Create async tasks for each workflow
        for workflow_name in workflows:
            if workflow_name in self.workflows:
                workflow = self.workflows[workflow_name]
                if workflow.enabled:
                    task = asyncio.create_task(
                        self._execute_workflow(workflow, context), name=workflow_name
                    )
                    tasks.append(task)

        logger.info(f"Triggering {len(tasks)} parallel workflows")

        # Execute all workflows concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        workflow_results = {}
        for i, result in enumerate(results):
            workflow_name = tasks[i].get_name()
            if isinstance(result, Exception):
                logger.error(f"Workflow {workflow_name} failed: {result}")
                workflow_results[workflow_name] = {
                    "status": "error",
                    "error": str(result),
                }
            else:
                workflow_results[workflow_name] = result

        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            "execution_time_seconds": execution_time,
            "workflows_executed": len(tasks),
            "results": workflow_results,
            "timestamp": datetime.now().isoformat(),
        }

    async def _execute_workflow(self, workflow: N8nWorkflow, context: dict) -> dict:
        """Execute a single n8n workflow"""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json"}

                if self.n8n_api_key:
                    headers["Authorization"] = f"Bearer {self.n8n_api_key}"

                payload = {
                    "workflow_id": workflow.id,
                    "context": context,
                    "parallel_nodes": workflow.parallel_nodes,
                    "timestamp": datetime.now().isoformat(),
                }

                async with session.post(
                    workflow.webhook_url,
                    json=payload,
                    headers=headers,
                    timeout=300,  # 5 minute timeout
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Workflow {workflow.name} completed successfully")
                        return {
                            "status": "success",
                            "workflow": workflow.name,
                            "result": result,
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Workflow {workflow.name} failed: {error_text}")
                        return {
                            "status": "error",
                            "workflow": workflow.name,
                            "error": error_text,
                        }

        except Exception as e:
            logger.error(f"Error executing workflow {workflow.name}: {e}")
            return {"status": "error", "workflow": workflow.name, "error": str(e)}

    async def execute_revenue_acceleration_pipeline(self) -> dict:
        """Execute the complete revenue acceleration pipeline"""

        logger.info("🚀 Starting Revenue Acceleration Pipeline")

        # Phase 1: Parallel Market Intelligence & Customer Discovery
        phase1_workflows = ["market_research", "customer_outreach"]
        phase1_context = {
            "target_revenue": 300,  # $300/day
            "industries": ["SaaS", "FinTech", "HealthTech", "EdTech"],
            "prospect_count": 100,
            "analysis_depth": "comprehensive",
        }

        phase1_results = await self.trigger_parallel_workflows(
            phase1_workflows, phase1_context
        )

        # Phase 2: Content Creation & Revenue Optimization (using Phase 1 results)
        phase2_workflows = ["content_generation", "revenue_optimization"]
        phase2_context = {
            **phase1_context,
            "market_insights": phase1_results.get("results", {}).get(
                "market_research", {}
            ),
            "prospect_data": phase1_results.get("results", {}).get(
                "customer_outreach", {}
            ),
        }

        phase2_results = await self.trigger_parallel_workflows(
            phase2_workflows, phase2_context
        )

        # Phase 3: Deployment Pipeline (if needed)
        if any("error" not in result for result in [phase1_results, phase2_results]):
            phase3_workflows = ["deployment_pipeline"]
            phase3_context = {
                **phase2_context,
                "deployment_trigger": "revenue_pipeline_success",
            }

            phase3_results = await self.trigger_parallel_workflows(
                phase3_workflows, phase3_context
            )
        else:
            phase3_results = {"skipped": "Previous phases had errors"}

        # Compile comprehensive results
        total_execution_time = (
            phase1_results.get("execution_time_seconds", 0)
            + phase2_results.get("execution_time_seconds", 0)
            + (
                phase3_results.get("execution_time_seconds", 0)
                if isinstance(phase3_results, dict)
                else 0
            )
        )

        return {
            "pipeline_status": "completed",
            "total_execution_time_seconds": total_execution_time,
            "phases": {
                "market_intelligence": phase1_results,
                "content_optimization": phase2_results,
                "deployment": phase3_results,
            },
            "revenue_impact_projection": self._calculate_revenue_impact(
                phase1_results, phase2_results
            ),
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_revenue_impact(
        self, market_results: dict, optimization_results: dict
    ) -> dict:
        """Calculate projected revenue impact from parallel workflows"""

        # Extract key metrics from workflow results
        market_results.get("results", {}).get("market_research", {})
        outreach_data = market_results.get("results", {}).get("customer_outreach", {})

        # Base projections
        prospects_reached = outreach_data.get("result", {}).get(
            "prospects_contacted", 0
        )
        conversion_rate = 0.15  # 15% trial conversion
        trial_to_paid = 0.25  # 25% trial to paid conversion
        avg_subscription = 99  # Average monthly subscription

        projected_trials = prospects_reached * conversion_rate
        projected_customers = projected_trials * trial_to_paid
        projected_monthly_revenue = projected_customers * avg_subscription
        projected_daily_revenue = projected_monthly_revenue / 30

        return {
            "prospects_reached": prospects_reached,
            "projected_trials": round(projected_trials),
            "projected_customers": round(projected_customers),
            "projected_monthly_revenue": round(projected_monthly_revenue, 2),
            "projected_daily_revenue": round(projected_daily_revenue, 2),
            "days_to_300_target": (
                round(300 / max(projected_daily_revenue, 1), 1)
                if projected_daily_revenue > 0
                else "∞"
            ),
        }

    def create_n8n_webhook_endpoints(self) -> dict[str, str]:
        """Generate n8n webhook endpoints configuration"""

        endpoints = {}

        for workflow_name, workflow in self.workflows.items():
            endpoints[workflow_name] = {
                "webhook_url": workflow.webhook_url,
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Webhook-Secret": self.webhook_secret,
                },
                "parallel_nodes": workflow.parallel_nodes,
                "sample_payload": {
                    "workflow_id": workflow.id,
                    "context": {"example": "data"},
                    "timestamp": datetime.now().isoformat(),
                },
            }

        return endpoints

    def get_workflow_status(self) -> dict:
        """Get status of all configured workflows"""

        status = {
            "total_workflows": len(self.workflows),
            "enabled_workflows": len([w for w in self.workflows.values() if w.enabled]),
            "high_priority_workflows": len(
                [w for w in self.workflows.values() if w.priority == 1]
            ),
            "workflows": {},
        }

        for name, workflow in self.workflows.items():
            status["workflows"][name] = {
                "enabled": workflow.enabled,
                "priority": workflow.priority,
                "parallel_nodes_count": len(workflow.parallel_nodes),
                "has_dependencies": len(workflow.dependencies) > 0,
            }

        return status


async def main():
    """Demo the n8n orchestrator"""

    orchestrator = N8nOrchestrator()

    print("🤖 n8n Workflow Orchestrator Demo")
    print("=" * 50)

    # Show workflow status
    status = orchestrator.get_workflow_status()
    print(f"Total workflows: {status['total_workflows']}")
    print(f"Enabled workflows: {status['enabled_workflows']}")

    # Execute revenue acceleration pipeline
    print("\n🚀 Executing Revenue Acceleration Pipeline...")
    results = await orchestrator.execute_revenue_acceleration_pipeline()

    print("\n📊 Pipeline Results:")
    print(
        f"Total execution time: {results['total_execution_time_seconds']:.2f} seconds"
    )

    revenue_impact = results["revenue_impact_projection"]
    print("\n💰 Revenue Impact Projection:")
    print(f"Prospects reached: {revenue_impact['prospects_reached']}")
    print(f"Projected customers: {revenue_impact['projected_customers']}")
    print(f"Projected daily revenue: ${revenue_impact['projected_daily_revenue']}")
    print(f"Days to $300 target: {revenue_impact['days_to_300_target']}")


if __name__ == "__main__":
    asyncio.run(main())
