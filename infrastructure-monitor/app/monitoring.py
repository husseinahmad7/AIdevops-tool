import psutil
import docker
import platform
import socket
import time

# flake8: noqa: F401

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import pika
import redis
from kubernetes import client, config

from .config import settings

logger = logging.getLogger(__name__)

# Redis client for caching
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL)
    redis_client.ping()  # Test connection
except redis.ConnectionError:
    logger.warning("Redis connection failed, caching disabled")
    redis_client = None

# Docker client
docker_client = None
if settings.DOCKER_ENABLED:
    try:
        docker_client = docker.DockerClient(base_url=settings.DOCKER_HOST)
    except Exception as e:
        logger.warning(f"Docker connection failed: {e}")

# Kubernetes client
k8s_client = None
if settings.K8S_ENABLED:
    try:
        if settings.K8S_CONFIG_PATH:
            config.load_kube_config(
                config_file=settings.K8S_CONFIG_PATH,
                context=settings.K8S_CONTEXT or None,
            )
        else:
            # Try in-cluster config for when running inside Kubernetes
            config.load_incluster_config()
        k8s_client = client.CoreV1Api()
    except Exception as e:
        logger.warning(f"Kubernetes connection failed: {e}")


# System metrics collection
async def get_system_metrics() -> Dict[str, Any]:
    """Collect system metrics including CPU, memory, disk, and network"""
    # Check cache first
    if redis_client:
        cached = redis_client.get("system_metrics")
        if cached:
            return json.loads(cached)

    # Collect metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    network = psutil.net_io_counters()

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(),
            "alert": cpu_percent > settings.CPU_THRESHOLD,
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "alert": memory.percent > settings.MEMORY_THRESHOLD,
        },
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "alert": disk.percent > settings.DISK_THRESHOLD,
        },
        "network": {
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
            "errin": network.errin,
            "errout": network.errout,
        },
    }

    # Cache the result
    if redis_client:
        redis_client.setex("system_metrics", settings.CACHE_TTL, json.dumps(metrics))

    # Send alerts if thresholds exceeded
    alerts = []
    if metrics["cpu"]["alert"]:
        alerts.append(
            {"type": "cpu", "value": cpu_percent, "threshold": settings.CPU_THRESHOLD}
        )
    if metrics["memory"]["alert"]:
        alerts.append(
            {
                "type": "memory",
                "value": memory.percent,
                "threshold": settings.MEMORY_THRESHOLD,
            }
        )
    if metrics["disk"]["alert"]:
        alerts.append(
            {
                "type": "disk",
                "value": disk.percent,
                "threshold": settings.DISK_THRESHOLD,
            }
        )

    if alerts:
        await send_alerts(alerts)

    return metrics


# Docker container metrics
async def get_docker_metrics() -> List[Dict[str, Any]]:
    """Collect metrics from Docker containers"""
    if not docker_client:
        return []

    # Check cache first
    if redis_client:
        cached = redis_client.get("docker_metrics")
        if cached:
            return json.loads(cached)

    try:
        containers = docker_client.containers.list()
        metrics = []

        for container in containers:
            stats = container.stats(stream=False)

            # Calculate CPU usage percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )

            # Guard against missing percpu_usage
            percpu = stats["cpu_stats"]["cpu_usage"].get("percpu_usage") or []
            n_cpus = max(len(percpu), 1)

            # Calculate CPU percentage
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * n_cpus * 100.0
            else:
                cpu_percent = 0.0

            # Calculate memory usage
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 1) or 1
            memory_percent = (memory_usage / memory_limit) * 100.0

            container_metrics = {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": (
                    container.image.tags[0]
                    if container.image.tags
                    else container.image.id
                ),
                "cpu_percent": cpu_percent,
                "memory_usage": memory_usage,
                "memory_limit": memory_limit,
                "memory_percent": memory_percent,
                "alert": cpu_percent > settings.CPU_THRESHOLD
                or memory_percent > settings.MEMORY_THRESHOLD,
            }

            metrics.append(container_metrics)

        # Cache the result
        if redis_client:
            redis_client.setex(
                "docker_metrics", settings.CACHE_TTL, json.dumps(metrics)
            )

        return metrics
    except Exception as e:
        logger.error(f"Error collecting Docker metrics: {e}")
        return []


