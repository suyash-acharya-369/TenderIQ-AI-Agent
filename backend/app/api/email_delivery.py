"""
Email Delivery API — Production-grade endpoints for TenderIQ AI email system.
Handles test delivery, test series, dashboard stats, retry, and provider status.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.notification import NotificationLog
from backend.app.models.user import User
from backend.app.api.deps import get_current_user, require_role
from backend.app.services.notification_service import notification_service
from backend.app.notifications.base import EmailResult
from backend.app.notifications import templates
from backend.app.config import settings

router = APIRouter(prefix="/email", tags=["Email Delivery"])


class TestEmailPayload(BaseModel):
    recipient: str = "ordinary01012024@gmail.com"


# ─── Provider Status ─────────────────────────────────────────────────────────

@router.get("/status")
def get_email_status(admin: User = Depends(require_role("Administrator"))):
    """Check email provider connectivity and configuration."""
    result = notification_service.check_connectivity()
    return {
        "provider": notification_service.get_provider_name(),
        "email_enabled": notification_service.is_enabled(),
        "connectivity": {
            "reachable": result.success,
            "http_status": result.http_status,
            "provider_response": result.provider_response,
            "error": result.error,
        },
        "configuration": {
            "email_provider": getattr(settings, "EMAIL_PROVIDER", "smtp"),
            "sender_email": getattr(settings, "SENDER_EMAIL", ""),
            "api_key_configured": bool(getattr(settings, "RESEND_API_KEY", "")),
            "smtp_host_configured": bool(getattr(settings, "SMTP_HOST", "")),
        },
    }


@router.get("/providers")
def get_available_providers(admin: User = Depends(require_role("Administrator"))):
    """List all available email providers."""
    return {
        "current": notification_service.get_provider_name(),
        "available": [
            {"name": "Resend", "key": "resend", "configured": bool(getattr(settings, "RESEND_API_KEY", ""))},
            {"name": "SMTP", "key": "smtp", "configured": bool(getattr(settings, "SMTP_HOST", ""))},
        ],
    }


# ─── Test Email ───────────────────────────────────────────────────────────────

@router.post("/test")
def send_test_email(
    payload: TestEmailPayload,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Send a single test email and record the result."""
    template = templates.test_email_template(
        provider_name=notification_service.get_provider_name(),
        environment=getattr(settings, "ENVIRONMENT", "development"),
    )

    result = notification_service.dispatch_email(
        to_email=payload.recipient,
        subject=template["subject"],
        html_content=template["html"],
    )

    # Record in notification log
    log = NotificationLog(
        channel="Email",
        recipient=payload.recipient,
        subject=template["subject"],
        content="[Test Email Template]",
        status="sent" if result.success else "failed",
        message_id=result.message_id,
        provider=result.provider,
        http_status=result.http_status,
        provider_response=result.provider_response,
        retry_count=result.retry_count,
        error_message=result.error,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "success": result.success,
        "notification_log_id": log.id,
        "message_id": result.message_id,
        "provider": result.provider,
        "http_status": result.http_status,
        "provider_response": result.provider_response,
        "error": result.error,
        "retry_count": result.retry_count,
        "recipient": payload.recipient,
        "subject": template["subject"],
        "sent_at": log.sent_at.isoformat() if log.sent_at else None,
    }


# ─── Test Series ──────────────────────────────────────────────────────────────

