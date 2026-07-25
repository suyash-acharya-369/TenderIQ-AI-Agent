import time
import logging
from typing import Optional, List, Dict, Any
from backend.app.config import settings
from backend.app.notifications.base import NotificationProvider, EmailResult
from backend.app.notifications.providers.resend_provider import ResendProvider
from backend.app.notifications.providers.smtp_provider import SMTPProvider

logger = logging.getLogger("TenderIQ.NotificationService")

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds between retries


class NotificationService:
    def __init__(self):
        self.provider: NotificationProvider = self._init_provider()
        self._email_enabled = True

    def _init_provider(self) -> NotificationProvider:
        provider_name = getattr(settings, "EMAIL_PROVIDER", "smtp").lower()

        if provider_name == "resend":
            api_key = getattr(settings, "RESEND_API_KEY", "")
            if not api_key:
                logger.warning("Resend selected but API key is missing. Email will be disabled.")
                self._email_enabled = False
            return ResendProvider(
                api_key=api_key,
                sender_email=getattr(settings, "SENDER_EMAIL", "onboarding@resend.dev"),
            )
        else:
            host = getattr(settings, "SMTP_HOST", "")
            if not host:
                logger.warning("SMTP selected but host is missing. Email will be disabled.")
                self._email_enabled = False
            return SMTPProvider(
                host=host,
                port=getattr(settings, "SMTP_PORT", 587),
                user=getattr(settings, "SMTP_USER", ""),
                password=getattr(settings, "SMTP_PASSWORD", ""),
                sender_email=getattr(settings, "SENDER_EMAIL", "notifications@tenderiq.ai"),
            )

    def reinitialize(self):
        """Reinitialize the provider (e.g. after settings change)."""
        self._email_enabled = True
        self.provider = self._init_provider()

    def check_connectivity(self) -> EmailResult:
        return self.provider.check_connectivity()

    def get_provider_name(self) -> str:
        return self.provider.get_provider_name()

    def is_enabled(self) -> bool:
        return self._email_enabled

    def dispatch_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None,
        retry: bool = True,
    ) -> EmailResult:
        """Send an email with automatic retry. Returns structured EmailResult."""
        if not self._email_enabled:
            return EmailResult(
                success=False,
                provider=self.provider.get_provider_name(),
                error="Email sending is disabled due to missing configuration.",
            )

        last_result = None
        max_attempts = MAX_RETRIES if retry else 1

        for attempt in range(max_attempts):
            result = self.provider.send_email(to_email, subject, html_content, reply_to)
            result.retry_count = attempt

            if result.success:
                return result

            last_result = result
            logger.warning(
                f"Email attempt {attempt + 1}/{max_attempts} failed: {result.error}"
            )

            if attempt < max_attempts - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                time.sleep(delay)

        # All retries exhausted
        if last_result:
            last_result.retry_count = max_attempts - 1
        return last_result or EmailResult(
            success=False,
            provider=self.provider.get_provider_name(),
            error="All retry attempts exhausted.",
            retry_count=max_attempts - 1,
        )


# Singleton instance
notification_service = NotificationService()
