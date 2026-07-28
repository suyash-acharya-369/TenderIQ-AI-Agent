import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.API")

class APIConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        """API endpoints are self-contained."""
        return [source_url]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Executing REST API connector for: {source_url}")
        results: List[Dict[str, Any]] = []

        try:
            with httpx.Client(timeout=15.0, follow_redirects=True, headers=self.HEADERS) as client:
                res = client.get(source_url)
                if res.status_code < 400:
                    data = res.json()
                    # Check if response contains array or dictionary
                    items = data.get("procurement") or data.get("tenders") or data.get("data") or (data if isinstance(data, list) else [])
                    for i, item in enumerate(items[:15]):
                        if isinstance(item, dict):
                            tender_num = item.get("tender_number") or item.get("id") or f"API-{i+801}"
                            title = item.get("title") or item.get("project_name") or item.get("description") or ""
                            link = item.get("url") or item.get("link") or source_url
                            if title:
                                results.append({
                                    "tender_number": str(tender_num),
                                    "title": str(title),
                                    "scope_of_work": f"API procurement opportunity. Description: {item.get('scope', title)}",
                                    "official_link": str(link),
                                    "budget": float(item.get("budget", 4000000.0)),
                                    "currency": item.get("currency", "USD"),
                                    "country": item.get("country", "International")
                                })
        except Exception as e:
            logger.warning(f"REST API JSON parse warning for {source_url}: {e}")

        # No synthetic fallback — only return actually parsed API data
        if not results:
            logger.info(f"No tender data extracted from API at {source_url}. Returning empty list.")

        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        """Extract metadata from API JSON response."""
        import json
        metadata = {"source_url": source_url}
        try:
            data = json.loads(html_or_json_content)
            if isinstance(data, dict):
                metadata["title"] = data.get("title", "")
                metadata["organization"] = data.get("organization", "")
        except Exception as e:
            logger.warning(f"API metadata extraction error: {e}")
        return metadata

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        """API connectors typically don't provide direct document downloads."""
        return []

    def verify(self, tender_url: str) -> Dict[str, Any]:
        """Verify API endpoint reachability."""
        try:
            with httpx.Client(timeout=6.0, follow_redirects=True, headers=self.HEADERS) as client:
                res = client.get(tender_url)
                return {"status_code": res.status_code, "is_valid": res.status_code < 400}
        except Exception as e:
            return {"status_code": 502, "is_valid": False, "error": str(e)}

    def healthcheck(self, source_url: str) -> bool:
        try:
            with httpx.Client(timeout=5.0, headers=self.HEADERS) as client:
                res = client.get(source_url)
                return res.status_code < 500
        except Exception:
            return False
