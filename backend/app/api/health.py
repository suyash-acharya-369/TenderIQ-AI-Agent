import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.config import settings

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("")
def check_system_health(db: Session = Depends(get_db)):
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    db_status = "Healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "Error"

    # Check AI engine readiness
    ai_status = "Ready" if (settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY) else "No API Key"

    return {
        "status": "Healthy" if db_status == "Healthy" and cpu < 95.0 else "Warning",
        "cpu_usage_pct": cpu,
        "ram_usage_pct": ram,
        "disk_usage_pct": disk,
        "database": db_status,
        "redis": "Not Configured",
        "crawler_workers": "On-Demand",
        "ai_engine": ai_status
    }