# Kubernetes metrics
async def get_kubernetes_metrics() -> Dict[str, Any]:
    """Collect metrics from Kubernetes cluster"""
    if not k8s_client:
        return {}

    # Check cache first
    if redis_client:
        cached = redis_client.get("k8s_metrics")
        if cached:
            return json.loads(cached)

    try:
        # Get nodes
        nodes = k8s_client.list_node().items
        node_metrics = []

        for node in nodes:
            conditions = {cond.type: cond.status for cond in node.status.conditions}
            node_info = {
                "name": node.metadata.name,
                "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
                "kubelet_version": node.status.node_info.kubelet_version,
                "os_image": node.status.node_info.os_image,
                "allocatable_cpu": node.status.allocatable.get("cpu"),
                "allocatable_memory": node.status.allocatable.get("memory"),
                "allocatable_pods": node.status.allocatable.get("pods"),
            }
            node_metrics.append(node_info)

        # Get pods
        pods = k8s_client.list_pod_for_all_namespaces().items
        pod_metrics = []

        for pod in pods:
            containers = []
            for container in pod.spec.containers:
                container_info = {
                    "name": container.name,
                    "image": container.image,
                    "resources": {
                        "requests": {
                            "cpu": (
                                container.resources.requests.get("cpu")
                                if container.resources.requests
                                else None
                            ),
                            "memory": (
                                container.resources.requests.get("memory")
                                if container.resources.requests
                                else None
                            ),
                        },
                        "limits": {
                            "cpu": (
                                container.resources.limits.get("cpu")
                                if container.resources.limits
                                else None
                            ),
                            "memory": (
                                container.resources.limits.get("memory")
                                if container.resources.limits
                                else None
                            ),
                        },
                    },
                }
                containers.append(container_info)

            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "host_ip": pod.status.host_ip,
                "pod_ip": pod.status.pod_ip,
                "start_time": (
                    pod.status.start_time.isoformat() if pod.status.start_time else None
                ),
                "containers": containers,
            }
            pod_metrics.append(pod_info)

        # Get services
        services = k8s_client.list_service_for_all_namespaces().items
        service_metrics = []

        for service in services:
            ports = []
            for port in service.spec.ports:
                port_info = {
                    "name": port.name,
                    "port": port.port,
                    "target_port": port.target_port,
                    "protocol": port.protocol,
                }
                ports.append(port_info)

            service_info = {
                "name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "cluster_ip": service.spec.cluster_ip,
                "type": service.spec.type,
                "ports": ports,
            }
            service_metrics.append(service_info)

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "nodes": node_metrics,
            "pods": pod_metrics,
            "services": service_metrics,
        }

        # Cache the result
        if redis_client:
            redis_client.setex("k8s_metrics", settings.CACHE_TTL, json.dumps(metrics))

        return metrics
    except Exception as e:
        logger.error(f"Error collecting Kubernetes metrics: {e}")
        return {}


# Send alerts to RabbitMQ
async def send_alerts(alerts: List[Dict[str, Any]]):
    """Send alerts to RabbitMQ"""
    try:
        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()

        # Ensure exchange exists
        channel.exchange_declare(
            exchange=settings.ALERT_EXCHANGE, exchange_type="topic", durable=True
        )

        for alert in alerts:
            message = {
                "timestamp": datetime.now().isoformat(),
                "hostname": socket.gethostname(),
                "alert_type": alert["type"],
                "value": alert["value"],
                "threshold": alert["threshold"],
                "message": f"{alert['type'].upper()} usage is {alert['value']:.2f}%, exceeding threshold of {alert['threshold']}%",
            }

            routing_key = f"infrastructure.alert.{alert['type']}"
            channel.basic_publish(
                exchange=settings.ALERT_EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type="application/json",
                ),
            )

            logger.warning(f"Alert sent: {message['message']}")

        connection.close()
    except Exception as e:
        logger.error(f"Failed to send alerts: {e}")


# Background monitoring task
async def monitoring_task():
    """Background task to collect metrics at regular intervals"""
    while True:
        try:
            await get_system_metrics()

            if settings.DOCKER_ENABLED:
                await get_docker_metrics()

            if settings.K8S_ENABLED:
                await get_kubernetes_metrics()

        except Exception as e:
            logger.error(f"Error in monitoring task: {e}")

        await asyncio.sleep(settings.MONITORING_INTERVAL)
