# Log Analysis Service

- URL (direct): http://localhost:8084
- Gateway: http://localhost/api/v1/logs
- Health: GET /health

## Purpose
Search and analytics on logs backed by Elasticsearch and Kafka.

## Endpoints
- GET /api/v1/logs/search?query=
- POST /api/v1/logs/ingest

## Config
- ELASTICSEARCH_URL, KAFKA_BROKER_URL, REDIS_URL

## Troubleshooting
- Startup may be slow while Elasticsearch cluster turns green.
- 5xx early on is expected; retry once ES/Kafka ready.

