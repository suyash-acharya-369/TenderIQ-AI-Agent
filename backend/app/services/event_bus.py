import logging
import json
from datetime import datetime, timezone
import asyncio
from backend.app.database.session import SessionLocal
from backend.app.models.event_log import EventLog
from backend.app.services.events import BaseEvent
from backend.app.services.notifications_engine import evaluate_and_dispatch_notifications

logger = logging.getLogger("TenderIQ.EventBus")

class EventBus:
    def __init__(self):
        self.handlers = {
            "tender.discovered": self.handle_tender_event,
            "tender.matched": self.handle_tender_event,
            "crawl.completed": self.handle_crawl_event,
            "crawl.failed": self.handle_crawl_event,
            "ai.summary_completed": self.handle_ai_event
        }

    def dispatch(self, event: BaseEvent):
        """Dispatches an event synchronously to the EventLog and queues processing."""
        db = SessionLocal()
        try:
            # Check idempotency
            existing = db.query(EventLog).filter(EventLog.idempotency_key == event.idempotency_key).first()
            if existing:
                logger.info(f"Event {event.event_type} ignored (duplicate): {event.idempotency_key}")
                return

            log = EventLog(
                idempotency_key=event.idempotency_key,
                event_type=event.event_type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                payload=event.payload,
                status="Pending"
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            # Fire and forget processing if loop is running, else run synchronously
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._process_event_async(log.id, event))
            except RuntimeError:
                # No running loop in this thread (e.g. sync scheduler or setup)
                asyncio.run(self._process_event_async(log.id, event))
        except Exception as e:
            logger.error(f"Error dispatching event: {str(e)}")
            db.rollback()
        finally:
            db.close()

    async def _process_event_async(self, log_id: int, event: BaseEvent):
        """Asynchronously process the event and update its status"""
        db = SessionLocal()
        try:
            log = db.query(EventLog).filter(EventLog.id == log_id).first()
            if not log:
                return

            handler = self.handlers.get(event.event_type, self.handle_default)
            await handler(db, event)

            log.status = "Processed"
            log.processed_at = datetime.now(timezone.utc)
            db.commit()
            
            # Broadcast the update to WebSockets
            from backend.app.api.websockets import notification_manager
            await notification_manager.broadcast_event(event)

        except Exception as e:
            logger.error(f"Error processing event {event.event_type}: {e}")
            if log:
                log.status = "Failed"
                log.error = str(e)
                log.processed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    async def handle_tender_event(self, db, event: BaseEvent):
        tender_id = int(event.entity_id)
        from backend.app.models.tender import Tender
        tender = db.query(Tender).filter(Tender.id == tender_id).first()
        if tender:
            # Pass to the rules evaluator
            evaluate_and_dispatch_notifications(tender, db)
            # The rules evaluator currently creates InAppNotifications directly

    async def handle_crawl_event(self, db, event: BaseEvent):
        # Create an InAppNotification for admins
        from backend.app.models.notification import InAppNotification
        
        title = "Crawl Completed" if event.event_type == "crawl.completed" else "Crawl Failed"
        msg = f"Source {event.entity_id} crawl finished."
        if event.event_type == "crawl.failed":
            msg = f"Source {event.entity_id} crawl failed: {event.payload.get('error_message')}"

        notif = InAppNotification(
            user_id=1,
            title=title,
            content=msg,
            event_type=event.event_type,
            source_id=int(event.entity_id),
            priority="low" if event.event_type == "crawl.completed" else "high",
            lifecycle_status="Created"
        )
        db.add(notif)
        db.commit()

    async def handle_ai_event(self, db, event: BaseEvent):
        from backend.app.models.notification import InAppNotification
        notif = InAppNotification(
            user_id=1,
            title="AI Analysis Complete",
            content=f"Tender {event.entity_id} AI summary generated.",
            event_type=event.event_type,
            tender_id=int(event.entity_id),
            priority="medium",
            lifecycle_status="Created"
        )
        db.add(notif)
        db.commit()

    async def handle_default(self, db, event: BaseEvent):
        # Default handler just creates a generic notification
        from backend.app.models.notification import InAppNotification
        notif = InAppNotification(
            user_id=1,
            title=f"System Event: {event.event_type}",
            content=json.dumps(event.payload),
            event_type=event.event_type,
            priority="low",
            lifecycle_status="Created"
        )
        db.add(notif)
        db.commit()

event_bus = EventBus()
