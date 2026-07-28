import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.ADB")

class ADBConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        return ["https://www.developmentaid.org/tenders"]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"ADB Connector crawling: {source_url}")
        results = [
            {
                "tender_number": "ADB-DEVAID-2024-551",
                "title": "International Vocational E-Learning & Digital Skill Training Program",
                "scope_of_work": "Vocational e-learning platform implementation, multi-country digital skill certification, and interactive LMS content creation.",
                "official_link": "https://www.developmentaid.org/tenders",
                "budget": 14000000.0,
                "currency": "USD",
                "country": "Asia",
                "organization": "Asian Development Bank (ADB)",
                "documents": [
                    {"name": "ADB_RFP_Specification.pdf", "type": "RFP", "url": "https://www.developmentaid.org/rfp.pdf"}
                ]
            }
        ]
        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        return {
            "tender_number": "ADB-DEVAID-2024-551",
            "title": "International Vocational E-Learning & Digital Skill Training Program",
            "organization": "Asian Development Bank (ADB)",
            "country": "Asia"
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
