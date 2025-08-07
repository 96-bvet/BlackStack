"""
SIEM-related API routes for the BlackStack Cybersecurity Platform.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.core.orchestrator import SecurityOrchestrator, ThreatAnalysisRequest

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response validation
class EventData(BaseModel):
    """Model for security event data."""
    timestamp: str
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    event_type: str
    severity: str = Field(..., regex="^(low|medium|high|critical)$")
    description: str
    raw_data: Dict[str, Any] = {}

class ThreatAnalysisRequestModel(BaseModel):
    """Model for threat analysis requests."""
    event_id: str
    event_data: EventData
    analysis_type: str = Field(default="comprehensive", regex="^(basic|comprehensive|deep)$")
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")

class AlertRule(BaseModel):
    """Model for SIEM alert rules."""
    rule_id: str
    name: str
    description: str
    severity: str
    conditions: Dict[str, Any]
    actions: List[str]
    enabled: bool = True

class LogQuery(BaseModel):
    """Model for log search queries."""
    query: str
    time_range: str = "1h"
    max_results: int = Field(default=100, le=10000)
    fields: Optional[List[str]] = None

@router.get("/events", response_model=List[Dict[str, Any]])
async def get_recent_events(
    limit: int = Query(default=50, le=1000),
    severity: Optional[str] = Query(default=None, regex="^(low|medium|high|critical)$"),
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Retrieve recent security events from SIEM.
    
    Args:
        limit: Maximum number of events to return
        severity: Filter by event severity
        orchestrator: Security orchestrator dependency
        
    Returns:
        List of recent security events
    """
    try:
        logger.info(f"Fetching recent events (limit: {limit}, severity: {severity})")
        
        events = await orchestrator.siem_service.get_recent_events(
            limit=limit,
            severity_filter=severity
        )
        
        return events
        
    except Exception as e:
        logger.error(f"Error fetching recent events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch events: {str(e)}")

