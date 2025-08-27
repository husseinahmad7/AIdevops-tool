from fastapi.testclient import TestClient
from app.main import app

def test_router_prefix():
    client = TestClient(app)
    # These shouldn't exist due to normalized paths
    assert client.get("/api/v1/logs/logs/search").status_code in (404, 405)
    # New path under normalized scheme
    # Will likely 401 due to auth, but it should reach the route
    res = client.get("/api/v1/logs/search")
    assert res.status_code in (200, 401)

