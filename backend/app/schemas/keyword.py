from typing import Optional, List
from pydantic import BaseModel

class KeywordGroupCreate(BaseModel):
    name: str
    positive_keywords: List[str]
    negative_keywords: Optional[List[str]] = []
    mandatory_keywords: Optional[List[str]] = []
    priority_weight: Optional[float] = 1.0
    color: Optional[str] = "#3B82F6"

class KeywordGroupResponse(KeywordGroupCreate):
    id: int
    language: str
    status: str

    class Config:
        from_attributes = True
