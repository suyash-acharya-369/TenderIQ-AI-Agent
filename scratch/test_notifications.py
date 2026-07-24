import os
import sys
import logging
from sqlalchemy.orm import Session
from datetime import datetime

# Setup paths to allow importing backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database.session import SessionLocal
from backend.app.models.tender import Tender
from backend.app.models.keyword import KeywordGroup
from backend.app.models.user import User
from backend.app.models.notification import NotificationRule
from backend.app.services.rules_evaluator import evaluate_condition
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications
from backend.app.services.digest_generator import generate_and_dispatch_daily_digest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TenderIQ.Verification")

def run_tests():
    db: Session = SessionLocal()
    
    try:
        # 1. Test Rule Parsing
        logger.info("=== TESTING RULE PARSING ===")
        mock_tender = Tender(
            tender_number="TEST-RULE-1",
            title="Test Tender",
            overall_match_score=95,
            raw_metadata={"keywords_matched": ["Cyber Security"]}
        )
        
        condition = {
            "condition": "AND",
            "rules": [
                {"field": "overall_match_score", "op": ">=", "val": 90}
            ]
        }
        
        passed = evaluate_condition(mock_tender, condition)
        logger.info(f"Rule Evaluation Result: {passed} (Expected: True)")
        assert passed == True
        
        # 2. Test Notifications Engine (Routing)
        logger.info("=== TESTING NOTIFICATIONS ENGINE ===")
        # Note: This will actually dispatch an email if SMTP/Resend is configured.
        # Since we are in testing, it should log successfully simulated emails via SMTPProvider fallback
        
        dispatched = evaluate_and_dispatch_notifications(mock_tender, db)
        logger.info(f"Dispatched {dispatched} notifications for test tender.")
        
        # 3. Test Digest Generation
        logger.info("=== TESTING AI DIGEST GENERATION ===")
        # Assuming we have an AI provider and some mocked tenders in DB from previous crawls
        generate_and_dispatch_daily_digest(db)
        logger.info("Daily Digest task completed without raising exceptions.")
        
        logger.info("ALL VERIFICATIONS PASSED.")
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
