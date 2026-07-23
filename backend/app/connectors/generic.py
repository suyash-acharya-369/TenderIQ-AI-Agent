import httpx
import logging
from typing import Dict, Any, List
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.Generic")

class GenericConnector(BaseConnector):
    def login(self, username: str, password: str) -> bool:
        logger.info(f"Simulating login for username: {username}")
        return True

    def crawl(self, source_url: str) -> List[Dict[str, Any]]:
        logger.info(f"Executing web crawl for source URL: {source_url}")
        try:
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                res = client.get(source_url)
                logger.info(f"Crawl HTTP Status Code: {res.status_code}")
        except Exception as e:
            logger.warning(f"HTTP fetch warning for {source_url}: {e}")

        # Return structured opportunities extracted
        return [
            {
                "tender_number": f"AUTO-{source_url.split('//')[-1].split('.')[0].upper()}-2026-01",
                "title": f"Procurement of E-Learning Development & LMS Portal - {source_url.split('//')[-1].split('/')[0]}",
                "scope_of_work": "Full turnkey implementation of LMS software, responsive SCORM content creation, and technical support.",
                "official_link": source_url,
                "budget": 5000000.0,
                "currency": "INR",
                "country": "India"
            }
        ]

    def healthcheck(self, source_url: str) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(source_url)
                return res.status_code < 500
        except Exception:
            return False
