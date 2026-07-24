from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_admin_token():
    res = client.post("/api/v1/auth/login", json={"email": "admin@tenderiq.ai", "password": "Admin@123456"})
    return res.json()["access_token"]

def test_analytics_exports():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # CSV
    res = client.get("/api/v1/analytics/export/csv", headers=headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]

    # Excel
    res = client.get("/api/v1/analytics/export/excel", headers=headers)
    assert res.status_code == 200

    # PDF
    res = client.get("/api/v1/analytics/export/pdf", headers=headers)
    assert res.status_code == 200
    assert "application/pdf" in res.headers["content-type"]
