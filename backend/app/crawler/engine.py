import os
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.tender import Tender, Organization, TenderVersion, TenderAttachment
from backend.app.models.keyword import KeywordGroup
from backend.app.services.event_bus import event_bus
from backend.app.services.events import (
    CrawlStartedEvent, CrawlCompletedEvent, CrawlFailedEvent,
    TenderDiscoveredEvent, TenderMatchedEvent, AISummaryCompletedEvent
)
from backend.app.connectors.generic import GenericConnector
from backend.app.connectors.rss import RSSConnector
from backend.app.connectors.api_connector import APIConnector
from backend.app.connectors.playwright_connector import PlaywrightConnector
from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.ai.router import get_ai_provider
from backend.app.utils.document_processor import extract_text_from_pdf
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications

logger = logging.getLogger("TenderIQ.CrawlerEngine")

def _get_connector_instance(connector_type: str):
    ctype = (connector_type or "Public").lower()
    if "rss" in ctype:
        return RSSConnector()
    elif "api" in ctype:
        return APIConnector()
    elif "playwright" in ctype:
        return PlaywrightConnector()
    return GenericConnector()

def run_source_crawl(source_id: int, db: Session) -> Dict[str, Any]:
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return {"status": "error", "message": "Source not found"}

    start_time = datetime.now(timezone.utc)
    
    # Create CrawlHistory record
    history = CrawlHistory(
        source_id=source.id,
        start_time=start_time,
        status="running"
    )
    db.add(history)
    db.commit()

    event_bus.dispatch(CrawlStartedEvent(source_id=source.id))

    try:
        connector = _get_connector_instance(source.connector_type)
        target_url = source.search_url or source.website_url
        opportunities = connector.crawl(
            source_url=target_url,
            tender_selector=source.tender_selector,
            pdf_selector=source.pdf_selector,
            pagination_selector=source.pagination_selector
        )
        
        keyword_groups = db.query(KeywordGroup).filter(KeywordGroup.status == "active").all()
        ai_provider = get_ai_provider()

        new_count = 0
        updated_count = 0

        for opp in opportunities:
            tender_num = opp.get("tender_number", f"TND-{int(start_time.timestamp())}")
            title = opp.get("title", "New Procurement Tender")
            official_link = opp.get("official_link", source.website_url)

            # Deduplication check by tender number, title, or official link
            existing_tender = db.query(Tender).filter(
                (Tender.tender_number == tender_num) |
                (Tender.title == title) |
                (Tender.official_link == official_link)
            ).first()

            if existing_tender:
                # Corrigendum / Amendment Version Detection
                ver = TenderVersion(
                    tender_id=existing_tender.id,
                    version_number=len(existing_tender.versions) + 1,
                    change_type="Corrigendum Update",
                    notes=f"Corrigendum details detected during automated crawl run on {start_time.strftime('%Y-%m-%d')}."
                )
                db.add(ver)
                updated_count += 1
            else:
                # Create New Tender
                org_name = source.name or "Government Procurement Board"
                org = db.query(Organization).filter(Organization.name == org_name).first()
                if not org:
                    org = Organization(name=org_name, country=source.country, sector=source.category)
                    db.add(org)
                    db.commit()

                scope = opp.get("scope_of_work", f"Procurement opportunity indexed from {source.name}.")
                scores = compute_tender_match_scores(title, scope, keyword_groups)

                # AI Analysis summary generation
                summary_data = ai_provider.generate_summary(f"Title: {title}\nScope: {scope}")
                ai_sum = summary_data.get("executive_summary", f"AI indexed tender matching target keywords from {source.name}.")
                rec = summary_data.get("bid_recommendation", "Bid" if scores["overall_match_score"] >= 80.0 else "Consider")
                win_prob = float(summary_data.get("win_probability", scores["overall_match_score"]))

                new_tender = Tender(
                    tender_number=tender_num,
                    title=title,
                    organization_id=org.id,
                    source_id=source.id,
                    country=source.country or opp.get("country", "India"),
                    sector=source.category or "Education",
                    budget=opp.get("budget", 3500000.0),
                    currency=opp.get("currency", "INR"),
                    publication_date=start_time,
                    submission_deadline=start_time + timedelta(days=21),
                    status="Active",
                    access_status="Verified",
                    official_link=official_link,
                    scope_of_work=scope,
                    deliverables="1. Software/LMS Core\n2. Digital Content Creation\n3. Maintenance & Support",
                    eligibility_criteria="Standard RFP requirements with mandatory past performance in education/IT.",
                    technical_requirements="Cloud architecture, SCORM compliance, API integrations.",
                    financial_requirements="Audited financial statements for the past 3 fiscal years.",
                    required_documents="1. Technical Bid\n2. Commercial Bid\n3. Past Work Certificates",
                    ai_summary=ai_sum,
                    risk_analysis="Standard contract delivery risk. Ensure compliance with submission deadlines.",
                    bid_recommendation=rec,
                    winning_probability=win_prob,
                    estimated_team="1 ID Lead, 3 Storyline Developers, 2 LMS Engineers",
                    estimated_duration="6 Months",
                    keyword_score=scores["keyword_score"],
                    semantic_score=scores["semantic_score"],
                    ai_score=scores["ai_score"],
                    priority_score=scores["priority_score"],
                    overall_match_score=scores["overall_match_score"]
                )
                db.add(new_tender)
                db.commit()
                db.refresh(new_tender)
                new_count += 1
                
                event_bus.dispatch(TenderDiscoveredEvent(
                    tender_id=new_tender.id, 
                    source_id=source.id, 
                    title=new_tender.title
                ))
                
                event_bus.dispatch(AISummaryCompletedEvent(
                    tender_id=new_tender.id,
                    summary=ai_sum,
                    match_score=scores["overall_match_score"]
                ))

                # If official link is a PDF, download and parse attachment
                if official_link.lower().endswith(".pdf"):
                    try:
                        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
                        os.makedirs(storage_dir, exist_ok=True)
                        file_name = f"tender_{new_tender.id}.pdf"
                        file_path = os.path.join(storage_dir, file_name)

                        with httpx.Client(timeout=15.0) as client:
                            pdf_res = client.get(official_link)
                            if pdf_res.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(pdf_res.content)
                                parsed_text = extract_text_from_pdf(pdf_res.content)
                                att = TenderAttachment(
                                    tender_id=new_tender.id,
                                    file_name=file_name,
                                    file_type="PDF",
                                    file_path=file_path,
                                    file_size_bytes=len(pdf_res.content),
                                    parsed_content=parsed_text[:2000]
                                )
                                db.add(att)
                                db.commit()
                    except Exception as e:
                        logger.warning(f"PDF download/extraction notice for {official_link}: {e}")

                # Dispatch notifications if high priority
                if new_tender.overall_match_score >= 80.0:
                    event_bus.dispatch(TenderMatchedEvent(
                        tender_id=new_tender.id,
                        source_id=source.id,
                        title=new_tender.title,
                        match_score=new_tender.overall_match_score,
                        keywords=[]
                    ))

        # Update CrawlHistory & Source last_crawl
        finish_time = datetime.now(timezone.utc)
        duration = int((finish_time - start_time).total_seconds())

        history.finish_time = finish_time
        history.duration_seconds = duration
        history.opportunities_found = len(opportunities)
        history.new_opportunities = new_count
        history.updated_opportunities = updated_count
        history.status = "completed"

        source.last_crawl = finish_time
        source.next_crawl = finish_time + timedelta(hours=24)
        db.commit()

        event_bus.dispatch(CrawlCompletedEvent(
            source_id=source.id, 
            items_found=len(opportunities)
        ))

        return {
            "status": "success",
            "source": source.name,
            "found_tenders": len(opportunities),
            "new_tenders": new_count,
            "updated_tenders": updated_count
        }

    except Exception as e:
        logger.error(f"Crawl execution failed for {source.name}: {e}")
        history.finish_time = datetime.now(timezone.utc)
        history.status = "failed"
        history.error_message = str(e)
        db.commit()
        
        event_bus.dispatch(CrawlFailedEvent(
            source_id=source.id, 
            error_message=str(e)
        ))
        
        return {"status": "error", "message": str(e)}
