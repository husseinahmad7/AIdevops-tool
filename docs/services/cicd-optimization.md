# CI/CD Optimization Service

- URL (direct): http://localhost:8085
- Gateway: http://localhost/api/v1/cicd
- Health: GET /health

## Endpoints
- GET /api/v1/cicd/pipelines
- GET /api/v1/cicd/pipelines/{id}/analysis
- GET /api/v1/cicd/metrics

## Auth
- Uses token verification via user-management. Some routes accept token query param.

## Troubleshooting
- Ensure Gateway forwards Authorization header and/or supply token query param.
