import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from elasticsearch import Elasticsearch, helpers
import redis
import pika

from .config import settings

logger = logging.getLogger(__name__)

# Initialize Elasticsearch client
es_client = None
try:
    if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
        es_client = Elasticsearch(
            settings.ELASTICSEARCH_URL,
            basic_auth=(
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD,
            ),
        )
    else:
        es_client = Elasticsearch(settings.ELASTICSEARCH_URL)

    # Test connection
    es_client.info()
    logger.info("Connected to Elasticsearch")
except Exception as e:
    logger.warning(f"Elasticsearch connection failed: {e}")
    es_client = None

# Ensure ILM policy exists
try:
    if es_client:
        policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "actions": {
                            "rollover": {
                                "max_age": f"{settings.LOG_RETENTION_DAYS}d",
                                "max_primary_shard_size": "50gb",
                            }
                        }
                    },
                    "delete": {
                        "min_age": f"{settings.LOG_RETENTION_DAYS}d",
                        "actions": {"delete": {}},
                    },
                }
            }
        }
        es_client.ilm.put_lifecycle(name="aidevops-logs-policy", policy=policy)
except Exception as e:
    logger.warning(f"Failed to ensure ILM policy: {e}")

# Redis client for caching
redis_client = None
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
    redis_client.ping()  # Test connection
    logger.info("Connected to Redis")
except redis.ConnectionError as e:
    logger.warning(f"Redis connection failed: {e}")
    redis_client = None

# Common log patterns
LOG_PATTERNS = {
    "nginx_access": re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<user>[^ ]*) \[(?P<time>[^\]]*)"  # noqa: W605
        r' (?P<timezone>[^\]]*)?\] "(?P<method>[A-Z]+) (?P<path>[^ ]*) '  # noqa: W605
        r'(?P<protocol>[^"]*)?" (?P<status>\d+) (?P<bytes>\d+) '  # noqa: W605
        r'"(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"'
    ),
    "apache_access": re.compile(
        r"(?P<ip>\d+\.\d+\.\d+\.\d+) - (?P<user>[^ ]*) \[(?P<time>[^\]]*)"  # noqa: W605
        r'\] "(?P<method>[A-Z]+) (?P<path>[^ ]*) (?P<protocol>[^"]*)?" '  # noqa: W605
        r'(?P<status>\d+) (?P<bytes>\d+) "(?P<referer>[^"]*)" '  # noqa: W605
        r'"(?P<user_agent>[^"]*)"'
    ),
    "kubernetes": re.compile(
        r"(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) "  # noqa: W605
        r"(?P<level>[A-Z]+) (?P<component>[^\s]+) (?P<message>.*)"
    ),
    "docker": re.compile(
        r"(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) "  # noqa: W605
        r"(?P<level>[A-Z]+) (?P<message>.*)"
    ),
    "application": re.compile(
        r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+) "  # noqa: W605
        r"(?P<level>[A-Z]+) \[(?P<thread>[^\]]+)\] "  # noqa: W605
        r"(?P<logger>[^\s]+) - (?P<message>.*)"
    ),
}

# Error patterns to detect
ERROR_PATTERNS = [
    re.compile(r"error", re.IGNORECASE),
    re.compile(r"exception", re.IGNORECASE),
    re.compile(r"fail", re.IGNORECASE),
    re.compile(r"critical", re.IGNORECASE),
    re.compile(r"warn", re.IGNORECASE),
    re.compile(r"timeout", re.IGNORECASE),
    re.compile(r"refused", re.IGNORECASE),
    re.compile(r"unavailable", re.IGNORECASE),
    re.compile(r"bad gateway", re.IGNORECASE),
    re.compile(r"unauthorized", re.IGNORECASE),
]


# Ingest logs into Elasticsearch
async def ingest_logs(logs: List[Dict[str, Any]], source: str) -> Dict[str, Any]:
    """Ingest logs into Elasticsearch"""
    if not es_client:
        return {"status": "error", "message": "Elasticsearch not available"}

    try:
        # Prepare index name with date suffix
        today = datetime.now().strftime("%Y.%m.%d")
        index_name = f"{settings.LOG_INDEX_PREFIX}{source}-{today}"

        # Ensure index exists
        # Optionally create an alias for rollover-ready patterns
        try:
            alias = f"{settings.LOG_INDEX_PREFIX}{source}-alias"
            if not es_client.indices.exists_alias(name=alias):
                es_client.indices.put_alias(index=index_name, name=alias)
        except Exception:
            pass

        if not es_client.indices.exists(index=index_name):
            es_client.indices.create(
                index=index_name,
                body={
                    "settings": {"index.lifecycle.name": "aidevops-logs-policy"},
                    "mappings": {
                        "properties": {
                            "timestamp": {"type": "date"},
                            "level": {"type": "keyword"},
                            "message": {"type": "text"},
                            "source": {"type": "keyword"},
                            "host": {"type": "keyword"},
                            "parsed": {"type": "object"},
                            "is_error": {"type": "boolean"},
                        }
                    },
                },
            )

        # Process logs
        actions = []
        for log in logs:
            # Ensure timestamp exists
            if "timestamp" not in log:
                log["timestamp"] = datetime.now().isoformat()

            # Add source
            log["source"] = source

            # Parse log message if not already parsed
            if "parsed" not in log and "message" in log:
                parsed = parse_log_message(log["message"], source)
                if parsed:
                    log["parsed"] = parsed

            # Detect if log is an error
            if "message" in log:
                log["is_error"] = is_error_log(log["message"])

            # Add to bulk actions
            actions.append({"_index": index_name, "_source": log})

        # Bulk insert
        if actions:
            helpers.bulk(es_client, actions)

        return {
            "status": "success",
            "message": f"Ingested {len(logs)} logs",
            "index": index_name,
        }
    except Exception as e:
        logger.error(f"Error ingesting logs: {e}")
        return {"status": "error", "message": str(e)}


