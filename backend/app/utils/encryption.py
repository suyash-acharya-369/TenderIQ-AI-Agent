import base64
import hashlib
from cryptography.fernet import Fernet
from backend.app.config import settings

def _get_fernet_key() -> bytes:
    # Key must be 32 url-safe base64-encoded bytes
    key_hash = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)

fernet = Fernet(_get_fernet_key())

def encrypt_data(data: str) -> str:
    if not data:
        return ""
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    if not token:
        return ""
    try:
        return fernet.decrypt(token.encode()).decode()
    except Exception:
        return ""
