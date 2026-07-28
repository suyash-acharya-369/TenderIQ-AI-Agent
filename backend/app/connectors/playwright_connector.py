import logging
import httpx
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.Playwright")

class PlaywrightConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        """Return the source URL as the listing page."""
        return [source_url]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"Executing Playwright browser automation crawl for: {source_url}")
        
        try:
            from playwright.sync_api import sync_playwright
            results: List[Dict[str, Any]] = []

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(source_url, timeout=20000, wait_until="domcontentloaded")

                # Use selector if provided
                target_selector = tender_selector or ".bid-card, .tender-list-row, table tr, article"
                elements = page.query_selector_all(target_selector)

                for i, el in enumerate(elements[:10]):
                    text = el.inner_text()
                    if text and len(text) > 15:
                        link_el = el.query_selector("a")
                        href = link_el.get_attribute("href") if link_el else source_url
                        results.append({
                            "tender_number": f"PW-{i+301}",
                            "title": text.split("\n")[0][:250],
                            "scope_of_work": f"Playwright browser rendered tender card: {text[:400]}",
                            "official_link": href or source_url,
                            "budget": 5000000.0,
                            "currency": "INR",
                            "country": "India"
                        })

                browser.close()
                if results:
                    logger.info(f"Playwright crawl extracted {len(results)} items from {source_url}")
                    return results

        except Exception as e:
            logger.warning(f"Playwright browser automation notice for {source_url}: {e}. Falling back to HTTPX/BeautifulSoup.")

        # Fallback to Generic HTTPX / BeautifulSoup connector
        from backend.app.connectors.generic import GenericConnector
        fallback = GenericConnector()
        return fallback.crawl(source_url, tender_selector, pdf_selector, pagination_selector)

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        """Extract metadata from rendered page content."""
        return {"source_url": source_url}

    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        """Delegate document download to generic connector."""
        from backend.app.connectors.generic import GenericConnector
        return GenericConnector().download_documents(tender_url, save_dir)

    def verify(self, tender_url: str) -> Dict[str, Any]:
        """Verify URL reachability."""
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
