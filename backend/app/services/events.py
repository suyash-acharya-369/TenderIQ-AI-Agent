from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import hashlib
import json

class BaseEvent(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    workspace_id: str = "default_ws"
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def idempotency_key(self) -> str:
        # Create a hash of the event contents to prevent duplicates
        content = f"{self.event_type}:{self.entity_type}:{self.entity_id}:{json.dumps(self.payload, sort_keys=True)}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

class TenderDiscoveredEvent(BaseEvent):
    def __init__(self, tender_id: int, source_id: int, title: str, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="tender.discovered",
            entity_type="tender",
            entity_id=str(tender_id),
            workspace_id=workspace_id,
            payload={"source_id": source_id, "title": title}
        )

class TenderMatchedEvent(BaseEvent):
    def __init__(self, tender_id: int, source_id: int, title: str, match_score: float, keywords: list, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="tender.matched",
            entity_type="tender",
            entity_id=str(tender_id),
            workspace_id=workspace_id,
            payload={"source_id": source_id, "title": title, "match_score": match_score, "keywords": keywords}
        )

class CrawlStartedEvent(BaseEvent):
    def __init__(self, source_id: int, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="crawl.started",
            entity_type="source",
            entity_id=str(source_id),
            workspace_id=workspace_id,
            payload={}
        )

class CrawlCompletedEvent(BaseEvent):
    def __init__(self, source_id: int, items_found: int, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="crawl.completed",
            entity_type="source",
            entity_id=str(source_id),
            workspace_id=workspace_id,
            payload={"items_found": items_found}
        )

class CrawlFailedEvent(BaseEvent):
    def __init__(self, source_id: int, error_message: str, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="crawl.failed",
            entity_type="source",
            entity_id=str(source_id),
            workspace_id=workspace_id,
            payload={"error_message": error_message}
        )

class AISummaryCompletedEvent(BaseEvent):
    def __init__(self, tender_id: int, summary: str, match_score: float, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="ai.summary_completed",
            entity_type="tender",
            entity_id=str(tender_id),
            workspace_id=workspace_id,
            payload={"summary_length": len(summary), "match_score": match_score}
        )

class UserCreatedEvent(BaseEvent):
    def __init__(self, user_id: int, email: str, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="user.created",
            entity_type="user",
            entity_id=str(user_id),
            workspace_id=workspace_id,
            payload={"email": email}
        )

class UserLoginEvent(BaseEvent):
    def __init__(self, user_id: int, workspace_id: str = "default_ws"):
        super().__init__(
            event_type="user.login",
            entity_type="user",
            entity_id=str(user_id),
            workspace_id=workspace_id,
            payload={}
        )
