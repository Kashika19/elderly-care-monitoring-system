import os
from fastapi.testclient import TestClient

# When running from project root, this import works because "api" is a package.
# If you ever run from inside api/, use "from main import app" instead.
from api.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert "time" in j

def test_version():
    r = client.get("/version")
    assert r.status_code == 200
    j = r.json()
    assert "version" in j and "title" in j

def test_docs_page():
    # Swagger UI can 200 or 30x depending on how the client follows redirects
    r = client.get("/docs")
    assert r.status_code in (200, 307, 308)

def test_ingest_demo():
    """Post a small demo payload. If INGEST_TOKEN is set, include it."""
    payload = {
        "device_id": "test-device",
        "heart_rate": 75,
        "spo2": 97,
        "temperature": 36.7,
        "fall_detected": False,
    }
    headers = {}
    tok = os.getenv("INGEST_TOKEN", "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    r = client.post("/ingest", json=payload, headers=headers)
    # If you have a token but didn't include it, backend would 401.
    # With correct auth or no token configured, you should get 200.
    assert r.status_code in (200, 401)
    if r.status_code == 200:
        j = r.json()
        for key in ["device_id", "heart_rate", "spo2", "temperature", "fall_detected"]:
            assert key in j

def test_alerts_are_returned_as_records():
    client.delete("/alerts")
    r = client.post("/ingest", json={
        "device_id": "test-device",
        "heart_rate": 75,
        "spo2": 85,
        "temperature": 36.7,
        "fall_detected": False,
    })
    assert r.status_code == 200
    alerts = client.get("/alerts")
    assert alerts.status_code == 200
    body = alerts.json()
    assert isinstance(body, list)
    assert body
    assert {"severity", "message", "created_at"}.issubset(body[0])
