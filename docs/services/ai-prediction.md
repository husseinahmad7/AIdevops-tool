# AI Prediction Service

- URL (direct): http://localhost:8083
- Gateway: http://localhost/api/v1/predictions
- Health: GET /health

## Endpoints
- POST /api/v1/predictions/forecast
- POST /api/v1/predictions/train

## Config
- MONGODB_URI, MLFLOW_TRACKING_URI, MLFLOW_S3_ENDPOINT_URL, AWS_ACCESS_KEY_ID/SECRET

## Notes
- Heavy ML dependencies may slow startup. The E2E tests use tiny sample data.

