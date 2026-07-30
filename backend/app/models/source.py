from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Float, JSON
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
    connector_type = Column(String(50), default="Public")  # GeMConnector, TEDConnector, etc.
    
    # Crawler parameters
    search_url = Column(String(512), nullable=True)
    tender_selector = Column(String(255), nullable=True)
    pdf_selector = Column(String(255), nullable=True)
    pagination_selector = Column(String(255), nullable=True)
    
    frequency = Column(String(50), default="daily")  
    cron_expression = Column(String(100), nullable=True, default="0 0 * * *")  
    timezone = Column(String(100), default="UTC")
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    status = Column(String(50), default="active")  
    health_status = Column(String(50), default="Healthy")  
    
    # Advanced Crawler parameters
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    capabilities_json = Column(JSON, nullable=True) # V3.1: Automatically detected capabilities
    rate_limit_config_json = Column(JSON, nullable=True) # V3.1: Rate Limit Manager
    
    # Incremental Crawling & State Tracking
    last_crawl = Column(DateTime, nullable=True)
    last_successful_crawl = Column(DateTime, nullable=True)
    next_crawl = Column(DateTime, nullable=True)
    last_tender_id = Column(String(255), nullable=True)
    last_cursor = Column(String(255), nullable=True)
    etag = Column(String(255), nullable=True)
    last_modified_header = Column(String(255), nullable=True)
    
    # Source Health Metrics
    avg_response_time_ms = Column(Float, default=0.0)
    robots_txt_status = Column(String(50), default="Allowed")
    ssl_valid = Column(Boolean, default=True)
    consecutive_failures = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trust_score = Column(Float, default=5.0)
    broken_pages_count = Column(Integer, default=0)

    credentials = relationship("SourceCredentials", back_populates="source", uselist=False, cascade="all, delete-orphan")
    crawls = relationship("CrawlHistory", back_populates="source", cascade="all, delete-orphan")
    analytics = relationship("SearchAnalytics", back_populates="source", cascade="all, delete-orphan")

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    search_time_ms = Column(Float, default=0.0)
    results_returned = Column(Integer, default=0)
    verified_results = Column(Integer, default=0)
    rejected_results = Column(Integer, default=0)
    new_opportunities = Column(Integer, default=0)
    updated_opportunities = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    avg_match_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    source = relationship("Source", back_populates="analytics")

class CrawlReplayLog(Base):
    __tablename__ = "crawl_replay_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    tender_id = Column(Integer, nullable=True)
    url = Column(String(512), nullable=False)
    http_status = Column(Integer, default=200)
    request_headers_json = Column(JSON, nullable=True)
    response_headers_json = Column(JSON, nullable=True)
    raw_html_snapshot = Column(Text, nullable=True)
    extracted_json = Column(JSON, nullable=True)
    documents_downloaded = Column(JSON, nullable=True)
    ai_prompt_payload = Column(Text, nullable=True)
    ai_response_payload = Column(Text, nullable=True)
    logs_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SourceCredentials(Base):
    __tablename__ = "source_credentials"
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, unique=True)
    auth_type = Column(String(50), default="basic")
    username = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=True)
    api_key_hash = Column(String(512), nullable=True)
    token_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source = relationship("Source", back_populates="credentials")

class ScheduledJobLog(Base):
    __tablename__ = "scheduled_job_logs"
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), nullable=False)
    status = Column(String(50), default="running")
    last_run = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    next_run = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    result_summary = Column(Text, nullable=True)
    error_log = Column(Text, nullable=True)

class CrawlHistory(Base):
    __tablename__ = "crawl_history"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finish_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")
    tenders_found = Column(Integer, default=0)
    tenders_added = Column(Integer, default=0)
    tenders_updated = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    
    source = relationship("Source", back_populates="crawls")
