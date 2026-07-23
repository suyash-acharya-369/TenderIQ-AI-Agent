from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    name = Column(String(255), nullable=False)
    website_url = Column(String(512), nullable=False)
    country = Column(String(100), default="India")
    category = Column(String(100), default="Government")
    connector_type = Column(String(50), default="Public")  # Public, RSS, API, Auth
    
    # Crawler parameters
    search_url = Column(String(512), nullable=True)
    tender_selector = Column(String(255), nullable=True)
    pdf_selector = Column(String(255), nullable=True)
    pagination_selector = Column(String(255), nullable=True)
    
    frequency = Column(String(50), default="daily")  # daily, hourly, manual
    priority = Column(Integer, default=1)
    status = Column(String(50), default="active")  # active, paused, failing
    health_status = Column(String(50), default="Healthy")  # Healthy, Warning, Error
    
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    
    last_crawl = Column(DateTime, nullable=True)
    next_crawl = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    credentials = relationship("SourceCredentials", back_populates="source", uselist=False, cascade="all, delete-orphan")
    crawls = relationship("CrawlHistory", back_populates="source", cascade="all, delete-orphan")

class SourceCredentials(Base):
    __tablename__ = "source_credentials"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, unique=True)
    encrypted_username = Column(Text, nullable=True)
    encrypted_password = Column(Text, nullable=True)
    encrypted_cookies = Column(Text, nullable=True)
    encrypted_tokens = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source = relationship("Source", back_populates="credentials")

class CrawlHistory(Base):
    __tablename__ = "crawl_history"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finish_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    pages_crawled = Column(Integer, default=0)
    opportunities_found = Column(Integer, default=0)
    new_opportunities = Column(Integer, default=0)
    updated_opportunities = Column(Integer, default=0)
    status = Column(String(50), default="completed")  # running, completed, failed, paused
    error_message = Column(Text, nullable=True)
    screenshot_path = Column(String(512), nullable=True)

    source = relationship("Source", back_populates="crawls")
