from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
import requests
import json
from datetime import datetime, timedelta
from .config import settings

router = APIRouter()

async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token with user management service (GET /users/validate)"""
    if not settings.auth_enabled:
        return {"user_id": "test_user", "role": "admin"}

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

@router.get("/templates")
async def get_report_templates(user: dict = Depends(verify_token)):
    """Get available report templates"""
    try:
        templates = [
            {
                "id": "system_health",
                "name": "System Health Report",
                "description": "Comprehensive system health and performance metrics",
                "category": "infrastructure",
                "parameters": ["time_range", "services"],
                "formats": ["pdf", "html", "json"]
            },
            {
                "id": "cost_analysis",
                "name": "Cost Analysis Report",
                "description": "Resource usage and cost optimization analysis",
                "category": "financial",
                "parameters": ["time_range", "cost_centers"],
                "formats": ["pdf", "excel", "json"]
            },
            {
                "id": "security_audit",
                "name": "Security Audit Report",
                "description": "Security vulnerabilities and compliance status",
                "category": "security",
                "parameters": ["time_range", "severity_levels"],
                "formats": ["pdf", "html"]
            },
            {
                "id": "performance_trends",
                "name": "Performance Trends Report",
                "description": "Application and infrastructure performance trends",
                "category": "performance",
                "parameters": ["time_range", "metrics"],
                "formats": ["pdf", "html", "json"]
            },
            {
                "id": "deployment_summary",
                "name": "Deployment Summary Report",
                "description": "CI/CD pipeline and deployment statistics",
                "category": "deployment",
                "parameters": ["time_range", "environments"],
                "formats": ["pdf", "html", "json"]
            }
        ]
        return {"status": "success", "data": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report templates: {str(e)}")

@router.post("/generate")
async def generate_report(report_request: Dict[str, Any], user: dict = Depends(verify_token)):
    """Generate a report based on template and parameters"""
    try:
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        template_id = report_request.get("template_id")
        parameters = report_request.get("parameters", {})
        format_type = report_request.get("format", "pdf")
        
        # Mock report generation
        report_data = {
            "report_id": report_id,
            "template_id": template_id,
            "title": f"Generated Report - {template_id}",
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": user.get("user_id", "unknown"),
            "parameters": parameters,
            "format": format_type,
            "status": "completed",
            "file_path": f"/reports/{report_id}.{format_type}",
            "file_size": "2.5MB",
            "sections": [
                {
                    "name": "Executive Summary",
                    "status": "completed"
                },
                {
                    "name": "Detailed Analysis",
                    "status": "completed"
                },
                {
                    "name": "Recommendations",
                    "status": "completed"
                },
                {
                    "name": "Appendix",
                    "status": "completed"
                }
            ]
        }
        
        return {"status": "success", "data": report_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/history")
async def get_report_history(limit: int = 20, offset: int = 0, user: dict = Depends(verify_token)):
    """Get report generation history"""
    try:
        # Mock report history
        reports = [
            {
                "report_id": "report_20240115_143022",
                "template_id": "system_health",
                "title": "System Health Report - January 2024",
                "generated_at": "2024-01-15T14:30:22Z",
                "generated_by": "admin",
                "format": "pdf",
                "status": "completed",
                "file_size": "3.2MB"
            },
            {
                "report_id": "report_20240114_091545",
                "template_id": "cost_analysis",
                "title": "Cost Analysis Report - Q4 2023",
                "generated_at": "2024-01-14T09:15:45Z",
                "generated_by": "finance_user",
                "format": "excel",
                "status": "completed",
                "file_size": "1.8MB"
            },
            {
                "report_id": "report_20240113_165030",
                "template_id": "security_audit",
                "title": "Security Audit Report - December 2023",
                "generated_at": "2024-01-13T16:50:30Z",
                "generated_by": "security_admin",
                "format": "pdf",
                "status": "completed",
                "file_size": "4.1MB"
            }
        ]
        
        # Apply pagination
        paginated_reports = reports[offset:offset + limit]
        
        return {
            "status": "success",
            "data": {
                "reports": paginated_reports,
                "total": len(reports),
                "limit": limit,
                "offset": offset
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report history: {str(e)}")

@router.get("/{report_id}")
async def get_report_details(report_id: str, user: dict = Depends(verify_token)):
    """Get detailed information about a specific report"""
    try:
        # Mock report details
        report_details = {
            "report_id": report_id,
            "template_id": "system_health",
            "title": "System Health Report - January 2024",
            "description": "Comprehensive analysis of system performance and health metrics",
            "generated_at": "2024-01-15T14:30:22Z",
            "generated_by": "admin",
            "format": "pdf",
            "status": "completed",
            "file_size": "3.2MB",
            "parameters": {
                "time_range": "2024-01-01 to 2024-01-15",
                "services": ["api-gateway", "user-management", "infrastructure-monitor"]
            },
            "sections": [
                {
                    "name": "Executive Summary",
                    "page_count": 2,
                    "status": "completed"
                },
                {
                    "name": "System Metrics",
                    "page_count": 8,
                    "status": "completed"
                },
                {
                    "name": "Performance Analysis",
                    "page_count": 12,
                    "status": "completed"
                },
                {
                    "name": "Recommendations",
                    "page_count": 3,
                    "status": "completed"
                }
            ],
            "download_url": f"/api/v1/reports/{report_id}/download",
            "expires_at": "2024-02-15T14:30:22Z"
        }
        
        return {"status": "success", "data": report_details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report details: {str(e)}")

@router.get("/{report_id}/download")
async def download_report(report_id: str, user: dict = Depends(verify_token)):
    """Download a generated report file"""
    try:
        # Mock file download - in real implementation, this would return the actual file
        # For now, we'll return a mock response indicating the download would start
        return {
            "status": "success",
            "message": f"Report {report_id} download would start here",
            "download_url": f"/reports/{report_id}.pdf",
            "content_type": "application/pdf"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download report: {str(e)}")

@router.post("/schedule")
async def schedule_report(schedule_request: Dict[str, Any], user: dict = Depends(verify_token)):
    """Schedule automatic report generation"""
    try:
        schedule_id = f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        schedule_data = {
            "schedule_id": schedule_id,
            "template_id": schedule_request.get("template_id"),
            "name": schedule_request.get("name", "Scheduled Report"),
            "frequency": schedule_request.get("frequency", "weekly"),
            "parameters": schedule_request.get("parameters", {}),
            "format": schedule_request.get("format", "pdf"),
            "recipients": schedule_request.get("recipients", []),
            "next_run": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user.get("user_id", "unknown")
        }
        
        return {"status": "success", "data": schedule_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule report: {str(e)}")

@router.get("/schedules/list")
async def get_scheduled_reports(user: dict = Depends(verify_token)):
    """Get list of scheduled reports"""
    try:
        schedules = [
            {
                "schedule_id": "schedule_20240115_100000",
                "name": "Weekly System Health Report",
                "template_id": "system_health",
                "frequency": "weekly",
                "next_run": "2024-01-22T10:00:00Z",
                "status": "active",
                "recipients": ["admin@example.com", "ops@example.com"]
            },
            {
                "schedule_id": "schedule_20240110_150000",
                "name": "Monthly Cost Analysis",
                "template_id": "cost_analysis",
                "frequency": "monthly",
                "next_run": "2024-02-01T15:00:00Z",
                "status": "active",
                "recipients": ["finance@example.com"]
            }
        ]
        
        return {"status": "success", "data": schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduled reports: {str(e)}")

@router.get("/analytics/usage")
async def get_reporting_analytics(user: dict = Depends(verify_token)):
    """Get reporting usage analytics"""
    try:
        analytics = {
            "total_reports_generated": 1247,
            "reports_this_month": 89,
            "most_popular_templates": [
                {"template_id": "system_health", "count": 456, "percentage": 36.6},
                {"template_id": "cost_analysis", "count": 312, "percentage": 25.0},
                {"template_id": "performance_trends", "count": 234, "percentage": 18.8},
                {"template_id": "security_audit", "count": 156, "percentage": 12.5},
                {"template_id": "deployment_summary", "count": 89, "percentage": 7.1}
            ],
            "format_distribution": {
                "pdf": 67.3,
                "html": 18.2,
                "excel": 9.8,
                "json": 4.7
            },
            "generation_trends": {
                "daily_average": 12.3,
                "peak_hours": [9, 10, 14, 15],
                "busiest_day": "Monday"
            },
            "scheduled_reports": {
                "total_active": 23,
                "total_executions": 456,
                "success_rate": 98.7
            }
        }
        
        return {"status": "success", "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reporting analytics: {str(e)}")