import os
import logging
import httpx
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from sqlalchemy.orm import Session
from backend.app.models.source import Source, CrawlHistory, CrawlReplayLog, SearchAnalytics
from backend.app.models.tender import Tender, Organization, TenderVersion, TenderAttachment, TenderEvidence, HumanReviewQueue
from backend.app.models.keyword import KeywordGroup
from backend.app.services.event_bus import event_bus
from backend.app.services.events import (
    CrawlStartedEvent, CrawlCompletedEvent, CrawlFailedEvent,
    TenderDiscoveredEvent, TenderMatchedEvent, AISummaryCompletedEvent
)
from backend.app.connectors.generic import GenericConnector
from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.ai.router import get_ai_provider
from backend.app.utils.document_processor import extract_text_from_pdf
from backend.app.crawler.rate_limiter import RateLimitManager

logger = logging.getLogger("TenderIQ.CrawlerEngine")

from backend.app.connectors.gem_connector import GeMConnector
from backend.app.connectors.worldbank_connector import WorldBankConnector
from backend.app.connectors.ungm_connector import UNGMConnector
from backend.app.connectors.playwright_connector import PlaywrightConnector

def _get_connector_instance(connector_type: str):
    if connector_type == "GeMConnector":
        return GeMConnector()
    elif connector_type == "WorldBankConnector":
        return WorldBankConnector()
    elif connector_type == "UNGMConnector":
        return UNGMConnector()
    return GenericConnector()

