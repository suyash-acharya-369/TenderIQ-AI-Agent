import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.source import CrawlHistory, Source
from backend.app.models.ai import AILog
from backend.app.models.audit import AuditLog, SystemHealthLog
from backend.app.models.user import User
from backend.app.api.deps import require_role

router = APIRouter(prefix="/admin", tags=["System Administration"])

@router.get("/crawl-history")
def get_crawl_history(
    limit: int = Query(20, le=100),
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    crawls = db.query(CrawlHistory).order_by(CrawlHistory.start_time.desc()).limit(limit).all()
    res = []
    for c in crawls:
        src = db.query(Source).filter(Source.id == c.source_id).first()
        res.append({
            "id": c.id,
            "source_name": src.name if src else "Unknown",
            "start_time": c.start_time,
            "finish_time": c.finish_time,
            "duration_seconds": c.duration_seconds,
            "opportunities_found": c.opportunities_found,
            "new_opportunities": c.new_opportunities,
            "updated_opportunities": c.updated_opportunities,
            "status": c.status,
            "error_message": c.error_message
        })
    return res

@router.get("/queue-status")
def get_queue_status(
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    running_crawls = db.query(CrawlHistory).filter(CrawlHistory.status == "running").count()
    completed_crawls = db.query(CrawlHistory).filter(CrawlHistory.status == "completed").count()
    failed_crawls = db.query(CrawlHistory).filter(CrawlHistory.status == "failed").count()

    return {
        "status": "Healthy",
        "active_queues": {
            "crawl_queue": {"running": running_crawls, "pending": 0, "completed": completed_crawls, "failed": failed_crawls},
            "ai_queue": {"running": 0, "pending": 0, "completed": db.query(AILog).count(), "failed": 0},
            "ocr_queue": {"running": 0, "pending": 0, "completed": 0, "failed": 0},
            "notification_queue": {"running": 0, "pending": 0, "completed": 0, "failed": 0}
        }
    }

@router.get("/ai-costs")
def get_ai_cost_dashboard(
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    logs = db.query(AILog).order_by(AILog.created_at.desc()).limit(50).all()
    total_cost = db.query(func.sum(AILog.total_cost_usd)).scalar() or 0.0
    total_tokens = db.query(func.sum(AILog.prompt_tokens + AILog.completion_tokens)).scalar() or 0
    total_executions = db.query(AILog).count()

    return {
        "summary": {
            "total_cost_usd": round(total_cost, 4),
            "total_tokens_consumed": total_tokens,
            "total_ai_executions": total_executions,
            "default_provider": "OpenRouter (openai/gpt-4o-mini)"
        },
        "recent_logs": [
            {
                "id": l.id,
                "task_name": l.task_name,
                "provider": l.provider,
                "model_used": l.model_used,
                "tokens": l.prompt_tokens + l.completion_tokens,
                "cost_usd": l.total_cost_usd,
                "status": l.status,
                "created_at": l.created_at
            }
            for l in logs
        ]
    }

@router.get("/audit-logs")
def get_audit_logs(
    q: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if q:
        query = query.filter((AuditLog.action.ilike(f"%{q}%")) | (AuditLog.user_email.ilike(f"%{q}%")))
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "user_email": l.user_email,
            "action": l.action,
            "created_at": l.created_at
        }
        for l in logs
    ]
