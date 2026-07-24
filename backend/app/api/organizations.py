from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.tender import Organization, Tender
from backend.app.models.user import User
from backend.app.schemas.tender import OrganizationResponse, TenderResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/organizations", tags=["Organizations"])

class OrganizationCreate(BaseModel):
    name: str
    country: Optional[str] = "India"
    sector: Optional[str] = "Government"
    website: Optional[str] = None
    ai_insights: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[str] = None
    ai_insights: Optional[str] = None

@router.get("", response_model=List[OrganizationResponse])
def list_organizations(
    q: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Organization)
    if q:
        query = query.filter(Organization.name.ilike(f"%{q}%"))
    if country:
        query = query.filter(Organization.country.ilike(f"%{country}%"))
    return [OrganizationResponse.from_orm(o) for o in query.all()]

@router.get("/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(Organization).filter(Organization.id == org_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationResponse.from_orm(o)

@router.get("/{org_id}/tenders", response_model=List[TenderResponse])
def get_organization_tenders(org_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenders = db.query(Tender).filter(Tender.organization_id == org_id).all()
    return [TenderResponse.from_orm(t) for t in tenders]

@router.post("", response_model=OrganizationResponse)
def create_organization(payload: OrganizationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Organization with this name already exists")
    o = Organization(
        name=payload.name,
        country=payload.country or "India",
        sector=payload.sector or "Government",
        website=payload.website,
        ai_insights=payload.ai_insights
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return OrganizationResponse.from_orm(o)

@router.put("/{org_id}", response_model=OrganizationResponse)
def update_organization(org_id: int, payload: OrganizationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(Organization).filter(Organization.id == org_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Organization not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return OrganizationResponse.from_orm(o)
