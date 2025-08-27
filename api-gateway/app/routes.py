from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import httpx
from typing import Dict, Any, Optional
import json

from .auth import get_current_user, get_admin_user
from .config import settings

router = APIRouter()

# Helper function to forward requests to microservices
async def forward_request(request: Request, service_url: str, path: str, current_user: Optional[Dict] = None):
    # Get request body as bytes
    body = await request.body()

    # Build headers for upstream, remove hop-by-hop and auto-set headers
    incoming_headers = dict(request.headers)
    for h in [
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "accept-encoding",
        "keep-alive",
        "proxy-connection",
        "upgrade",
    ]:
        incoming_headers.pop(h, None)

    # Query parameters
    params = dict(request.query_params)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=f"{service_url}{path}",
                content=body if body else None,
                headers=incoming_headers,
                params=params,
                timeout=30.0,
            )
            # Pass through response (excluding hop-by-hop)
            upstream_headers = dict(response.headers)
            upstream_headers.pop("content-encoding", None)
            upstream_headers.pop("transfer-encoding", None)
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=upstream_headers,
                media_type=upstream_headers.get("content-type"),
            )
        except httpx.RequestError as exc:
            return JSONResponse(
                status_code=503,
                content={"detail": f"Service unavailable: {str(exc)}"},
            )


# Uniform per-service health endpoints through the Gateway (no auth required)
@router.get("/monitoring/health")
async def monitoring_health(request: Request):
    return await forward_request(request, settings.INFRASTRUCTURE_MONITOR_URL, "/health", None)

@router.get("/predictions/health")
async def predictions_health(request: Request):
    return await forward_request(request, settings.AI_PREDICTION_URL, "/health", None)

@router.get("/logs/health")
async def logs_health(request: Request):
    return await forward_request(request, settings.LOG_ANALYSIS_URL, "/health", None)

@router.get("/cicd/health")
async def cicd_health(request: Request):
    return await forward_request(request, settings.CICD_OPTIMIZATION_URL, "/health", None)

@router.get("/resources/health")
async def resources_health(request: Request):
    return await forward_request(request, settings.RESOURCE_OPTIMIZATION_URL, "/health", None)

@router.get("/nlp/health")
async def nlp_health(request: Request):
    return await forward_request(request, settings.NATURAL_LANGUAGE_URL, "/health", None)

@router.get("/notifications/health")
async def notifications_health(request: Request):
    return await forward_request(request, settings.NOTIFICATION_URL, "/health", None)

@router.get("/reports/health")
async def reports_health(request: Request):
    return await forward_request(request, settings.REPORTING_URL, "/health", None)

@router.get("/users/health")
async def users_health(request: Request):
    return await forward_request(request, settings.USER_MANAGEMENT_URL, "/health", None)

# User Management Service routes
@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def auth_route(request: Request, path: str):
    return await forward_request(request, settings.USER_MANAGEMENT_URL, f"/api/v1/auth/{path}", None)

@router.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def users_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.USER_MANAGEMENT_URL, f"/api/v1/users/{path}", current_user)

# Infrastructure Monitoring Service routes
@router.api_route("/monitoring/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def monitoring_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.INFRASTRUCTURE_MONITOR_URL, f"/api/v1/monitoring/{path}", current_user)

# AI Prediction Service routes
@router.api_route("/predictions/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def predictions_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.AI_PREDICTION_URL, f"/api/v1/predictions/{path}", current_user)

# Log Analysis Service routes
@router.api_route("/logs/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def logs_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.LOG_ANALYSIS_URL, f"/api/v1/logs/{path}", current_user)

# CI/CD Optimization Service routes
@router.api_route("/cicd/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def cicd_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.CICD_OPTIMIZATION_URL, f"/api/v1/cicd/{path}", current_user)

# Resource Optimization Service routes
@router.api_route("/resources/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def resources_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.RESOURCE_OPTIMIZATION_URL, f"/api/v1/resources/{path}", current_user)

# Natural Language Interface Service routes
@router.api_route("/nlp/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def nlp_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.NATURAL_LANGUAGE_URL, f"/api/v1/nlp/{path}", current_user)

# Notification Service routes
@router.api_route("/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def notifications_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.NOTIFICATION_URL, f"/api/v1/notifications/{path}", current_user)

# Reporting Service routes
@router.api_route("/reports/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def reports_route(request: Request, path: str, current_user: Dict = Depends(get_current_user)):
    return await forward_request(request, settings.REPORTING_URL, f"/api/v1/reports/{path}", current_user)

# Admin routes - requires admin role
@router.api_route("/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def admin_route(request: Request, path: str, admin_user: Dict = Depends(get_admin_user)):
    # Determine which service to forward to based on the path
    if path.startswith("users"):
        service_url = settings.USER_MANAGEMENT_URL
        path = path.replace("users", "admin/users")
    elif path.startswith("monitoring"):
        service_url = settings.INFRASTRUCTURE_MONITOR_URL
        path = path.replace("monitoring", "admin/monitoring")
    else:
        # Default to user management for other admin routes
        service_url = settings.USER_MANAGEMENT_URL

    return await forward_request(request, service_url, f"/api/v1/{path}", admin_user)