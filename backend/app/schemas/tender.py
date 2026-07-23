from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel

class TenderAttachmentResponse(BaseModel):
    id: int
    file_name: str
    file_type: str
    file_path: str
    file_size_bytes: int

    class Config:
        from_attributes = True

class TenderVersionResponse(BaseModel):
    id: int
    version_number: int
    change_type: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationResponse(BaseModel):
    id: int
    name: str
    country: str
    sector: str
    website: Optional[str] = None

    class Config:
        from_attributes = True

class TenderResponse(BaseModel):
    id: int
    tender_number: str
    title: str
    country: str
    state: Optional[str] = None
    sector: str
    budget: Optional[float] = None
    currency: str
    publication_date: Optional[datetime] = None
    submission_deadline: Optional[datetime] = None
    status: str
    access_status: str
    official_link: Optional[str] = None
    
    scope_of_work: Optional[str] = None
    deliverables: Optional[str] = None
    eligibility_criteria: Optional[str] = None
    technical_requirements: Optional[str] = None
    financial_requirements: Optional[str] = None
    required_documents: Optional[str] = None
    ai_summary: Optional[str] = None
    risk_analysis: Optional[str] = None
    bid_recommendation: Optional[str] = None
    winning_probability: Optional[float] = None
    estimated_team: Optional[str] = None
    estimated_duration: Optional[str] = None
    
    keyword_score: float
    semantic_score: float
    ai_score: float
    priority_score: float
    overall_match_score: float
    
    organization: Optional[OrganizationResponse] = None
    attachments: List[TenderAttachmentResponse] = []
    versions: List[TenderVersionResponse] = []

    class Config:
        from_attributes = True
