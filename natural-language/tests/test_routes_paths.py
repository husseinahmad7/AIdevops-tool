from fastapi.testclient import TestClient
from app.main import app

def test_router_prefix():
    client = TestClient(app)
    assert client.post("/api/v1/nlp/query").status_code in (200, 400, 401, 422)
    assert client.post("/api/v1/nlp/generate-iac").status_code in (200, 400, 401, 422)

