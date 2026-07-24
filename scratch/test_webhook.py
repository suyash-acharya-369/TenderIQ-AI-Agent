import httpx

url = "http://127.0.0.1:8000/api/v1/notifications/webhook"
payload = {
    "type": "email.opened",
    "data": {
        "email_id": "req_123",
        "to": ["test@example.com"]
    }
}

try:
    res = httpx.post(url, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Failed to post to webhook: {e}")