@router.post("/test-series")
def send_test_series(
    payload: TestEmailPayload,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Send all 6 verification template emails."""
    template_generators = [
        ("Welcome", templates.welcome_template),
        ("Tender Alert", templates.tender_alert_template),
        ("AI Summary", templates.ai_summary_template),
        ("Crawl Completed", templates.crawl_completed_template),
        ("Daily Digest", templates.daily_digest_template),
        ("System Alert", templates.system_alert_template),
    ]

    results = []

    for name, gen_fn in template_generators:
        tmpl = gen_fn()
        result = notification_service.dispatch_email(
            to_email=payload.recipient,
            subject=tmpl["subject"],
            html_content=tmpl["html"],
        )

        log = NotificationLog(
            channel="Email",
            recipient=payload.recipient,
            subject=tmpl["subject"],
            content=f"[{name} Template - Test Series]",
            status="sent" if result.success else "failed",
            message_id=result.message_id,
            provider=result.provider,
            http_status=result.http_status,
            provider_response=result.provider_response,
            retry_count=result.retry_count,
            error_message=result.error,
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        results.append({
            "template": name,
            "success": result.success,
            "notification_log_id": log.id,
            "message_id": result.message_id,
            "error": result.error,
        })

    total = len(results)
    successful = sum(1 for r in results if r["success"])

    return {
        "total": total,
        "successful": successful,
        "failed": total - successful,
        "results": results,
    }


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_email_dashboard(
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Aggregate email delivery statistics."""
    total = db.query(NotificationLog).filter(NotificationLog.channel == "Email").count()
    sent = db.query(NotificationLog).filter(
        NotificationLog.channel == "Email",
        NotificationLog.status == "sent",
    ).count()
    failed = db.query(NotificationLog).filter(
        NotificationLog.channel == "Email",
        NotificationLog.status == "failed",
    ).count()
    pending = db.query(NotificationLog).filter(
        NotificationLog.channel == "Email",
        NotificationLog.status == "pending",
    ).count()

    last_sent = (
        db.query(NotificationLog)
        .filter(NotificationLog.channel == "Email", NotificationLog.status == "sent")
        .order_by(NotificationLog.sent_at.desc())
        .first()
    )

    last_failed = (
        db.query(NotificationLog)
        .filter(NotificationLog.channel == "Email", NotificationLog.status == "failed")
        .order_by(NotificationLog.sent_at.desc())
        .first()
    )

    return {
        "statistics": {
            "total_emails": total,
            "successful": sent,
            "failed": failed,
            "pending": pending,
        },
        "provider": {
            "name": notification_service.get_provider_name(),
            "enabled": notification_service.is_enabled(),
        },
        "last_successful_send": {
            "recipient": last_sent.recipient if last_sent else None,
            "subject": last_sent.subject if last_sent else None,
            "message_id": last_sent.message_id if last_sent else None,
            "sent_at": last_sent.sent_at.isoformat() if last_sent and last_sent.sent_at else None,
        },
        "last_failure": {
            "recipient": last_failed.recipient if last_failed else None,
            "error": last_failed.error_message if last_failed else None,
            "sent_at": last_failed.sent_at.isoformat() if last_failed and last_failed.sent_at else None,
        },
    }


# ─── Email Logs ───────────────────────────────────────────────────────────────

@router.get("/logs")
def get_email_logs(
    limit: int = Query(50, le=200),
    status: Optional[str] = Query(None),
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Get email delivery logs with optional status filter."""
    query = db.query(NotificationLog).filter(NotificationLog.channel == "Email")
    if status:
        query = query.filter(NotificationLog.status == status)
    logs = query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()

    return [
        {
            "id": log.id,
            "recipient": log.recipient,
            "subject": log.subject,
            "status": log.status,
            "message_id": log.message_id,
            "provider": log.provider,
            "http_status": log.http_status,
            "retry_count": log.retry_count,
            "error": log.error_message,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
        }
        for log in logs
    ]


# ─── Retry ────────────────────────────────────────────────────────────────────

@router.post("/retry/{log_id}")
def retry_failed_email(
    log_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Retry a failed email delivery."""
    log = db.query(NotificationLog).filter(
        NotificationLog.id == log_id,
        NotificationLog.channel == "Email",
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Email log not found")
    if log.status == "sent":
        raise HTTPException(status_code=400, detail="Email was already sent successfully")

    result = notification_service.dispatch_email(
        to_email=log.recipient,
        subject=log.subject or "Retry - TenderIQ AI",
        html_content=log.content,
        retry=False,
    )

    log.status = "sent" if result.success else "failed"
    log.message_id = result.message_id or log.message_id
    log.provider = result.provider
    log.http_status = result.http_status
    log.provider_response = result.provider_response
    log.retry_count = (log.retry_count or 0) + 1
    log.error_message = result.error
    db.commit()

    return {
        "success": result.success,
        "log_id": log.id,
        "message_id": result.message_id,
        "retry_count": log.retry_count,
        "error": result.error,
    }


# ─── Cancel ───────────────────────────────────────────────────────────────────

@router.post("/cancel/{log_id}")
def cancel_pending_email(
    log_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db),
):
    """Cancel a pending email."""
    log = db.query(NotificationLog).filter(
        NotificationLog.id == log_id,
        NotificationLog.channel == "Email",
        NotificationLog.status == "pending",
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Pending email not found")

    log.status = "cancelled"
    db.commit()
    return {"success": True, "log_id": log.id, "status": "cancelled"}
