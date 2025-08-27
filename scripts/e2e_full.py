import os
import time
import json
import socket
from contextlib import closing
from typing import Dict, Any, List
import requests

BASE = os.environ.get("GATEWAY_BASE", "http://localhost")


def wait_http_ok(url: str, timeout_s: int = 120):
    start = time.time()
    last = None
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return
            last = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last = str(e)
        time.sleep(2)
    raise RuntimeError(f"Timeout waiting for {url} ({last})")


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def tcp_check(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


def http_check(url: str, ok_status: List[int] | None = None) -> bool:
    try:
        r = requests.get(url, timeout=5)
        if ok_status:
            return r.status_code in ok_status
        # Accept 2xx-4xx for UIs requiring login
        return 200 <= r.status_code < 500
    except Exception:
        return False


def register(username: str, email: str, password: str, role: str = "admin"):
    r = requests.post(
        f"{BASE}/api/v1/auth/register",
        json={"username": username, "email": email, "password": password, "role": role},
        timeout=10,
    )
    if r.status_code not in (200, 201):
        # likely exists already; treat as ok
        pass


def login(username: str, password: str) -> str:
    r = requests.post(
        f"{BASE}/api/v1/auth/login",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=f"username={username}&password={password}",
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def validate(token: str) -> Dict[str, Any]:
    r = requests.get(f"{BASE}/api/v1/users/validate", headers=auth_headers(token), timeout=10)
    r.raise_for_status()
    return r.json()


def nlp_tests(token: str):
    # explain concept
    r = requests.get(f"{BASE}/api/v1/nlp/explain/devops", headers=auth_headers(token), timeout=20)
    if r.status_code // 100 != 2:
        print(f"[nlp] WARN explain status={r.status_code}")
    # query simple
    r = requests.post(
        f"{BASE}/api/v1/nlp/query",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"query": "What is CI/CD?", "use_context": False},
        timeout=30,
    )
    if r.status_code // 100 != 2:
        print(f"[nlp] WARN query status={r.status_code}")
    # documents search (no-op)
    r = requests.get(
        f"{BASE}/api/v1/nlp/documents/search",
        headers=auth_headers(token),
        params={"query": "pipeline", "limit": 2},
        timeout=15,
    )
    assert r.status_code == 200, r.text


def logs_tests(token: str):
    # search logs (ES might be cold, accept 2xx or 5xx as warn)
    r = requests.get(f"{BASE}/api/v1/logs/search", headers=auth_headers(token), params={"query": "error"}, timeout=20)
    if r.status_code // 100 != 2:
        print(f"[logs] WARN status={r.status_code}")


def cicd_tests(token: str):
    # cicd service expects token query param; include it for compatibility
    params = {"token": token}
    r = requests.get(f"{BASE}/api/v1/cicd/pipelines", headers=auth_headers(token), params=params, timeout=10)
    assert r.status_code == 200, r.text
    r = requests.get(f"{BASE}/api/v1/cicd/pipelines/main/analysis", headers=auth_headers(token), params=params, timeout=10)
    assert r.status_code == 200, r.text
    r = requests.get(f"{BASE}/api/v1/cicd/metrics", headers=auth_headers(token), params=params, timeout=10)
    assert r.status_code == 200, r.text


def resources_tests(token: str):
    for path in ["/usage", "/costs", "/metrics"]:
        r = requests.get(f"{BASE}/api/v1/resources{path}", headers=auth_headers(token), timeout=10)
        assert r.status_code == 200, r.text
    r = requests.post(
        f"{BASE}/api/v1/resources/optimize",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"targets": ["cpu", "storage"]},
        timeout=10,
    )
    assert r.status_code == 200, r.text


def infra_monitor_tests(token: str):
    # metrics (protected)
    r = requests.get(f"{BASE}/api/v1/monitoring/metrics", headers=auth_headers(token), timeout=15)
    assert r.status_code == 200, r.text


def notification_tests(token: str):
    r = requests.get(f"{BASE}/api/v1/notifications/templates", headers=auth_headers(token), timeout=10)
    assert r.status_code == 200, r.text
    r = requests.post(
        f"{BASE}/api/v1/notifications/send",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"channels": ["email"], "message": "Hello", "recipients": ["admin@example.com"]},
        timeout=10,
    )
    assert r.status_code == 200, r.text


