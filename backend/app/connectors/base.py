from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseConnector(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """Authenticate with protected portal."""
        pass

    @abstractmethod
    def discover(self, source_url: str) -> List[str]:
        """Discover tender detail URLs from portal index/listing page."""
        pass

    @abstractmethod
    def crawl(
        self,
        source_url: str,
        tender_selector: Optional[str] = None,
        pdf_selector: Optional[str] = None,
        pagination_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Crawl portal opportunities."""
        pass

    @abstractmethod
    def extract_metadata(self, html_or_json_content: str, source_url: str) -> Dict[str, Any]:
        """Extract structured tender metadata fields from portal page content."""
        pass

    @abstractmethod
    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        """Locate and download all attached documents (RFP, BOQ, Corrigendum, Annexures)."""
        pass

    @abstractmethod
    def verify(self, tender_url: str) -> Dict[str, Any]:
        """Verify URL reachability, status code, and page existence."""
        pass

    @abstractmethod
    def healthcheck(self, source_url: str) -> bool:
        """Check if source site is reachable."""
        pass
