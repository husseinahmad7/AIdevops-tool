import numpy as np
import pandas as pd
import joblib
import os
import logging
import json
import redis
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from prophet import Prophet
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.arima.model import ARIMA

from .config import settings

logger = logging.getLogger(__name__)

# Redis client for caching
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
    redis_client.ping()  # Test connection
except redis.ConnectionError:
    logger.warning("Redis connection failed, caching disabled")
    redis_client = None

# Ensure model directory exists
os.makedirs(settings.MODEL_DIR, exist_ok=True)
# Optional MLflow logging
try:
    import mlflow
    from mlflow import sklearn as mlflow_sklearn
except Exception:
    mlflow = None

# Optional MongoDB client
try:
    from pymongo import MongoClient
    mongo_client = MongoClient(settings.MONGODB_URI)
    mongo_db = mongo_client[settings.MONGODB_DB]
except Exception:
    mongo_client = None
    mongo_db = None


# Time series forecasting with Prophet
async def forecast_time_series(
    data: List[Dict[str, Union[str, float]]],
    metric_name: str,
    days: int = None,
    cache_key: str = None
) -> Dict[str, Any]:
    """Forecast time series data using Prophet"""
    if days is None:
        days = settings.DEFAULT_FORECAST_DAYS

    if days > settings.MAX_FORECAST_DAYS:
        days = settings.MAX_FORECAST_DAYS

    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df.columns = ['ds', 'y']
        df['ds'] = pd.to_datetime(df['ds'])

        # Train Prophet model
        model = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=True)
        model.fit(df)

        # Make future dataframe for prediction
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)

        # Prepare results
        results = {
            "metric": metric_name,
            "forecast_days": days,
            "timestamp": datetime.now().isoformat(),
            "forecast": []
        }

        # Add historical data
        for _, row in df.iterrows():
            results["forecast"].append({
                "date": row['ds'].strftime("%Y-%m-%d"),
                "value": float(row['y']),
                "type": "historical"
            })

        # Add forecast data (only future dates)
        last_date = df['ds'].max()
        for _, row in forecast[forecast['ds'] > last_date].iterrows():
            results["forecast"].append({
                "date": row['ds'].strftime("%Y-%m-%d"),
                "value": float(row['yhat']),
                "lower_bound": float(row['yhat_lower']),
                "upper_bound": float(row['yhat_upper']),
                "type": "forecast"
            })

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(results))

        return results
    except Exception as e:
        logger.error(f"Error in forecast_time_series: {e}")
        raise

# Anomaly detection with Isolation Forest
async def detect_anomalies(
    data: List[Dict[str, Union[str, float]]],
    metric_name: str,
    threshold: float = None,
    cache_key: str = None
) -> Dict[str, Any]:
    """Detect anomalies in time series data using Isolation Forest"""
    if threshold is None:
        threshold = settings.ANOMALY_DETECTION_THRESHOLD

    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'value']
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Extract features (you might want to add more sophisticated feature engineering)
        X = df['value'].values.reshape(-1, 1)

        # Train Isolation Forest model
        model = IsolationForest(contamination=0.05, random_state=42)
        df['anomaly_score'] = model.fit_predict(X)

        # Convert scores to probabilities (higher means more likely to be an anomaly)
        df['anomaly_probability'] = model.score_samples(X)
        df['anomaly_probability'] = 1 - (df['anomaly_probability'] - df['anomaly_probability'].min()) / \
                                   (df['anomaly_probability'].max() - df['anomaly_probability'].min())

        # Determine anomalies based on threshold
        df['is_anomaly'] = df['anomaly_probability'] > threshold

        # Prepare results
        results = {
            "metric": metric_name,
            "threshold": threshold,
            "timestamp": datetime.now().isoformat(),
            "data": [],
            "anomalies": []
        }

        # Add data points
        for _, row in df.iterrows():
            point = {
                "timestamp": row['timestamp'].isoformat(),
                "value": float(row['value']),
                "anomaly_probability": float(row['anomaly_probability']),
                "is_anomaly": bool(row['is_anomaly'])
            }
            results["data"].append(point)

            if row['is_anomaly']:
                results["anomalies"].append(point)

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(results))

        return results
    except Exception as e:
        logger.error(f"Error in detect_anomalies: {e}")
        raise

