# Services and Containers Reference (docker-compose.yml)

This guide documents every service and container defined in docker-compose.yml: what it does, how to access it locally, health checks, key endpoints (if applicable), sample requests, configuration, and troubleshooting.

Tip: The API Gateway exposes unified routes at http://localhost:8080 (or via Nginx at http://localhost). Most microservices are protected by JWT; obtain a token via /api/v1/auth/login.

## Core Entry Points
- API Gateway UI (docs): http://localhost:8080/docs
- Admin Test UI (Gateway): http://localhost:8080/admin
- Nginx proxy (routes /api/v1/* to Gateway): http://localhost
- Health: http://localhost/health

---

## API Gateway (api-gateway)
- Purpose: Front door for all microservices; auth enforcement and routing
- Port: 8080 (host)
- Health: GET http://localhost:8080/health
- Docs: http://localhost:8080/docs
- Admin Test UI: http://localhost:8080/admin
- Key proxied prefixes:
  - /api/v1/auth, /api/v1/users → user-management
  - /api/v1/nlp → natural-language
  - /api/v1/logs → log-analysis
  - /api/v1/predictions → ai-prediction
  - /api/v1/monitoring → infrastructure-monitor
  - /api/v1/cicd → cicd-optimization
  - /api/v1/resources → resource-optimization
  - /api/v1/notifications → notification
  - /api/v1/reports → reporting
- Env: DEBUG, AUTH_ENABLED, USER_MANAGEMENT_URL, DB/Redis/RabbitMQ URLs
- Troubleshooting: Check docker logs and /health; ensure User Management is up for token validation

## Nginx (nginx)
- Purpose: Reverse proxy in front of API Gateway
- Port: 80 (host)
- Routes: proxies /api/v1/* to API Gateway; /health available
- Troubleshooting: docker logs aidevops-nginx; verify conf.d mappings

---

## User Management (user-management)
- Purpose: Users, JWT auth, roles
- Port: 8081 (host)
- Health: GET http://localhost:8081/health
- Endpoints (via Gateway):
  - POST /api/v1/auth/register {username,email,password,role}
  - POST /api/v1/auth/login (form-encoded)
  - GET /api/v1/users/validate (Authorization: Bearer <token>)
- Env: DATABASE_URL, DEBUG, SEED_ADMIN=true, DEFAULT_ADMIN_* for first-run seeding
- Sample: curl -X POST http://localhost/api/v1/auth/login -d 'username=demo&password=demo123' -H 'Content-Type: application/x-www-form-urlencoded'

## Natural Language (natural-language)
- Purpose: LLM-based endpoints via HTTP APIs only (no heavy local ML)
- Port: 8088 (host)
- Health: GET http://localhost:8088/health
- Endpoints (via Gateway):
  - GET /api/v1/nlp/explain/{concept}
  - POST /api/v1/nlp/query {query, use_context}
  - GET /api/v1/nlp/documents/search?query=...&limit=...
- Env: LLM_PROVIDER, OPENROUTER_API_KEY, HUGGINGFACE_API_KEY, OLLAMA_BASE_URL
- Notes: In DEBUG or without keys, responses are stubbed for tests

## Log Analysis (log-analysis)
- Purpose: Search/ingest logs via Elasticsearch/Kafka
- Port: 8084 (host)
- Health: GET http://localhost:8084/health
- Endpoints (via Gateway):
  - GET /api/v1/logs/search?query=...
  - POST /api/v1/logs/ingest
- Env: ELASTICSEARCH_URL, KAFKA_BROKER_URL, REDIS_URL
- Troubleshooting: Ensure elasticsearch, zookeeper, kafka up; first calls may 500 until ready

## AI Prediction (ai-prediction)
- Purpose: Forecasts/predictions with MLflow metadata and MinIO artifacts
- Port: 8083 (host)
- Health: GET http://localhost:8083/health
- Endpoints (via Gateway):
  - POST /api/v1/predictions/forecast {data, metric_name, days}
  - POST /api/v1/predictions/train {...}
- Env: MONGODB_URI, MLFLOW_TRACKING_URI, MLFLOW_S3_ENDPOINT_URL, AWS_*

## Infrastructure Monitor (infrastructure-monitor)
- Purpose: Basic infra metrics/dockerd info
- Port: 8082 (host)
- Health: GET http://localhost:8082/health
- Endpoints (via Gateway):
  - GET /api/v1/monitoring/metrics
- Env: DOCKER_ENABLED, DOCKER_HOST, REDIS_URL

## CI/CD Optimization (cicd-optimization)
- Purpose: Pipeline listings, metrics, and optimization recommendations
- Port: 8085 (host)
- Health: GET http://localhost:8085/health
- Endpoints (via Gateway):
  - GET /api/v1/cicd/pipelines
  - GET /api/v1/cicd/pipelines/{id}/analysis
  - GET /api/v1/cicd/metrics
- Auth: Some routes accept token in query param (token=...)

## Resource Optimization (resource-optimization)
- Purpose: Usage/cost metrics and optimization plans
- Port: 8086 (host)
- Health: GET http://localhost:8086/health
- Endpoints (via Gateway):
  - GET /api/v1/resources/usage
  - GET /api/v1/resources/costs
  - GET /api/v1/resources/metrics
  - POST /api/v1/resources/optimize {targets}

## Notification (notification)
- Purpose: Email/notification workflows
- Port: 8087 (host)
- Health: GET http://localhost:8087/health
- Endpoints (via Gateway):
  - GET /api/v1/notifications/templates
  - POST /api/v1/notifications/send {channels,message,recipients}

## Reporting (reporting)
- Purpose: Generate reports across services
- Port: 8089 (host)
- Health: GET http://localhost:8089/health
- Endpoints (via Gateway):
  - GET /api/v1/reports/templates
  - POST /api/v1/reports/generate {template_id, parameters, format}
- Troubleshooting: May require other services to be ready; 401 indicates missing/invalid token

---

## Supporting Infrastructure

### Postgres (postgres)
- Port: 5432; Data: volume postgres_data
- Health: docker ps shows healthy; psql inside container for checks

### Redis (redis)
- Port: 6379; Data: volume redis_data
- Health: redis-cli ping

### Zookeeper (zookeeper)
- Port: 2181

### Kafka (kafka)
- Port: 9092; Depends on zookeeper

### Elasticsearch (elasticsearch)
- Port: 9200; Health: green expected; Data: elasticsearch_data

### MinIO (minio)
- Ports: 9000 (S3), 9001 (console)
- Default creds: aidevops / aidevops_secret

### MongoDB (mongodb)
- Port: 27017; Data: mongo_data

### MLflow (mlflow)
- Port: 5000; Backed by MinIO (S3)

### RabbitMQ (rabbitmq)
- Ports: 5672 (AMQP), 15672 (UI)
- Default creds: aidevops / aidevops_password

### Prometheus (prometheus)
- Port: 9090; Ready: GET /-/ready

### Grafana (grafana)
- Port: 3000; Login: admin / admin; Dashboards provisioned via grafana/ directory

### Chroma (chroma)
- Port: 8000; Data: chroma_data

---

## How to run locally (without unnecessary rebuilds)
- Start/ensure running:
  - docker compose up -d
- View processes:
  - docker compose ps
- Logs for specific service:
  - docker compose logs --tail=200 <service>
- Restart a specific app after code changes:
  - docker compose up -d <service>

## E2E Test Scripts
- Full coverage test: python -m scripts.e2e_full
  - Registers/logs in via Gateway, validates token, hits all service endpoints and checks key infra ports/UIs
- Basic smoke test: python -m scripts.e2e_smoke

Set env for tests:
- GATEWAY_BASE (default http://localhost)
- SMOKE_USER, SMOKE_EMAIL, SMOKE_PASSWORD

## Troubleshooting
- 401 from API routes: ensure Authorization: Bearer <token>
- NLP failures: set LLM_PROVIDER and API keys, or rely on DEBUG stubs
- Log Analysis 5xx: wait for Elasticsearch/Kafka to be green
- RabbitMQ UI 401/403: use credentials (aidevops / aidevops_password)

