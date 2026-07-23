from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.tender import Tender
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.ai import AILog

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/kpis")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    total_opportunities = db.query(Tender).count()
    high_priority = db.query(Tender).filter(Tender.overall_match_score >= 90.0).count()
    closing_soon = db.query(Tender).filter(Tender.status == "Active").count()
    pipeline_value = db.query(func.sum(Tender.budget)).filter(Tender.status == "Active").scalar() or 0.0

    by_category = {
        "government": db.query(Tender).filter(Tender.sector == "Government").count(),
        "corporate": db.query(Tender).filter(Tender.sector == "Corporate").count(),
        "universities": db.query(Tender).filter(Tender.sector == "Education").count(),
        "ngos": db.query(Tender).filter(Tender.sector == "NGOs").count(),
        "international": db.query(Tender).filter(Tender.country == "International").count(),
    }

    return {
        "total_opportunities": total_opportunities,
        "high_priority": high_priority,
        "closing_soon": closing_soon,
        "pipeline_value_inr": pipeline_value,
        "categories": by_category
    }

@router.get("/recent-crawls")
def get_recent_crawls(db: Session = Depends(get_db)):
    crawls = db.query(CrawlHistory).order_by(CrawlHistory.start_time.desc()).limit(5).all()
    result = []
    for c in crawls:
        src = db.query(Source).filter(Source.id == c.source_id).first()
        result.append({
            "id": c.id,
            "source_name": src.name if src else "Unknown Source",
            "start_time": c.start_time,
            "duration_seconds": c.duration_seconds,
            "opportunities_found": c.opportunities_found,
            "status": c.status
        })
    return result

@router.get("/recent-ai")
def get_recent_ai_analyses(db: Session = Depends(get_db)):
    tenders = db.query(Tender).filter(Tender.ai_summary.isnot(None)).order_by(Tender.updated_at.desc()).limit(5).all()
    return [
        {
            "id": t.id,
            "tender_number": t.tender_number,
            "title": t.title,
            "overall_match_score": t.overall_match_score,
            "bid_recommendation": t.bid_recommendation,
            "winning_probability": t.winning_probability,
            "ai_summary": t.ai_summary
        }
        for t in tenders
    ]
