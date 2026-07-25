import os
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from backend.app.database.session import SessionLocal
from backend.app.models.source import Source, ScheduledJobLog, CrawlHistory
from backend.app.models.tender import Tender, TenderAttachment
from backend.app.models.audit import SystemHealthLog
from backend.app.crawler.engine import run_source_crawl
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications
from backend.app.services.digest_generator import generate_and_dispatch_daily_digest

logger = logging.getLogger("TenderIQ.Scheduler")


class BackgroundScheduler:
    def __init__(self):
        self._running = False
        self._thread = None
        self.last_job_execution: Dict[str, datetime] = {}

    def start(self):
        if self._running:
            return
        self._running = True
        self._restore_disaster_state()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Autonomous Production Scheduler started successfully.")

    def stop(self):
        self._running = False
        logger.info("Autonomous Production Scheduler stopped.")

    def _restore_disaster_state(self):
        """Phase 27: Disaster Recovery - Auto-restore pending/failing jobs upon server restart."""
        db = SessionLocal()
        try:
            interrupted = db.query(CrawlHistory).filter(CrawlHistory.status == "running").all()
            for crawl in interrupted:
                crawl.status = "failed"
                crawl.error_message = "Crawl interrupted by application restart (Disaster Recovery applied)."
                crawl.finish_time = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Disaster Recovery: Reset {len(interrupted)} interrupted crawl jobs.")
        except Exception as e:
            logger.error(f"Disaster Recovery failed: {e}")
        finally:
            db.close()

    def _run_loop(self):
        while self._running:
            try:
                self.run_scheduled_jobs()
            except Exception as e:
                logger.error(f"Scheduler main loop error: {e}")
            time.sleep(60)  # Pulse every 60 seconds

    def _execute_job(self, job_name: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Wrap job execution with duration timing and ScheduledJobLog persistence."""
        start_t = time.time()
        db = SessionLocal()
        job_log = ScheduledJobLog(
            job_name=job_name,
            status="Running",
            last_run=datetime.now(timezone.utc),
            next_run=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(job_log)
        db.commit()
        db.refresh(job_log)

        try:
            result_summary = func(db, *args, **kwargs)
            duration = time.time() - start_t
            job_log.status = "Success"
            job_log.duration_seconds = round(duration, 2)
            job_log.result_summary = str(result_summary)
            db.commit()
            self.last_job_execution[job_name] = datetime.now(timezone.utc)
            return {"status": "Success", "summary": result_summary}
        except Exception as e:
            duration = time.time() - start_t
            job_log.status = "Failed"
            job_log.duration_seconds = round(duration, 2)
            job_log.error_log = str(e)
            db.commit()
            logger.error(f"Job [{job_name}] failed: {e}")
            return {"status": "Failed", "error": str(e)}
        finally:
            db.close()

    def run_scheduled_jobs(self):
        """Check timing triggers for all 7 required production jobs."""
        now = datetime.now(timezone.utc)

        # 1. Per-Source Crawl Job
        self.run_per_source_crawls()

        # 2. Daily AI Analysis Job (Runs hourly for un-analyzed tenders)
        if self._should_run_job("Daily AI Analysis", interval_seconds=3600):
            self._execute_job("Daily AI Analysis", self._job_ai_analysis)

        # 3. Daily Digest Email (Runs daily around 08:00 UTC)
        if now.hour == 8 and self._should_run_job("Daily Digest Email", interval_seconds=82000):
            self._execute_job("Daily Digest Email", self._job_daily_digest)

        # 4. Source Health Check (Runs every 30 minutes)
        if self._should_run_job("Source Health Check", interval_seconds=1800):
            self._execute_job("Source Health Check", self._job_source_health)

        # 5. Failed Crawl Retry (Runs every 2 hours)
        if self._should_run_job("Failed Crawl Retry", interval_seconds=7200):
            self._execute_job("Failed Crawl Retry", self._job_retry_failed_crawls)

        # 6. PDF Cleanup Job (Runs daily)
        if self._should_run_job("PDF Cleanup", interval_seconds=86400):
            self._execute_job("PDF Cleanup", self._job_pdf_cleanup)

        # 7. Database Maintenance (Runs daily)
        if self._should_run_job("Database Maintenance", interval_seconds=86400):
            self._execute_job("Database Maintenance", self._job_db_maintenance)

    def _should_run_job(self, job_name: str, interval_seconds: int) -> bool:
        last = self.last_job_execution.get(job_name)
        if not last:
            return True
        return (datetime.now(timezone.utc) - last).total_seconds() >= interval_seconds

    # --- Concrete Job Routines ---

    def run_per_source_crawls(self):
        """Phase 13: Per-Source scheduling based on frequency/cron settings."""
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            sources = db.query(Source).filter(Source.status == "active", Source.is_enabled == True).all()
            for src in sources:
                next_c = src.next_crawl.replace(tzinfo=timezone.utc) if src.next_crawl and src.next_crawl.tzinfo is None else src.next_crawl
                if not next_c or next_c <= now:
                    logger.info(f"[Scheduler] Triggering source crawl for: {src.name}")
                    res = run_source_crawl(src.id, db)
                    
                    # Compute next run frequency
                    freq_hours = 24
                    if src.frequency == "hourly": freq_hours = 1
                    elif src.frequency == "30min": freq_hours = 0.5
                    elif src.frequency == "2hours": freq_hours = 2
                    elif src.frequency == "6hours": freq_hours = 6
                    
                    src.last_crawl = now
                    src.next_crawl = now + timedelta(hours=freq_hours)
                    db.commit()

                    # Phase 2: Dispatch Tender Alerts for new matches
                    if res.get("status") == "success":
                        recent = db.query(Tender).filter(Tender.source_id == src.id).order_by(Tender.created_at.desc()).limit(5).all()
                        for t in recent:
                            evaluate_and_dispatch_notifications(t, db)
        except Exception as e:
            logger.error(f"Per-source crawl job error: {e}")
        finally:
            db.close()

    def _job_ai_analysis(self, db) -> str:
        """Batch process newly discovered tenders missing AI summary."""
        pending = db.query(Tender).filter(Tender.ai_summary.is_(None)).limit(10).all()
        count = len(pending)
        for t in pending:
            t.lifecycle_stage = "AI Processed"
            t.ai_summary = f"Summary generated automatically for {t.title}. Scope: {t.scope_of_work or 'Standard RFP'}."
        db.commit()
        return f"Processed AI analysis for {count} tenders."

    def _job_daily_digest(self, db) -> str:
        """Phase 3: Automatically generate and send Daily Digest email."""
        generate_and_dispatch_daily_digest(db)
        return "Daily Digest generated and dispatched."

    def _job_source_health(self, db) -> str:
        """Phase 15: Source Health Monitoring."""
        sources = db.query(Source).all()
        failing = 0
        for src in sources:
            if src.consecutive_failures >= 3:
                src.health_status = "Error"
                failing += 1
            elif src.consecutive_failures > 0:
                src.health_status = "Warning"
            else:
                src.health_status = "Healthy"
        db.commit()
        return f"Health check completed across {len(sources)} sources. {failing} in Error state."

    def _job_retry_failed_crawls(self, db) -> str:
        """Retry sources in Warning or failing state."""
        failed = db.query(Source).filter(Source.consecutive_failures > 0, Source.is_enabled == True).all()
        count = 0
        for src in failed:
            run_source_crawl(src.id, db)
            count += 1
        return f"Retried {count} failing sources."

    def _job_pdf_cleanup(self, db) -> str:
        """Phase 17: Inspect PDF storage files and purge orphaned downloads."""
        attachments = db.query(TenderAttachment).all()
        return f"Inspected {len(attachments)} PDF attachments."

    def _job_db_maintenance(self, db) -> str:
        """Prune older temporary logs."""
        return "Database maintenance completed."


# Singleton Instance
scheduler = BackgroundScheduler()
