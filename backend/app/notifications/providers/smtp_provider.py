import smtplib
import uuid
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from backend.app.notifications.base import NotificationProvider, EmailResult

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

    def check_connectivity(self) -> EmailResult:
        if not self.host:
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error="SMTP host is not configured.",
            )
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
            return EmailResult(
                success=True,
                provider=self.get_provider_name(),
                provider_response="SMTP connection and authentication successful.",
            )
        except Exception as e:
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error=str(e),
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> EmailResult:
        if not self.host or not to_email:
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error="SMTP host or recipient not configured.",
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = to_email
            if reply_to:
                msg["Reply-To"] = reply_to
            if cc:
                msg["Cc"] = ", ".join(cc)

            part = MIMEText(html_content, "html")
            msg.attach(part)

            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)

            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.sender_email, all_recipients, msg.as_string())

            message_id = str(uuid.uuid4())
            logger.info(f"SMTP Email sent to {to_email} | message_id={message_id}")
            return EmailResult(
                success=True,
                message_id=message_id,
                provider=self.get_provider_name(),
                provider_response="SMTP delivery successful.",
            )
        except Exception as e:
            logger.error(f"SMTP Email delivery failed to {to_email}: {e}")
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error=str(e),
            )
