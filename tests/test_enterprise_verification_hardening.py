import os
import sys
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import SessionLocal
from backend.app.models.tender import Tender, TenderAttachment, Organization
from backend.app.models.source import Source, CrawlReplayLog
from backend.app.services.integrity_verifier import (
    audit_and_verify_tender,
    audit_all_database_tenders,
    generate_ai_citations,
    generate_keyword_evidence,
    detect_and_fuse_duplicates,
    calculate_source_trust_score,
    validate_tender_for_email
)
from backend.app.crawler.engine import _get_connector_instance
from backend.app.connectors.gem_connector import GeMConnector
from backend.app.connectors.worldbank_connector import WorldBankConnector
from backend.app.connectors.ungm_connector import UNGMConnector
from backend.app.connectors.adb_connector import ADBConnector
from backend.app.connectors.unicef_connector import UNICEFConnector

client = TestClient(app)


def get_admin_headers():
    db = SessionLocal()
    from backend.app.models.user import User
    from backend.app.utils.security import hash_password
    from backend.app.utils.jwt import create_access_token
    admin = db.query(User).filter(User.email == "admin@tenderiq.ai").first()
    if not admin:
        admin = User(
            id=999,
            email="admin@tenderiq.ai",
            hashed_password=hash_password("adminpassword123"),
            full_name="System Admin",
            role="Administrator",
            is_active=True
        )
        db.add(admin)
        db.commit()

    # Ensure tender 1 exists
    t1 = db.query(Tender).filter(Tender.id == 1).first()
    if not t1:
        t1 = Tender(
            id=1,
            tender_number="RFP-UNESCO-2024-ED01",
            title="Development of Global Digital Learning Platform & SCORM E-Content",
            official_link="https://www.ungm.org/Public/Notice",
            verification_status="VERIFIED",
            moderation_status="VERIFIED",
            integrity_score=96.0
        )
        db.add(t1)
        db.commit()
    db.close()

    token = create_access_token({"sub": str(admin.id), "role": "Administrator", "user_id": admin.id})
    return {"Authorization": f"Bearer {token}"}


def test_requirement_1_source_specific_connectors():
    """Requirement 1: Verify source-specific connectors for GeM, WB, UNGM, ADB, UNICEF."""
    gem = _get_connector_instance("gem")
    wb = _get_connector_instance("worldbank")
    ungm = _get_connector_instance("ungm")
    adb = _get_connector_instance("adb")
    unicef = _get_connector_instance("unicef")

    assert isinstance(gem, GeMConnector)
    assert isinstance(wb, WorldBankConnector)
    assert isinstance(ungm, UNGMConnector)
    assert isinstance(adb, ADBConnector)
    assert isinstance(unicef, UNICEFConnector)

    gem_data = gem.crawl("https://gem.gov.in")
    assert len(gem_data) > 0
    assert "GEM/" in gem_data[0]["tender_number"]


def test_requirement_2_and_3_multi_document_and_pdf_hashes():
    """Requirement 2 & 3: Multi-document collection and SHA-256 hash calculation."""
    db = SessionLocal()
    tenders = db.query(Tender).all()
    assert len(tenders) > 0

    for t in tenders:
        att = db.query(TenderAttachment).filter(TenderAttachment.tender_id == t.id).first()
        if att and att.file_path and os.path.exists(att.file_path):
            assert len(att.hash_sha256) == 64  # Valid SHA-256 hex string length
    db.close()


def test_requirement_6_and_7_citations_and_keyword_evidence():
    """Requirement 6 & 7: AI Citations and Keyword Evidence Snippets."""
    db = SessionLocal()
    t = db.query(Tender).first()
    assert t is not None

    citations = generate_ai_citations(t)
    assert "Submission Deadline" in citations
    assert "Page" in citations["Submission Deadline"]

    evidence = generate_keyword_evidence(t, ["LMS", "SCORM", "EdTech"])
    assert len(evidence) > 0
    assert "matching_sentence" in evidence[0]
    assert "page" in evidence[0]
    db.close()


def test_requirement_5_source_trust_score():
    """Requirement 5: Calculate 5-Star Source Trust Score Rating."""
    db = SessionLocal()
    src = db.query(Source).first()
    if not src:
        src = Source(name="GeM Test Source", website_url="https://gem.gov.in", health_status="Healthy")
        db.add(src)
        db.commit()

    score = calculate_source_trust_score(src, db)
    assert 1.0 <= score <= 5.0
    db.close()


def test_requirement_9_pre_send_qa_guard():
    """Requirement 9: Pre-Send Quality Assurance Guard validation."""
    db = SessionLocal()
    verified_t = db.query(Tender).filter(Tender.verification_status == "VERIFIED").first()
    if verified_t:
        qa_res = validate_tender_for_email(verified_t)
        assert qa_res["is_valid"] is True
    db.close()


def test_requirement_8_and_11_crawler_quality_dashboard_and_inspector():
    """Requirement 8 & 11: Crawler Quality Dashboard and Tender Inspector Endpoints."""
    headers = get_admin_headers()
    assert "Authorization" in headers

    # Crawler Quality Dashboard
    res_dash = client.get("/api/v1/admin/crawler-quality-dashboard", headers=headers)
    assert res_dash.status_code == 200
    assert "sources" in res_dash.json()

    # Tender Inspector Details
    res_insp = client.get("/api/v1/admin/tenders/1/inspector", headers=headers)
    assert res_insp.status_code == 200
    insp_data = res_insp.json()
    assert "citations" in insp_data
    assert "keyword_evidence" in insp_data
    assert "replay_trace" in insp_data


def test_requirement_10_moderation_state_machine():
    """Requirement 10: Human Moderation State Machine transition."""
    headers = get_admin_headers()
    assert "Authorization" in headers

    res = client.post("/api/v1/admin/tenders/1/moderate?status=VERIFIED", headers=headers)
    assert res.status_code == 200
    assert res.json()["moderation_status"] == "VERIFIED"
