"""
Legacy email dispatch function — delegates to the unified NotificationService.
Kept for backward compatibility with existing code that imports send_email_notification.
"""
import logging
from backend.app.services.notification_service import notification_service

logger = logging.getLogger("TenderIQ.Notifications.Email")


def send_email_notification(recipient: str, subject: str, body_html: str) -> bool:
    """Send an email notification via the configured provider.
    Returns True on success, False on failure."""
    result = notification_service.dispatch_email(recipient, subject, body_html)
    return result.success
