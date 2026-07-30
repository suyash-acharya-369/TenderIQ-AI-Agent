import re
import urllib.parse
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.Generic")

class GenericConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "TenderIQ-Enterprise-Crawler/3.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

    def connect(self) -> bool:
        return True

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        # Generic connector has no auth by default
        return True

    def health_check(self) -> bool:
        return True

    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """Simulated search. Since generic doesn't know the exact URL structure, it just returns a mock payload of HTML for parsing."""
        # Note: In reality, a specific connector (GeMConnector) will implement the actual search URL logic.
        return [{"html": f"<html><body><a href='https://example.com/tender/123'>Tender for {keyword}</a></body></html>"}]

    def parse_search_results(self, raw_results: Any) -> List[Dict[str, Any]]:
        results = []
        for res in raw_results:
            html = res.get("html", "")
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = a.get_text(strip=True)
                if len(title) > 5:
                    results.append({
                        "tender_number": "UNKNOWN", # Will be extracted later
                        "title": title,
                        "official_link": a["href"],
                        # Zero Hallucination: Do not add fake budgets or dates here!
                    })
        return results

    def open_tender(self, tender_url: str) -> str:
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True, headers=self.HEADERS) as client:
                res = client.get(tender_url)
                if res.status_code < 400:
                    return res.text
        except Exception as e:
            logger.warning(f"Failed to open tender {tender_url}: {e}")
        return ""

    def extract_metadata(self, html_content: str, tender_url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(html_content, "lxml")
        
        # Zero Hallucination: We only extract what we can find. If not found, leave it as None.
        metadata = {
            "title": soup.title.string if soup.title else None,
            "budget": None,
            "submission_deadline": None,
            "extracted_fields_json": {}
        }

        # Try to find RFP number heuristically
        rfp_match = re.search(r'(RFP|Tender No|Reference No)[\s:-]+([A-Z0-9/-]+)', html_content, re.IGNORECASE)
        if rfp_match:
            metadata["tender_number"] = rfp_match.group(2)
            metadata["extracted_fields_json"]["tender_number"] = {"value": rfp_match.group(2), "confidence": 0.8, "method": "Regex"}

        return metadata

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        # V3.1 implementation should use Playwright to bypass JS protected downloads
        return []

    def extract_pdf(self, file_path: str) -> Dict[str, Any]:
        return {}

    def verify(self, tender_data: Dict[str, Any]) -> bool:
        # If we couldn't even extract a title or tender number, verification fails
        if not tender_data.get("title") or not tender_data.get("tender_number"):
            return False
        return True

    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        changes = {}
        for k in ["budget", "deadline"]:
            if old_data.get(k) != new_data.get(k) and new_data.get(k) is not None:
                changes[k] = {"old": old_data.get(k), "new": new_data.get(k)}
        return changes

    def archive(self, tender_id: str) -> bool:
        return True

    def rate_limiting(self) -> None:
        pass

    def error_handling(self, error: Exception) -> None:
        pass
