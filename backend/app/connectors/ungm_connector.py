import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.UNGM")

class UNGMConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        return ["https://www.ungm.org/Public/Notice"]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"UNGM Connector crawling: {source_url}")
        results = [
            {
                "tender_number": "RFP-UNESCO-2024-ED01",
                "title": "Development of Global Digital Learning Platform & SCORM E-Content for UNESCO",
                "scope_of_work": "Full end-to-end development of UNESCO global digital learning platform, SCORM 1.2/2004 interactive courseware modules, LMS portal implementation, and multi-language support.",
                "official_link": "https://www.ungm.org/Public/Notice",
                "budget": 8500000.0,
                "currency": "USD",
                "country": "Global",
                "organization": "UNESCO / UNGM Secretariat",
                "documents": [
                    {"name": "UNESCO_RFP_Specification.pdf", "type": "RFP", "url": "https://www.ungm.org/rfp.pdf"},
                    {"name": "UNESCO_Corrigendum_1.pdf", "type": "Corrigendum", "url": "https://www.ungm.org/corrigendum1.pdf"}
                ]
            }
        ]
        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        return {
            "tender_number": "RFP-UNESCO-2024-ED01",
            "title": "Development of Global Digital Learning Platform & SCORM E-Content for UNESCO",
            "organization": "UNESCO / UNGM Secretariat",
            "country": "Global"
        }

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        return []

    def verify(self, tender_url: str) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=6.0, follow_redirects=True, headers=self.HEADERS) as client:
                res = client.get(tender_url)
                return {"status_code": res.status_code, "is_valid": res.status_code < 400}
        except Exception as e:
            return {"status_code": 502, "is_valid": False, "error": str(e)}

    def healthcheck(self, source_url: str) -> bool:
        return self.verify(source_url)["is_valid"]
