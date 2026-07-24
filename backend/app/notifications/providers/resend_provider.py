import logging
import httpx
from typing import Optional
from backend.app.notifications.base import NotificationProvider

logger = logging.getLogger("TenderIQ.ResendProvider")

class ResendProvider(NotificationProvider):
    def __init__(self, api_key: str, sender_email: str, sender_name: str = "TenderIQ"):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.api_url = "https://api.resend.com/emails"
    
    def get_provider_name(self) -> str:
        return "Resend"
    
    def send_email(self, to_email: str, subject: str, html_content: str, reply_to: Optional[str] = None) -> bool:
        if not self.api_key:
            logger.error("Resend API Key is missing.")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": f"{self.sender_name} <{self.sender_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        if reply_to:
            payload["reply_to"] = reply_to

        try:
            # Synchronous call since it's executed in a background worker thread
            res = httpx.post(self.api_url, json=payload, headers=headers, timeout=10.0)
            if res.status_code in [200, 201]:
                logger.info(f"Resend email dispatched successfully to {to_email}")
                return True
            else:
                logger.error(f"Resend failed. Status: {res.status_code}. Response: {res.text}")
                return False
        except Exception as e:
            logger.error(f"Resend HTTP request failed: {e}")
            return False
