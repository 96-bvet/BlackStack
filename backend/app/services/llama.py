"""
Llama AI API integration service for the BlackStack Cybersecurity Platform.
"""

import os
import json
import logging
import httpx
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class LlamaService:
    """Service class for Llama AI API integration."""
    
    def __init__(self):
        """Initialize Llama service with configuration."""
        self.api_url = os.getenv("LLAMA_API_URL", "https://api.llama-ai.example.com")
        self.api_key = os.getenv("LLAMA_API_KEY")
        self.model_name = os.getenv("LLAMA_MODEL", "llama-2-70b-chat")
        self.timeout = int(os.getenv("LLAMA_TIMEOUT", "60"))
        self.max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", "2048"))
        
        if not self.api_key:
            logger.warning("LLAMA_API_KEY not set - service will not function")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BlackStack-Cybersecurity-Platform/1.0"
        }
        
        logger.info(f"Llama service initialized with model {self.model_name}")
    
    async def health_check(self) -> str:
        """
        Check Llama service health and connectivity.
        
        Returns:
            Health status string
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/health",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return "healthy"
                else:
                    return f"unhealthy (HTTP {response.status_code})"
                    
        except Exception as e:
            logger.error(f"Llama health check failed: {str(e)}")
            return f"unhealthy: {str(e)}"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Llama model.
        
        Returns:
            Model information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/models/{self.model_name}",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                return {
                    "model_name": self.model_name,
                    "status": "available",
                    "capabilities": data.get("capabilities", []),
                    "max_tokens": self.max_tokens
                }
                
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {
                "model_name": self.model_name,
                "status": "error",
                "error": str(e)
            }
    
    async def analyze_security_event(
        self, 
        prompt: str, 
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze security event using Llama model.
        
        Args:
            prompt: Analysis prompt
            event_data: Security event data
            
        Returns:
            Analysis results
        """
        try:
            # Prepare the analysis prompt
            system_prompt = """You are a cybersecurity expert AI assistant. Analyze the provided security event data and respond with a structured JSON analysis. Your analysis should include:

1. threat_score: A numerical score from 0-10 indicating threat severity
2. classification: The type of threat (e.g., malware, phishing, intrusion, etc.)
3. confidence: Your confidence level in the analysis (0-1)
4. attack_vectors: Potential attack vectors identified
5. recommendations: List of recommended actions
6. indicators: Key indicators of compromise found

Be precise and base your analysis on the actual data provided."""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nEvent Data: {json.dumps(event_data, indent=2)}"}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Extract and parse the analysis
                analysis_text = data["choices"][0]["message"]["content"]
                analysis_result = json.loads(analysis_text)
                
                # Add metadata
                analysis_result["model_used"] = self.model_name
                analysis_result["tokens_used"] = data.get("usage", {}).get("total_tokens", 0)
                
                logger.info("Llama security event analysis completed")
                return analysis_result
                
        except Exception as e:
            logger.error(f"Error in Llama security analysis: {str(e)}")
            return {
                "error": str(e),
                "threat_score": 0,
                "classification": "unknown",
                "confidence": 0.0,
                "recommendations": ["Analysis failed - manual review required"]
            }
    
    async def analyze_threat_intelligence(
        self, 
        indicators: List[str], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze threat intelligence indicators using Llama.
        
        Args:
            indicators: List of IOCs to analyze
            context: Additional context for analysis
            
        Returns:
            Threat intelligence analysis
        """
        try:
            prompt = f"""
            Analyze the following threat indicators and provide intelligence assessment:
            
            Indicators: {indicators}
            Context: {json.dumps(context, indent=2)}
            
            Provide analysis including:
            - Malicious indicators classification
            - Associated threat actors (if identifiable)
            - Campaign associations
            - Threat level assessment
            - Attribution confidence
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a threat intelligence analyst. Analyze IOCs and provide structured intelligence assessment in JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                analysis_text = data["choices"][0]["message"]["content"]
                result = json.loads(analysis_text)
                
                logger.info(f"Llama threat intelligence analysis completed for {len(indicators)} indicators")
                return result
                
        except Exception as e:
            logger.error(f"Error in Llama threat intelligence analysis: {str(e)}")
            return {
                "error": str(e),
                "malicious_indicators": [],
                "threat_actors": [],
                "campaigns": []
            }
    
    async def classify_malware_family(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify malware family using Llama model.
        
        Args:
            analysis_data: Malware analysis data
            
        Returns:
            Malware family classification
        """
        try:
            prompt = f"""
            Analyze the following malware data and classify the malware family:
            
            Analysis Data: {json.dumps(analysis_data, indent=2)}
            
            Provide classification including:
            - Malware family name
            - Classification confidence
            - Family characteristics
            - Known variants
            - Typical behaviors
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a malware analyst. Classify malware families based on analysis data and provide structured results in JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                analysis_text = data["choices"][0]["message"]["content"]
                result = json.loads(analysis_text)
                
                logger.info("Llama malware family classification completed")
                return result
                
        except Exception as e:
            logger.error(f"Error in Llama malware classification: {str(e)}")
            return {
                "error": str(e),
                "family": "unknown",
                "confidence": 0.0
            }
    
    async def analyze_phishing(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze phishing content using Llama model.
        
        Args:
            analysis_data: Phishing analysis data
            
        Returns:
            Phishing analysis results
        """
        try:
            prompt = f"""
            Analyze the following content for phishing indicators:
            
            Analysis Data: {json.dumps(analysis_data, indent=2)}
            
            Provide analysis including:
            - Is this phishing? (boolean)
            - Phishing confidence score (0-1)
            - Phishing type/category
            - Suspicious indicators found
            - Target analysis
            - Recommended actions
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a phishing detection expert. Analyze content for phishing indicators and provide structured results in JSON format."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.1,
                "response_format": {"type": "json_object"}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                analysis_text = data["choices"][0]["message"]["content"]
                result = json.loads(analysis_text)
                
                logger.info("Llama phishing analysis completed")
                return result
                
        except Exception as e:
            logger.error(f"Error in Llama phishing analysis: {str(e)}")
            return {
                "error": str(e),
                "is_phishing": False,
                "confidence": 0.0,
                "indicators": []
            }
    
    async def generate_incident_summary(self, incident_data: Dict[str, Any]) -> str:
        """
        Generate human-readable incident summary using Llama.
        
        Args:
            incident_data: Incident data to summarize
            
        Returns:
            Human-readable incident summary
        """
        try:
            prompt = f"""
            Generate a concise, professional incident summary for the following security incident data:
            
            Incident Data: {json.dumps(incident_data, indent=2)}
            
            The summary should be suitable for management reporting and include:
            - Incident overview
            - Impact assessment
            - Current status
            - Recommended next steps
            
            Keep it concise but informative.
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cybersecurity analyst writing incident summaries for management. Be clear, concise, and professional."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                summary = data["choices"][0]["message"]["content"]
                
                logger.info("Llama incident summary generated")
                return summary
                
        except Exception as e:
            logger.error(f"Error generating incident summary: {str(e)}")
            return f"Error generating summary: {str(e)}"