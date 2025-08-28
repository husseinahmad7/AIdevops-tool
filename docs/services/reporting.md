# Reporting Service

- URL (direct): http://localhost:8089
- Gateway: http://localhost/api/v1/reports
- Health: GET /health

## Endpoints
- GET /api/v1/reports/templates
- POST /api/v1/reports/generate

## Config
- INFRASTRUCTURE_MONITOR_URL, AI_PREDICTION_URL, LOG_ANALYSIS_URL, RESOURCE_OPTIMIZATION_URL, REDIS_URL, USER_MANAGEMENT_URL

## Troubleshooting
- 401 indicates missing/invalid token
- May depend on other services; ensure their health first
