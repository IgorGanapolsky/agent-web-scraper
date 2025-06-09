"""
Jobs API endpoint for Celery task management
"""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.logging import get_logger
from app.core.celery_app import celery_app
from app.tasks.scraping_tasks import (
    analyze_market_trends,
    generate_insight_report,
    scrape_reddit_pain_points,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobSubmissionRequest(BaseModel):
    job_type: str
    parameters: dict[str, Any]


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    current: int = 0
    total: int = 100
    result: dict[str, Any] = None
    error: str = None


@router.post("/submit", response_model=dict[str, str])
async def submit_job(request: JobSubmissionRequest):
    """
    Submit a background job to the Celery task queue
    """
    try:
        task = None

        if request.job_type == "reddit_scrape":
            query = request.parameters.get("query", "SaaS pain points")
            max_posts = request.parameters.get("max_posts", 50)
            task = scrape_reddit_pain_points.delay(query, max_posts)

        elif request.job_type == "market_analysis":
            data = request.parameters.get("data", {})
            task = analyze_market_trends.delay(data)

        elif request.job_type == "insight_report":
            scrape_results = request.parameters.get("scrape_results", {})
            task = generate_insight_report.delay(scrape_results)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown job type: {request.job_type}"
            )

        logger.info(f"Job submitted: {task.id} (type: {request.job_type})")

        return {
            "task_id": task.id,
            "status": "submitted",
            "message": f"Job {request.job_type} submitted successfully",
        }

    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}", response_model=JobStatusResponse)
async def get_job_status(task_id: str):
    """
    Get the status of a background job
    """
    try:
        result = AsyncResult(task_id, app=celery_app)

        response = JobStatusResponse(task_id=task_id, status=result.status)

        if result.state == "PENDING":
            response.current = 0
            response.total = 100

        elif result.state == "PROGRESS":
            if result.info:
                response.current = result.info.get("current", 0)
                response.total = result.info.get("total", 100)

        elif result.state == "SUCCESS":
            response.current = 100
            response.total = 100
            response.result = (
                result.info.get("results") if result.info else result.result
            )

        elif result.state == "FAILURE":
            response.error = str(result.info) if result.info else "Task failed"

        return response

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=list[dict[str, Any]])
async def list_jobs():
    """
    List all active and recent jobs
    """
    try:
        # Get active tasks
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()

        jobs = []

        # Add active tasks
        if active_tasks:
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    jobs.append(
                        {
                            "task_id": task["id"],
                            "name": task["name"],
                            "status": "RUNNING",
                            "worker": worker,
                            "args": task.get("args", []),
                            "kwargs": task.get("kwargs", {}),
                        }
                    )

        # Add scheduled tasks
        if scheduled_tasks:
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    jobs.append(
                        {
                            "task_id": task["request"]["id"],
                            "name": task["request"]["task"],
                            "status": "SCHEDULED",
                            "worker": worker,
                            "eta": task.get("eta"),
                        }
                    )

        return jobs

    except Exception as e:
        logger.error(f"Job listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cancel/{task_id}")
async def cancel_job(task_id: str):
    """
    Cancel a running job
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        logger.info(f"Job cancelled: {task_id}")

        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Job cancelled successfully",
        }

    except Exception as e:
        logger.error(f"Job cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def job_system_health():
    """
    Check the health of the job system
    """
    try:
        # Check Celery worker status
        inspect = celery_app.control.inspect()
        stats = inspect.stats()

        if not stats:
            return {
                "status": "unhealthy",
                "message": "No Celery workers available",
                "workers": 0,
            }

        return {
            "status": "healthy",
            "message": "Job system operational",
            "workers": len(stats),
            "worker_stats": stats,
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "message": str(e), "workers": 0}
