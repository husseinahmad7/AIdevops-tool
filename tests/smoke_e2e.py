import os
import time
import json
import sys
from urllib.parse import urlencode
import requests

BASE = os.environ.get("GATEWAY_BASE", "http://localhost")


def wait_health(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


def register_login(base: str):
    # Register (idempotent: if user exists returns error, but we can ignore and proceed to login)
    reg_body = {
        "username": "demo",
        "email": "demo@example.com",
        "password": "demo123",
        "role": "admin",
    }
    try:
        requests.post(f"{base}/api/v1/auth/register", json=reg_body, timeout=10)
    except requests.RequestException:
        pass

    # Login form-encoded
    form = {"username": "demo", "password": "demo123"}
    r = requests.post(
        f"{base}/api/v1/auth/login",
        data=urlencode(form),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    r.raise_for_status()
    token = r.json().get("access_token")
    if not token:
        raise RuntimeError("No token received from login")
    return token


def call_with_token(base: str, token: str, method: str, path: str, **kwargs):
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, f"{base}{path}", headers=headers, timeout=15, **kwargs)


def main():
    assert wait_health(f"{BASE}/health", timeout=90), "Gateway health failed"

    # Acquire token (seeded admin ensures login works on first run)
    token = register_login(BASE)

    # Validate user
    rv = call_with_token(BASE, token, "GET", "/api/v1/users/validate")
    assert rv.status_code == 200, (rv.status_code, rv.text)
    user = rv.json()
    print("Validated user:", user)

    # NLP explain
    rv = call_with_token(BASE, token, "GET", "/api/v1/nlp/explain/devops")
    print("NLP explain status:", rv.status_code)

    # Logs health
    rv = call_with_token(BASE, token, "GET", "/api/v1/logs/health")
    print("Logs health status:", rv.status_code)

    # Predictions health
    rv = call_with_token(BASE, token, "GET", "/api/v1/predictions/health")
    print("Predictions health status:", rv.status_code)

    # Monitoring health
    rv = call_with_token(BASE, token, "GET", "/api/v1/monitoring/health")
    print("Monitoring health status:", rv.status_code)

    # Resources health
    rv = call_with_token(BASE, token, "GET", "/api/v1/resources/health")
    print("Resources health status:", rv.status_code)

    # Notifications health
    rv = call_with_token(BASE, token, "GET", "/api/v1/notifications/health")
    print("Notifications health status:", rv.status_code)

    # Reporting health
    rv = call_with_token(BASE, token, "GET", "/api/v1/reports/health")
    print("Reports health status:", rv.status_code)

    print("E2E smoke completed")


if __name__ == "__main__":
    main()

