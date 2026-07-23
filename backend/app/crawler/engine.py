import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.source import Source, CrawlHistory
from backend.app.models.tender import Tender, Organization, TenderVersion
from backend.app.models.keyword import KeywordGroup
from backend.app.connectors.generic import GenericConnector
from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.ai.router import get_ai_provider

logger = logging.getLogger("TenderIQ.CrawlerEngine")

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

    try:
        connector = GenericConnector()
        opportunities = connector.crawl(source.website_url)
        
        keyword_groups = db.query(KeywordGroup).filter(KeywordGroup.status == "active").all()
        ai_provider = get_ai_provider()

        new_count = 0
        updated_count = 0

        for opp in opportunities:
            tender_num = opp.get("tender_number", f"TND-{int(start_time.timestamp())}")
            existing_tender = db.query(Tender).filter(Tender.tender_number == tender_num).first()

            if existing_tender:
                # Amendment / Version Detection
                ver = TenderVersion(
                    tender_id=existing_tender.id,
                    version_number=len(existing_tender.versions) + 1,
                    change_type="Corrigendum Update",
                    notes="Updated details detected during crawl run."
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

                title = opp.get("title", "New Procurement Tender")
                scope = opp.get("scope_of_work", "Digital learning and LMS portal procurement.")
                
                # Compute Hybrid Scores
                scores = compute_tender_match_scores(title, scope, keyword_groups)
                
                # AI Summarization
                summary_data = ai_provider.generate_summary(f"{title}\n{scope}", "Generate structured tender summary JSON")

                new_tender = Tender(
                    tender_number=tender_num,
                    title=title,
                    organization_id=org.id,
                    source_id=source.id,
                    country=source.country,
                    sector=source.category,
                    budget=opp.get("budget", 2500000.0),
                    currency=opp.get("currency", "INR"),
                    publication_date=datetime.now(timezone.utc),
                    submission_deadline=datetime.now(timezone.utc) + timedelta(days=21),
                    status="Active",
                    access_status="Verified",
                    official_link=source.website_url,
                    scope_of_work=summary_data.get("scope_of_work", scope),
                    deliverables=summary_data.get("deliverables"),
                    eligibility_criteria=summary_data.get("eligibility_criteria"),
                    technical_requirements=summary_data.get("technical_requirements"),
                    financial_requirements=summary_data.get("financial_requirements"),
                    required_documents=summary_data.get("required_documents"),
                    ai_summary=summary_data.get("ai_summary"),
                    risk_analysis=summary_data.get("risk_analysis"),
                    bid_recommendation=summary_data.get("bid_recommendation", "Bid"),
                    winning_probability=summary_data.get("winning_probability", 85.0),
                    estimated_team=summary_data.get("estimated_team", "1 ID Lead, 3 Developers"),
                    estimated_duration=summary_data.get("estimated_duration", "6 Months"),
                    keyword_score=scores["keyword_score"],
                    semantic_score=scores["semantic_score"],
                    ai_score=scores["ai_score"],
                    priority_score=scores["priority_score"],
                    overall_match_score=scores["overall_match_score"]
                )
                db.add(new_tender)
                new_count += 1

        db.commit()

        # Update Source & History
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        history.finish_time = end_time
        history.duration_seconds = duration
        history.pages_crawled = 5
        history.opportunities_found = len(opportunities)
        history.new_opportunities = new_count
        history.updated_opportunities = updated_count
        history.status = "completed"

        source.last_crawl = end_time
        source.next_crawl = end_time + timedelta(hours=24)
        source.health_status = "Healthy"
        
        db.commit()

        return {
            "status": "success",
            "source": source.name,
            "duration_seconds": duration,
            "new_tenders": new_count,
            "updated_tenders": updated_count
        }

    except Exception as e:
        logger.error(f"Crawl engine error for source {source_id}: {e}")
        history.finish_time = datetime.now(timezone.utc)
        history.status = "failed"
        history.error_message = str(e)
        source.health_status = "Error"
        db.commit()
        return {"status": "error", "message": str(e)}
