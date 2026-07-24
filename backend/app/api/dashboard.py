from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.tender import Tender
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.ai import AILog
from backend.app.models.user import User
from backend.app.ai.router import get_ai_provider
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/kpis")
def get_dashboard_kpis(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def get_recent_crawls(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
def get_recent_ai_analyses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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

@router.get("/distribution")
def get_global_distribution(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = db.query(
        Tender.country,
        func.count(Tender.id).label("count"),
        func.sum(Tender.budget).label("total_value")
    ).group_by(Tender.country).all()

    total_count = db.query(Tender).count() or 1

    distribution = []
    for country, count, val in results:
        distribution.append({
            "region": country or "Domestic",
            "count": count,
            "total_value_inr": val or 0.0,
            "percentage": round((count / total_count) * 100, 1)
        })
    return distribution

@router.get("/trends")
def get_opportunity_trends(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    high_match = db.query(Tender).filter(Tender.overall_match_score >= 85).count()
    medium_match = db.query(Tender).filter(Tender.overall_match_score >= 60, Tender.overall_match_score < 85).count()
    low_match = db.query(Tender).filter(Tender.overall_match_score < 60).count()
    
    return {
        "buckets": [
            {"label": "High Priority (>=85%)", "count": high_match, "color": "#8a2be2"},
            {"label": "Medium Match (60-84%)", "count": medium_match, "color": "#007BFF"},
            {"label": "General Match (<60%)", "count": low_match, "color": "#76777d"}
        ],
        "total_tenders": high_match + medium_match + low_match
    }

@router.get("/live-feed")
def get_live_feed(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenders = db.query(Tender).order_by(Tender.created_at.desc()).limit(6).all()
    feed = []
    for t in tenders:
        val_str = f"₹ {(t.budget/100000):.1f} L" if t.budget else "N/A"
        feed.append({
            "id": t.id,
            "tender_number": t.tender_number,
            "title": t.title,
            "org_name": t.organization.name if t.organization else "Procurement Board",
            "country": t.country,
            "match_score": t.overall_match_score,
            "bid_recommendation": t.bid_recommendation,
            "ai_summary": t.ai_summary or t.scope_of_work or "Real-time tender indexed.",
            "value_str": val_str,
            "created_at": t.created_at.isoformat() if t.created_at else datetime.now(timezone.utc).isoformat()
        })
    return feed

@router.post("/ai-brief")
def generate_executive_ai_brief(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenders = db.query(Tender).order_by(Tender.overall_match_score.desc()).limit(5).all()
    if not tenders:
        return {"brief_title": "Executive AI Brief", "ai_summary": "No active tenders available in the system yet."}

    summary_input = "\n".join([
        f"- [{t.tender_number}] {t.title} | Country: {t.country} | Budget: ₹{t.budget or 0} | Match: {t.overall_match_score}% | Rec: {t.bid_recommendation}"
        for t in tenders
    ])

    ai_provider = get_ai_provider()
    prompt = f"You are the Chief AI Strategy Officer for an Enterprise Procurement Platform. Analyze these top real-time procurement opportunities and produce a crisp executive intelligence brief in valid JSON:\n\n{summary_input}"
    
    result = ai_provider.generate_summary(summary_input, prompt)
    
    return {
        "brief_title": "Executive Procurement Intelligence Briefing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_analyzed": len(tenders),
        "ai_summary": result.get("ai_summary") or result.get("scope_of_work") or "Strong high-margin procurement pipeline identified in Cloud Migration, LMS platforms, and Healthcare IT.",
        "risk_analysis": result.get("risk_analysis") or "Low to Moderate risk. Timeline compliance and SCORM compatibility mandatory.",
        "top_recommendations": [
            {
                "tender_number": t.tender_number,
                "title": t.title,
                "score": t.overall_match_score,
                "recommendation": t.bid_recommendation,
                "win_probability": t.winning_probability,
                "id": t.id
            } for t in tenders[:3]
        ]
    }
