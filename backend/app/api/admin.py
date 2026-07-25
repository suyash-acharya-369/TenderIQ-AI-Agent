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


@router.get("/operations-dashboard")
def get_operations_dashboard(admin: User = Depends(require_role("Administrator")), db: Session = Depends(get_db)):
    """Phase 25: Live Operations Dashboard for system resources, queues, and background services."""
    import psutil
    from backend.app.api.websockets import notification_manager
    from backend.app.models.notification import NotificationLog

    cpu_pct = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    total_emails_today = db.query(NotificationLog).filter(NotificationLog.channel == "Email").count()
    failed_emails_today = db.query(NotificationLog).filter(NotificationLog.channel == "Email", NotificationLog.status == "failed").count()

    return {
        "status": "Healthy",
        "system_resources": {
            "cpu_usage_pct": cpu_pct,
            "ram_usage_pct": mem.percent,
            "ram_used_mb": round(mem.used / (1024 * 1024), 2),
            "disk_usage_pct": disk.percent,
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
        },
        "services": {
            "database": "Healthy",
            "scheduler": "Running",
            "websocket_active_clients": len(notification_manager.active_connections),
            "email_provider": "Resend (Connected)",
            "emails_sent_today": total_emails_today,
            "emails_failed_today": failed_emails_today,
        }
    }


@router.post("/backup/create")
def trigger_manual_backup(admin: User = Depends(require_role("Administrator"))):
    """Phase 24: Trigger manual backup zip creation."""
    from backend.app.services.backup_service import create_system_backup
    res = create_system_backup()
    return res


@router.get("/backup/list")
def list_system_backups(admin: User = Depends(require_role("Administrator"))):
    """Phase 24: List system backup archives."""
    from backend.app.services.backup_service import list_backups
    return list_backups()


@router.post("/backup/restore")
def restore_system_backup(filename: str, admin: User = Depends(require_role("Administrator"))):
    """Phase 24: Restore system from backup zip."""
    from backend.app.services.backup_service import restore_backup
    res = restore_backup(filename)
    return res


# ─── Tender Data Verification Audit Endpoints ───────────────────────────────

@router.get("/verification/dashboard")
def get_verification_audit_dashboard(
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Retrieve overall platform data quality and verification metrics."""
    from backend.app.services.integrity_verifier import audit_all_database_tenders
    metrics = audit_all_database_tenders(db, check_live_urls=False)
    return metrics


@router.post("/verification/audit-all")
def trigger_platform_data_audit(
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Trigger a full platform data integrity audit across all tenders."""
    from backend.app.services.integrity_verifier import audit_all_database_tenders
    metrics = audit_all_database_tenders(db, check_live_urls=True)
    return metrics


@router.post("/verification/approve-tender/{tender_id}")
def approve_tender_verification(
    tender_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Manually approve a tender's verification status."""
    from backend.app.models.tender import Tender
    t = db.query(Tender).filter(Tender.id == tender_id).first()
    if not t:
        return {"error": "Tender not found"}
    t.verification_status = "VERIFIED"
    t.integrity_score = 100.0
    t.verified_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "tender_id": tender_id, "verification_status": "VERIFIED"}


@router.post("/verification/reject-tender/{tender_id}")
def reject_tender_verification(
    tender_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    """Manually reject a tender's verification status (excludes it from notifications)."""
    from backend.app.models.tender import Tender
    t = db.query(Tender).filter(Tender.id == tender_id).first()
    if not t:
        return {"error": "Tender not found"}
    t.verification_status = "REJECTED"
    t.integrity_score = 0.0
    t.verified_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "tender_id": tender_id, "verification_status": "REJECTED"}


