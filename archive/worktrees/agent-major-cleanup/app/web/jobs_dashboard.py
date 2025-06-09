"""
Simple jobs dashboard using FastAPI and Jinja2 templates
"""

from typing import Any

import httpx
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config.logging import get_logger

logger = get_logger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def get_job_data() -> dict[str, Any]:
    """Get job data from the jobs API"""
    try:
        async with httpx.AsyncClient() as client:
            # Get job list
            jobs_response = await client.get("http://localhost:8000/jobs/list")
            jobs = jobs_response.json() if jobs_response.status_code == 200 else []

            # Get detailed status for each job
            detailed_jobs = []
            for job in jobs:
                try:
                    status_response = await client.get(
                        f"http://localhost:8000/jobs/status/{job['task_id']}"
                    )
                    if status_response.status_code == 200:
                        detailed_jobs.append(status_response.json())
                except Exception as e:
                    logger.warning(
                        f"Failed to get status for job {job['task_id']}: {e}"
                    )
                    detailed_jobs.append(job)

            # Get system health
            health_response = await client.get("http://localhost:8000/jobs/health")
            health = (
                health_response.json() if health_response.status_code == 200 else None
            )

            return {"jobs": detailed_jobs, "health": health}
    except Exception as e:
        logger.error(f"Failed to get job data: {e}")
        return {"jobs": [], "health": None}


@router.get("/", response_class=HTMLResponse)
async def jobs_dashboard(request: Request):
    """
    Main jobs dashboard page
    """
    job_data = await get_job_data()

    return templates.TemplateResponse(
        "jobs_dashboard.html",
        {"request": request, "jobs": job_data["jobs"], "health": job_data["health"]},
    )


@router.post("/submit-job")
async def submit_job(
    request: Request,
    job_type: str = Form(...),
    query: str = Form("SaaS pain points"),
    max_posts: int = Form(50),
):
    """
    Submit a new job via the dashboard
    """
    try:
        # Prepare job parameters
        parameters = {"query": query, "max_posts": max_posts}

        # Submit job via API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/jobs/submit",
                json={"job_type": job_type, "parameters": parameters},
            )

            if response.status_code == 200:
                logger.info(f"Job submitted successfully: {job_type}")
                return RedirectResponse(url="/dashboard/", status_code=303)
            else:
                logger.error(f"Job submission failed: {response.text}")
                raise HTTPException(status_code=400, detail="Job submission failed")

    except Exception as e:
        logger.error(f"Job submission error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cancel-job")
async def cancel_job(request: Request, task_id: str = Form(...)):
    """
    Cancel a running job
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://localhost:8000/jobs/cancel/{task_id}"
            )

            if response.status_code == 200:
                logger.info(f"Job cancelled successfully: {task_id}")
            else:
                logger.error(f"Job cancellation failed: {response.text}")

        return RedirectResponse(url="/dashboard/", status_code=303)

    except Exception as e:
        logger.error(f"Job cancellation error: {e}")
        return RedirectResponse(url="/dashboard/", status_code=303)


@router.get("/job/{task_id}", response_class=HTMLResponse)
async def job_detail(request: Request, task_id: str):
    """
    Detailed view for a specific job
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/jobs/status/{task_id}")

            if response.status_code == 200:
                job = response.json()

                return templates.TemplateResponse(
                    "job_detail.html", {"request": request, "job": job}
                )
            else:
                raise HTTPException(status_code=404, detail="Job not found")

    except Exception as e:
        logger.error(f"Job detail error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
