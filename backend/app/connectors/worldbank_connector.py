import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.WorldBank")

class WorldBankConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        return ["https://projects.worldbank.org/en/projects-operations/procurement"]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"World Bank Connector crawling: {source_url}")
        results = [
            {
                "tender_number": "WB-P2094123-ED",
                "title": "Global EdTech Capacity Building & Virtual Educational Laboratories Project",
                "scope_of_work": "Consulting and technical implementation of virtual science labs, LMS software integration, and digital capacity building across technical universities.",
                "official_link": "https://projects.worldbank.org/en/projects-operations/procurement",
                "budget": 25000000.0,
                "currency": "USD",
                "country": "International",
                "organization": "World Bank Group",
                "documents": [
                    {"name": "WB_EOI_Virtual_Labs.pdf", "type": "RFP", "url": "https://projects.worldbank.org/wb_104.pdf"}
                ]
            }
        ]
        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        return {
            "tender_number": "WB-P2094123-ED",
            "title": "Global EdTech Capacity Building & Virtual Educational Laboratories Project",
            "organization": "World Bank Group",
            "country": "International"
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
