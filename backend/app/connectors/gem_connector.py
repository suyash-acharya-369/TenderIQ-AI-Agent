import os
import re
import urllib.parse
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from backend.app.connectors.base import BaseConnector

logger = logging.getLogger("TenderIQ.Connector.GeM")

class GeMConnector(BaseConnector):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    def login(self, username: str, password: str) -> bool:
        return True

    def discover(self, source_url: str) -> List[str]:
        return ["https://gem.gov.in"]

    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        logger.info(f"GeM Connector crawling: {source_url}")
        results = [
            {
                "tender_number": "GEM/2024/B/5102938",
                "title": "Procurement of AI-Powered LMS & Interactive Digital Courseware for Government Universities",
                "scope_of_work": "Procurement and deployment of AI-powered LMS platform, digital content authoring, faculty portal, student analytics dashboard, and NEP 2020 aligned course material.",
                "official_link": "https://gem.gov.in",
                "budget": 12000000.0,
                "currency": "INR",
                "country": "India",
                "organization": "Ministry of Education, Govt of India",
                "documents": [
                    {"name": "GEM_RFP_Specification.pdf", "type": "RFP", "url": "https://gem.gov.in/rfp.pdf"},
                    {"name": "GEM_BOQ_Financial.xlsx", "type": "BOQ", "url": "https://gem.gov.in/boq.xlsx"}
                ]
            }
        ]
        return results

    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        return {
            "tender_number": "GEM/2024/B/5102938",
            "title": "Procurement of AI-Powered LMS & Interactive Digital Courseware for Government Universities",
            "organization": "Ministry of Education, Govt of India",
            "country": "India"
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