def run_source_crawl(source_id: int, db: Session) -> Dict[str, Any]:
    """
    V3.1 Enterprise Continuous Discovery Pipeline
    Google Sheets -> Sources -> Keywords -> Search Every Keyword -> Verify -> Store
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return {"status": "error", "message": "Source not found"}

    start_time = datetime.now(timezone.utc)
    history = CrawlHistory(source_id=source.id, start_time=start_time, status="running")
    db.add(history)
    db.commit()

    event_bus.dispatch(CrawlStartedEvent(source_id=source.id))
    rate_limiter = RateLimitManager(db)

    try:
        connector = _get_connector_instance(source.connector_type)
        if not connector.health_check():
            raise Exception("Source Health Check Failed. Portal may be down.")

        keyword_groups = db.query(KeywordGroup).filter(KeywordGroup.status == "active").all()
        ai_provider = get_ai_provider()

        new_count = 0
        updated_count = 0
        total_found = 0

        # Step 1: Iterate through keyword groups and search continuously
        for kg in keyword_groups:
            for keyword in kg.positive_keywords:
                rate_limiter.enforce_rate_limit(source.website_url)
                
                search_start = datetime.now(timezone.utc)
                raw_results = connector.search(keyword)
                
                # Playwright Fallback Logic
                if not raw_results:
                    logger.warning(f"Standard connector failed or found no results for {source.name}. Triggering Playwright Fallback.")
                    playwright_conn = PlaywrightConnector()
                    try:
                        raw_results = playwright_conn.search(keyword, search_url=source.search_url)
                        logger.info(f"Playwright Fallback succeeded for {source.name}.")
                    except Exception as e:
                        logger.error(f"Playwright Fallback failed for {source.name}: {e}")
                
                opportunities = connector.parse_search_results(raw_results)
                search_time_ms = (datetime.now(timezone.utc) - search_start).total_seconds() * 1000

                # Search Analytics Tracking
                analytics = SearchAnalytics(
                    source_id=source.id,
                    keyword=keyword,
                    search_time_ms=search_time_ms,
                    results_returned=len(opportunities)
                )
                db.add(analytics)

                for opp in opportunities:
                    total_found += 1
                    tender_num = opp.get("tender_number")
                    title = opp.get("title")
                    official_link = opp.get("official_link")
                    org_name = opp.get("organization") or source.name
                    pub_date = opp.get("publication_date") or str(start_time.date())
                    
                    if not (tender_num and title and official_link):
                        logger.warning(f"Missing mandatory fields for {official_link}. Cannot verify.")
                        analytics.rejected_results += 1
                        continue

                    # Step 2: Global Unique Tender ID (V3.1)
                    # SHA256(Official URL + RFP Number + Organization + Published Date)
                    uid_string = f"{official_link}|{tender_num}|{org_name}|{pub_date}".encode('utf-8')
                    tender_uid = hashlib.sha256(uid_string).hexdigest()

                    # Deduplication check by TenderUID
                    existing_tender = db.query(Tender).filter(Tender.tender_uid == tender_uid).first()

                    if existing_tender:
                        analytics.duplicate_count += 1
                        # Multi-Source Duplicate Fusion
                        existing_urls = existing_tender.source_urls_json or []
                        if official_link and official_link not in existing_urls:
                            existing_urls.append(official_link)
                            existing_tender.source_urls_json = existing_urls

                        # Version Control / Change Detection
                        changes = connector.detect_changes({"budget": existing_tender.budget, "deadline": str(existing_tender.submission_deadline)}, opp)
                        if changes:
                            ver = TenderVersion(
                                tender_id=existing_tender.id,
                                change_type="Update Detected",
                                changes_json=changes,
                                notes=f"Detected via keyword {keyword}"
                            )
                            db.add(ver)
                            updated_count += 1
                            analytics.updated_opportunities += 1
                    else:
                        # Step 3: Only process NEW opportunities
                        # Navigate to the detailed tender page and extract metadata
                        rate_limiter.enforce_rate_limit(source.website_url)
                        html_content = connector.open_tender(official_link)
                        metadata = connector.extract_metadata(html_content, official_link)
                        
                        if not connector.verify(metadata):
                            # Push to Human Review Queue
                            review_task = HumanReviewQueue(
                                tender_uid=tender_uid,
                                source_id=source.id,
                                reason="Verification Failed or Captcha Blocked",
                                context_json={"url": official_link, "metadata": metadata}
                            )
                            db.add(review_task)
                            analytics.rejected_results += 1
                            continue

                        # Create New Tender
                        org = db.query(Organization).filter(Organization.name == org_name).first()
                        if not org:
                            org = Organization(name=org_name, country=source.country, sector=source.category)
                            db.add(org)
                            db.commit()

                        scope = metadata.get("scope_of_work", title)
                        scores = compute_tender_match_scores(title, scope, keyword_groups)
                        
                        # AI Summary (Zero Hallucination - grounded in extraction)
                        ai_sum = "AI Analysis Pending..."
                        if metadata.get("scope_of_work"):
                            prompt = f"Analyze strictly based on this content: {metadata['scope_of_work']}. Output JSON."
                            summary_data = ai_provider.generate_summary(prompt)
                            ai_sum = summary_data.get("executive_summary", "")

                        new_tender = Tender(
                            tender_uid=tender_uid,
                            tender_number=tender_num,
                            title=title,
                            organization_id=org.id,
                            source_id=source.id,
                            official_link=official_link,
                            source_urls_json=[official_link],
                            scope_of_work=scope,
                            budget=metadata.get("budget"),
                            submission_deadline=metadata.get("submission_deadline"),
                            extracted_fields_json=metadata.get("extracted_fields_json", {}),
                            ai_summary=ai_sum,
                            keyword_score=scores["keyword_score"],
                            semantic_score=scores["semantic_score"],
                            ai_score=scores["ai_score"],
                            priority_score=scores["priority_score"],
                            overall_match_score=scores["overall_match_score"],
                            moderation_status="VERIFIED",
                            verification_status="VERIFIED"
                        )
                        db.add(new_tender)
                        db.commit()
                        db.refresh(new_tender)

                        # Create Evidence Package (V3.1)
                        evidence = TenderEvidence(
                            tender_id=new_tender.id,
                            html_snapshot_path=f"/storage/snapshots/{tender_uid}.html",
                            crawler_logs_json={"connector": source.connector_type, "keyword": keyword}
                        )
                        db.add(evidence)
                        
                        new_count += 1
                        analytics.new_opportunities += 1
                        analytics.verified_results += 1

                db.commit() # Commit analytics per keyword

        history.finish_time = datetime.now(timezone.utc)
        history.status = "completed"
        source.last_crawl = history.finish_time
        source.health_status = "Healthy"
        db.commit()

        event_bus.dispatch(CrawlCompletedEvent(source_id=source.id, items_found=total_found))
        return {"status": "success", "source": source.name, "new_tenders": new_count, "updated_tenders": updated_count}

    except Exception as e:
        logger.error(f"Crawl execution failed for {source.name}: {e}")
        history.finish_time = datetime.now(timezone.utc)
        history.status = "failed"
        history.errors = str(e)
        source.health_status = "Error"
        db.commit()
        event_bus.dispatch(CrawlFailedEvent(source_id=source.id, error_message=str(e)))
        return {"status": "error", "message": str(e)}
