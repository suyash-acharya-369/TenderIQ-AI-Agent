from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseConnector(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """Authenticate with protected portal."""
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
    def healthcheck(self, source_url: str) -> bool:
        """Check if source site is reachable."""
        pass
