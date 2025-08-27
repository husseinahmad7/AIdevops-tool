import os
import requests

BASE = os.environ.get("GATEWAY_BASE", "http://localhost:8080")


def test_gateway_health():
    r = requests.get(f"{BASE}/health", timeout=10)
    assert r.status_code == 200


def test_docs_available():
    r = requests.get(f"{BASE}/docs", timeout=10)
    assert r.status_code in (200, 307, 308)

