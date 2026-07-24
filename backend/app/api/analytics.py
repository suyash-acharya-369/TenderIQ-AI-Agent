import csv
import io
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database.session import get_db
from backend.app.models.tender import Tender
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.user import User
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

@router.get("/export/csv")
def export_tenders_csv(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenders = db.query(Tender).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Tender Number", "Title", "Country", "Sector", "Budget", "Currency",
        "Overall Score", "Status", "Bid Recommendation", "Deadline"
    ])

    for t in tenders:
        writer.writerow([
            t.id, t.tender_number, t.title, t.country, t.sector, t.budget, t.currency,
            t.overall_match_score, t.status, t.bid_recommendation, t.submission_deadline
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=TenderIQ_Report.csv"}
    )

@router.get("/export/excel")
def export_tenders_excel(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tender Intelligence"

    headers = ["ID", "Tender Number", "Title", "Country", "Sector", "Budget (INR)", "Match Score", "Recommendation", "Deadline"]
    ws.append(headers)

    tenders = db.query(Tender).all()
    for t in tenders:
        ws.append([
            t.id, t.tender_number, t.title, t.country, t.sector, t.budget or 0,
            t.overall_match_score, t.bid_recommendation,
            t.submission_deadline.strftime("%Y-%m-%d") if t.submission_deadline else "N/A"
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=TenderIQ_Intelligence_Report.xlsx"}
    )

@router.get("/export/pdf")
def export_tenders_pdf(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "TenderIQ AI — Executive Opportunity Intelligence Report")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, f"Generated on: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | Requested by: {current_user.email}")
    
    p.line(50, height - 80, width - 50, height - 80)

    tenders = db.query(Tender).order_by(Tender.overall_match_score.desc()).limit(15).all()
    y = height - 110

    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Top High-Priority Opportunities:")
    y -= 25

    for t in tenders:
        if y < 60:
            p.showPage()
            y = height - 50

        p.setFont("Helvetica-Bold", 10)
        p.drawString(50, y, f"[{t.tender_number}] {t.title[:65]}...")
        p.setFont("Helvetica", 9)
        p.drawString(450, y, f"Score: {t.overall_match_score}% | Rec: {t.bid_recommendation}")
        y -= 15
        p.drawString(60, y, f"Country: {t.country} | Sector: {t.sector} | Budget: ₹ {t.budget:,.0f}" if t.budget else f"Country: {t.country} | Sector: {t.sector}")
        y -= 20

    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=TenderIQ_Executive_Brief.pdf"}
    )

@router.get("/summary-stats")
def get_analytics_summary_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_tenders = db.query(Tender).count()
    active_tenders = db.query(Tender).filter(Tender.status == "Active").count()
    avg_score = db.query(func.avg(Tender.overall_match_score)).scalar() or 0.0
    total_sources = db.query(Source).count()

    by_sector = db.query(Tender.sector, func.count(Tender.id)).group_by(Tender.sector).all()

    return {
        "total_tenders": total_tenders,
        "active_tenders": active_tenders,
        "avg_match_score": round(avg_score, 1),
        "total_sources": total_sources,
        "sector_breakdown": [{"sector": s or "General", "count": c} for s, c in by_sector]
    }
