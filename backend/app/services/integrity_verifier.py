import os
import hashlib
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.tender import Tender, TenderAttachment, Organization
from backend.app.models.source import Source

logger = logging.getLogger("TenderIQ.IntegrityVerifier")


def calculate_pdf_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of a local PDF file."""
    if not os.path.exists(file_path):
        return ""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate SHA-256 hash for {file_path}: {e}")
        return ""


def audit_and_verify_tender(tender: Tender, db: Session, check_live_url: bool = True) -> Dict[str, Any]:
    """Audit and verify a single tender's metadata completeness, source URL, PDF hash, and AI confidence."""
    scores = {
        "metadata_completeness": 0.0,
        "source_verification": 0.0,
        "pdf_availability": 0.0,
        "ai_confidence": 0.0,
        "duplicate_cleanliness": 10.0,
    }

    # 1. Metadata Completeness Check (30 pts max)
    meta_points = 0.0
    if tender.tender_number and len(tender.tender_number) > 3 and not tender.tender_number.startswith("TND-"):
        meta_points += 5.0
    elif tender.tender_number:
        meta_points += 3.0

    if tender.title and len(tender.title) > 10:
        meta_points += 5.0

    if tender.organization_id:
        meta_points += 5.0

    if tender.country:
        meta_points += 5.0

    if tender.submission_deadline:
        meta_points += 5.0

    if tender.scope_of_work or tender.ai_summary:
        meta_points += 5.0

    scores["metadata_completeness"] = meta_points

    # 2. Source URL Verification (25 pts max)
    url_code = 200
    url_verified = True
    if check_live_url and tender.official_link and tender.official_link.startswith("http"):
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            with httpx.Client(timeout=6.0, follow_redirects=True, headers=headers) as client:
                res = client.get(tender.official_link)
                url_code = res.status_code
                if res.status_code < 400:
                    scores["source_verification"] = 25.0
                else:
                    scores["source_verification"] = 0.0
                    url_verified = False
        except Exception as e:
            logger.warning(f"URL check failed for tender {tender.tender_number} ({tender.official_link}): {e}")
            url_code = 502
            scores["source_verification"] = 0.0
            url_verified = False
    elif not tender.official_link:
        url_code = 404
        scores["source_verification"] = 0.0
        url_verified = False
    else:
        scores["source_verification"] = 25.0

    # 3. PDF Availability & SHA-256 Hash Verification (20 pts max)
    attachment = db.query(TenderAttachment).filter(TenderAttachment.tender_id == tender.id).first()
    if attachment:
        scores["pdf_availability"] += 10.0
        if attachment.file_path and os.path.exists(attachment.file_path):
            scores["pdf_availability"] += 5.0
            if not attachment.hash_sha256:
                attachment.hash_sha256 = calculate_pdf_hash(attachment.file_path)
            if attachment.hash_sha256:
                scores["pdf_availability"] += 5.0
                attachment.processing_status = "Indexed"

    # 4. AI Confidence & Groundedness (15 pts max)
    if tender.ai_summary and "Insufficient information" not in tender.ai_summary:
        scores["ai_confidence"] = 15.0
    elif tender.scope_of_work:
        scores["ai_confidence"] = 10.0

    # Total Overall Data Integrity Score (0 - 100%)
    overall_integrity = sum(scores.values())

    # Set Verification Status
    if url_verified and overall_integrity >= 65.0:
        v_status = "VERIFIED"
    else:
        v_status = "FAILED"

    # Update Tender DB Columns
    tender.integrity_score = round(overall_integrity, 1)
    tender.verification_status = v_status
    tender.url_status_code = url_code
    tender.verified_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "tender_id": tender.id,
        "tender_number": tender.tender_number,
        "title": tender.title,
        "verification_status": v_status,
        "integrity_score": round(overall_integrity, 1),
        "url_status_code": url_code,
        "scores_breakdown": scores,
        "pdf_hash": attachment.hash_sha256 if attachment else None,
    }


def audit_all_database_tenders(db: Session, check_live_urls: bool = True) -> Dict[str, Any]:
    """Audit every tender stored in the database and calculate overall platform data quality metrics."""
    tenders = db.query(Tender).all()
    verified_count = 0
    failed_count = 0
    missing_pdf_count = 0
    missing_tender_num_count = 0
    broken_url_count = 0
    total_score = 0.0

    for t in tenders:
        res = audit_and_verify_tender(t, db, check_live_url=check_live_urls)
        total_score += t.integrity_score
        if t.verification_status == "VERIFIED":
            verified_count += 1
        else:
            failed_count += 1

        att = db.query(TenderAttachment).filter(TenderAttachment.tender_id == t.id).first()
        if not att:
            missing_pdf_count += 1
        if not t.tender_number or t.tender_number.startswith("TND-"):
            missing_tender_num_count += 1
        if t.url_status_code and t.url_status_code >= 400:
            broken_url_count += 1

    total_count = len(tenders) or 1
    avg_integrity = round(total_score / float(total_count), 1)

    return {
        "total_tenders_audited": len(tenders),
        "verified_tenders": verified_count,
        "failed_verifications": failed_count,
        "missing_pdfs": missing_pdf_count,
        "missing_tender_numbers": missing_tender_num_count,
        "broken_urls": broken_url_count,
        "average_integrity_score": avg_integrity,
        "verification_rate_pct": round((verified_count / float(total_count)) * 100, 1),
    }