# Parse log message
def parse_log_message(message: str, source: str) -> Optional[Dict[str, Any]]:
    """Parse log message using regex patterns"""
    try:
        # Try to parse as JSON first
        try:
            return json.loads(message)
        except json.JSONDecodeError:
            pass

        # Try regex patterns
        for _pattern_name, pattern in LOG_PATTERNS.items():
            match = pattern.match(message)
            if match:
                return match.groupdict()

        # No pattern matched
        return None
    except Exception as e:
        logger.error(f"Error parsing log message: {e}")
        return None


# Check if log is an error
def is_error_log(message: str) -> bool:
    """Check if log message contains error patterns"""
    for pattern in ERROR_PATTERNS:
        if pattern.search(message):
            return True
    return False


# Search logs
async def search_logs(
    query: str,
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Search logs in Elasticsearch"""
    if not es_client:
        return {"status": "error", "message": "Elasticsearch not available"}

    try:
        # Build query
        es_query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "query_string": {
                                "query": query,
                                "fields": ["message", "parsed.*"],
                            }
                        }
                    ],
                    "filter": [],
                }
            },
            "sort": [{sort_by: {"order": sort_order}}],
            "from": offset,
            "size": limit,
        }

        # Add source filter
        if source:
            es_query["query"]["bool"]["filter"].append({"term": {"source": source}})

        # Add time range filter
        if start_time or end_time:
            time_filter = {"range": {"timestamp": {}}}
            if start_time:
                time_filter["range"]["timestamp"]["gte"] = start_time
            if end_time:
                time_filter["range"]["timestamp"]["lte"] = end_time
            es_query["query"]["bool"]["filter"].append(time_filter)

        # Add additional filters
        if filters:
            for field, value in filters.items():
                es_query["query"]["bool"]["filter"].append({"term": {field: value}})

        # Determine indices to search
        indices = f"{settings.LOG_INDEX_PREFIX}*"
        if source:
            indices = f"{settings.LOG_INDEX_PREFIX}{source}-*"

        # Execute search
        response = es_client.search(index=indices, body=es_query)

        # Process results
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        logs = []
        for hit in hits:
            log = hit["_source"]
            log["_id"] = hit["_id"]
            logs.append(log)

        return {
            "status": "success",
            "total": total,
            "logs": logs,
            "query": query,
            "source": source,
            "start_time": start_time,
            "end_time": end_time,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return {"status": "error", "message": str(e)}


# Get log statistics
async def get_log_statistics(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = "hour",
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Get log statistics from Elasticsearch"""
    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    if not es_client:
        return {"status": "error", "message": "Elasticsearch not available"}

    try:
        # Set default time range if not provided
        if not end_time:
            end_time = datetime.now().isoformat()
        if not start_time:
            start_time = (datetime.now() - timedelta(days=1)).isoformat()

        # Build query
        es_query = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"timestamp": {"gte": start_time, "lte": end_time}}}
                    ]
                }
            },
            "aggs": {
                "logs_over_time": {
                    "date_histogram": {
                        "field": "timestamp",
                        "calendar_interval": interval,
                    },
                    "aggs": {"error_count": {"filter": {"term": {"is_error": True}}}},
                },
                "error_types": {"terms": {"field": "level.keyword", "size": 10}},
                "sources": {"terms": {"field": "source", "size": 10}},
            },
            "size": 0,  # We only want aggregations, not actual documents
        }

        # Add source filter
        if source:
            es_query["query"]["bool"]["filter"].append({"term": {"source": source}})

        # Determine indices to search
        indices = f"{settings.LOG_INDEX_PREFIX}*"
        if source:
            indices = f"{settings.LOG_INDEX_PREFIX}{source}-*"

        # Execute search
        response = es_client.search(index=indices, body=es_query)

        # Process results
        time_buckets = response["aggregations"]["logs_over_time"]["buckets"]
        error_buckets = response["aggregations"]["error_types"]["buckets"]
        source_buckets = response["aggregations"]["sources"]["buckets"]

        # Format time series data
        time_series = []
        for bucket in time_buckets:
            time_series.append(
                {
                    "timestamp": bucket["key_as_string"],
                    "count": bucket["doc_count"],
                    "error_count": bucket["error_count"]["doc_count"],
                }
            )

        # Format error types
        error_types = []
        for bucket in error_buckets:
            error_types.append({"level": bucket["key"], "count": bucket["doc_count"]})

        # Format sources
        sources = []
        for bucket in source_buckets:
            sources.append({"source": bucket["key"], "count": bucket["doc_count"]})

        result = {
            "status": "success",
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval,
            "time_series": time_series,
            "error_types": error_types,
            "sources": sources,
        }

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(result))

        return result
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        return {"status": "error", "message": str(e)}


