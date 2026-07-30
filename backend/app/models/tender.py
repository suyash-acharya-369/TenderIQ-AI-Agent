from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    country = Column(String(100), default="India")
    website = Column(String(512), nullable=True)
    sector = Column(String(100), default="Government")
    previous_tenders_count = Column(Integer, default=0)
    ai_insights = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tenders = relationship("Tender", back_populates="organization")

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    tender_uid = Column(String(64), unique=True, index=True, nullable=False) # SHA256(URL+RFP+Org+Date)
    tender_number = Column(String(100), index=True, nullable=False)
    title = Column(String(512), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    
    country = Column(String(100), default="India", index=True)
    state = Column(String(100), nullable=True)
    sector = Column(String(100), default="Education", index=True)
    
    budget = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")
    publication_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    submission_deadline = Column(DateTime, nullable=True, index=True)
    
    status = Column(String(50), default="Active", index=True)  # Active, Expired, Awarded, Cancelled
    lifecycle_stage = Column(String(50), default="Discovered", index=True)  
    moderation_status = Column(String(50), default="VERIFIED", index=True) 
    access_status = Column(String(50), default="Verified")     
    verification_status = Column(String(50), default="VERIFIED", index=True)  
    integrity_score = Column(Float, default=100.0)  
    url_status_code = Column(Integer, default=200)
    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    official_link = Column(String(512), nullable=True)
    source_urls_json = Column(JSON, nullable=True)  
    
    state_region = Column(String(100), nullable=True)
    buyer_contact = Column(String(255), nullable=True)
    procurement_method = Column(String(100), nullable=True)
    cpv_code = Column(String(50), nullable=True)
    industry_classification = Column(String(100), nullable=True)
    funding_agency = Column(String(150), nullable=True)
    contract_duration = Column(String(100), nullable=True)
    
    # Field-Level extraction data (V3.1 Requirement)
    # Stored as JSON: {"budget": {"value": 10000, "confidence": 99, "method": "Regex", "evidence": "page 2"}, ...}
    extracted_fields_json = Column(JSON, nullable=True)
    
    scope_of_work = Column(Text, nullable=True)
    deliverables = Column(Text, nullable=True)
    eligibility_criteria = Column(Text, nullable=True)
    technical_requirements = Column(Text, nullable=True)
    financial_requirements = Column(Text, nullable=True)
    required_documents = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_citations = Column(JSON, nullable=True)     
    keyword_evidence = Column(JSON, nullable=True) 
    search_explanation_json = Column(JSON, nullable=True) # V3.1 Detailed matching logic
    risk_analysis = Column(Text, nullable=True)
    bid_recommendation = Column(String(50), default="Bid")     
    winning_probability = Column(Float, default=75.0)
    estimated_team = Column(String(255), nullable=True)
    estimated_duration = Column(String(100), nullable=True)
    
    keyword_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    ai_score = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0)
    overall_match_score = Column(Float, default=0.0, index=True)
    
    raw_metadata = Column(JSON, nullable=True)
    parsed_text = Column(Text, nullable=True)
    embedding_json = Column(JSON, nullable=True)  
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization", back_populates="tenders")
    versions = relationship("TenderVersion", back_populates="tender", cascade="all, delete-orphan")
    attachments = relationship("TenderAttachment", back_populates="tender", cascade="all, delete-orphan")
    evidence_package = relationship("TenderEvidence", back_populates="tender", uselist=False, cascade="all, delete-orphan")

class TenderEvidence(Base):
    __tablename__ = "tender_evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, unique=True)
    html_snapshot_path = Column(String(512), nullable=True)
    screenshot_path = Column(String(512), nullable=True)
    crawler_logs_json = Column(JSON, nullable=True)
    network_traces_json = Column(JSON, nullable=True)
    verification_timeline_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    tender = relationship("Tender", back_populates="evidence_package")

class TenderVersion(Base):
    __tablename__ = "tender_versions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, default=1)
    change_type = Column(String(100), default="Corrigendum")  # Deadline, Budget, Corrigendum, Scope
    changes_json = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="versions")

class TenderAttachment(Base):
    __tablename__ = "tender_attachments"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(50), default="default_ws", index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), default="PDF")  
    document_classification = Column(String(100), default="Tender Notice") # V3.1 Document Classification
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    pages = Column(Integer, default=0)
    language = Column(String(50), default="en")
    version_number = Column(Integer, default=1)
    processing_status = Column(String(50), default="Pending")  
    ocr_applied = Column(Boolean, default=False)
    virus_scanned = Column(Boolean, default=True)
    hash_sha256 = Column(String(64), nullable=True)
    parsed_content = Column(Text, nullable=True)
    table_extraction_json = Column(JSON, nullable=True) # Multi-Document OCR
    layout_extraction_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="attachments")

class HumanReviewQueue(Base):
    __tablename__ = "human_review_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    tender_uid = Column(String(64), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(255), nullable=False) # e.g., "CAPTCHA Required", "Low OCR Confidence"
    context_json = Column(JSON, nullable=True)
    status = Column(String(50), default="Pending") # Pending, Approved, Rejected, Retried
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
