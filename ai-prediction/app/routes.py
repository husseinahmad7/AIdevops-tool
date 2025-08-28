from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import httpx

from .config import settings
from .prediction import (
    forecast_time_series,
    detect_anomalies,
    predict_resource_usage,
    predict_incidents,
    train_and_log_model,
)

router = APIRouter()


# Verify token with User Management Service
async def verify_token(request: Request):
    if not settings.AUTH_ENABLED:
        return {"id": "anonymous", "username": "anonymous", "role": "user"}

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_MANAGEMENT_URL}/api/v1/users/validate",
                headers={"Authorization": auth_header},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.RequestError:
        # If user service is down, we'll still accept the request in development mode
        if settings.DEBUG:
            return {"id": "debug", "username": "debug", "role": "admin"}
        raise HTTPException(
            status_code=503, detail="Authentication service unavailable"
        )


# Time series forecasting
@router.post("/forecast")
async def forecast(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    time_series_data = data.get("data")
    metric_name = data.get("metric_name")
    days = data.get("days", settings.DEFAULT_FORECAST_DAYS)

    if not time_series_data or not metric_name:
        raise HTTPException(status_code=400, detail="Data and metric_name are required")

    # Generate cache key
    cache_key = f"forecast:{metric_name}:{days}:{len(time_series_data)}"

    # Perform forecast
    result = await forecast_time_series(time_series_data, metric_name, days, cache_key)

    return result


# Anomaly detection
@router.post("/anomalies")
async def anomalies(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    time_series_data = data.get("data")
    metric_name = data.get("metric_name")
    threshold = data.get("threshold", settings.ANOMALY_DETECTION_THRESHOLD)

    if not time_series_data or not metric_name:
        raise HTTPException(status_code=400, detail="Data and metric_name are required")

    # Generate cache key
    cache_key = f"anomalies:{metric_name}:{threshold}:{len(time_series_data)}"

    # Perform anomaly detection
    result = await detect_anomalies(time_series_data, metric_name, threshold, cache_key)

    return result


# Resource usage prediction
@router.post("/resources/predict")
async def predict_resources(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    historical_data = data.get("data")
    resource_type = data.get("resource_type")
    hours = data.get("hours", 24)

    if not historical_data or not resource_type:
        raise HTTPException(
            status_code=400, detail="Data and resource_type are required"
        )

    # Generate cache key
    cache_key = f"resource_prediction:{resource_type}:{hours}:{len(historical_data)}"

    # Predict resource usage
    result = await predict_resource_usage(
        historical_data, resource_type, hours, cache_key
    )

    return result


# Incident prediction
@router.post("/incidents/predict")
async def predict_potential_incidents(
    request: Request, data: Dict[str, Any] = Body(...)
):
    user = await verify_token(request)

    historical_incidents = data.get("historical_incidents", [])
    system_metrics = data.get("system_metrics", [])

    if not system_metrics:
        raise HTTPException(status_code=400, detail="System metrics are required")

    # Generate cache key
    cache_key = f"incident_prediction:{len(historical_incidents)}:{len(system_metrics)}"

    # Predict incidents
    result = await predict_incidents(historical_incidents, system_metrics, cache_key)

    return result


# Train model and log to MLflow
@router.post("/train")
async def train_model(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)
    dataset = data.get("data")
    model_name = data.get("model_name", "prophet")
    if not dataset:
        raise HTTPException(status_code=400, detail="Data is required")
    result = await train_and_log_model(dataset, model_name)
    return result


# Batch predictions
@router.post("/batch")
async def batch_predictions(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    predictions = data.get("predictions", [])

    if not predictions:
        raise HTTPException(status_code=400, detail="Predictions are required")

    results = {}

    for prediction in predictions:
        prediction_type = prediction.get("type")
        prediction_data = prediction.get("data", {})

        if prediction_type == "forecast":
            time_series_data = prediction_data.get("data")
            metric_name = prediction_data.get("metric_name")
            days = prediction_data.get("days", settings.DEFAULT_FORECAST_DAYS)

            if time_series_data and metric_name:
                cache_key = f"forecast:{metric_name}:{days}:{len(time_series_data)}"
                result = await forecast_time_series(
                    time_series_data, metric_name, days, cache_key
                )
                results[f"forecast_{metric_name}"] = result

        elif prediction_type == "anomalies":
            time_series_data = prediction_data.get("data")
            metric_name = prediction_data.get("metric_name")
            threshold = prediction_data.get(
                "threshold", settings.ANOMALY_DETECTION_THRESHOLD
            )

            if time_series_data and metric_name:
                cache_key = (
                    f"anomalies:{metric_name}:{threshold}:{len(time_series_data)}"
                )
                result = await detect_anomalies(
                    time_series_data, metric_name, threshold, cache_key
                )
                results[f"anomalies_{metric_name}"] = result

        elif prediction_type == "resource_prediction":
            historical_data = prediction_data.get("data")
            resource_type = prediction_data.get("resource_type")
            hours = prediction_data.get("hours", 24)

            if historical_data and resource_type:
                cache_key = f"resource_prediction:{resource_type}:{hours}:{len(historical_data)}"
                result = await predict_resource_usage(
                    historical_data, resource_type, hours, cache_key
                )
                results[f"resource_prediction_{resource_type}"] = result

    return {"batch_results": results, "count": len(results)}
