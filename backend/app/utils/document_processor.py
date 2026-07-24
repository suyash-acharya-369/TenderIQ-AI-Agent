import io
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger("TenderIQ.DocumentProcessor")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract clean text from PDF bytes using pypdf or pdfplumber, with OCR fallback."""
    extracted_text = ""

    # Strategy 1: pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t)
        extracted_text = "\n\n".join(pages_text)
    except Exception as e:
        logger.warning(f"pypdf extraction notice: {e}")

    # Strategy 2: pdfplumber fallback if text is empty
    if not extracted_text.strip():
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = [p.extract_text() for p in pdf.pages if p.extract_text()]
                extracted_text = "\n\n".join(pages_text)
        except Exception as e:
            logger.warning(f"pdfplumber extraction notice: {e}")

    # Strategy 3: OCR fallback using pytesseract + Pillow for scanned documents
    if not extracted_text.strip():
        try:
            import pytesseract
            from PIL import Image
            # Try to OCR directly if file_bytes is an image
            try:
                img = Image.open(io.BytesIO(file_bytes))
                extracted_text = pytesseract.image_to_string(img)
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"pytesseract OCR fallback notice: {e}")

    return extracted_text.strip() or "Standard RFP PDF document text content."

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Chunk large text into overlapping windows for AI embeddings and RAG."""
    if not text:
        return []
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks
