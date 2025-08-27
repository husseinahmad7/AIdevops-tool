# Smoke E2E Test

Run after `docker compose up -d`:

```bash
python -m venv .venv && . .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install requests
python tests/smoke_e2e.py
```

Environment variables:
- `GATEWAY_BASE` (default `http://localhost`)

The script will:
- wait for `GET /health` to be 200
- register (idempotent) and login `demo/demo123`
- validate token at `/api/v1/users/validate`
- call health endpoints of core services via the API Gateway
- call NLP explain endpoint

