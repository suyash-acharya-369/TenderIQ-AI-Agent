from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON, Float
from backend.app.database.session import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    channel = Column(String(50), nullable=False)  # Email, WhatsApp, Webhook
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    status = Column(String(50), default="sent")   # sent, failed, pending
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)

class NotificationRule(Base):
    __tablename__ = "notification_rules"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    name = Column(String(255), nullable=False)
    min_score_threshold = Column(Float, default=90.0)
    channels = Column(JSON, nullable=False)  # ["Email", "WhatsApp"]
    event_types = Column(JSON, nullable=False) # ["HighPriority", "Corrigendum", "ClosingSoon"]
    conditions = Column(JSON, nullable=True) # Rules Engine JSON
    recipients = Column(JSON, nullable=False)
    is_active = Column(Integer, default=1)

class InAppNotification(Base):
    __tablename__ = "in_app_notifications"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Integer, default=0)
    action_url = Column(String(500), nullable=True)
    
    # Enterprise Tracking
    event_type = Column(String(100), default="generic")
    source_id = Column(Integer, nullable=True)
    tender_id = Column(Integer, nullable=True)
    priority = Column(String(20), default="medium")
    lifecycle_status = Column(String(50), default="Created")
    
    # Soft Deletes and Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = Column(DateTime, nullable=True)
    is_archived = Column(Integer, default=0)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
