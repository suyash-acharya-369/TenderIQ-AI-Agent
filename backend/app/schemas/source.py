from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SourceBase(BaseModel):
    name: str
    website_url: str
    country: Optional[str] = "India"
    category: Optional[str] = "Government"
    connector_type: Optional[str] = "Public"
    search_url: Optional[str] = None
    tender_selector: Optional[str] = None
    pdf_selector: Optional[str] = None
    pagination_selector: Optional[str] = None
    frequency: Optional[str] = "daily"
    priority: Optional[int] = 1

class SourceCreate(SourceBase):
    username: Optional[str] = None
    password: Optional[str] = None

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    connector_type: Optional[str] = None
    frequency: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

class SourceResponse(SourceBase):
    id: int
    status: str
    health_status: str
    last_crawl: Optional[datetime] = None
    next_crawl: Optional[datetime] = None

    class Config:
        from_attributes = True
