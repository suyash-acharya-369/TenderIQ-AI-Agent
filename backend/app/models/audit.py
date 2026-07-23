from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float
from backend.app.database.session import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    user_email = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SystemHealthLog(Base):
    __tablename__ = "system_health_logs"

    id = Column(Integer, primary_key=True, index=True)
    cpu_usage_pct = Column(Float, default=0.0)
    ram_usage_pct = Column(Float, default=0.0)
    disk_usage_pct = Column(Float, default=0.0)
    db_status = Column(String(50), default="Healthy")
    redis_status = Column(String(50), default="Healthy")
    crawler_status = Column(String(50), default="Idle")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
