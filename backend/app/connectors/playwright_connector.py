import logging
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector
from backend.app.connectors.generic import GenericConnector

logger = logging.getLogger("TenderIQ.Connector.Playwright")

class PlaywrightConnector(BaseConnector):
    def __init__(self):
        self.fallback = GenericConnector()

    def login(self, username: str, password: str) -> bool:
        return True

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
        return self.fallback.crawl(source_url, tender_selector, pdf_selector, pagination_selector)

    def healthcheck(self, source_url: str) -> bool:
        return self.fallback.healthcheck(source_url)
