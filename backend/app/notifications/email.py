import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.config import settings

logger = logging.getLogger("TenderIQ.Notifications.Email")

def send_email_notification(recipient: str, subject: str, body_html: str) -> bool:
    if not settings.SMTP_HOST or not recipient:
        logger.info(f"[SIMULATED EMAIL] To: {recipient} | Subject: {subject}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SENDER_EMAIL
        msg["To"] = recipient
        
        part = MIMEText(body_html, "html")
        msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, recipient, msg.as_string())

        logger.info(f"Email successfully sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Email delivery failed to {recipient}: {e}")
        return False
