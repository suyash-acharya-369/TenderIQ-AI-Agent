from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from backend.app.database.session import Base

class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True)
    entity_id = Column(String(100), nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), default="Pending") # Pending, Processed, Failed
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
