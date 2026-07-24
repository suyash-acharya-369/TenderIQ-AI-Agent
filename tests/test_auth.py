from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.utils.security import hash_password, verify_password
from backend.app.utils.jwt import create_access_token, decode_token

client = TestClient(app)

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

def test_login_api():
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tenderiq.ai", "password": "Admin@123456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "admin@tenderiq.ai"

def test_protected_route_without_token():
    response = client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 401

def test_protected_route_with_token():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@tenderiq.ai", "password": "Admin@123456"}
    )
    token = login_res.json()["access_token"]
    response = client.get(
        "/api/v1/dashboard/kpis",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_opportunities" in data
