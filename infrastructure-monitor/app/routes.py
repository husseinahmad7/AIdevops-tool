from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import httpx
import asyncio
import json
import prometheus_client
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from fastapi.responses import Response
from datetime import datetime, timedelta

from .config import settings
from .monitoring import (
    get_system_metrics,
    get_docker_metrics,
    get_kubernetes_metrics,
    monitoring_task
)

router = APIRouter()

# Initialize Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])
CPU_GAUGE = Gauge('system_cpu_usage_percent', 'Current CPU Usage Percentage')
MEMORY_GAUGE = Gauge('system_memory_usage_percent', 'Current Memory Usage Percentage')
DISK_GAUGE = Gauge('system_disk_usage_percent', 'Current Disk Usage Percentage')
DOCKER_CONTAINERS = Gauge('docker_containers_total', 'Total number of Docker containers')
DOCKER_RUNNING = Gauge('docker_containers_running', 'Number of running Docker containers')

# Start background monitoring task
monitoring_task_handle = None

@router.on_event("startup")
async def startup_event():
    global monitoring_task_handle
    monitoring_task_handle = asyncio.create_task(monitoring_task())

@router.on_event("shutdown")
async def shutdown_event():
    if monitoring_task_handle:
        monitoring_task_handle.cancel()

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
                headers={"Authorization": auth_header}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            return response.json()
    except httpx.RequestError:
        # If user service is down, we'll still accept the request in development mode
        if settings.DEBUG:
            return {"id": "debug", "username": "debug", "role": "admin"}
        raise HTTPException(status_code=503, detail="Authentication service unavailable")

# Get current system metrics
@router.get("/metrics/system")
async def get_current_system_metrics(request: Request):
    user = await verify_token(request)
    metrics = await get_system_metrics()
    return metrics

# Get Docker container metrics
@router.get("/metrics/docker")
async def get_current_docker_metrics(request: Request):
    user = await verify_token(request)
    
    if not settings.DOCKER_ENABLED:
        raise HTTPException(status_code=400, detail="Docker monitoring is disabled")
    
    metrics = await get_docker_metrics()
    return metrics

# Get Kubernetes metrics
@router.get("/metrics/kubernetes")
async def get_current_kubernetes_metrics(request: Request):
    user = await verify_token(request)
    
    if not settings.K8S_ENABLED:
        raise HTTPException(status_code=400, detail="Kubernetes monitoring is disabled")
    
    metrics = await get_kubernetes_metrics()
    return metrics

# Prometheus metrics endpoint
@router.get("/prometheus-metrics")
async def prometheus_metrics():
    # Update metrics based on current system state
    system_metrics = await get_system_metrics()
    CPU_GAUGE.set(system_metrics["cpu"]["percent"])
    MEMORY_GAUGE.set(system_metrics["memory"]["percent"])
    DISK_GAUGE.set(system_metrics["disk"]["percent"])
    
    # Update Docker metrics if enabled
    if settings.DOCKER_ENABLED:
        docker_metrics = await get_docker_metrics()
        DOCKER_CONTAINERS.set(len(docker_metrics))
        running_containers = sum(1 for container in docker_metrics if container["status"] == "running")
        DOCKER_RUNNING.set(running_containers)
    
    # Return metrics in Prometheus format
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Get all metrics
@router.get("/metrics")
async def get_all_metrics(request: Request):
    user = await verify_token(request)
    
    system_metrics = await get_system_metrics()
    
    result = {
        "system": system_metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    if settings.DOCKER_ENABLED:
        docker_metrics = await get_docker_metrics()
        result["docker"] = docker_metrics
    
    if settings.K8S_ENABLED:
        k8s_metrics = await get_kubernetes_metrics()
        result["kubernetes"] = k8s_metrics
    
    return result

# Get resource usage history (mock implementation - would use a time-series database in production)
@router.get("/metrics/history/{resource_type}")
async def get_resource_history(
    request: Request,
    resource_type: str,
    days: int = 1
):
    user = await verify_token(request)
    
    if resource_type not in ["cpu", "memory", "disk", "network"]:
        raise HTTPException(status_code=400, detail=f"Invalid resource type: {resource_type}")
    
    if days < 1 or days > settings.METRICS_RETENTION_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Days must be between 1 and {settings.METRICS_RETENTION_DAYS}"
        )
    
    # Mock historical data (in a real implementation, this would come from a database)
    now = datetime.now()
    history = []
    
    for i in range(days * 24):  # Hourly data points
        timestamp = now - timedelta(hours=i)
        
        if resource_type == "cpu":
            value = 50 + (i % 30)  # Mock CPU percentage between 50-80%
        elif resource_type == "memory":
            value = 60 + (i % 20)  # Mock memory percentage between 60-80%
        elif resource_type == "disk":
            value = 70 + (i % 15)  # Mock disk percentage between 70-85%
        else:  # network
            value = 5000000 + (i % 1000000)  # Mock network bytes between 5-6 MB
        
        history.append({
            "timestamp": timestamp.isoformat(),
            "value": value
        })
    
    return {
        "resource_type": resource_type,
        "days": days,
        "data_points": len(history),
        "history": history
    }

# Admin-only endpoints

# Update monitoring settings
@router.post("/admin/settings")
async def update_settings(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)
    
    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update settings (in a real implementation, this would update environment variables or a config file)
    updated = {}
    
    if "monitoring_interval" in data:
        interval = data["monitoring_interval"]
        if interval < 10 or interval > 3600:
            raise HTTPException(status_code=400, detail="Interval must be between 10 and 3600 seconds")
        settings.MONITORING_INTERVAL = interval
        updated["monitoring_interval"] = interval
    
    if "cpu_threshold" in data:
        threshold = data["cpu_threshold"]
        if threshold < 0 or threshold > 100:
            raise HTTPException(status_code=400, detail="CPU threshold must be between 0 and 100")
        settings.CPU_THRESHOLD = threshold
        updated["cpu_threshold"] = threshold
    
    if "memory_threshold" in data:
        threshold = data["memory_threshold"]
        if threshold < 0 or threshold > 100:
            raise HTTPException(status_code=400, detail="Memory threshold must be between 0 and 100")
        settings.MEMORY_THRESHOLD = threshold
        updated["memory_threshold"] = threshold
    
    if "disk_threshold" in data:
        threshold = data["disk_threshold"]
        if threshold < 0 or threshold > 100:
            raise HTTPException(status_code=400, detail="Disk threshold must be between 0 and 100")
        settings.DISK_THRESHOLD = threshold
        updated["disk_threshold"] = threshold
    
    return {
        "message": "Settings updated successfully",
        "updated": updated
    }

# Trigger a manual metrics collection
@router.post("/admin/collect")
async def trigger_collection(request: Request):
    user = await verify_token(request)
    
    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Collect metrics
    system_metrics = await get_system_metrics()
    
    result = {
        "system": system_metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    if settings.DOCKER_ENABLED:
        docker_metrics = await get_docker_metrics()
        result["docker"] = docker_metrics
    
    if settings.K8S_ENABLED:
        k8s_metrics = await get_kubernetes_metrics()
        result["kubernetes"] = k8s_metrics
    
    return result