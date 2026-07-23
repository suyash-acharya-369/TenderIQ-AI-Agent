import httpx
import logging
from backend.app.config import settings

logger = logging.getLogger("TenderIQ.Notifications.WhatsApp")

def send_whatsapp_notification(phone_number: str, message_text: str) -> bool:
    if not settings.WHATSAPP_PHONE_ID or not settings.WHATSAPP_ACCESS_TOKEN:
        logger.info(f"[SIMULATED WHATSAPP] To: {phone_number} | Message: {message_text[:100]}...")
        return True

    url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message_text}
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                logger.info(f"WhatsApp alert delivered to {phone_number}")
                return True
            else:
                logger.error(f"WhatsApp API error {res.status_code}: {res.text}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp dispatch exception: {e}")
        return False
