import os
import zipfile
import shutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = logging.getLogger("TenderIQ.BackupService")

BACKUP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/backups"))


def create_system_backup() -> Dict[str, Any]:
    """Phase 24: Package SQLite DB, PDF attachments, and system configurations into a zip archive."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    zip_filename = f"tenderiq_backup_{timestamp}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_filename)

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../tenderiq.db"))
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.env"))
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage"))

    files_backed_up = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(db_path):
            zipf.write(db_path, arcname="tenderiq.db")
            files_backed_up += 1
        if os.path.exists(env_path):
            zipf.write(env_path, arcname=".env")
            files_backed_up += 1

        if os.path.exists(storage_dir):
            for root, _, files in os.walk(storage_dir):
                if "backups" in root:
                    continue  # Don't recurse into backups dir
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, storage_dir)
                    zipf.write(full_p, arcname=os.path.join("storage", rel_p))
                    files_backed_up += 1

    file_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
    logger.info(f"System Backup created: {zip_filename} ({file_size} bytes, {files_backed_up} files)")

    return {
        "success": True,
        "backup_filename": zip_filename,
        "backup_path": zip_path,
        "size_bytes": file_size,
        "files_count": files_backed_up,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def list_backups() -> List[Dict[str, Any]]:
    """List available backup archives."""
    if not os.path.exists(BACKUP_DIR):
        return []
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".zip"):
            p = os.path.join(BACKUP_DIR, f)
            stat = os.stat(p)
            backups.append({
                "filename": f,
                "path": p,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    backups.sort(key=lambda x: x["created_at"], reverse=True)
    return backups


def restore_backup(backup_filename: str) -> Dict[str, Any]:
    """Restore system state from a specified backup zip archive."""
    zip_path = os.path.join(BACKUP_DIR, backup_filename)
    if not os.path.exists(zip_path):
        return {"success": False, "error": f"Backup file {backup_filename} not found."}

    extract_tmp = os.path.join(BACKUP_DIR, "tmp_restore")
    os.makedirs(extract_tmp, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_tmp)

        restored = []
        # Restore DB if present
        restored_db = os.path.join(extract_tmp, "tenderiq.db")
        target_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../tenderiq.db"))
        if os.path.exists(restored_db):
            shutil.copy2(restored_db, target_db)
            restored.append("Database (tenderiq.db)")

        shutil.rmtree(extract_tmp, ignore_errors=True)
        return {
            "success": True,
            "backup_filename": backup_filename,
            "restored_components": restored,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"Backup restore failed: {e}")
        return {"success": False, "error": str(e)}
