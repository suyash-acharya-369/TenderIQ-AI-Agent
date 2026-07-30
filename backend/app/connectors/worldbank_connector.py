import logging
import httpx
from typing import Dict, Any, List
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.WorldBank")

class WorldBankConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "TenderIQ-Enterprise-Crawler/3.1",
        "Accept": "application/json"
    }

    def connect(self) -> bool:
        return True

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        return True

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.head("https://search.worldbank.org/")
                return res.status_code < 400
        except:
            return False

    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        url = f"https://search.worldbank.org/api/v2/projects?format=json&qterm={keyword}"
        logger.info(f"WorldBank Connector LIVE search: {url}")
        
        try:
            with httpx.Client(timeout=15.0, headers=self.HEADERS) as client:
                res = client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    projects = data.get("projects", {})
                    # WorldBank API returns a dict of projects where keys are project IDs
                    results = []
                    for pid, pdata in projects.items():
                        if isinstance(pdata, dict):
                            results.append(pdata)
                    return results
        except Exception as e:
            logger.error(f"WorldBank API Search failed: {e}")
            
        return []

    def parse_search_results(self, raw_results: Any) -> List[Dict[str, Any]]:
        results = []
        for pdata in raw_results:
            pid = pdata.get("id")
            title = pdata.get("project_name")
            if not pid or not title:
                continue
                
            results.append({
                "tender_number": pid,
                "title": title,
                "official_link": f"https://projects.worldbank.org/en/projects-operations/project-detail/{pid}",
                "organization": "World Bank Group",
                "publication_date": pdata.get("boardapprovaldate"),
                "budget": pdata.get("totalamt"),
                "country": pdata.get("countryshortname")
            })
        return results

    def open_tender(self, tender_url: str) -> str:
        try:
            with httpx.Client(timeout=15.0, headers=self.HEADERS) as client:
                res = client.get(tender_url)
                return res.text if res.status_code == 200 else ""
        except:
            return ""

    def extract_metadata(self, html_content: str, tender_url: str) -> Dict[str, Any]:
        """Since we already have basic metadata from the API, we can parse HTML for more details or return empty."""
        metadata = {
            "extracted_fields_json": {}
        }
        # In a full implementation, BeautifulSoup would parse the Project Detail page for more specifics
        return metadata

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        return []

    def extract_pdf(self, file_path: str) -> Dict[str, Any]:
        return {}

    def verify(self, tender_data: Dict[str, Any]) -> bool:
        if not tender_data.get("title") or not tender_data.get("tender_number"):
            return False
        return True

    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        changes = {}
        if old_data.get("budget") != new_data.get("budget") and new_data.get("budget"):
            changes["budget"] = {"old": old_data.get("budget"), "new": new_data.get("budget")}
        return changes

    def archive(self, tender_id: str) -> bool:
        return True

    def rate_limiting(self) -> None:
        pass

    def error_handling(self, error: Exception) -> None:
        pass
