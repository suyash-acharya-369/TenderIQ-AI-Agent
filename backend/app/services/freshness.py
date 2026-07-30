import logging
import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.models.tender import Tender, TenderVersion
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Freshness")

class FreshnessService:
    def __init__(self, db: Session, connector: BaseConnector):
        self.db = db
        self.connector = connector

    def verify_live_status(self, tender: Tender) -> bool:
        """Verify if the official tender link is still active."""
        if not tender.official_link:
            return False
            
        is_live = False
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                res = client.head(tender.official_link)
                # Some portals block HEAD, fallback to GET
                if res.status_code in (405, 403):
                    res = client.get(tender.official_link)
                is_live = res.status_code < 400
        except Exception as e:
            logger.warning(f"Live verification failed for {tender.official_link}: {e}")
            
        if not is_live:
            self.archive_dead_tender(tender)
            
        return is_live

    def archive_dead_tender(self, tender: Tender):
        """Mark a tender as Expired or Archived if the link is dead or past deadline."""
        tender.status = "Archived"
        tender.lifecycle_stage = "Expired/Dead Link"
        
        ver = TenderVersion(
            tender_id=tender.id,
            change_type="Status Update",
            notes="Tender archived due to dead official link or past deadline."
        )
        self.db.add(ver)
        self.db.commit()
        logger.info(f"Archived tender {tender.tender_number} (UID: {tender.tender_uid}).")

    def diff_and_update(self, tender: Tender, latest_metadata: dict):
        """Compare latest metadata from portal with DB and create version history."""
        changes = self.connector.detect_changes(
            {"budget": tender.budget, "deadline": str(tender.submission_deadline)}, 
            latest_metadata
        )
        
        if changes:
            ver = TenderVersion(
                tender_id=tender.id,
                change_type="Corrigendum Detected",
                changes_json=changes,
                notes="Changes detected during freshness check."
            )
            
            # Apply updates
            if "budget" in changes:
                tender.budget = changes["budget"]["new"]
            if "deadline" in changes:
                tender.submission_deadline = changes["deadline"]["new"]
                
            self.db.add(ver)
            self.db.commit()
            logger.info(f"Updated tender {tender.tender_number} with new changes.")
        
        return changes
