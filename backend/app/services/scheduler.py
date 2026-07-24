import logging
import threading
import time
from datetime import datetime, timezone
from backend.app.database.session import SessionLocal
from backend.app.models.source import Source
from backend.app.crawler.engine import run_source_crawl
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications
from backend.app.models.tender import Tender

logger = logging.getLogger("TenderIQ.Scheduler")

class BackgroundScheduler:
    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Background job scheduler started successfully.")

    def stop(self):
        self._running = False
        logger.info("Background job scheduler stopped.")

    def _run_loop(self):
        while self._running:
            try:
                self.run_scheduled_crawls()
                self.run_daily_digest()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            time.sleep(300)  # Check every 5 minutes

    def run_daily_digest(self):
        # Extremely simple daily trigger: check if time is ~08:00 UTC
        # In a real app we'd track last_digest_sent date
        now = datetime.now(timezone.utc)
        if now.hour == 8 and now.minute < 5:
            from backend.app.services.digest_generator import generate_and_dispatch_daily_digest
            db = SessionLocal()
            try:
                generate_and_dispatch_daily_digest(db)
            finally:
                db.close()

    def run_scheduled_crawls(self):
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            sources = db.query(Source).filter(Source.status == "active").all()
            for src in sources:
                next_crawl_time = src.next_crawl.replace(tzinfo=timezone.utc) if src.next_crawl and src.next_crawl.tzinfo is None else src.next_crawl
                if not next_crawl_time or next_crawl_time <= now:
                    logger.info(f"Running automated crawl for source: {src.name}")
                    res = run_source_crawl(src.id, db)
                    if res.get("status") == "success":
                        # Check newly indexed tenders for notifications
                        recent = db.query(Tender).filter(Tender.source_id == src.id).order_by(Tender.created_at.desc()).limit(3).all()
                        for t in recent:
                            evaluate_and_dispatch_notifications(t, db)
        finally:
            db.close()

scheduler = BackgroundScheduler()
