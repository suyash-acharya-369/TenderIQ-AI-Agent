from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class EmailResult:
    """Structured result from an email send operation."""
    success: bool = False
    message_id: Optional[str] = None
    provider: str = ""
    http_status: Optional[int] = None
    provider_response: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class NotificationProvider(ABC):
    @abstractmethod
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> EmailResult:
        """Send an email and return a structured result."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider."""
        pass

    @abstractmethod
    def check_connectivity(self) -> EmailResult:
        """Verify the provider is reachable and credentials are valid."""
        pass
