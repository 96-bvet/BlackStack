"""
LibreSIEM API integration service for the BlackStack Cybersecurity Platform.
"""

import os
import json
import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LibreSIEMService:
    """Service class for LibreSIEM API integration."""
    
    def __init__(self):
        """Initialize LibreSIEM service with configuration."""
        self.base_url = os.getenv("LIBRESIEM_API_URL", "https://libresiem-api.example.com")
        self.api_key = os.getenv("LIBRESIEM_API_KEY")
        self.timeout = int(os.getenv("LIBRESIEM_TIMEOUT", "30"))
        
        if not self.api_key:
            logger.warning("LIBRESIEM_API_KEY not set - some operations may fail")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BlackStack-Cybersecurity-Platform/1.0"
        }
        
        logger.info(f"LibreSIEM service initialized for {self.base_url}")
    
    async def health_check(self) -> str:
        """
        Check LibreSIEM service health and connectivity.
        
        Returns:
            Health status string
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/health",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return "healthy"
                else:
                    return f"unhealthy (HTTP {response.status_code})"
                    
        except Exception as e:
            logger.error(f"LibreSIEM health check failed: {str(e)}")
            return f"unhealthy: {str(e)}"
    
    async def get_recent_events(
        self, 
        limit: int = 50, 
        severity_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve recent security events from LibreSIEM.
        
        Args:
            limit: Maximum number of events to return
            severity_filter: Optional severity filter
            
        Returns:
            List of recent security events
        """
        try:
            params = {"limit": limit}
            if severity_filter:
                params["severity"] = severity_filter
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/events",
                    headers=self.headers,
                    params=params
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Retrieved {len(data.get('events', []))} events from LibreSIEM")
                return data.get("events", [])
                
        except Exception as e:
            logger.error(f"Error fetching recent events: {str(e)}")
            raise
    
    async def get_active_threats(self) -> List[Dict[str, Any]]:
        """
        Get current active threats from LibreSIEM.
        
        Returns:
            List of active threats
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/threats/active",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Retrieved {len(data.get('threats', []))} active threats")
                return data.get("threats", [])
                
        except Exception as e:
            logger.error(f"Error fetching active threats: {str(e)}")
            raise
    
    async def enrich_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich security event data with additional context from LibreSIEM.
        
        Args:
            event_id: Event identifier
            event_data: Original event data
            
        Returns:
            Enriched event data
        """
        try:
            payload = {
                "event_id": event_id,
                "event_data": event_data
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/events/enrich",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                enriched_data = response.json()
                
                logger.info(f"Event {event_id} enriched successfully")
                return enriched_data
                
        except Exception as e:
            logger.error(f"Error enriching event {event_id}: {str(e)}")
            # Return original data if enrichment fails
            return event_data
    
    async def search_logs(
        self, 
        query: str, 
        time_range: str = "1h", 
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search LibreSIEM logs with specified criteria.
        
        Args:
            query: Search query string
            time_range: Time range for search
            max_results: Maximum number of results
            
        Returns:
            Search results
        """
        try:
            payload = {
                "query": query,
                "time_range": time_range,
                "max_results": max_results
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/logs/search",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                logger.info(f"Log search returned {len(results)} results")
                return results
                
        except Exception as e:
            logger.error(f"Error searching logs: {str(e)}")
            raise
    
    async def create_alert_rule(self, rule_data: Dict[str, Any]) -> str:
        """
        Create a new alert rule in LibreSIEM.
        
        Args:
            rule_data: Alert rule configuration
            
        Returns:
            Created rule ID
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/rules",
                    headers=self.headers,
                    json=rule_data
                )
                
                response.raise_for_status()
                data = response.json()
                
                rule_id = data.get("rule_id")
                logger.info(f"Alert rule created with ID: {rule_id}")
                return rule_id
                
        except Exception as e:
            logger.error(f"Error creating alert rule: {str(e)}")
            raise
    
    async def get_alert_rules(self) -> List[Dict[str, Any]]:
        """
        Get all configured alert rules from LibreSIEM.
        
        Returns:
            List of alert rules
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/rules",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                rules = data.get("rules", [])
                logger.info(f"Retrieved {len(rules)} alert rules")
                return rules
                
        except Exception as e:
            logger.error(f"Error fetching alert rules: {str(e)}")
            raise
    
    async def update_alert_rule(self, rule_id: str, rule_data: Dict[str, Any]) -> None:
        """
        Update an existing alert rule in LibreSIEM.
        
        Args:
            rule_id: Rule identifier
            rule_data: Updated rule configuration
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.put(
                    f"{self.base_url}/api/v1/rules/{rule_id}",
                    headers=self.headers,
                    json=rule_data
                )
                
                response.raise_for_status()
                logger.info(f"Alert rule {rule_id} updated successfully")
                
        except Exception as e:
            logger.error(f"Error updating alert rule {rule_id}: {str(e)}")
            raise
    
    async def delete_alert_rule(self, rule_id: str) -> None:
        """
        Delete an alert rule from LibreSIEM.
        
        Args:
            rule_id: Rule identifier
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(
                    f"{self.base_url}/api/v1/rules/{rule_id}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                logger.info(f"Alert rule {rule_id} deleted successfully")
                
        except Exception as e:
            logger.error(f"Error deleting alert rule {rule_id}: {str(e)}")
            raise
    
    async def log_analysis_result(self, analysis_result: Dict[str, Any]) -> None:
        """
        Log analysis result back to LibreSIEM for record keeping.
        
        Args:
            analysis_result: Analysis result to log
        """
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "analysis_result": analysis_result,
                "source": "BlackStack-AI-Platform"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/analysis/log",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                logger.info("Analysis result logged to LibreSIEM")
                
        except Exception as e:
            logger.warning(f"Failed to log analysis result: {str(e)}")
            # Don't raise exception as this is non-critical
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data and metrics from LibreSIEM.
        
        Returns:
            Dashboard data with security metrics
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/dashboard",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info("Dashboard data retrieved from LibreSIEM")
                return data
                
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {str(e)}")
            raise
    
    async def create_incident(self, incident_data: Dict[str, Any]) -> str:
        """
        Create a new security incident in LibreSIEM.
        
        Args:
            incident_data: Incident information
            
        Returns:
            Created incident ID
        """
        try:
            payload = {
                **incident_data,
                "created_by": "BlackStack-AI-Platform",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/incidents",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                incident_id = data.get("incident_id")
                logger.info(f"Security incident created with ID: {incident_id}")
                return incident_id
                
        except Exception as e:
            logger.error(f"Error creating incident: {str(e)}")
            raise
    
    async def enrich_threat_indicators(self, indicators: List[str]) -> Dict[str, Any]:
        """
        Enrich threat indicators with SIEM historical data.
        
        Args:
            indicators: List of IOCs to enrich
            
        Returns:
            Enrichment data for indicators
        """
        try:
            payload = {
                "indicators": indicators,
                "include_historical": True,
                "include_context": True
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/threat-intel/enrich",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Enriched {len(indicators)} threat indicators")
                return data
                
        except Exception as e:
            logger.error(f"Error enriching threat indicators: {str(e)}")
            return {"error": str(e), "enrichments": []}