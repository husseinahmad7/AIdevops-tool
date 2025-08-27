from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List, Dict, Any
import requests
import json
from datetime import datetime
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

@router.post("/send")
async def send_notification(notification_request: Dict[str, Any], user: dict = Depends(verify_token)):
    """Send notification via specified channels"""
    try:
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Mock notification sending
        channels = notification_request.get("channels", ["email"])
        message = notification_request.get("message", "")
        subject = notification_request.get("subject", "Notification")
        recipients = notification_request.get("recipients", [])
        priority = notification_request.get("priority", "normal")
        
        sent_channels = []
        for channel in channels:
            if channel == "email":
                # Mock email sending
                sent_channels.append({
                    "channel": "email",
                    "status": "sent",
                    "recipients": recipients,
                    "sent_at": datetime.utcnow().isoformat()
                })
            elif channel == "slack":
                # Mock Slack sending
                sent_channels.append({
                    "channel": "slack",
                    "status": "sent",
                    "channel_id": "#alerts",
                    "sent_at": datetime.utcnow().isoformat()
                })
            elif channel == "sms":
                # Mock SMS sending
                sent_channels.append({
                    "channel": "sms",
                    "status": "sent",
                    "recipients": recipients,
                    "sent_at": datetime.utcnow().isoformat()
                })
        
        result = {
            "notification_id": notification_id,
            "status": "sent",
            "channels": sent_channels,
            "message": message,
            "subject": subject,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@router.get("/templates")
async def get_notification_templates(user: dict = Depends(verify_token)):
    """Get available notification templates"""
    try:
        templates = [
            {
                "id": "alert_critical",
                "name": "Critical Alert",
                "subject": "🚨 Critical Alert: {alert_name}",
                "template": "A critical alert has been triggered:\n\nAlert: {alert_name}\nSeverity: {severity}\nTime: {timestamp}\nDescription: {description}\n\nPlease investigate immediately.",
                "channels": ["email", "slack", "sms"]
            },
            {
                "id": "deployment_success",
                "name": "Deployment Success",
                "subject": "✅ Deployment Successful: {service_name}",
                "template": "Deployment completed successfully:\n\nService: {service_name}\nVersion: {version}\nEnvironment: {environment}\nTime: {timestamp}\n\nAll systems operational.",
                "channels": ["email", "slack"]
            },
            {
                "id": "system_maintenance",
                "name": "System Maintenance",
                "subject": "🔧 Scheduled Maintenance: {maintenance_window}",
                "template": "Scheduled maintenance notification:\n\nMaintenance Window: {maintenance_window}\nAffected Services: {services}\nExpected Duration: {duration}\nImpact: {impact}\n\nPlease plan accordingly.",
                "channels": ["email", "slack"]
            }
        ]
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")

@router.post("/templates/{template_id}/send")
async def send_templated_notification(template_id: str, template_data: Dict[str, Any], user: dict = Depends(verify_token)):
    """Send notification using a template"""
    try:
        # Mock template processing
        notification_id = f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        result = {
            "notification_id": notification_id,
            "template_id": template_id,
            "status": "sent",
            "recipients": template_data.get("recipients", []),
            "channels": template_data.get("channels", ["email"]),
            "sent_at": datetime.utcnow().isoformat()
        }
        
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send templated notification: {str(e)}")

@router.get("/history")
async def get_notification_history(limit: int = 50, offset: int = 0, user: dict = Depends(verify_token)):
    """Get notification history"""
    try:
        # Mock notification history
        history = [
            {
                "notification_id": "notif_20240115_143022",
                "subject": "Critical Alert: High CPU Usage",
                "channels": ["email", "slack"],
                "status": "delivered",
                "recipients": ["admin@example.com"],
                "sent_at": "2024-01-15T14:30:22Z",
                "delivered_at": "2024-01-15T14:30:25Z"
            },
            {
                "notification_id": "notif_20240115_142015",
                "subject": "Deployment Successful: api-gateway",
                "channels": ["slack"],
                "status": "delivered",
                "recipients": ["#deployments"],
                "sent_at": "2024-01-15T14:20:15Z",
                "delivered_at": "2024-01-15T14:20:18Z"
            }
        ]
        
        # Apply pagination
        paginated_history = history[offset:offset + limit]
        
        return {
            "status": "success",
            "data": {
                "notifications": paginated_history,
                "total": len(history),
                "limit": limit,
                "offset": offset
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification history: {str(e)}")

@router.post("/channels/test")
async def test_notification_channel(channel_config: Dict[str, Any], user: dict = Depends(verify_token)):
    """Test notification channel configuration"""
    try:
        channel_type = channel_config.get("type")
        
        # Mock channel testing
        test_result = {
            "channel_type": channel_type,
            "status": "success",
            "message": f"{channel_type.title()} channel is configured correctly",
            "test_sent_at": datetime.utcnow().isoformat(),
            "response_time_ms": 150
        }
        
        return {"status": "success", "data": test_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test channel: {str(e)}")

@router.get("/stats")
async def get_notification_stats(user: dict = Depends(verify_token)):
    """Get notification statistics"""
    try:
        stats = {
            "total_sent": 1247,
            "total_delivered": 1198,
            "total_failed": 49,
            "delivery_rate": 96.1,
            "channels": {
                "email": {
                    "sent": 856,
                    "delivered": 832,
                    "failed": 24,
                    "delivery_rate": 97.2
                },
                "slack": {
                    "sent": 312,
                    "delivered": 298,
                    "failed": 14,
                    "delivery_rate": 95.5
                },
                "sms": {
                    "sent": 79,
                    "delivered": 68,
                    "failed": 11,
                    "delivery_rate": 86.1
                }
            },
            "recent_activity": {
                "last_24h": 45,
                "last_7d": 312,
                "last_30d": 1247
            }
        }
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification stats: {str(e)}")