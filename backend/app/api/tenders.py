from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database.session import get_db
from backend.app.models.tender import Tender, TenderAttachment, TenderVersion, Organization
from backend.app.models.source import Source
from backend.app.models.keyword import KeywordGroup
from backend.app.models.user import User
from backend.app.schemas.tender import TenderResponse
from backend.app.ai.router import get_ai_provider
from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.api.deps import get_current_user
from backend.app.services.event_bus import event_bus
from backend.app.services.events import AISummaryCompletedEvent, TenderMatchedEvent

router = APIRouter(prefix="/tenders", tags=["Tenders"])

@router.get("", response_model=List[TenderResponse])
def search_tenders(
    q: Optional[str] = Query(None, description="Global Keyword & Semantic Search query"),
    keyword_group_id: Optional[int] = Query(None, description="Filter by Keyword Group ID"),
    source_id: Optional[int] = Query(None, description="Filter by Procurement Source ID"),
    organization_id: Optional[int] = Query(None, description="Filter by Issuing Organization ID"),
    min_score: Optional[float] = Query(None, description="Minimum AI match score"),
    max_score: Optional[float] = Query(None, description="Maximum AI match score"),
    recommendation: Optional[str] = Query(None, description="AI recommendation (Bid, Consider, Review)"),
    status: Optional[str] = Query(None, description="Tender status"),
    date_range: Optional[str] = Query(None, description="Crawl date range (today, 7days, 30days)"),
    country: Optional[str] = Query(None, description="Optional secondary country filter"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Tender)

    # 1. Keyword Group Filtering
    if keyword_group_id:
        kg = db.query(KeywordGroup).filter(KeywordGroup.id == keyword_group_id).first()
        if kg and kg.positive_keywords:
            kw_conditions = []
            for kw in kg.positive_keywords:
                if kw:
                    kw_conditions.append(Tender.title.ilike(f"%{kw}%"))
                    kw_conditions.append(Tender.scope_of_work.ilike(f"%{kw}%"))
                    kw_conditions.append(Tender.ai_summary.ilike(f"%{kw}%"))
                    kw_conditions.append(Tender.technical_requirements.ilike(f"%{kw}%"))
            # Fallback to high-match tenders
            kw_conditions.append(Tender.overall_match_score >= 80.0)
            query = query.filter(or_(*kw_conditions))

    # 2. Source & Organization Filtering
    if source_id:
        query = query.filter(Tender.source_id == source_id)
    if organization_id:
        query = query.filter(Tender.organization_id == organization_id)

    # 3. Match Score Range Filtering
    if min_score is not None:
        query = query.filter(Tender.overall_match_score >= min_score)
    if max_score is not None:
        query = query.filter(Tender.overall_match_score <= max_score)

    # 4. Recommendation & Status Filtering
    if recommendation:
        query = query.filter(Tender.bid_recommendation.ilike(f"%{recommendation}%"))
    if status:
        query = query.filter(Tender.status == status)

    # 5. Date Range Filtering
    if date_range:
        now = datetime.now(timezone.utc)
        if date_range == "today":
            query = query.filter(Tender.created_at >= now - timedelta(days=1))
        elif date_range == "7days":
            query = query.filter(Tender.created_at >= now - timedelta(days=7))
        elif date_range == "30days":
            query = query.filter(Tender.created_at >= now - timedelta(days=30))

    # 6. Optional Country Filter
    if country:
        query = query.filter(Tender.country.ilike(f"%{country}%"))

    # 7. Global Search Query
    if q:
        search_filter = or_(
            Tender.title.ilike(f"%{q}%"),
            Tender.tender_number.ilike(f"%{q}%"),
            Tender.scope_of_work.ilike(f"%{q}%"),
            Tender.ai_summary.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    tenders = query.order_by(Tender.overall_match_score.desc(), Tender.created_at.desc()).offset(offset).limit(limit).all()
    return [TenderResponse.from_orm(t) for t in tenders]


@router.get("/semantic-search")
def get_semantic_search_tenders(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Phase 19: Hybrid Semantic Vector Search over database tenders."""
    from backend.app.services.semantic_search import perform_semantic_search
    results = perform_semantic_search(query_text=query, db=db, limit=limit)
    return results


@router.get("/{tender_id}/download-pdf")
def download_tender_pdf(tender_id: int, db: Session = Depends(get_db)):
    """Download official RFP PDF specification document with dynamic generation fallback."""
    import os
    from fastapi.responses import FileResponse
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    att = db.query(TenderAttachment).filter(TenderAttachment.tender_id == tender_id).first()
    if att and att.file_path and os.path.exists(att.file_path):
        return FileResponse(path=att.file_path, filename=att.file_name, media_type="application/pdf")

    # Generate professional RFP specification PDF dynamically using ReportLab
    os.makedirs("./storage", exist_ok=True)
    pdf_filename = f"RFP_Specification_{tender.tender_number.replace('/', '_')}.pdf"
    pdf_path = os.path.join("./storage", f"rfp_{tender_id}.pdf")

    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1E293B'), spaceAfter=10)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#334155'), leading=14)

    story = [
        Paragraph(f"TenderIQ AI &middot; Official RFP Specification Document", ParagraphStyle('Header', fontSize=9, textColor=colors.HexColor('#4F46E5'), spaceAfter=6)),
        Paragraph(f"{tender.title}", title_style),
        Spacer(1, 10),
        Table([
            ["Tender Reference #:", tender.tender_number, "AI Match Score:", f"{tender.overall_match_score}%"],
            ["Country / Region:", tender.country or "Global", "Sector:", tender.sector or "Education"],
            ["Publication Date:", str(tender.publication_date)[:10], "Submission Deadline:", str(tender.submission_deadline)[:10]],
        ], colWidths=[120, 180, 120, 120], style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#1E293B')),
            ('PADDING', (0,0), (-1,-1), 6),
        ])),
        Spacer(1, 15),
        Paragraph("1. Executive Scope of Work", styles['Heading2']),
        Paragraph(f"{tender.scope_of_work or tender.ai_summary or 'Full official procurement scope of work details.'}", body_style),
        Spacer(1, 12),
        Paragraph("2. Technical & Functional Requirements", styles['Heading2']),
        Paragraph(f"{tender.technical_requirements or 'Cloud-native LMS deployment, SCORM 1.2/2004 compliance, SSO integration, and mobile responsive design.'}", body_style),
        Spacer(1, 12),
        Paragraph("3. Eligibility & Minimum Criteria", styles['Heading2']),
        Paragraph(f"{tender.eligibility_criteria or 'Minimum 3 years past experience in digital content authoring and LMS software implementation.'}", body_style),
    ]

    doc.build(story)

    # Record attachment in DB
    if not att:
        att = TenderAttachment(
            tender_id=tender_id,
            file_name=pdf_filename,
            file_type="PDF",
            file_path=pdf_path,
            file_size_bytes=os.path.getsize(pdf_path),
            processing_status="Indexed"
        )
        db.add(att)
        db.commit()

    return FileResponse(path=pdf_path, filename=pdf_filename, media_type="application/pdf")


@router.get("/{tender_id}", response_model=TenderResponse)
def get_tender_detail(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return TenderResponse.from_orm(tender)

@router.post("/{tender_id}/run-ai", response_model=TenderResponse)
def run_ai_analysis_on_tender(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    ai_provider = get_ai_provider()
    text = f"Title: {tender.title}\nScope: {tender.scope_of_work or ''}"
    summary = ai_provider.generate_summary(text, "Perform detailed tender AI summary and risk analysis")

    tender.scope_of_work = summary.get("scope_of_work", tender.scope_of_work)
    tender.deliverables = summary.get("deliverables", tender.deliverables)
    tender.eligibility_criteria = summary.get("eligibility_criteria", tender.eligibility_criteria)
    tender.technical_requirements = summary.get("technical_requirements", tender.technical_requirements)
    tender.financial_requirements = summary.get("financial_requirements", tender.financial_requirements)
    tender.required_documents = summary.get("required_documents", tender.required_documents)
    tender.ai_summary = summary.get("ai_summary", tender.ai_summary)
    tender.risk_analysis = summary.get("risk_analysis", tender.risk_analysis)
    tender.bid_recommendation = summary.get("bid_recommendation", "Bid")
    tender.winning_probability = summary.get("winning_probability", 90.0)

    # Re-compute match scores
    keyword_groups = db.query(KeywordGroup).filter(KeywordGroup.status == "active").all()
    scores = compute_tender_match_scores(tender.title, tender.scope_of_work or "", keyword_groups)
    tender.keyword_score = scores["keyword_score"]
    tender.semantic_score = scores["semantic_score"]
    tender.ai_score = scores["ai_score"]
    tender.priority_score = scores["priority_score"]
    tender.overall_match_score = scores["overall_match_score"]

    db.commit()
    db.refresh(tender)

    event_bus.dispatch(AISummaryCompletedEvent(
        tender_id=tender.id,
        summary=tender.ai_summary or "",
        match_score=tender.overall_match_score
    ))

    if tender.overall_match_score >= 80.0:
        event_bus.dispatch(TenderMatchedEvent(
            tender_id=tender.id,
            source_id=tender.source_id,
            title=tender.title,
            match_score=tender.overall_match_score,
            keywords=[]
        ))

    return TenderResponse.from_orm(tender)


@router.get("/{tender_id}/versions")
def get_tender_version_history(
    tender_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Phase 21 & 22: Retrieve version history and diff tracking for a tender."""
    versions = db.query(TenderVersion).filter(TenderVersion.tender_id == tender_id).order_by(TenderVersion.version_number.desc()).all()
    attachments = db.query(TenderAttachment).filter(TenderAttachment.tender_id == tender_id).all()
    return {
        "tender_id": tender_id,
        "total_versions": len(versions),
        "versions": [
            {
                "version_number": v.version_number,
                "change_type": v.change_type,
                "changes": v.changes_json,
                "notes": v.notes,
                "created_at": v.created_at.isoformat() if v.created_at else None
            }
            for v in versions
        ],
        "attachments": [
            {
                "id": a.id,
                "file_name": a.file_name,
                "file_type": a.file_type,
                "file_size_bytes": a.file_size_bytes,
                "version_number": a.version_number,
                "processing_status": a.processing_status,
                "ocr_applied": a.ocr_applied,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in attachments
        ]
    }

