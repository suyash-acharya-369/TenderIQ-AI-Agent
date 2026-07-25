import json
import logging
import httpx
from typing import Optional, List
from backend.app.notifications.base import NotificationProvider, EmailResult

logger = logging.getLogger("TenderIQ.ResendProvider")


class ResendProvider(NotificationProvider):
    def __init__(self, api_key: str, sender_email: str, sender_name: str = "TenderIQ AI"):
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.api_url = "https://api.resend.com/emails"
        self.timeout = 15.0

    def get_provider_name(self) -> str:
        return "Resend"

    def check_connectivity(self) -> EmailResult:
        """Check if the Resend API key is valid by hitting the domains endpoint."""
        if not self.api_key:
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error="Resend API key is not configured.",
            )
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            res = httpx.get(
                "https://api.resend.com/domains",
                headers=headers,
                timeout=self.timeout,
            )
            if res.status_code == 200:
                return EmailResult(
                    success=True,
                    provider=self.get_provider_name(),
                    http_status=res.status_code,
                    provider_response=res.text[:500],
                )
            else:
                return EmailResult(
                    success=False,
                    provider=self.get_provider_name(),
                    http_status=res.status_code,
                    provider_response=res.text[:500],
                    error=f"API returned status {res.status_code}",
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
        if not self.api_key:
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error="Resend API key is missing.",
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": f"{self.sender_name} <{self.sender_email}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        if reply_to:
            payload["reply_to"] = reply_to
        if cc:
            payload["cc"] = cc
        if bcc:
            payload["bcc"] = bcc

        try:
            res = httpx.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )

            response_text = res.text
            message_id = None

            if res.status_code in [200, 201]:
                try:
                    data = res.json()
                    message_id = data.get("id")
                except Exception:
                    pass

                logger.info(
                    f"Resend email sent to {to_email} | message_id={message_id}"
                )
                return EmailResult(
                    success=True,
                    message_id=message_id,
                    provider=self.get_provider_name(),
                    http_status=res.status_code,
                    provider_response=response_text[:500],
                )
            else:
                logger.error(
                    f"Resend failed. Status: {res.status_code}. Response: {response_text}"
                )
                return EmailResult(
                    success=False,
                    provider=self.get_provider_name(),
                    http_status=res.status_code,
                    provider_response=response_text[:500],
                    error=f"Resend API returned status {res.status_code}: {response_text[:200]}",
                )
        except httpx.TimeoutException:
            logger.error(f"Resend timeout sending to {to_email}")
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error="Request timed out after 15 seconds.",
            )
        except Exception as e:
            logger.error(f"Resend HTTP request failed: {e}")
            return EmailResult(
                success=False,
                provider=self.get_provider_name(),
                error=str(e),
            )
