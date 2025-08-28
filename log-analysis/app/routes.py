from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import httpx

from .config import settings
from .log_analyzer import (
    ingest_logs,
    search_logs,
    get_log_statistics,
    detect_log_anomalies,
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


# Helpers
from datetime import datetime  # noqa: E402 (used by helpers below)


def _iso_or_none(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        v = value.strip().replace("Z", "+00:00")
        # Accept digits like '1' as invalid; return None
        if len(v) < 8:
            return None
        # fromisoformat supports 'YYYY-MM-DD' and with times
        datetime.fromisoformat(v)
        return v
    except Exception:
        return None


def _http_error_for(result: Dict[str, Any]):
    msg = (result or {}).get("message", "")
    if "Elasticsearch not available" in msg:
        return 503
    if "index_not_found_exception" in msg:
        return 404
    return 500


# Ingest logs
@router.post("/ingest")
async def ingest_log_data(request: Request, data: Dict[str, Any] = Body(...)):
    user = await verify_token(request)

    logs = data.get("logs", [])
    source = data.get("source")

    if not logs:
        raise HTTPException(status_code=400, detail="Logs are required")
    if not source:
        raise HTTPException(status_code=400, detail="Source is required")

    if len(logs) > settings.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {settings.MAX_BATCH_SIZE}",
        )

    result = await ingest_logs(logs, source)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


# Search logs
@router.get("/search")
async def search_log_data(
    request: Request,
    query: str,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
):
    user = await verify_token(request)
    start_time = _iso_or_none(start_time)
    end_time = _iso_or_none(end_time)

    result = await search_logs(
        query=query,
        source=source,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=_http_error_for(result), detail=result.get("message")
        )

    return result


# Get log statistics
@router.get("/statistics")
async def get_log_stats(
    request: Request,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = "hour",
):
    user = await verify_token(request)

    start_time = _iso_or_none(start_time)
    end_time = _iso_or_none(end_time)

    # Generate cache key
    cache_key = (
        f"log_stats:{source or 'all'}:{start_time or ''}:{end_time or ''}:{interval}"
    )

    result = await get_log_statistics(
        source=source,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
        cache_key=cache_key,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=_http_error_for(result), detail=result.get("message")
        )

    return result


# Detect log anomalies
@router.get("/anomalies")
async def detect_anomalies(
    request: Request,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = "hour",
    threshold: float = 2.0,
):
    user = await verify_token(request)

    # Generate cache key
    cache_key = f"log_anomalies:{source or 'all'}:{start_time or ''}:{end_time or ''}:{interval}:{threshold}"

    result = await detect_log_anomalies(
        source=source,
        start_time=start_time,
        end_time=end_time,
        interval=interval,
        threshold=threshold,
        cache_key=cache_key,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return result


# Log digest (summary)
@router.get("/digest")
async def log_digest(
    request: Request,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = "hour",
):
    user = await verify_token(request)

    start_time = _iso_or_none(start_time)
    end_time = _iso_or_none(end_time)

    # Stats for counts over time, error types, sources
    stats = await get_log_statistics(
        source=source, start_time=start_time, end_time=end_time, interval=interval
    )
    if stats.get("status") == "error":
        raise HTTPException(
            status_code=_http_error_for(stats), detail=stats.get("message")
        )

    # Recent error samples
    error_query = "error OR exception OR fail OR critical OR timeout"
    recent_errors = await search_logs(
        query=error_query,
        source=source,
        start_time=start_time,
        end_time=end_time,
        limit=20,
        sort_by="timestamp",
        sort_order="desc",
    )
    if recent_errors.get("status") == "error":
        # Don't fail digest if error search fails; just return stats
        recent_list = []
    else:
        recent_list = [
            {
                "timestamp": item.get("timestamp"),
                "level": item.get("level"),
                "message": item.get("message", "")[:300],
            }
            for item in recent_errors.get("logs", [])
        ]

    # Compose digest
    return {
        "status": "success",
        "summary": {
            "time_range": {
                "start": stats.get("start_time"),
                "end": stats.get("end_time"),
            },
            "total": sum([p.get("count", 0) for p in stats.get("time_series", [])]),
            "errors": sum(
                [p.get("error_count", 0) for p in stats.get("time_series", [])]
            ),
            "top_sources": stats.get("sources", [])[:5],
            "error_types": stats.get("error_types", [])[:5],
        },
        "recent_errors": recent_list,
        "time_series": stats.get("time_series", []),
    }


# Admin-only endpoints


# Get all log sources
@router.get("/admin/logs/sources")
async def get_log_sources(request: Request):
    user = await verify_token(request)

    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get log statistics to extract sources
    result = await get_log_statistics(interval="day")

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))

    return {"sources": result.get("sources", [])}


# Admin: Elasticsearch health
@router.get("/admin/elastic/health")
async def admin_es_health(request: Request):
    user = await verify_token(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        from .log_analyzer import es_client

        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        info = es_client.info()
        health = es_client.cluster.health()
        return {"status": "success", "info": info, "health": health}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Admin: List indices
@router.get("/admin/elastic/indices")
async def admin_es_indices(request: Request, pattern: Optional[str] = None):
    user = await verify_token(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        from .log_analyzer import es_client

        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        patt = pattern or f"{settings.LOG_INDEX_PREFIX}*"
        indices = es_client.cat.indices(index=patt, format="json")
        return {"status": "success", "indices": indices}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete logs
@router.delete("/admin/logs")
async def delete_logs(
    request: Request,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    user = await verify_token(request)

    # Check if user has admin role
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # This is a placeholder for actual implementation
    # In a real implementation, you would delete logs from Elasticsearch

    return {
        "status": "success",
        "message": "Logs deleted successfully",
        "source": source,
        "start_time": start_time,
        "end_time": end_time,
    }


# Admin: delete-by-query
@router.delete("/admin/logs/delete")
async def admin_delete_by_query(
    request: Request,
    query: str,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
):
    user = await verify_token(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Build a search-equivalent filter
    try:
        from .log_analyzer import es_client

        if not es_client:
            raise HTTPException(status_code=503, detail="Elasticsearch not available")
        must = [{"query_string": {"query": query, "fields": ["message", "parsed.*"]}}]
        filters = []
        if source:
            filters.append({"term": {"source": source}})
        st = _iso_or_none(start_time)
        et = _iso_or_none(end_time)
        if st or et:
            rng = {"range": {"timestamp": {}}}
            if st:
                rng["range"]["timestamp"]["gte"] = st
            if et:
                rng["range"]["timestamp"]["lte"] = et
            filters.append(rng)
        dq = {"query": {"bool": {"must": must, "filter": filters}}}
        indices = (
            f"{settings.LOG_INDEX_PREFIX}*"
            if not source
            else f"{settings.LOG_INDEX_PREFIX}{source}-*"
        )
        resp = es_client.delete_by_query(
            index=indices, body=dq, conflicts="proceed", refresh=True, slices="auto"
        )
        return {
            "status": "success",
            "deleted": resp.get("deleted", 0),
            "took": resp.get("took"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
