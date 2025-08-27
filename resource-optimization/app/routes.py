from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List, Dict, Any
import requests
import json
from datetime import datetime, timedelta
from .config import settings

router = APIRouter()

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token with user management service (GET /users/validate)"""
    if not settings.auth_enabled:
        return {"id": "test_user", "role": "admin"}

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    try:
        response = requests.get(
            f"{settings.user_management_url}/api/v1/users/validate",
            headers={"Authorization": authorization},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="User management service unavailable")

@router.get("/usage")
async def get_resource_usage(authorization: Optional[str] = Header(None), user: dict = Depends(verify_token)):
    """Get current resource usage metrics (real host metrics via infrastructure-monitor)"""
    try:
        headers = {"Authorization": authorization} if authorization else None
        resp = requests.get(f"{settings.infrastructure_monitor_url}/api/v1/monitoring/metrics", headers=headers, timeout=5)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Infra monitor unavailable")
        metrics = resp.json()
        # Map to expected structure
        usage_data = {
            "timestamp": metrics.get("timestamp"),
            "cpu": {
                "total_cores": metrics.get("cpu", {}).get("cores"),
                "used_cores": round((metrics.get("cpu", {}).get("percent", 0) / 100.0) * max(metrics.get("cpu", {}).get("cores", 1), 1), 2),
                "utilization_percent": metrics.get("cpu", {}).get("percent")
            },
            "memory": {
                "total_gb": round(metrics.get("memory", {}).get("total", 0) / (1024**3), 2),
                "used_gb": round((metrics.get("memory", {}).get("total", 0) - metrics.get("memory", {}).get("available", 0)) / (1024**3), 2),
                "utilization_percent": metrics.get("memory", {}).get("percent")
            },
            "storage": {
                "total_gb": round(metrics.get("disk", {}).get("total", 0) / (1024**3), 2),
                "used_gb": round(metrics.get("disk", {}).get("used", 0) / (1024**3), 2),
                "utilization_percent": metrics.get("disk", {}).get("percent")
            },
            "network": {
                "ingress_mbps": round(metrics.get("network", {}).get("bytes_recv", 0) * 8 / 1_000_000, 2),
                "egress_mbps": round(metrics.get("network", {}).get("bytes_sent", 0) * 8 / 1_000_000, 2)
            }
        }
        return {"status": "success", "data": usage_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get resource usage: {str(e)}")

@router.get("/costs")
async def get_cost_analysis(authorization: Optional[str] = Header(None), user: dict = Depends(verify_token)):
    """Get cost analysis and breakdown (derived from usage rates)"""
    try:
        headers = {"Authorization": authorization} if authorization else None
        usage_resp = requests.get(f"{settings.infrastructure_monitor_url}/api/v1/monitoring/metrics", headers=headers, timeout=5)
        if usage_resp.status_code != 200:
            raise HTTPException(status_code=usage_resp.status_code, detail="Infra monitor unavailable")
        metrics = usage_resp.json()
        cpu_util = metrics.get("cpu", {}).get("percent", 0)
        mem_util = metrics.get("memory", {}).get("percent", 0)
        disk_util = metrics.get("disk", {}).get("percent", 0)
        # Simple rate model (example values)
        compute_cost = round(cpu_util * 1.2, 2)
        storage_cost = round(disk_util * 0.8, 2)
        network_cost =  round((metrics.get("network", {}).get("bytes_sent", 0) + metrics.get("network", {}).get("bytes_recv", 0)) * 8 / 1_000_000_000, 2)
        database_cost = round(mem_util * 0.9, 2)
        total = round(compute_cost + storage_cost + network_cost + database_cost, 2)
        cost_data = {
            "period": "current_snapshot",
            "total_cost": total,
            "breakdown": {
                "compute": compute_cost,
                "storage": storage_cost,
                "network": network_cost,
                "database": database_cost
            }
        }
        return {"status": "success", "data": cost_data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost analysis: {str(e)}")

@router.post("/optimize")
async def optimize_resources(optimization_request: Dict[str, Any], authorization: Optional[str] = Header(None), user: dict = Depends(verify_token)):
    """Generate resource optimization recommendations (based on current metrics)"""
    try:
        headers = {"Authorization": authorization} if authorization else None
        metrics_resp = requests.get(f"{settings.infrastructure_monitor_url}/api/v1/monitoring/metrics", headers=headers, timeout=5)
        if metrics_resp.status_code != 200:
            raise HTTPException(status_code=metrics_resp.status_code, detail="Infra monitor unavailable")
        m = metrics_resp.json()
        cpu = m.get("cpu", {}).get("percent", 0)
        mem = m.get("memory", {}).get("percent", 0)
        disk = m.get("disk", {}).get("percent", 0)
        recs = []
        if cpu > 70:
            recs.append({"type":"scale_out","resource":"compute","recommendation":"Add more CPU capacity","impact":"performance","confidence":0.9})
        elif cpu < 20:
            recs.append({"type":"rightsizing","resource":"compute","recommendation":"Reduce CPU allocation","impact":"cost","confidence":0.85})
        if mem > 75:
            recs.append({"type":"memory_tuning","resource":"memory","recommendation":"Increase memory or tune usage","impact":"stability","confidence":0.88})
        if disk > 80:
            recs.append({"type":"storage_cleanup","resource":"storage","recommendation":"Clean up unused data or expand storage","impact":"availability","confidence":0.82})
        if not recs:
            recs.append({"type":"opt_ok","resource":"all","recommendation":"Resources are within optimal ranges","impact":"none","confidence":0.7})
        result = {
            "optimization_id": f"opt_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "recommendations": recs
        }
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate optimization recommendations: {str(e)}")

@router.get("/metrics")
async def get_optimization_metrics(user: dict = Depends(verify_token)):
    """Get resource optimization metrics and KPIs (derived from infra monitor)"""
    try:
        resp = requests.get(f"{settings.infrastructure_monitor_url}/api/v1/monitoring/metrics", timeout=5)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Infra monitor unavailable")
        m = resp.json()
        cpu = m.get("cpu", {}).get("percent", 0)
        mem = m.get("memory", {}).get("percent", 0)
        disk = m.get("disk", {}).get("percent", 0)
        eff = max(0, 100 - ((cpu + mem + disk) / 3))  # simplistic inverse of utilization
        metrics = {
            "efficiency_score": round(eff, 1),
            "cost_efficiency": {
                "score": round(eff * 0.9, 1),
                "trend": "+5.2%" if eff > 50 else "-2.1%"
            },
            "resource_utilization": {
                "cpu": cpu,
                "memory": mem,
                "storage": disk
            },
            "waste_indicators": {
                "idle_resources": round(max(0, 100 - cpu) * 0.2, 1),
                "over_provisioned": round(max(0, 100 - mem) * 0.1, 1),
                "underutilized": round(max(0, 100 - disk) * 0.15, 1)
            },
            "optimization_history": []
        }
        return {"status": "success", "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization metrics: {str(e)}")

@router.post("/alerts")
async def create_resource_alert(alert_config: Dict[str, Any], user: dict = Depends(verify_token)):
    """Create resource usage alerts"""
    try:
        # Mock alert creation
        alert = {
            "alert_id": f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "type": alert_config.get("type", "threshold"),
            "resource": alert_config.get("resource", "cpu"),
            "threshold": alert_config.get("threshold", 80),
            "status": "active",
            "created_at": datetime.utcnow().isoformat()
        }
        return {"status": "success", "data": alert}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")