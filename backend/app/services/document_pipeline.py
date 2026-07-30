import os
import hashlib
import logging
import httpx
from typing import Dict, Any, List
from backend.app.models.tender import TenderAttachment
from backend.app.utils.document_processor import extract_text_from_pdf

logger = logging.getLogger("TenderIQ.DocumentPipeline")

class DocumentPipeline:
    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def download_and_hash(self, url: str, file_name: str) -> Dict[str, Any]:
        """Download file securely, compute SHA256, and return metadata."""
        safe_name = "".join(c for c in file_name if c.isalnum() or c in " ._-").strip()
        file_path = os.path.join(self.storage_dir, safe_name)
        
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                res = client.get(url)
                res.raise_for_status()
                content = res.content
                
                sha256_hash = hashlib.sha256(content).hexdigest()
                
                with open(file_path, "wb") as f:
                    f.write(content)
                    
                return {
                    "file_path": file_path,
                    "file_size": len(content),
                    "hash": sha256_hash,
                    "content_bytes": content
                }
        except Exception as e:
            logger.error(f"Failed to download document from {url}: {e}")
            return {}

    def process_document(self, tender_id: int, file_info: Dict[str, Any]) -> TenderAttachment:
        """Run OCR if PDF, extract text, and return Attachment object."""
        file_path = file_info["file_path"]
        content = file_info["content_bytes"]
        
        parsed_text = ""
        if file_path.lower().endswith(".pdf"):
            parsed_text = extract_text_from_pdf(content)
            
        attachment = TenderAttachment(
            tender_id=tender_id,
            file_name=os.path.basename(file_path),
            file_type="PDF" if file_path.lower().endswith(".pdf") else "Document",
            file_path=file_path,
            file_size_bytes=file_info["file_size"],
            hash_sha256=file_info["hash"],
            parsed_content=parsed_text[:5000],  # Store first 5k chars in DB, rest in S3/disk
            ocr_applied=True if parsed_text else False
        )
        return attachment
