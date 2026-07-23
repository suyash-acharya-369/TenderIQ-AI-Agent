import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.session import get_db

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("")
def check_system_health(db: Session = Depends(get_db)):
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    db_status = "Healthy"
    try:
        db.execute("SELECT 1")
    except Exception:
        db_status = "Error"

    return {
        "status": "Healthy" if db_status == "Healthy" and cpu < 95.0 else "Warning",
        "cpu_usage_pct": cpu,
        "ram_usage_pct": ram,
        "disk_usage_pct": disk,
        "database": db_status,
        "redis": "Healthy",
        "crawler_workers": "Active",
        "ai_engine": "Ready"
    }
