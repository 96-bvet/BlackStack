"""
Security Orchestrator module for coordinating SIEM and AI operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.services.libresiem import LibreSIEMService
from app.services.llama import LlamaService
from app.services.mistral import MistralService
from app.core.attribution import AttributionAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThreatAnalysisRequest:
    """Request model for threat analysis."""
    event_id: str
    event_data: Dict[str, Any]
    analysis_type: str = "comprehensive"
    priority: str = "medium"

@dataclass
class ThreatAnalysisResponse:
    """Response model for threat analysis."""
    event_id: str
    threat_score: float
    threat_classification: str
    attribution_analysis: Dict[str, Any]
    recommendations: List[str]
    timestamp: str
    ai_models_used: List[str]

class SecurityOrchestrator:
    """Main orchestrator for cybersecurity operations."""
    
    def __init__(self):
        """Initialize the security orchestrator."""
        self.siem_service = LibreSIEMService()
        self.llama_service = LlamaService()
        self.mistral_service = MistralService()
        self.attribution_analyzer = AttributionAnalyzer()
        
        logger.info("Security Orchestrator initialized")
    
    async def analyze_threat(self, request: ThreatAnalysisRequest) -> ThreatAnalysisResponse:
        """
        Perform comprehensive threat analysis using SIEM data and AI models.
        
        Args:
            request: Threat analysis request
            
        Returns:
            Comprehensive threat analysis response
        """
        logger.info(f"Starting threat analysis for event {request.event_id}")
        
        try:
            # Enrich event data from SIEM
            enriched_data = await self.siem_service.enrich_event(
                request.event_id, 
                request.event_data
            )
            
            # Prepare AI analysis tasks
            tasks = []
            
            # Llama analysis for general threat detection
            tasks.append(self._analyze_with_llama(enriched_data))
            
            # Mistral analysis for specialized threat patterns
            tasks.append(self._analyze_with_mistral(enriched_data))
            
            # Attribution analysis
            tasks.append(self.attribution_analyzer.analyze_attribution(enriched_data))
            
            # Execute AI analyses concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            llama_result = results[0] if not isinstance(results[0], Exception) else {}
            mistral_result = results[1] if not isinstance(results[1], Exception) else {}
            attribution_result = results[2] if not isinstance(results[2], Exception) else {}
            
            # Combine and correlate results
            final_analysis = self._correlate_analyses(
                llama_result, 
                mistral_result, 
                attribution_result,
                enriched_data
            )
            
            response = ThreatAnalysisResponse(
                event_id=request.event_id,
                threat_score=final_analysis["threat_score"],
                threat_classification=final_analysis["classification"],
                attribution_analysis=attribution_result,
                recommendations=final_analysis["recommendations"],
                timestamp=self.get_current_timestamp(),
                ai_models_used=["llama", "mistral"]
            )
            
            # Log to SIEM
            await self.siem_service.log_analysis_result(response.__dict__)
            
            logger.info(f"Threat analysis completed for event {request.event_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error in threat analysis for event {request.event_id}: {str(e)}")
            raise
    
    async def _analyze_with_llama(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze event with Llama model."""
        prompt = self._build_threat_analysis_prompt(event_data, "general")
        return await self.llama_service.analyze_security_event(prompt, event_data)
    
    async def _analyze_with_mistral(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze event with Mistral model."""
        prompt = self._build_threat_analysis_prompt(event_data, "specialized")
        return await self.mistral_service.analyze_security_event(prompt, event_data)
    
    def _build_threat_analysis_prompt(self, event_data: Dict[str, Any], analysis_type: str) -> str:
        """Build appropriate prompt for AI analysis."""
        base_prompt = f"""
        Analyze the following cybersecurity event for potential threats:
        
        Event Data: {json.dumps(event_data, indent=2)}
        
        Analysis Type: {analysis_type}
        
        Please provide:
        1. Threat severity score (0-10)
        2. Threat classification
        3. Potential attack vectors
        4. Recommended actions
        5. Confidence level
        """
        
        if analysis_type == "specialized":
            base_prompt += """
            
            Focus on:
            - Advanced persistent threats (APT)
            - Zero-day vulnerabilities
            - Nation-state indicators
            - Supply chain attacks
            """
        
        return base_prompt
    
    def _correlate_analyses(
        self, 
        llama_result: Dict[str, Any], 
        mistral_result: Dict[str, Any],
        attribution_result: Dict[str, Any],
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Correlate results from multiple AI analyses."""
        
        # Extract threat scores
        llama_score = llama_result.get("threat_score", 0)
        mistral_score = mistral_result.get("threat_score", 0)
        
        # Calculate weighted average (Mistral weighted higher for specialized threats)
        final_score = (llama_score * 0.4 + mistral_score * 0.6)
        
        # Determine classification
        if final_score >= 8:
            classification = "critical"
        elif final_score >= 6:
            classification = "high"
        elif final_score >= 4:
            classification = "medium"
        else:
            classification = "low"
        
        # Combine recommendations
        recommendations = []
        recommendations.extend(llama_result.get("recommendations", []))
        recommendations.extend(mistral_result.get("recommendations", []))
        
        # Remove duplicates while preserving order
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        return {
            "threat_score": round(final_score, 2),
            "classification": classification,
            "recommendations": unique_recommendations[:10],  # Limit to top 10
            "analysis_details": {
                "llama_analysis": llama_result,
                "mistral_analysis": mistral_result,
                "attribution_analysis": attribution_result
            }
        }
    
    async def get_real_time_threats(self) -> List[Dict[str, Any]]:
        """Get real-time threats from SIEM."""
        return await self.siem_service.get_active_threats()
    
    async def check_service_health(self) -> Dict[str, str]:
        """Check health of all integrated services."""
        health_status = {}
        
        try:
            # Check SIEM health
            health_status["libresiem"] = await self.siem_service.health_check()
        except Exception as e:
            health_status["libresiem"] = f"unhealthy: {str(e)}"
        
        try:
            # Check Llama service health
            health_status["llama"] = await self.llama_service.health_check()
        except Exception as e:
            health_status["llama"] = f"unhealthy: {str(e)}"
        
        try:
            # Check Mistral service health
            health_status["mistral"] = await self.mistral_service.health_check()
        except Exception as e:
            health_status["mistral"] = f"unhealthy: {str(e)}"
        
        return health_status
    
    @staticmethod
    def get_current_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat() + "Z"