# Resource usage prediction with ARIMA
async def predict_resource_usage(
    data: List[Dict[str, Union[str, float]]],
    resource_type: str,
    hours: int = 24,
    cache_key: str = None
) -> Dict[str, Any]:
    """Predict resource usage (CPU, memory, etc.) using ARIMA"""
    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df.columns = ['timestamp', 'value']
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        # Fit ARIMA model
        model = ARIMA(df['value'].values, order=(5, 1, 0))
        model_fit = model.fit()

        # Make prediction
        forecast = model_fit.forecast(steps=hours)

        # Generate future timestamps
        last_timestamp = df['timestamp'].max()
        future_timestamps = [last_timestamp + timedelta(hours=i+1) for i in range(hours)]

        # Prepare results
        results = {
            "resource_type": resource_type,
            "forecast_hours": hours,
            "timestamp": datetime.now().isoformat(),
            "historical": [],
            "forecast": []
        }

        # Add historical data
        for _, row in df.iterrows():
            results["historical"].append({
                "timestamp": row['timestamp'].isoformat(),
                "value": float(row['value'])
            })
        

        # Add forecast data
        for i, timestamp in enumerate(future_timestamps):
            results["forecast"].append({
                "timestamp": timestamp.isoformat(),
                "value": float(forecast[i])
            })

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(results))

        return results
    except Exception as e:
        logger.error(f"Error in predict_resource_usage: {e}")
        raise

# Train simple model and log to MLflow
async def train_and_log_model(dataset: List[Dict[str, Union[str, float]]], model_name: str = "prophet") -> Dict[str, Any]:
    try:
        # Simple training: fit IsolationForest on values
        df = pd.DataFrame(dataset)
        if df.shape[1] >= 2:
            df.columns = ["timestamp", "value"]
        X = df["value"].values.reshape(-1, 1)
        model = IsolationForest(contamination=0.05, random_state=42)
        model.fit(X)

        metadata = {
            "model_name": model_name,
            "n_samples": len(X),
            "timestamp": datetime.now().isoformat(),
        }

        # Log to MLflow if available
        if mlflow:
            mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
            mlflow.set_experiment("aidevops-prediction")
            with mlflow.start_run() as run:
                mlflow.log_params({"model": model_name, "n_samples": len(X)})
                mlflow_sklearn.log_model(model, artifact_path="model")
                metadata["mlflow_run_id"] = run.info.run_id

        # Save metadata to MongoDB if available
        if mongo_db:
            mongo_db.models.insert_one(metadata)

        return {"status": "success", "metadata": metadata}
    except Exception as e:
        logger.error(f"Error in train_and_log_model: {e}")
        return {"status": "error", "message": str(e)}


# Incident prediction
async def predict_incidents(
    historical_incidents: List[Dict[str, Any]],
    system_metrics: List[Dict[str, Any]],
    cache_key: str = None
) -> Dict[str, Any]:
    """Predict potential incidents based on historical incidents and current system metrics"""
    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        # This is a simplified mock implementation
        # In a real-world scenario, you would use a more sophisticated ML model

        # Extract current metrics
        current_cpu = next((m for m in system_metrics if m.get("metric") == "cpu"), {}).get("value", 0)
        current_memory = next((m for m in system_metrics if m.get("metric") == "memory"), {}).get("value", 0)
        current_disk = next((m for m in system_metrics if m.get("metric") == "disk"), {}).get("value", 0)

        # Simple rule-based prediction
        potential_incidents = []

        if current_cpu > 80:
            potential_incidents.append({
                "type": "high_cpu",
                "probability": min(current_cpu / 100, 0.99),
                "message": "High CPU usage detected, potential performance degradation",
                "estimated_impact": "medium"
            })

        if current_memory > 85:
            potential_incidents.append({
                "type": "memory_leak",
                "probability": min(current_memory / 100, 0.99),
                "message": "High memory usage detected, potential memory leak",
                "estimated_impact": "high"
            })

        if current_disk > 90:
            potential_incidents.append({
                "type": "disk_full",
                "probability": min(current_disk / 100, 0.99),
                "message": "Disk space running low, potential disk full incident",
                "estimated_impact": "critical"
            })

        # Prepare results
        results = {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": {
                "cpu": current_cpu,
                "memory": current_memory,
                "disk": current_disk
            },
            "potential_incidents": potential_incidents,
            "prediction_confidence": 0.8  # Mock confidence level
        }

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(results))

        return results
    except Exception as e:
        logger.error(f"Error in predict_incidents: {e}")
        raise