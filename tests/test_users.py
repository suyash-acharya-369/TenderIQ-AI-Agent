from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def get_admin_token():
    res = client.post("/api/v1/auth/login", json={"email": "admin@tenderiq.ai", "password": "Admin@123456"})
    return res.json()["access_token"]

def test_users_crud():
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List users
    res = client.get("/api/v1/users", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 2. Create user
    res = client.post("/api/v1/users", headers=headers, json={
        "email": "analyst@tenderiq.ai",
        "password": "Password@123",
        "full_name": "Senior Analyst",
        "role": "Manager"
    })
    assert res.status_code == 200
    new_user = res.json()
    assert new_user["email"] == "analyst@tenderiq.ai"
    user_id = new_user["id"]

    # 3. Update user
    res = client.put(f"/api/v1/users/{user_id}", headers=headers, json={"role": "Administrator"})
    assert res.status_code == 200
    assert res.json()["role"] == "Administrator"

    # 4. Delete user
    res = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
