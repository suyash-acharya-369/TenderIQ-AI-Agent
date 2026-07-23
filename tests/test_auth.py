from backend.app.utils.security import hash_password, verify_password
from backend.app.utils.jwt import create_access_token, decode_token

def test_password_hashing():
    raw_pw = "AdminPass123"
    hashed = hash_password(raw_pw)
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token():
    payload = {"sub": "1", "email": "test@tenderiq.ai", "role": "Administrator"}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["email"] == "test@tenderiq.ai"
    assert decoded["role"] == "Administrator"
