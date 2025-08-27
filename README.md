# AI DevOps Assistant

A scalable AI DevOps Assistant using microservices architecture that automates and optimizes DevOps workflows through intelligent monitoring, prediction, and natural language interaction.

## Project Structure

```
├── api-gateway/            # API Gateway Service
├── user-management/        # User Management Service
├── infrastructure-monitor/ # Infrastructure Monitoring Service
├── ai-prediction/          # AI Prediction Service
├── log-analysis/           # Log Analysis Service
├── cicd-optimization/      # CI/CD Optimization Service
├── resource-optimization/  # Resource Optimization Service
├── natural-language/       # Natural Language Interface Service
├── notification/           # Notification Service
├── reporting/              # Reporting Service
└── shared/                 # Shared libraries and utilities
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Pipenv
- Postgres, Redis, RabbitMQ, Elasticsearch, Chroma, Prometheus, Grafana images

### Setup

1. Put your API keys in api-key.env (example):

```
HUGGINGFACE_API_KEY=hf_...
OPENROUTER_API_KEY=sk-or-...
```

2. Build and start:

```
docker compose up -d --build
```

3. Access:
- API Gateway: http://localhost:8080
- API Docs: http://localhost/docs (via gateway)
- Prometheus: http://localhost:80/prometheus
- Grafana: http://localhost:80/grafana

## Normalized API Paths

- Log Analysis mounted at /api/v1/logs (paths: /ingest, /search, /statistics, /anomalies)
- Natural Language mounted at /api/v1/nlp (paths: /query, /generate-iac, /explain/{concept}, /documents, /documents/load, /documents/search)

## Prometheus Targets

- Infrastructure Monitor: /api/v1/monitoring/prometheus-metrics
- Natural Language: port 8088 target fixed

## Testing

- Local unit tests per service using pytest (see service/tests)
- CI pipeline runs linting and tests for each service

Run locally for a service:

```
cd api-gateway
pipenv install --dev --system --deploy || pipenv install --system
pytest -q
```

## Pre-commit

Install hooks:

```
pip install pre-commit
pre-commit install
```

## Next Enhancements

- Kafka, MinIO, MongoDB, MLflow integration for AI Prediction
- Helm charts / K8s manifests per service
- Security hardening and e2e tests

## License

MIT