from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseConnector(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Initialize connection parameters."""
        pass

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the source using provided credentials."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the source is online and reachable."""
        pass

    @abstractmethod
    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """Perform a boolean/exact match search on the portal."""
        pass

    @abstractmethod
    def parse_search_results(self, raw_results: Any) -> List[Dict[str, Any]]:
        """Parse raw search results into standard tender summaries."""
        pass

    @abstractmethod
    def open_tender(self, tender_url: str) -> str:
        """Navigate to or fetch the detailed tender page."""
        pass

    @abstractmethod
    def extract_metadata(self, html_content: str, tender_url: str) -> Dict[str, Any]:
        """Extract all metadata fields with regex/DOM parsing."""
        pass

    @abstractmethod
    def download_documents(self, tender_url: str, save_dir: str) -> List[Dict[str, Any]]:
        """Download all attachments (RFP, BOQ, Corrigendum)."""
        pass

    @abstractmethod
    def extract_pdf(self, file_path: str) -> Dict[str, Any]:
        """OCR and extract text/tables from a downloaded PDF."""
        pass

    @abstractmethod
    def verify(self, tender_data: Dict[str, Any]) -> bool:
        """Verify the integrity of extracted data."""
        pass

    @abstractmethod
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two versions and identify diffs."""
        pass

    @abstractmethod
    def archive(self, tender_id: str) -> bool:
        """Mark a tender as expired, 404, or cancelled."""
        pass

    @abstractmethod
    def rate_limiting(self) -> None:
        """Enforce domain-specific rate limits and backoffs."""
        pass

    @abstractmethod
    def error_handling(self, error: Exception) -> None:
        """Handle 403, 404, Captcha, or Timeout events."""
        pass
