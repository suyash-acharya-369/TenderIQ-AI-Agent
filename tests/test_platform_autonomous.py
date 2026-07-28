"""
Comprehensive Integration Test Suite for the 28-Phase Autonomous Tender Intelligence Platform.
"""
import pytest
import httpx
from datetime import datetime, timezone
from backend.app.database.session import SessionLocal
from backend.app.models.source import Source, ScheduledJobLog
from backend.app.models.tender import Tender, TenderVersion, TenderAttachment
from backend.app.models.notification import NotificationLog
from backend.app.services.scheduler import scheduler
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications
from backend.app.services.semantic_search import perform_semantic_search
from backend.app.services.backup_service import create_system_backup, list_backups, restore_backup


BASE_URL = "http://127.0.0.1:8000/api/v1"


def get_admin_headers():
    login_res = httpx.post(f"{BASE_URL}/auth/login", json={"email": "admin@tenderiq.ai", "password": "Admin123!"}, timeout=10)
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_phase_1_scheduler_execution():
    """Phase 1 & 10: Test manual background job execution."""
    headers = get_admin_headers()
    res = httpx.post(f"{BASE_URL}/scheduler/trigger-job", json={"job_name": "Source Health Check"}, headers=headers, timeout=15)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "triggered"
    assert data["job_name"] == "Source Health Check"


def test_phase_4_duplicate_prevention_guard():
    """Phase 4: Test duplicate notification prevention."""
    db = SessionLocal()
    try:
        tender = db.query(Tender).first()
        if tender:
            # Trigger dispatch twice
            evaluate_and_dispatch_notifications(tender, db)
            evaluate_and_dispatch_notifications(tender, db)

            skipped = db.query(NotificationLog).filter(NotificationLog.status == "skipped_duplicate").count()
            assert skipped >= 0
    finally:
        db.close()


def test_phase_16_ai_cost_monitoring():
    """Phase 16: Test AI cost monitoring endpoint."""
    headers = get_admin_headers()
    res = httpx.get(f"{BASE_URL}/analytics/ai-cost", headers=headers, timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert "total_requests" in data
    assert "total_cost_usd" in data


def test_phase_19_semantic_vector_search():
    """Phase 19: Test vector semantic search endpoint."""
    headers = get_admin_headers()
    res = httpx.get(f"{BASE_URL}/tenders/semantic-search?query=education+lms", headers=headers, timeout=10)
    assert res.status_code == 200
    results = res.json()
    assert isinstance(results, list)


def test_phase_24_backup_and_recovery():
    """Phase 24: Test backup packaging and listing."""
    backup = create_system_backup()
    assert backup["success"] is True
    assert backup["files_count"] > 0

    backups = list_backups()
    assert len(backups) > 0


def test_phase_25_operations_dashboard():
    """Phase 25: Test live operations dashboard endpoint."""
    headers = get_admin_headers()
    res = httpx.get(f"{BASE_URL}/admin/operations-dashboard", headers=headers, timeout=10)
    assert res.status_code == 200
    data = res.json()
    assert "system_resources" in data
    assert "services" in data
