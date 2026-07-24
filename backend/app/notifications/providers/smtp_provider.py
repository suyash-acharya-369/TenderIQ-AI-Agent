import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from backend.app.notifications.base import NotificationProvider

logger = logging.getLogger("TenderIQ.SMTPProvider")

class SMTPProvider(NotificationProvider):
    def __init__(self, host: str, port: int, user: str, password: str, sender_email: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.sender_email = sender_email
    
    def get_provider_name(self) -> str:
        return "SMTP"

    def send_email(self, to_email: str, subject: str, html_content: str, reply_to: Optional[str] = None) -> bool:
        if not self.host or not to_email:
            logger.info(f"[SIMULATED SMTP EMAIL] To: {to_email} | Subject: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = to_email
            if reply_to:
                msg["Reply-To"] = reply_to
            
            part = MIMEText(html_content, "html")
            msg.attach(part)

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.sender_email, to_email, msg.as_string())

            logger.info(f"SMTP Email successfully sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"SMTP Email delivery failed to {to_email}: {e}")
            return False
