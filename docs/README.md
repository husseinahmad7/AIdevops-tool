# AI DevOps Assistant - Microservices Documentation

## Overview
This repository contains a microservices-based AI DevOps Assistant. An API Gateway fronts service traffic and Nginx proxies all /api/v1 requests to the Gateway. Authentication/authorization is handled by the User Management service using JWTs. The Natural Language service uses LLMs via HTTP APIs only (no heavy local ML deps).

## Architecture
- Nginx (reverse proxy): routes /api/v1/* to API Gateway
- API Gateway (FastAPI): request routing and auth enforcement
- User Management (FastAPI + Postgres): users, JWT auth, API keys
- Natural Language (FastAPI): LLM-powered endpoints via HTTP APIs (OpenRouter/HuggingFace/Ollama)
- Log Analysis (FastAPI + Elasticsearch): log ingest/search/analysis
- AI Prediction (FastAPI + scikit-learn/prophet): modeling endpoints
- Infrastructure Monitor (FastAPI): infra metrics endpoints
- CI/CD Optimization (FastAPI): pipeline tuning endpoints
- Resource Optimization (FastAPI): resource planning endpoints
- Notification (FastAPI): email/notification workflows
- Reporting (FastAPI): PDF/visual reports
- Support services: Postgres, Redis, RabbitMQ, Elasticsearch, Zookeeper, Kafka, Chroma, MongoDB, MinIO, MLflow, Prometheus, Grafana

## Getting Started
1) Ensure Docker and Docker Compose are installed.
2) Create an optional env file for API keys (e.g. api-key.env):
   - OPENROUTER_API_KEY=...
   - HUGGINGFACE_API_KEY=...
3) Start the stack:
   docker compose --env-file api-key.env up -d --build
4) Gateway health:
   http://localhost/health → 200
5) API docs (Gateway):
   http://localhost/docs

## Authentication and Seeding
- JWT is issued by User Management (/api/v1/auth/login) and validated by /api/v1/users/validate.
- Default admin seeding: a seed script runs on user-management startup when SEED_ADMIN=true (default).
  - File: user-management/app/seed_admin.py
  - Defaults: admin / admin@example.com / admin123
  - Control via env vars:
    - SEED_ADMIN=true|false
    - DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD

## Natural Language (API-only LLMs)
- No heavy local ML libraries. Calls out to:
  - OpenRouter (chat/completions)
  - Hugging Face Inference API
  - Optional local Ollama (CPU-only models supported) via HTTP API
- Configure via env:
  - LLM_PROVIDER=openrouter|huggingface|ollama
  - OPENROUTER_API_KEY (for OpenRouter)
  - HUGGINGFACE_API_KEY (for HF Inference)
  - OLLAMA_BASE_URL (default http://localhost:11434)
- Vector DB/embeddings disabled: vector_db endpoints are no-ops.

## API Gateway Routing
- Base: /api/v1
- Proxied prefixes:
  - /api/v1/auth → user-management /api/v1/auth/*
  - /api/v1/users → user-management /api/v1/users/* (protected)
  - /api/v1/nlp → natural-language /api/v1/nlp/* (protected)
  - /api/v1/logs → log-analysis /api/v1/logs/* (protected)
  - /api/v1/predictions → ai-prediction /api/v1/predictions/* (protected)
  - /api/v1/monitoring → infrastructure-monitor /api/v1/monitoring/* (protected)
  - /api/v1/cicd → cicd-optimization /api/v1/cicd/* (protected)
  - /api/v1/resources → resource-optimization /api/v1/resources/* (protected)
  - /api/v1/notifications → notification /api/v1/notifications/* (protected)
  - /api/v1/reports → reporting /api/v1/reports/* (protected)

Note: Many services expose /health on their local root (e.g. :808X/health) which is not proxied. Consider adding /api/v1/<service>/health for uniformity.

## E2E Smoke Tests (Python)
A Python script performs end-to-end checks through the API Gateway.
- File: scripts/e2e_smoke.py
- What it does:
  1) Gateway /health
  2) Register demo user (idempotent)
  3) Login to get JWT
  4) Validate token via /api/v1/users/validate
  5) NLP no-op documents/search
  6) Log-analysis search (warns if backend not fully ready)

Run:
  python -m scripts.e2e_smoke

Environment:
- GATEWAY_BASE (default http://localhost)
- SMOKE_USER, SMOKE_EMAIL, SMOKE_PASSWORD to customize credentials

## Managing and Operating
- Build/start/stop:
  - docker compose --env-file api-key.env up -d --build
  - docker compose ps
  - docker compose logs --tail=200 <service>
  - docker compose down
- Restart a service:
  - docker compose up -d --build api-gateway
- Override auth for dev:
  - Some services accept DEBUG=true or AUTH_ENABLED=false; check each service config.

## Service Notes
- User Management
  - Register: POST /api/v1/auth/register {username,email,password,role}
  - Login: POST /api/v1/auth/login (form-urlencoded)
  - Validate: GET /api/v1/users/validate (Bearer token)
  - DB: DATABASE_URL env, defaults to Postgres in compose

- Natural Language
  - Base: /api/v1/nlp
  - Endpoints: /query (POST), /explain/{concept} (GET), /documents/*
  - Requires Authorization header unless AUTH_ENABLED=false

- Log Analysis
  - Base: /api/v1/logs
  - Endpoints: /ingest (POST), /search (GET), /statistics, /anomalies, admin-only utilities
  - Requires Authorization header

- AI Prediction
  - Base: /api/v1/predictions
  - Typical: model training/inference endpoints (check service routes)

- Infrastructure Monitor
  - Base: /api/v1/monitoring
  - Typical: metrics/system health endpoints (check service routes)

- CI/CD Optimization
  - Base: /api/v1/cicd
  - Typical: pipeline optimization endpoints

- Resource Optimization
  - Base: /api/v1/resources
  - Typical: resource planning endpoints

- Notification
  - Base: /api/v1/notifications
  - Typical: email templating and sending endpoints

- Reporting
  - Base: /api/v1/reports
  - Typical: report generation endpoints

## Security
- Set a strong shared JWT secret in both API Gateway and User Management:
  - JWT_SECRET_KEY=... (ensure both agree)
- Restrict CORS in production.
- Use TLS termination in front of Nginx for production deployments.

## Performance and Scaling
- Natural-language uses remote APIs or CPU-only local Ollama; no GPU dependencies in images.
- Services are horizontally scalable behind the Gateway; introduce a proper reverse proxy/load balancer and service discovery for production.

## Troubleshooting
- If /api/v1 calls 401: ensure you include Authorization: Bearer <token>.
- If NLP calls fail: set LLM_PROVIDER and relevant API keys; or use Ollama with a CPU model.
- If log-analysis returns 503: ensure Elasticsearch, Zookeeper, Kafka are up and ready.
