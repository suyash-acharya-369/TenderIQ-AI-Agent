from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class NotificationProvider(ABC):
    @abstractmethod
    def send_email(self, to_email: str, subject: str, html_content: str, reply_to: Optional[str] = None) -> bool:
        """Send an email."""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the provider."""
        pass
