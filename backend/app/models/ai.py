from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from backend.app.database.session import Base

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)  # Summary, Risk, Scoring, Notification
    task_type = Column(String(100), nullable=False)
    template_text = Column(Text, nullable=False)
    provider = Column(String(50), default="openai")
    is_active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="SET NULL"), nullable=True)
    task_name = Column(String(100), nullable=False)
    provider = Column(String(50), default="openai")
    model_used = Column(String(100), default="gpt-4o")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    execution_time_seconds = Column(Float, default=0.0)
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
