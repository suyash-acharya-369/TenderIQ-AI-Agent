from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.app.config import settings

router = APIRouter(prefix="/settings", tags=["Admin Settings"])

class SettingsPayload(BaseModel):
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    default_ai_provider: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    sender_email: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None
    whatsapp_account_id: Optional[str] = None
    whatsapp_access_token: Optional[str] = None
    storage_provider: Optional[str] = None

@router.get("")
def get_system_settings():
    # Never expose full API keys for security, mask middle characters
    def mask(val: str) -> str:
        if not val:
            return ""
        return val[:4] + "••••••••" + val[-4:] if len(val) > 8 else "••••••••"

    return {
        "default_ai_provider": settings.DEFAULT_AI_PROVIDER,
        "openai_api_key_masked": mask(settings.OPENAI_API_KEY),
        "anthropic_api_key_masked": mask(settings.ANTHROPIC_API_KEY),
        "gemini_api_key_masked": mask(settings.GEMINI_API_KEY),
        "smtp_host": settings.SMTP_HOST,
        "smtp_port": settings.SMTP_PORT,
        "smtp_user": settings.SMTP_USER,
        "sender_email": settings.SENDER_EMAIL,
        "whatsapp_phone_id": settings.WHATSAPP_PHONE_ID,
        "whatsapp_account_id": settings.WHATSAPP_ACCOUNT_ID,
        "storage_provider": settings.STORAGE_PROVIDER
    }

@router.post("")
def update_system_settings(payload: SettingsPayload):
    if payload.openai_api_key is not None:
        settings.OPENAI_API_KEY = payload.openai_api_key
    if payload.anthropic_api_key is not None:
        settings.ANTHROPIC_API_KEY = payload.anthropic_api_key
    if payload.gemini_api_key is not None:
        settings.GEMINI_API_KEY = payload.gemini_api_key
    if payload.default_ai_provider is not None:
        settings.DEFAULT_AI_PROVIDER = payload.default_ai_provider
    if payload.smtp_host is not None:
        settings.SMTP_HOST = payload.smtp_host
    if payload.smtp_port is not None:
        settings.SMTP_PORT = payload.smtp_port
    if payload.smtp_user is not None:
        settings.SMTP_USER = payload.smtp_user
    if payload.smtp_password is not None:
        settings.SMTP_PASSWORD = payload.smtp_password
    if payload.sender_email is not None:
        settings.SENDER_EMAIL = payload.sender_email
    if payload.whatsapp_phone_id is not None:
        settings.WHATSAPP_PHONE_ID = payload.whatsapp_phone_id
    if payload.whatsapp_account_id is not None:
        settings.WHATSAPP_ACCOUNT_ID = payload.whatsapp_account_id
    if payload.whatsapp_access_token is not None:
        settings.WHATSAPP_ACCESS_TOKEN = payload.whatsapp_access_token
    if payload.storage_provider is not None:
        settings.STORAGE_PROVIDER = payload.storage_provider

    return {"status": "success", "message": "System settings updated successfully."}
