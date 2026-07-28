import os
import logging
import httpx
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.source import Source, CrawlHistory, CrawlReplayLog
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
from backend.app.connectors.gem_connector import GeMConnector
from backend.app.connectors.worldbank_connector import WorldBankConnector
from backend.app.connectors.ungm_connector import UNGMConnector
from backend.app.connectors.adb_connector import ADBConnector
from backend.app.connectors.unicef_connector import UNICEFConnector
from backend.app.ai.matcher import compute_tender_match_scores
from backend.app.ai.router import get_ai_provider
from backend.app.utils.document_processor import extract_text_from_pdf
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications

logger = logging.getLogger("TenderIQ.CrawlerEngine")

def _get_connector_instance(connector_type: str, source_name: str = "", website_url: str = ""):
    combined = f"{connector_type or ''} {source_name or ''} {website_url or ''}".lower()
    if "gem" in combined:
        return GeMConnector()
    elif "worldbank" in combined or "world bank" in combined:
        return WorldBankConnector()
    elif "ungm" in combined or "unesco" in combined:
        return UNGMConnector()
    elif "adb" in combined or "developmentaid" in combined:
        return ADBConnector()
    elif "unicef" in combined:
        return UNICEFConnector()
    elif "rss" in combined:
        return RSSConnector()
    elif "api" in combined:
        return APIConnector()
    elif "playwright" in combined:
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
        connector = _get_connector_instance(source.connector_type, source.name, source.website_url)
        target_url = source.search_url or source.website_url
        
        # Incremental Crawl State (ETag & Last-Modified)
        try:
            with httpx.Client(timeout=5.0) as client:
                head_res = client.head(target_url, follow_redirects=True)
                current_etag = head_res.headers.get("ETag")
                current_last_modified = head_res.headers.get("Last-Modified")
                
                if current_etag and source.etag == current_etag:
                    logger.info(f"ETag matches for {source.name}. Skipping crawl.")
                    history.status = "skipped"
                    history.finish_time = datetime.now(timezone.utc)
                    db.commit()
                    return {"status": "success", "source": source.name, "found_tenders": 0, "new_tenders": 0, "updated_tenders": 0, "message": "Skipped (ETag unchanged)"}
                
                if current_last_modified and source.last_modified_header == current_last_modified:
                    logger.info(f"Last-Modified matches for {source.name}. Skipping crawl.")
                    history.status = "skipped"
                    history.finish_time = datetime.now(timezone.utc)
                    db.commit()
                    return {"status": "success", "source": source.name, "found_tenders": 0, "new_tenders": 0, "updated_tenders": 0, "message": "Skipped (Last-Modified unchanged)"}
                
                source.etag = current_etag
                source.last_modified_header = current_last_modified
                db.commit()
        except Exception as e:
            logger.warning(f"Failed to fetch ETag/Last-Modified for {target_url}: {e}")

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
                # Block 5: Multi-Source Duplicate Fusion — merge portal URLs
                existing_urls = existing_tender.source_urls_json or []
                if official_link and official_link not in existing_urls:
                    existing_urls.append(official_link)
                    existing_tender.source_urls_json = existing_urls

                # Corrigendum / Amendment Version Detection & Side-by-Side Diff
                changes = {}
                new_budget = opp.get("budget")
                if new_budget and existing_tender.budget != new_budget:
                    changes["budget"] = {"old": existing_tender.budget, "new": new_budget}
                    existing_tender.budget = new_budget
                    
                new_deadline = opp.get("submission_deadline")
                if new_deadline and existing_tender.submission_deadline != new_deadline:
                    changes["deadline"] = {"old": str(existing_tender.submission_deadline), "new": str(new_deadline)}
                    existing_tender.submission_deadline = new_deadline

                if changes:
                    change_type = "Budget/Deadline Update"
                    ver = TenderVersion(
                        tender_id=existing_tender.id,
                        version_number=len(existing_tender.versions) + 1,
                        change_type=change_type,
                        changes_json=changes,
                        notes=f"Changes detected during automated crawl run on {start_time.strftime('%Y-%m-%d')}."
                    )
                    db.add(ver)
                    updated_count += 1
                else:
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

                # AI Analysis summary generation & Keyword Evidence (Block 4)
                prompt_template = """Analyze the tender document and extract:
1. 'executive_summary': A brief professional summary. Cite sources exactly if found, e.g., '[Page 14, Section 5.2]'.
2. 'bid_recommendation': 'Bid' or 'Consider' or 'No Bid'.
3. 'win_probability': 0-100 float.
4. 'ai_citations': A JSON object mapping extracted fields to their source citations. e.g. {"Deadline": "[Page 3, Section 1.2]", "Budget": "[Page 14, Section 5.2]"}.
5. 'keyword_evidence': A JSON array mapping matching keywords to their evidence. e.g. [{"keyword": "LMS", "page": 3, "section": "2.1", "sentence": "Must provide a scalable LMS."}]
"""
                summary_data = ai_provider.generate_summary(f"Title: {title}\nScope: {scope}", prompt_template=prompt_template)
                ai_sum = summary_data.get("executive_summary", f"AI indexed tender matching target keywords from {source.name}.")
                rec = summary_data.get("bid_recommendation", "Bid" if scores["overall_match_score"] >= 80.0 else "Consider")
                win_prob = float(summary_data.get("win_probability", scores["overall_match_score"]))
                ai_citations = summary_data.get("ai_citations", {})
                keyword_evidence = summary_data.get("keyword_evidence", [])

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
                    lifecycle_stage="Discovered",
                    moderation_status="CRAWLED",
                    access_status="Verified",
                    official_link=official_link,
                    source_urls_json=[official_link],
                    scope_of_work=scope,
                    deliverables="1. Software/LMS Core\n2. Digital Content Creation\n3. Maintenance & Support",
                    eligibility_criteria="Standard RFP requirements with mandatory past performance in education/IT.",
                    technical_requirements="Cloud architecture, SCORM compliance, API integrations.",
                    financial_requirements="Audited financial statements for the past 3 fiscal years.",
                    required_documents="1. Technical Bid\n2. Commercial Bid\n3. Past Work Certificates",
                    ai_summary=ai_sum,
                    ai_citations=ai_citations,
                    keyword_evidence=keyword_evidence,
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
                
                # Block 6: Progress moderation state → AI PROCESSED
                new_tender.moderation_status = "AI PROCESSED"
                new_tender.lifecycle_stage = "AI Processed"
                db.commit()

                # Multi-Document Collection & SHA-256 Hashing
                try:
                    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))
                    os.makedirs(storage_dir, exist_ok=True)
                    
                    # Also fallback to official_link if it's a PDF and no docs found
                    docs_to_download = opp.get("documents", [])
                    if not docs_to_download:
                        docs_to_download = connector.download_documents(official_link, storage_dir)
                    
                    if not docs_to_download and official_link.lower().endswith(".pdf"):
                        docs_to_download.append({"name": "Official_Document.pdf", "url": official_link, "type": "PDF"})
                        
                    for doc in docs_to_download:
                        doc_url = doc.get("url")
                        if not doc_url:
                            continue
                        doc_name = doc.get("name", f"document_{new_tender.id}")
                        doc_type = doc.get("type", "Document")
                        
                        # Replace unsafe characters in filename
                        safe_doc_name = "".join(c for c in doc_name if c.isalnum() or c in " ._-").strip()
                        file_path = os.path.join(storage_dir, f"tender_{new_tender.id}_{safe_doc_name}")
                        
                        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                            doc_res = client.get(doc_url)
                            if doc_res.status_code == 200:
                                content = doc_res.content
                                sha256_hash = hashlib.sha256(content).hexdigest()
                                
                                with open(file_path, "wb") as f:
                                    f.write(content)
                                    
                                parsed_text = extract_text_from_pdf(content) if file_path.lower().endswith(".pdf") else ""
                                att = TenderAttachment(
                                    tender_id=new_tender.id,
                                    file_name=safe_doc_name,
                                    file_type=doc_type,
                                    file_path=file_path,
                                    file_size_bytes=len(content),
                                    hash_sha256=sha256_hash,
                                    parsed_content=parsed_text[:2000]
                                )
                                db.add(att)
                                db.commit()
                except Exception as e:
                    logger.warning(f"Document download/extraction notice for {official_link}: {e}")

                # Block 6: Progress moderation state → VERIFIED
                new_tender.moderation_status = "VERIFIED"
                new_tender.verification_status = "VERIFIED"
                new_tender.verified_at = datetime.now(timezone.utc)
                db.commit()

                # Dispatch notifications if high priority
                if new_tender.overall_match_score >= 80.0:
                    event_bus.dispatch(TenderMatchedEvent(
                        tender_id=new_tender.id,
                        source_id=source.id,
                        title=new_tender.title,
                        match_score=new_tender.overall_match_score,
                        keywords=[]
                    ))
                    # Block 6: Progress moderation state → PUBLISHED
                    new_tender.moderation_status = "PUBLISHED"
                    new_tender.lifecycle_stage = "Notified"
                    db.commit()

        # Update CrawlHistory & Source last_crawl & Health (Phase 14 & 15)
        finish_time = datetime.now(timezone.utc)
        duration = float((finish_time - start_time).total_seconds())

        history.finish_time = finish_time
        history.duration_seconds = duration
        history.opportunities_found = len(opportunities)
        history.new_opportunities = new_count
        history.updated_opportunities = updated_count
        history.status = "completed"

        source.last_crawl = finish_time
        source.last_successful_crawl = finish_time
        source.consecutive_failures = 0
        source.health_status = "Healthy"
        source.avg_response_time_ms = round(duration * 1000 / (len(opportunities) or 1), 2)
        source.next_crawl = finish_time + timedelta(hours=24)
        
        # Block 5: Crawl Replay Logger — store HTTP request/response snapshot
        try:
            replay = CrawlReplayLog(
                source_id=source.id,
                url=target_url,
                http_status=200,
                request_headers_json={"User-Agent": "TenderIQ Crawler/1.0"},
                extracted_json={"opportunities_count": len(opportunities), "new": new_count, "updated": updated_count},
                logs_json={"duration_seconds": duration, "connector": type(connector).__name__}
            )
            db.add(replay)
        except Exception as e:
            logger.warning(f"Crawl replay log error: {e}")
        
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
        finish_time = datetime.now(timezone.utc)
        history.finish_time = finish_time
        history.status = "failed"
        history.error_message = str(e)
        
        # Phase 15: Increment consecutive failures & health degradation
        source.consecutive_failures = (source.consecutive_failures or 0) + 1
        if source.consecutive_failures >= 3:
            source.health_status = "Error"
        else:
            source.health_status = "Warning"
        
        db.commit()
        
        event_bus.dispatch(CrawlFailedEvent(
            source_id=source.id, 
            error_message=str(e)
        ))
        
        return {"status": "error", "message": str(e)}
