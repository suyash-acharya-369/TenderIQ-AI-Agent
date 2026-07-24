from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON
from backend.app.database.session import Base

class KeywordGroup(Base):
    __tablename__ = "keyword_groups"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    positive_keywords = Column(JSON, nullable=False)  # List of strings
    negative_keywords = Column(JSON, nullable=True)   # List of strings
    mandatory_keywords = Column(JSON, nullable=True)  # List of strings
    priority_weight = Column(Float, default=1.0)
    language = Column(String(50), default="English")
    status = Column(String(50), default="active")
    color = Column(String(50), default="#3B82F6")
    routed_teams = Column(JSON, nullable=True)
    routed_roles = Column(JSON, nullable=True)
    routed_recipients = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
