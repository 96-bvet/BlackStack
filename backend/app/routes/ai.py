"""
AI-related API routes for the BlackStack Cybersecurity Platform.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.core.orchestrator import SecurityOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response validation
class AIAnalysisRequest(BaseModel):
    """Model for AI analysis requests."""
    model_config = {"protected_namespaces": ()}
    
    text: str = Field(..., min_length=1, max_length=50000)
    analysis_type: str = Field(default="security", pattern="^(security|attribution|malware|phishing)$")
    model_preference: Optional[str] = Field(default=None, pattern="^(llama|mistral|both)$")
    context: Optional[Dict[str, Any]] = {}

class ThreatIntelRequest(BaseModel):
    """Model for threat intelligence requests."""
    indicators: List[str] = Field(..., min_items=1, max_items=100)
    ioc_types: List[str] = Field(default=["ip", "domain", "hash", "url"])
    enrich_data: bool = True

class MalwareAnalysisRequest(BaseModel):
    """Model for malware analysis requests."""
    file_hash: Optional[str] = None
    file_name: Optional[str] = None
    behavioral_data: Optional[Dict[str, Any]] = {}
    static_analysis: Optional[Dict[str, Any]] = {}

class PhishingAnalysisRequest(BaseModel):
    """Model for phishing analysis requests."""
    email_content: Optional[str] = None
    url: Optional[str] = None
    sender_info: Optional[Dict[str, Any]] = {}
    attachments: Optional[List[str]] = []

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_with_ai(
    request: AIAnalysisRequest,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Perform AI-powered security analysis on provided text/data.
    
    Args:
        request: AI analysis request with text and parameters
        orchestrator: Security orchestrator dependency
        
    Returns:
        AI analysis results from specified or all models
    """
    try:
        logger.info(f"Starting AI analysis (type: {request.analysis_type})")
        
        results = {}
        
        # Determine which models to use
        use_llama = request.model_preference in [None, "llama", "both"]
        use_mistral = request.model_preference in [None, "mistral", "both"]
        
        # Prepare analysis context
        analysis_context = {
            "text": request.text,
            "analysis_type": request.analysis_type,
            "context": request.context
        }
        
        # Llama analysis
        if use_llama:
            try:
                llama_result = await orchestrator.llama_service.analyze_security_event(
                    request.text, analysis_context
                )
                results["llama_analysis"] = llama_result
            except Exception as e:
                logger.warning(f"Llama analysis failed: {str(e)}")
                results["llama_analysis"] = {"error": str(e)}
        
        # Mistral analysis
        if use_mistral:
            try:
                mistral_result = await orchestrator.mistral_service.analyze_security_event(
                    request.text, analysis_context
                )
                results["mistral_analysis"] = mistral_result
            except Exception as e:
                logger.warning(f"Mistral analysis failed: {str(e)}")
                results["mistral_analysis"] = {"error": str(e)}
        
        # Combine results if both models were used
        if use_llama and use_mistral:
            results["combined_analysis"] = _combine_ai_results(
                results.get("llama_analysis", {}),
                results.get("mistral_analysis", {})
            )
        
        results["timestamp"] = orchestrator.get_current_timestamp()
        results["analysis_type"] = request.analysis_type
        
        return results
        
    except Exception as e:
        logger.error(f"Error in AI analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@router.post("/threat-intel", response_model=Dict[str, Any])
async def analyze_threat_intelligence(
    request: ThreatIntelRequest,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Analyze threat intelligence indicators using AI models.
    
    Args:
        request: Threat intelligence request with IOCs
        orchestrator: Security orchestrator dependency
        
    Returns:
        Threat intelligence analysis results
    """
    try:
        logger.info(f"Analyzing {len(request.indicators)} threat indicators")
        
        # Prepare threat intel context
        threat_context = {
            "indicators": request.indicators,
            "ioc_types": request.ioc_types,
            "enrich_data": request.enrich_data
        }
        
        # Analyze with both models for comprehensive threat intel
        llama_intel = await orchestrator.llama_service.analyze_threat_intelligence(
            request.indicators, threat_context
        )
        
        mistral_intel = await orchestrator.mistral_service.analyze_threat_intelligence(
            request.indicators, threat_context
        )
        
        # Combine threat intelligence results
        combined_results = _combine_threat_intel_results(llama_intel, mistral_intel)
        
        # Enrich with SIEM data if requested
        if request.enrich_data:
            siem_enrichment = await orchestrator.siem_service.enrich_threat_indicators(
                request.indicators
            )
            combined_results["siem_enrichment"] = siem_enrichment
        
        combined_results["timestamp"] = orchestrator.get_current_timestamp()
        
        return combined_results
        
    except Exception as e:
        logger.error(f"Error in threat intelligence analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Threat intel analysis failed: {str(e)}")

@router.post("/malware", response_model=Dict[str, Any])
async def analyze_malware(
    request: MalwareAnalysisRequest,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Perform AI-powered malware analysis.
    
    Args:
        request: Malware analysis request
        orchestrator: Security orchestrator dependency
        
    Returns:
        Malware analysis results
    """
    try:
        logger.info(f"Starting malware analysis")
        
        analysis_data = {
            "file_hash": request.file_hash,
            "file_name": request.file_name,
            "behavioral_data": request.behavioral_data,
            "static_analysis": request.static_analysis
        }
        
        # Use Mistral for specialized malware analysis
        malware_analysis = await orchestrator.mistral_service.analyze_malware(
            analysis_data
        )
        
        # Use Llama for additional context and family classification
        family_analysis = await orchestrator.llama_service.classify_malware_family(
            analysis_data
        )
        
        results = {
            "malware_analysis": malware_analysis,
            "family_classification": family_analysis,
            "timestamp": orchestrator.get_current_timestamp()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in malware analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Malware analysis failed: {str(e)}")

@router.post("/phishing", response_model=Dict[str, Any])
async def analyze_phishing(
    request: PhishingAnalysisRequest,
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Perform AI-powered phishing analysis.
    
    Args:
        request: Phishing analysis request
        orchestrator: Security orchestrator dependency
        
    Returns:
        Phishing analysis results
    """
    try:
        logger.info("Starting phishing analysis")
        
        analysis_data = {
            "email_content": request.email_content,
            "url": request.url,
            "sender_info": request.sender_info,
            "attachments": request.attachments
        }
        
        # Use both models for comprehensive phishing analysis
        llama_phishing = await orchestrator.llama_service.analyze_phishing(
            analysis_data
        )
        
        mistral_phishing = await orchestrator.mistral_service.analyze_phishing(
            analysis_data
        )
        
        # Combine phishing analysis results
        combined_analysis = _combine_phishing_results(llama_phishing, mistral_phishing)
        
        results = {
            "phishing_analysis": combined_analysis,
            "timestamp": orchestrator.get_current_timestamp()
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in phishing analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Phishing analysis failed: {str(e)}")

@router.get("/models/status", response_model=Dict[str, Any])
async def get_ai_models_status(
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Get status and health information for AI models.
    
    Args:
        orchestrator: Security orchestrator dependency
        
    Returns:
        AI models status and health information
    """
    try:
        logger.info("Checking AI models status")
        
        # Check Llama service health
        llama_status = await orchestrator.llama_service.health_check()
        llama_info = await orchestrator.llama_service.get_model_info()
        
        # Check Mistral service health  
        mistral_status = await orchestrator.mistral_service.health_check()
        mistral_info = await orchestrator.mistral_service.get_model_info()
        
        return {
            "llama": {
                "status": llama_status,
                "model_info": llama_info
            },
            "mistral": {
                "status": mistral_status,
                "model_info": mistral_info
            },
            "timestamp": orchestrator.get_current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Error checking AI models status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/attribution", response_model=Dict[str, Any])
async def analyze_attribution(
    event_data: Dict[str, Any] = Body(...),
    orchestrator: SecurityOrchestrator = Depends()
):
    """
    Perform threat actor attribution analysis using AI.
    
    Args:
        event_data: Security event data for attribution analysis
        orchestrator: Security orchestrator dependency
        
    Returns:
        Attribution analysis results
    """
    try:
        logger.info("Starting attribution analysis")
        
        attribution_result = await orchestrator.attribution_analyzer.analyze_attribution(
            event_data
        )
        
        return attribution_result
        
    except Exception as e:
        logger.error(f"Error in attribution analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Attribution analysis failed: {str(e)}")

# Helper functions for combining AI results
def _combine_ai_results(llama_result: Dict[str, Any], mistral_result: Dict[str, Any]) -> Dict[str, Any]:
    """Combine results from Llama and Mistral analyses."""
    combined = {
        "consensus_score": 0.0,
        "combined_classification": "unknown",
        "confidence": 0.0,
        "recommendations": []
    }
    
    try:
        # Average threat scores if available
        llama_score = llama_result.get("threat_score", 0)
        mistral_score = mistral_result.get("threat_score", 0)
        
        if llama_score or mistral_score:
            combined["consensus_score"] = (llama_score + mistral_score) / 2
        
        # Combine recommendations
        llama_recs = llama_result.get("recommendations", [])
        mistral_recs = mistral_result.get("recommendations", [])
        all_recs = llama_recs + mistral_recs
        combined["recommendations"] = list(dict.fromkeys(all_recs))[:10]
        
        # Calculate consensus confidence
        llama_conf = llama_result.get("confidence", 0)
        mistral_conf = mistral_result.get("confidence", 0)
        combined["confidence"] = (llama_conf + mistral_conf) / 2
        
    except Exception as e:
        logger.warning(f"Error combining AI results: {str(e)}")
    
    return combined

def _combine_threat_intel_results(llama_result: Dict[str, Any], mistral_result: Dict[str, Any]) -> Dict[str, Any]:
    """Combine threat intelligence results from both models."""
    combined = {
        "threat_assessment": {},
        "malicious_indicators": [],
        "threat_actors": [],
        "campaigns": []
    }
    
    try:
        # Combine malicious indicators
        llama_indicators = llama_result.get("malicious_indicators", [])
        mistral_indicators = mistral_result.get("malicious_indicators", [])
        combined["malicious_indicators"] = list(set(llama_indicators + mistral_indicators))
        
        # Combine threat actors
        llama_actors = llama_result.get("threat_actors", [])
        mistral_actors = mistral_result.get("threat_actors", [])
        combined["threat_actors"] = list(set(llama_actors + mistral_actors))
        
        # Combine campaigns
        llama_campaigns = llama_result.get("campaigns", [])
        mistral_campaigns = mistral_result.get("campaigns", [])
        combined["campaigns"] = list(set(llama_campaigns + mistral_campaigns))
        
    except Exception as e:
        logger.warning(f"Error combining threat intel results: {str(e)}")
    
    return combined

def _combine_phishing_results(llama_result: Dict[str, Any], mistral_result: Dict[str, Any]) -> Dict[str, Any]:
    """Combine phishing analysis results from both models."""
    combined = {
        "is_phishing": False,
        "confidence": 0.0,
        "phishing_type": "unknown",
        "indicators": []
    }
    
    try:
        # Determine if phishing based on both models
        llama_phishing = llama_result.get("is_phishing", False)
        mistral_phishing = mistral_result.get("is_phishing", False)
        combined["is_phishing"] = llama_phishing or mistral_phishing
        
        # Average confidence scores
        llama_conf = llama_result.get("confidence", 0)
        mistral_conf = mistral_result.get("confidence", 0)
        combined["confidence"] = (llama_conf + mistral_conf) / 2
        
        # Combine indicators
        llama_indicators = llama_result.get("indicators", [])
        mistral_indicators = mistral_result.get("indicators", [])
        combined["indicators"] = list(set(llama_indicators + mistral_indicators))
        
    except Exception as e:
        logger.warning(f"Error combining phishing results: {str(e)}")
    
    return combined