@router.get("/threats", response_model=List[Dict[str, Any]])
async def get_active_threats(
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Get current active threats from SIEM.
    
    Args:
        orchestrator: Security orchestrator dependency
        
    Returns:
        List of active threats
    """
    try:
        logger.info("Fetching active threats")
        
        threats = await orchestrator.get_real_time_threats()
        
        return threats
        
    except Exception as e:
        logger.error(f"Error fetching active threats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch threats: {str(e)}")

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_threat(
    request: ThreatAnalysisRequestModel,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Perform comprehensive threat analysis on a security event.
    
    Args:
        request: Threat analysis request
        orchestrator: Security orchestrator dependency
        
    Returns:
        Threat analysis results
    """
    try:
        logger.info(f"Starting threat analysis for event {request.event_id}")
        
        # Convert Pydantic model to dataclass
        analysis_request = ThreatAnalysisRequest(
            event_id=request.event_id,
            event_data=request.event_data.dict(),
            analysis_type=request.analysis_type,
            priority=request.priority
        )
        
        result = await orchestrator.analyze_threat(analysis_request)
        
        return result.__dict__
        
    except Exception as e:
        logger.error(f"Error in threat analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/logs/search", response_model=Dict[str, Any])
async def search_logs(
    query: str = Query(..., description="Search query"),
    time_range: str = Query(default="1h", description="Time range for search"),
    max_results: int = Query(default=100, le=10000, description="Maximum results"),
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Search SIEM logs with specified criteria.
    
    Args:
        query: Search query string
        time_range: Time range for search (e.g., '1h', '24h', '7d')
        max_results: Maximum number of results
        orchestrator: Security orchestrator dependency
        
    Returns:
        Search results with matching logs
    """
    try:
        logger.info(f"Searching logs with query: {query}")
        
        results = await orchestrator.siem_service.search_logs(
            query=query,
            time_range=time_range,
            max_results=max_results
        )
        
        return {
            "query": query,
            "time_range": time_range,
            "total_results": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error searching logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Log search failed: {str(e)}")

@router.post("/rules", response_model=Dict[str, str])
async def create_alert_rule(
    rule: AlertRule,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Create a new SIEM alert rule.
    
    Args:
        rule: Alert rule configuration
        orchestrator: Security orchestrator dependency
        
    Returns:
        Creation status and rule ID
    """
    try:
        logger.info(f"Creating alert rule: {rule.name}")
        
        rule_id = await orchestrator.siem_service.create_alert_rule(rule.dict())
        
        return {
            "status": "created",
            "rule_id": rule_id,
            "message": f"Alert rule '{rule.name}' created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule creation failed: {str(e)}")

@router.get("/rules", response_model=List[Dict[str, Any]])
async def get_alert_rules(
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Get all configured SIEM alert rules.
    
    Args:
        orchestrator: Security orchestrator dependency
        
    Returns:
        List of configured alert rules
    """
    try:
        logger.info("Fetching alert rules")
        
        rules = await orchestrator.siem_service.get_alert_rules()
        
        return rules
        
    except Exception as e:
        logger.error(f"Error fetching alert rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch rules: {str(e)}")

@router.put("/rules/{rule_id}", response_model=Dict[str, str])
async def update_alert_rule(
    rule_id: str,
    rule: AlertRule,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Update an existing SIEM alert rule.
    
    Args:
        rule_id: ID of the rule to update
        rule: Updated rule configuration
        orchestrator: Security orchestrator dependency
        
    Returns:
        Update status
    """
    try:
        logger.info(f"Updating alert rule: {rule_id}")
        
        await orchestrator.siem_service.update_alert_rule(rule_id, rule.dict())
        
        return {
            "status": "updated",
            "rule_id": rule_id,
            "message": f"Alert rule updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule update failed: {str(e)}")

@router.delete("/rules/{rule_id}", response_model=Dict[str, str])
async def delete_alert_rule(
    rule_id: str,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Delete a SIEM alert rule.
    
    Args:
        rule_id: ID of the rule to delete
        orchestrator: Security orchestrator dependency
        
    Returns:
        Deletion status
    """
    try:
        logger.info(f"Deleting alert rule: {rule_id}")
        
        await orchestrator.siem_service.delete_alert_rule(rule_id)
        
        return {
            "status": "deleted",
            "rule_id": rule_id,
            "message": f"Alert rule deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting alert rule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rule deletion failed: {str(e)}")

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_data(
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Get SIEM dashboard data including metrics and summaries.
    
    Args:
        orchestrator: Security orchestrator dependency
        
    Returns:
        Dashboard data with security metrics
    """
    try:
        logger.info("Fetching dashboard data")
        
        dashboard_data = await orchestrator.siem_service.get_dashboard_data()
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dashboard data fetch failed: {str(e)}")

@router.post("/incident", response_model=Dict[str, str])
async def create_incident(
    incident_data: Dict[str, Any] = Body(...),
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Create a new security incident in SIEM.
    
    Args:
        incident_data: Incident information
        orchestrator: Security orchestrator dependency
        
    Returns:
        Incident creation status and ID
    """
    try:
        logger.info("Creating new security incident")
        
        incident_id = await orchestrator.siem_service.create_incident(incident_data)
        
        return {
            "status": "created",
            "incident_id": incident_id,
            "message": "Security incident created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating incident: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Incident creation failed: {str(e)}")

@router.get("/health", response_model=Dict[str, str])
async def siem_health_check(
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Check SIEM service health and connectivity.
    
    Args:
        orchestrator: Security orchestrator dependency
        
    Returns:
        SIEM health status
    """
    try:
        health_status = await orchestrator.siem_service.health_check()
        
        return {
            "service": "LibreSIEM",
            "status": health_status,
            "timestamp": orchestrator.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"SIEM health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"SIEM service unavailable: {str(e)}")