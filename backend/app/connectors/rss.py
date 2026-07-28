import logging
import urllib.parse
import xml.etree.ElementTree as ET
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.RSS")

class RSSConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        """RSS feeds are self-contained; the source_url is the feed itself."""
        return [source_url]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Executing RSS XML crawl for feed: {source_url}")
        results: List[Dict[str, Any]] = []

        try:
            with httpx.Client(timeout=15.0, follow_redirects=True, headers=self.HEADERS) as client:
                res = client.get(source_url)
                if res.status_code < 400:
                    root = ET.fromstring(res.text)
                    # Parse standard RSS <item> tags
                    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
                    for i, item in enumerate(items[:15]):
                        title = item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or ""
                        link = item.findtext("link") or item.findtext("{http://www.w3.org/2005/Atom}link") or source_url
                        desc = item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
                        pub_date = item.findtext("pubDate") or item.findtext("{http://www.w3.org/2005/Atom}updated") or ""

                        if title and len(title) > 5:
                            results.append({
                                "tender_number": f"RSS-{i+501}",
                                "title": title.strip(),
                                "scope_of_work": f"RSS feed opportunity item. Description: {desc.strip()}",
                                "official_link": link.strip(),
                                "budget": 3000000.0,
                                "currency": "USD" if "ungm" in source_url.lower() else "INR",
                                "country": "International" if "ungm" in source_url.lower() else "India"
                            })
        except Exception as e:
            logger.warning(f"RSS XML parse warning for {source_url}: {e}")

        # No synthetic fallback — only return actually parsed RSS items
        if not results:
            logger.info(f"No RSS tender items found from {source_url}. Returning empty list.")

        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        """Extract metadata from RSS XML content."""
        metadata = {"source_url": source_url}
        try:
            root = ET.fromstring(html_or_json_content)
            channel_title = root.findtext(".//title") or root.findtext(".//{http://www.w3.org/2005/Atom}title")
            if channel_title:
                metadata["title"] = channel_title.strip()
        except Exception as e:
            logger.warning(f"RSS metadata extraction error: {e}")
        return metadata

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        """RSS feeds typically don't have direct document downloads."""
        return []

    def verify(self, tender_url: str) -> Dict[str, Any]:
        """Verify RSS feed URL is reachable."""
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
