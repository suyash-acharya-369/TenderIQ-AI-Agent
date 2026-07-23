from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.database.session import get_db
from backend.app.models.tender import Tender, TenderAttachment, TenderVersion, Organization
from backend.app.models.keyword import KeywordGroup
from backend.app.schemas.tender import TenderResponse
from backend.app.ai.router import get_ai_provider
from backend.app.ai.matcher import compute_tender_match_scores

router = APIRouter(prefix="/tenders", tags=["Tenders"])

@router.get("", response_model=List[TenderResponse])
def search_tenders(
    q: Optional[str] = Query(None, description="Global / Semantic Search query"),
    country: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    min_budget: Optional[float] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    query = db.query(Tender)

    if q:
        search_filter = or_(
            Tender.title.ilike(f"%{q}%"),
            Tender.tender_number.ilike(f"%{q}%"),
            Tender.scope_of_work.ilike(f"%{q}%"),
            Tender.ai_summary.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)

    if country:
        query = query.filter(Tender.country.ilike(f"%{country}%"))
    if sector:
        query = query.filter(Tender.sector.ilike(f"%{sector}%"))
    if status:
        query = query.filter(Tender.status == status)
    if min_score:
        query = query.filter(Tender.overall_match_score >= min_score)
    if min_budget:
        query = query.filter(Tender.budget >= min_budget)

    tenders = query.order_by(Tender.overall_match_score.desc(), Tender.created_at.desc()).offset(offset).limit(limit).all()
    return [TenderResponse.from_orm(t) for t in tenders]

@router.get("/{tender_id}", response_model=TenderResponse)
def get_tender_detail(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return TenderResponse.from_orm(tender)

@router.post("/{tender_id}/run-ai", response_model=TenderResponse)
def run_ai_analysis_on_tender(tender_id: int, db: Session = Depends(get_db)):
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
    tender.estimated_team = summary.get("estimated_team", "1 ID Lead, 3 Developers")
    tender.estimated_duration = summary.get("estimated_duration", "6 Months")

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
    return TenderResponse.from_orm(tender)