# Detect log anomalies
async def detect_log_anomalies(
    source: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    interval: str = "hour",
    threshold: float = 2.0,
    cache_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Detect anomalies in log patterns"""
    # Check cache first
    if redis_client and cache_key:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

    try:
        # Get log statistics
        stats = await get_log_statistics(source, start_time, end_time, interval)

        if stats.get("status") != "success":
            return stats

        # Extract time series data
        time_series = stats["time_series"]

        # Convert to pandas DataFrame
        df = pd.DataFrame(time_series)

        # Calculate moving average and standard deviation
        window_size = 5
        if len(df) >= window_size:
            df["moving_avg"] = df["count"].rolling(window=window_size).mean()
            df["moving_std"] = df["count"].rolling(window=window_size).std()

            # Calculate z-scores
            df["z_score"] = np.nan
            mask = df["moving_std"] > 0
            df.loc[mask, "z_score"] = (
                df.loc[mask, "count"] - df.loc[mask, "moving_avg"]
            ) / df.loc[mask, "moving_std"]

            # Detect anomalies
            df["is_anomaly"] = abs(df["z_score"]) > threshold
        else:
            # Not enough data points for moving statistics
            df["moving_avg"] = df["count"]
            df["moving_std"] = 0
            df["z_score"] = 0
            df["is_anomaly"] = False

        # Format results
        anomalies = []
        for _, row in df[df["is_anomaly"]].iterrows():
            anomalies.append(
                {
                    "timestamp": row["timestamp"],
                    "count": int(row["count"]),
                    "expected": float(row["moving_avg"]),
                    "z_score": float(row["z_score"]),
                    "error_count": int(row["error_count"]),
                }
            )

        result = {
            "status": "success",
            "start_time": start_time,
            "end_time": end_time,
            "interval": interval,
            "threshold": threshold,
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "time_series": [
                {
                    "timestamp": row["timestamp"],
                    "count": int(row["count"]),
                    "expected": (
                        float(row["moving_avg"])
                        if not pd.isna(row["moving_avg"])
                        else None
                    ),
                    "z_score": (
                        float(row["z_score"]) if not pd.isna(row["z_score"]) else None
                    ),
                    "is_anomaly": bool(row["is_anomaly"]),
                    "error_count": int(row["error_count"]),
                }
                for _, row in df.iterrows()
            ],
        }

        # Send alerts for anomalies
        if anomalies:
            await send_anomaly_alerts(anomalies, source)

        # Cache the result
        if redis_client and cache_key:
            redis_client.setex(cache_key, settings.CACHE_TTL, json.dumps(result))

        return result
    except Exception as e:
        logger.error(f"Error detecting log anomalies: {e}")
        return {"status": "error", "message": str(e)}


# Send anomaly alerts to RabbitMQ
async def send_anomaly_alerts(
    anomalies: List[Dict[str, Any]], source: Optional[str] = None
):
    """Send anomaly alerts to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()

        # Ensure exchange exists
        channel.exchange_declare(
            exchange=settings.ALERT_EXCHANGE, exchange_type="topic", durable=True
        )

        for anomaly in anomalies:
            message = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": "log_anomaly",
                "source": source or "unknown",
                "anomaly_timestamp": anomaly["timestamp"],
                "count": anomaly["count"],
                "expected": anomaly["expected"],
                "z_score": anomaly["z_score"],
                "error_count": anomaly["error_count"],
                "message": f"Log anomaly detected in {source or 'logs'}: {anomaly['count']} logs at {anomaly['timestamp']} (expected around {anomaly['expected']:.2f})",
            }

            routing_key = f"logs.anomaly.{source or 'general'}"
            channel.basic_publish(
                exchange=settings.ALERT_EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )

            logger.warning(f"Anomaly alert sent: {message['message']}")

        connection.close()
    except Exception as e:
        logger.error(f"Failed to send anomaly alerts: {e}")
