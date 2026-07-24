import os
import sys
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.session import SessionLocal
from backend.app.services.events import CrawlStartedEvent, CrawlCompletedEvent
from backend.app.services.event_bus import event_bus
from backend.app.models.event_log import EventLog
from backend.app.models.notification import InAppNotification

async def main():
    db: Session = SessionLocal()
    print("Testing Event Pipeline...")
    
    # 1. Dispatch a mock event
    print("Dispatching CrawlStartedEvent...")
    event = CrawlStartedEvent(source_id=999)
    event_bus.dispatch(event)
    
    # 2. Wait for async processing to finish
    await asyncio.sleep(2)
    
    # 3. Check EventLog
    log = db.query(EventLog).filter(EventLog.idempotency_key == event.idempotency_key).first()
    if log:
        print(f"✅ EventLog recorded successfully. Status: {log.status}")
    else:
        print("❌ EventLog not found.")
        
    # 4. Check InAppNotification 
    event2 = CrawlCompletedEvent(source_id=998, items_found=10)
    event_bus.dispatch(event2)
    
    await asyncio.sleep(2)
    
    notif = db.query(InAppNotification).filter(InAppNotification.source_id == 998).first()
    if notif:
        print(f"✅ InAppNotification generated successfully via EventBus. Lifecycle: {notif.lifecycle_status}")
    else:
        print("❌ InAppNotification not found.")

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
