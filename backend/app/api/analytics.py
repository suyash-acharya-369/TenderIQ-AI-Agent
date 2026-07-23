import csv
import io
from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.tender import Tender

router = APIRouter(prefix="/analytics", tags=["Analytics & Reports"])

@router.get("/export/csv")
def export_tenders_csv(db: Session = Depends(get_db)):
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
