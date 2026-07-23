from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.keyword import KeywordGroup
from backend.app.schemas.keyword import KeywordGroupCreate, KeywordGroupResponse

router = APIRouter(prefix="/keywords", tags=["Keyword Manager"])

@router.get("", response_model=List[KeywordGroupResponse])
def list_keyword_groups(db: Session = Depends(get_db)):
    groups = db.query(KeywordGroup).all()
    return [KeywordGroupResponse.from_orm(g) for g in groups]

@router.post("", response_model=KeywordGroupResponse)
def create_keyword_group(payload: KeywordGroupCreate, db: Session = Depends(get_db)):
    group = KeywordGroup(
        name=payload.name,
        positive_keywords=payload.positive_keywords,
        negative_keywords=payload.negative_keywords,
        mandatory_keywords=payload.mandatory_keywords,
        priority_weight=payload.priority_weight,
        color=payload.color,
        status="active"
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return KeywordGroupResponse.from_orm(group)

@router.delete("/{group_id}")
def delete_keyword_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    db.delete(group)
    db.commit()
    return {"status": "success", "deleted_id": group_id}