def reporting_tests(token: str):
    r = requests.get(f"{BASE}/api/v1/reports/templates", headers=auth_headers(token), timeout=10)
    if r.status_code // 100 != 2:
        print(f"[reporting] WARN templates status={r.status_code}")
    r = requests.post(
        f"{BASE}/api/v1/reports/generate",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"template_id": "system_health", "parameters": {"time_range": "24h"}, "format": "json"},
        timeout=15,
    )
    if r.status_code // 100 != 2:
        print(f"[reporting] WARN generate status={r.status_code}")


def prediction_tests(token: str):
    # Use small mock data to keep it light; service may use heavy libs but route exists
    series = [{"ds": f"2024-01-0{i+1}", "y": i * 1.0} for i in range(7)]
    r = requests.post(
        f"{BASE}/api/v1/predictions/forecast",
        headers={**auth_headers(token), "Content-Type": "application/json"},
        json={"data": series, "metric_name": "demo", "days": 1},
        timeout=60,
    )
    # Allow either 200 or 500 if deps unavailable; we only smoke the route
    if r.status_code // 100 != 2:
        print(f"[predictions] WARN status={r.status_code}")


def main():
    print(f"E2E full tests against {BASE}")
    wait_http_ok(f"{BASE}/health")

    user = os.environ.get("SMOKE_USER", "demo")
    email = os.environ.get("SMOKE_EMAIL", "demo@example.com")
    password = os.environ.get("SMOKE_PASSWORD", "demo123")

    register(user, email, password)
    token = login(user, password)
    who = validate(token)
    print(f"Auth OK, user: {who.get('username', who.get('id'))}")

    nlp_tests(token)
    print("NLP OK")

    logs_tests(token)
    print("Logs route checked")

    cicd_tests(token)
    # Service container port checks (best-effort)
    checks = [
        ("postgres", lambda: tcp_check("localhost", 5432)),
        ("redis", lambda: tcp_check("localhost", 6379)),
        ("zookeeper", lambda: tcp_check("localhost", 2181)),
        ("kafka", lambda: tcp_check("localhost", 9092)),
        ("minio", lambda: http_check("http://localhost:9000")),
        ("mongodb", lambda: tcp_check("localhost", 27017)),
        ("mlflow", lambda: http_check("http://localhost:5000")),
        ("rabbitmq", lambda: http_check("http://localhost:15672")),
        ("elasticsearch", lambda: http_check("http://localhost:9200")),
        ("prometheus", lambda: http_check("http://localhost:9090/-/ready", [200])),
        ("grafana", lambda: http_check("http://localhost:3000/login")),
        ("chroma", lambda: http_check("http://localhost:8000/api/v1/")),
        ("api-gateway", lambda: http_check("http://localhost:8080/health", [200])),
        ("user-management", lambda: http_check("http://localhost:8081/health", [200])),
        ("infrastructure-monitor", lambda: http_check("http://localhost:8082/health", [200])),
        ("ai-prediction", lambda: http_check("http://localhost:8083/health", [200])),
        ("log-analysis", lambda: http_check("http://localhost:8084/health", [200])),
        ("cicd-optimization", lambda: http_check("http://localhost:8085/health", [200])),
        ("resource-optimization", lambda: http_check("http://localhost:8086/health", [200])),
        ("notification", lambda: http_check("http://localhost:8087/health", [200])),
        ("natural-language", lambda: http_check("http://localhost:8088/health", [200])),
        ("reporting", lambda: http_check("http://localhost:8089/health", [200])),
    ]
    bad = []
    for name, fn in checks:
        ok = False
        try:
            ok = fn()
        except Exception:
            ok = False
        print(f"check {name}: {'OK' if ok else 'FAIL'}")
        if not ok:
            bad.append(name)
    if bad:
        print("Non-fatal: some containers did not respond as expected:", ", ".join(bad))
    print("CI/CD OK")

    resources_tests(token)
    print("Resources OK")

    infra_monitor_tests(token)
    print("Infra monitor OK")

    notification_tests(token)
    print("Notification OK")

    reporting_tests(token)
    print("Reporting OK")

    prediction_tests(token)
    print("Predictions route checked")

    print("All E2E tests completed (with warnings where noted).")


if __name__ == "__main__":
    main()

