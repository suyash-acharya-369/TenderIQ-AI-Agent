from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_admin_token():
    res = client.post("/api/v1/auth/login", json={"email": "admin@tenderiq.ai", "password": "Admin@123456"})
    return res.json()["access_token"]

import time

def test_organizations_crud():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List
    res = client.get("/api/v1/organizations", headers=headers)
    assert res.status_code == 200

    # 2. Create
    org_name = f"National Skill Development Corporation ({int(time.time())})"
    res = client.post("/api/v1/organizations", headers=headers, json={
        "name": org_name,
        "country": "India",
        "sector": "Education",
        "website": "https://nsdcindia.org"
    })
    assert res.status_code == 200
    org = res.json()
    assert org["name"] == org_name
    org_id = org["id"]

    # 3. Get single
    res = client.get(f"/api/v1/organizations/{org_id}", headers=headers)
    assert res.status_code == 200

    # 4. Get tenders
    res = client.get(f"/api/v1/organizations/{org_id}/tenders", headers=headers)
    assert res.status_code == 200
