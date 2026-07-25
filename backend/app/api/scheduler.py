"""
Scheduler Management API — Exposes background job tracking, execution history, and manual trigger controls.
"""
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.source import ScheduledJobLog, Source
from backend.app.models.user import User
from backend.app.api.deps import require_role, get_current_user
from backend.app.services.scheduler import scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler Engine"])


class JobTriggerPayload(BaseModel):
    job_name: str  # "Daily Tender Crawl", "Daily AI Analysis", "Daily Digest Email", "Source Health Check", "Failed Crawl Retry", "PDF Cleanup", "Database Maintenance"


@router.get("/dashboard")
def get_scheduler_dashboard(admin: User = Depends(require_role("Administrator")), db: Session = Depends(get_db)):
    """Phase 1: Scheduler Monitoring Dashboard metrics."""
    jobs = db.query(ScheduledJobLog).order_by(ScheduledJobLog.last_run.desc()).limit(20).all()
    active_sources_count = db.query(Source).filter(Source.status == "active", Source.is_enabled == True).count()

    return {
        "status": "Running" if scheduler._running else "Stopped",
        "active_sources_scheduled": active_sources_count,
        "last_pulse": datetime.now(timezone.utc).isoformat(),
        "recent_executions": [
            {
                "id": j.id,
                "job_name": j.job_name,
                "status": j.status,
                "last_run": j.last_run.isoformat() if j.last_run else None,
                "next_run": j.next_run.isoformat() if j.next_run else None,
                "duration_seconds": j.duration_seconds,
                "summary": j.result_summary,
                "error": j.error_log,
            }
            for j in jobs
        ]
    }


@router.get("/jobs")
def list_scheduled_job_history(
    limit: int = Query(50, le=200),
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Retrieve full execution history for background jobs."""
    logs = db.query(ScheduledJobLog).order_by(ScheduledJobLog.last_run.desc()).limit(limit).all()
    return logs


@router.post("/trigger-job")
def trigger_manual_scheduler_job(
    payload: JobTriggerPayload,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Phase 10: Trigger manual execution of real backend jobs."""
    job_name = payload.job_name
    if job_name == "Daily Tender Crawl":
        res = scheduler._execute_job("Daily Tender Crawl", lambda d: scheduler.run_per_source_crawls())
    elif job_name == "Daily AI Analysis":
        res = scheduler._execute_job("Daily AI Analysis", scheduler._job_ai_analysis)
    elif job_name == "Daily Digest Email":
        res = scheduler._execute_job("Daily Digest Email", scheduler._job_daily_digest)
    elif job_name == "Source Health Check":
        res = scheduler._execute_job("Source Health Check", scheduler._job_source_health)
    elif job_name == "Failed Crawl Retry":
        res = scheduler._execute_job("Failed Crawl Retry", scheduler._job_retry_failed_crawls)
    elif job_name == "PDF Cleanup":
        res = scheduler._execute_job("PDF Cleanup", scheduler._job_pdf_cleanup)
    elif job_name == "Database Maintenance":
        res = scheduler._execute_job("Database Maintenance", scheduler._job_db_maintenance)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown job name: {job_name}")

    return {
        "status": "triggered",
        "job_name": job_name,
        "execution_result": res,
        "triggered_at": datetime.now(timezone.utc).isoformat()
    }
