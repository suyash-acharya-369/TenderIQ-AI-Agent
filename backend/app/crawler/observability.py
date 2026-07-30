import logging
from typing import Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.source import Source, SearchAnalytics
from backend.app.models.tender import TenderEvidence

logger = logging.getLogger("TenderIQ.Observability")

class CrawlerObservability:
    def __init__(self, db: Session):
        self.db = db

    def log_search_analytics(self, source_id: int, keyword: str, search_time_ms: float, results_count: int, verified_count: int, rejected_count: int, duplicate_count: int) -> SearchAnalytics:
        """Log search performance and quality metrics."""
        analytics = SearchAnalytics(
            source_id=source_id,
            keyword=keyword,
            search_time_ms=search_time_ms,
            results_returned=results_count,
            verified_results=verified_count,
            rejected_results=rejected_count,
            duplicate_count=duplicate_count,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(analytics)
        self.db.commit()
        return analytics

    def update_source_health(self, source_id: int, success: bool, response_time_ms: float = 0.0) -> Source:
        """Update source health status based on consecutive failures and response times."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return None
            
        if success:
            source.consecutive_failures = 0
            source.health_status = "Healthy"
            source.last_successful_crawl = datetime.now(timezone.utc)
        else:
            source.consecutive_failures = (source.consecutive_failures or 0) + 1
            if source.consecutive_failures >= 5:
                source.health_status = "Critical"
            elif source.consecutive_failures >= 3:
                source.health_status = "Error"
            else:
                source.health_status = "Warning"
                
        # Moving average for response time
        if response_time_ms > 0:
            if source.avg_response_time_ms:
                source.avg_response_time_ms = (source.avg_response_time_ms * 0.9) + (response_time_ms * 0.1)
            else:
                source.avg_response_time_ms = response_time_ms
                
        self.db.commit()
        return source

    def generate_evidence_package(self, tender_id: int, snapshot_path: str, logs: Dict[str, Any]) -> TenderEvidence:
        """Generate and store an evidence package verifying the source of a tender."""
        evidence = TenderEvidence(
            tender_id=tender_id,
            html_snapshot_path=snapshot_path,
            crawler_logs_json=logs,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(evidence)
        self.db.commit()
        return evidence
