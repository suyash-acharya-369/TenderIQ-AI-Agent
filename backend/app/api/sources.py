from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.source import Source, SourceCredentials
from backend.app.models.user import User
from backend.app.schemas.source import SourceCreate, SourceUpdate, SourceResponse
from backend.app.crawler.engine import run_source_crawl
from backend.app.utils.encryption import encrypt_data
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/sources", tags=["Source Manager"])

@router.get("", response_model=List[SourceResponse])
def list_sources(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.priority.desc(), Source.id.asc()).all()
    return [SourceResponse.from_orm(s) for s in sources]

@router.post("", response_model=SourceResponse)
def create_source(payload: SourceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = Source(
        name=payload.name,
        website_url=payload.website_url,
        country=payload.country,
        category=payload.category,
        connector_type=payload.connector_type,
        search_url=payload.search_url,
        tender_selector=payload.tender_selector,
        pdf_selector=payload.pdf_selector,
        pagination_selector=payload.pagination_selector,
        frequency=payload.frequency,
        priority=payload.priority,
        status="active",
        health_status="Healthy"
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    if payload.username or payload.password:
        creds = SourceCredentials(
            source_id=source.id,
            encrypted_username=encrypt_data(payload.username) if payload.username else None,
            encrypted_password=encrypt_data(payload.password) if payload.password else None
        )
        db.add(creds)
        db.commit()

    return SourceResponse.from_orm(source)

@router.post("/{source_id}/run-crawl")
def trigger_source_crawl(source_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    res = run_source_crawl(source_id, db)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/{source_id}/toggle-pause")
def toggle_source_pause(source_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.status = "paused" if source.status == "active" else "active"
    db.commit()
    return {"status": "success", "new_status": source.status}

@router.delete("/{source_id}")
def delete_source(source_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"status": "success", "deleted_id": source_id}

@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, payload: SourceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    update_data = payload.model_dump(exclude_unset=True)
    # Handle credentials separately
    cred_fields = {"username", "password"}
    for key, val in update_data.items():
        if key not in cred_fields:
            setattr(source, key, val)
    if update_data.get("username") or update_data.get("password"):
        creds = db.query(SourceCredentials).filter(SourceCredentials.source_id == source.id).first()
        if not creds:
            creds = SourceCredentials(source_id=source.id)
            db.add(creds)
        if update_data.get("username"):
            creds.encrypted_username = encrypt_data(update_data["username"])
        if update_data.get("password"):
            creds.encrypted_password = encrypt_data(update_data["password"])
    db.commit()
    db.refresh(source)
    return SourceResponse.from_orm(source)

@router.get("/{source_id}/logs")
def get_source_crawl_logs(source_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    crawls = db.query(CrawlHistory).filter(CrawlHistory.source_id == source_id).order_by(CrawlHistory.start_time.desc()).limit(20).all()
    return [
        {
            "id": c.id,
            "start_time": c.start_time,
            "finish_time": c.finish_time,
            "duration_seconds": c.duration_seconds,
            "opportunities_found": c.opportunities_found,
            "new_opportunities": c.new_opportunities,
            "updated_opportunities": c.updated_opportunities,
            "status": c.status,
            "error_message": c.error_message
        }
        for c in crawls
    ]

