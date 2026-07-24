from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.user import UserCreate, UserUpdate, UserResponse
from backend.app.utils.security import hash_password
from backend.app.api.deps import require_role

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = Query(None),
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    return [UserResponse.from_orm(u) for u in query.all()]

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(u)

@router.post("", response_model=UserResponse)
def create_user(
    payload: UserCreate,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="User email already exists")

    u = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role or "Viewer",
        is_active=True
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    audit = AuditLog(user_email=admin.email, action=f"Created User: {u.email} ({u.role})")
    db.add(audit)
    db.commit()

    return UserResponse.from_orm(u)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        u.hashed_password = hash_password(data.pop("password"))

    for k, v in data.items():
        setattr(u, k, v)

    db.commit()
    db.refresh(u)

    audit = AuditLog(user_email=admin.email, action=f"Updated User ID: {u.id}")
    db.add(audit)
    db.commit()

    return UserResponse.from_orm(u)

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(require_role("Administrator")),
    db: Session = Depends(get_db)
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(u)
    db.commit()

    audit = AuditLog(user_email=admin.email, action=f"Deleted User: {u.email}")
    db.add(audit)
    db.commit()

    return {"status": "success"}

from pydantic import BaseModel
from typing import Dict, Any

class PreferencesPayload(BaseModel):
    preferences: Dict[str, Any]

from backend.app.api.deps import get_current_user

@router.put("/me/preferences")
def update_my_preferences(
    payload: PreferencesPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.notification_preferences = payload.preferences
    db.commit()
    db.refresh(current_user)
    return {"status": "success", "preferences": current_user.notification_preferences}
