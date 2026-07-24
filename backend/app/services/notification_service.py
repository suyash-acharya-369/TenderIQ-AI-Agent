import os
import logging
from typing import Optional, Any
from backend.app.config import settings
from backend.app.notifications.base import NotificationProvider
from backend.app.notifications.providers.resend_provider import ResendProvider
from backend.app.notifications.providers.smtp_provider import SMTPProvider

logger = logging.getLogger("TenderIQ.NotificationService")

class NotificationService:
    def __init__(self):
        self.provider = self._init_provider()

    def _init_provider(self) -> NotificationProvider:
        # In a real enterprise system, this might fetch from a database `EmailSettings` table.
        # For now, we rely on the environment / settings module.
        # We assume settings has EMAIL_PROVIDER which could be "resend" or "smtp"
        provider_name = getattr(settings, "EMAIL_PROVIDER", "smtp").lower()
        
        if provider_name == "resend":
            api_key = getattr(settings, "RESEND_API_KEY", "")
            return ResendProvider(
                api_key=api_key,
                sender_email=getattr(settings, "SENDER_EMAIL", "notifications@tenderiq.ai")
            )
        else:
            return SMTPProvider(
                host=getattr(settings, "SMTP_HOST", ""),
                port=getattr(settings, "SMTP_PORT", 587),
                user=getattr(settings, "SMTP_USER", ""),
                password=getattr(settings, "SMTP_PASSWORD", ""),
                sender_email=getattr(settings, "SENDER_EMAIL", "notifications@tenderiq.ai")
            )

    def dispatch_email(self, to_email: str, subject: str, html_content: str, reply_to: Optional[str] = None) -> bool:
        """Synchronously send an email using the configured provider. 
        Use FastAPIs BackgroundTasks to call this asynchronously."""
        try:
            success = self.provider.send_email(to_email, subject, html_content, reply_to)
            return success
        except Exception as e:
            logger.error(f"Failed to dispatch email via {self.provider.get_provider_name()}: {e}")
            return False

# Singleton instance
notification_service = NotificationService()
