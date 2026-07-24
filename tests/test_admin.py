from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_admin_token():
    res = client.post("/api/v1/auth/login", json={"email": "admin@tenderiq.ai", "password": "Admin@123456"})
    return res.json()["access_token"]

def test_admin_dashboards():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Crawl history
    res = client.get("/api/v1/admin/crawl-history", headers=headers)
    assert res.status_code == 200

    # 2. Queue status
    res = client.get("/api/v1/admin/queue-status", headers=headers)
    assert res.status_code == 200
    assert "active_queues" in res.json()

    # 3. AI costs
    res = client.get("/api/v1/admin/ai-costs", headers=headers)
    assert res.status_code == 200
    assert "summary" in res.json()

    # 4. Audit logs
    res = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert res.status_code == 200
