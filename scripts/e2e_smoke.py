import time
import os
import sys
import json
from typing import Optional

import requests

BASE = os.environ.get("GATEWAY_BASE", "http://localhost")


def wait_for(url: str, timeout_s: int = 120, expect_status: int = 200):
    start = time.time()
    last_err: Optional[str] = None
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == expect_status:
                return True
            last_err = f"HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(2)
    raise RuntimeError(f"Timeout waiting for {url}: {last_err}")


def register_user(username: str, email: str, password: str, role: str = "admin"):
    url = f"{BASE}/api/v1/auth/register"
    payload = {"username": username, "email": email, "password": password, "role": role}
    r = requests.post(url, json=payload, timeout=10)
    if r.status_code in (200, 201):
        return r.json()
    # Already exists -> OK for idempotent runs
    if r.status_code in (400, 409, 422):
        return {"status": "exists", "detail": r.text}
    r.raise_for_status()


def login(username: str, password: str) -> str:
    url = f"{BASE}/api/v1/auth/login"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"username={username}&password={password}"
    r = requests.post(url, headers=headers, data=data, timeout=10)
    r.raise_for_status()
    js = r.json()
    token = js.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in response: {js}")
    return token


def auth_get(path: str, token: str, params: Optional[dict] = None) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"}
    return requests.get(f"{BASE}{path}", headers=headers, params=params, timeout=15)


def main():
    print(f"Using API Gateway at {BASE}")

    # 1) Gateway health
    print("[1/6] Checking gateway /health ...", end=" ")
    wait_for(f"{BASE}/health")
    print("OK")

    # 2) Register/login via Gateway
    username = os.environ.get("SMOKE_USER", "demo")
    email = os.environ.get("SMOKE_EMAIL", "demo@example.com")
    password = os.environ.get("SMOKE_PASSWORD", "demo123")

    print("[2/6] Registering demo user (idempotent) ...", end=" ")
    _ = register_user(username, email, password)
    print("OK")

    print("[3/6] Logging in to obtain JWT ...", end=" ")
    token = login(username, password)
    print("OK")

    # 3) Validate
    print("[4/6] Validating token ...", end=" ")
    rv = auth_get("/api/v1/users/validate", token)
    assert rv.status_code == 200, rv.text
    user = rv.json()
    print(f"OK (user_id={user.get('id')})")

    # 4) Natural-language minimal call that requires no external LLM
    print("[5/6] NLP documents/search (no-op embedding) ...", end=" ")
    rv = auth_get(
        "/api/v1/nlp/documents/search", token, params={"query": "test", "limit": 2}
    )
    assert rv.status_code == 200, rv.text
    js = rv.json()
    assert "results" in js, js
    print("OK")

    # 5) Log analysis search (depends on Elasticsearch; accept any 2xx or meaningful 4xx)
    print("[6/6] Log analysis search ...", end=" ")
    rv = auth_get("/api/v1/logs/search", token, params={"query": "error"})
    if rv.status_code // 100 == 2:
        print("OK")
    else:
        print(f"WARN (status={rv.status_code})")

    print("\nSmoke tests completed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"E2E smoke FAILED: {e}")
        sys.exit(1)
