from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseConnector(ABC):
    @abstractmethod
    def login(self, username: str, password: str) -> bool:
        """Authenticate with protected portal."""
        pass

    @abstractmethod
    def crawl(self, source_url: str) -> List[Dict[str, Any]]:
        """Crawl portal opportunities."""
        pass

    @abstractmethod
    def healthcheck(self, source_url: str) -> bool:
        """Check if source site is reachable."""
        pass
