from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.ai import PromptTemplate
from backend.app.models.user import User
from backend.app.api.deps import require_role

router = APIRouter(prefix="/prompts", tags=["AI Prompt Templates"])

class PromptUpdate(BaseModel):
    template_text: str
    provider: str = "openai"

@router.get("")
def list_prompts(admin: User = Depends(require_role("Administrator")), db: Session = Depends(get_db)):
    prompts = db.query(PromptTemplate).all()
    return prompts

@router.put("/{prompt_id}")
def update_prompt(prompt_id: int, payload: PromptUpdate, admin: User = Depends(require_role("Administrator")), db: Session = Depends(get_db)):
    pt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Prompt Template not found")
    pt.template_text = payload.template_text
    pt.provider = payload.provider
    db.commit()
    db.refresh(pt)
    return pt

