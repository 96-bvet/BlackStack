"""
Mistral AI API integration service for the BlackStack Cybersecurity Platform.
"""

import os
import json
import logging
import httpx
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MistralService:
    """Service class for Mistral AI API integration."""
    
    def __init__(self):
        """Initialize Mistral service with configuration."""
        self.api_url = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai")
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.model_name = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
        self.timeout = int(os.getenv("MISTRAL_TIMEOUT", "60"))
        self.max_tokens = int(os.getenv("MISTRAL_MAX_TOKENS", "2048"))
        
        if not self.api_key:
            logger.warning("MISTRAL_API_KEY not set - service will not function")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "BlackStack-Cybersecurity-Platform/1.0"
        }
        
        logger.info(f"Mistral service initialized with model {self.model_name}")
    
    async def health_check(self) -> str:
        """
        Check Mistral service health and connectivity.
        
        Returns:
            Health status string
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/models",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return "healthy"
                else:
                    return f"unhealthy (HTTP {response.status_code})"
                    
        except Exception as e:
            logger.error(f"Mistral health check failed: {str(e)}")
            return f"unhealthy: {str(e)}"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Mistral model.
        
        Returns:
            Model information
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/v1/models",
                    headers=self.headers
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Find the specific model info
                model_info = None
                for model in data.get("data", []):
                    if model.get("id") == self.model_name:
                        model_info = model
                        break
                
                return {
                    "model_name": self.model_name,
                    "status": "available" if model_info else "not_found",
                    "max_tokens": self.max_tokens,
                    "model_info": model_info
                }
                
        except Exception as e:
            logger.error(f"Error getting Mistral model info: {str(e)}")
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
        Analyze security event using Mistral model for specialized threat detection.
        
        Args:
            prompt: Analysis prompt
            event_data: Security event data
            
        Returns:
            Analysis results
        """
        try:
            # Prepare specialized prompt for Mistral
            system_prompt = """You are an advanced cybersecurity threat analyst specializing in sophisticated attacks, APTs, and zero-day exploits. Analyze the provided security event with focus on:

1. Advanced persistent threats (APT) indicators
2. Nation-state attack patterns  
3. Zero-day vulnerabilities
4. Supply chain compromise indicators
5. Fileless and living-off-the-land techniques

Respond with structured JSON analysis including:
- threat_score: Numerical score 0-10 for threat severity
- classification: Threat type with APT/nation-state focus
- confidence: Analysis confidence 0-1
- apt_indicators: Specific APT/sophisticated attack indicators
- attribution_hints: Potential threat actor attribution clues
- recommendations: Specialized containment/response actions
- sophistication_level: Attack sophistication assessment"""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{prompt}\n\nEvent Data: {json.dumps(event_data, indent=2)}"}
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
                
                # Extract and parse the analysis
                analysis_text = data["choices"][0]["message"]["content"]
                analysis_result = json.loads(analysis_text)
                
                # Add metadata
                analysis_result["model_used"] = self.model_name
                analysis_result["tokens_used"] = data.get("usage", {}).get("total_tokens", 0)
                
                logger.info("Mistral specialized security event analysis completed")
                return analysis_result
                
        except Exception as e:
            logger.error(f"Error in Mistral security analysis: {str(e)}")
            return {
                "error": str(e),
                "threat_score": 0,
                "classification": "unknown",
                "confidence": 0.0,
                "recommendations": ["Specialized analysis failed - expert review required"]
            }
    
    async def analyze_threat_intelligence(
        self, 
        indicators: List[str], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform advanced threat intelligence analysis using Mistral.
        
        Args:
            indicators: List of IOCs to analyze
            context: Additional context for analysis
            
        Returns:
            Advanced threat intelligence analysis
        """
        try:
            prompt = f"""
            Perform advanced threat intelligence analysis on these indicators with focus on nation-state and APT activities:
            
            Indicators: {indicators}
            Context: {json.dumps(context, indent=2)}
            
            Provide detailed intelligence assessment including:
            - Advanced threat actor attribution
            - Campaign analysis and TTPs
            - Geopolitical context and motivation
            - Infrastructure analysis
            - Timeline and evolution patterns
            - Countermeasure recommendations
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert threat intelligence analyst specializing in APT groups and nation-state actors. Focus on sophisticated threat analysis and attribution."
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
                
                logger.info(f"Mistral advanced threat intelligence analysis completed for {len(indicators)} indicators")
                return result
                
        except Exception as e:
            logger.error(f"Error in Mistral threat intelligence analysis: {str(e)}")
            return {
                "error": str(e),
                "malicious_indicators": [],
                "threat_actors": [],
                "campaigns": []
            }
    
    async def analyze_malware(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform specialized malware analysis using Mistral.
        
        Args:
            analysis_data: Malware analysis data
            
        Returns:
            Detailed malware analysis
        """
        try:
            prompt = f"""
            Perform advanced malware analysis with focus on sophisticated threats:
            
            Analysis Data: {json.dumps(analysis_data, indent=2)}
            
            Provide comprehensive analysis including:
            - Malware family and variant identification
            - Advanced evasion techniques detected
            - Payload analysis and capabilities
            - C2 infrastructure analysis
            - Attribution indicators
            - Advanced persistent mechanisms
            - Zero-day exploit indicators
            - Recommended containment strategies
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert malware reverse engineer specializing in advanced threats, APT malware, and sophisticated evasion techniques."
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
                
                logger.info("Mistral advanced malware analysis completed")
                return result
                
        except Exception as e:
            logger.error(f"Error in Mistral malware analysis: {str(e)}")
            return {
                "error": str(e),
                "malware_family": "unknown",
                "sophistication": "unknown",
                "capabilities": []
            }
    
    async def analyze_phishing(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform advanced phishing analysis using Mistral.
        
        Args:
            analysis_data: Phishing analysis data
            
        Returns:
            Advanced phishing analysis results
        """
        try:
            prompt = f"""
            Perform advanced phishing analysis with focus on sophisticated social engineering:
            
            Analysis Data: {json.dumps(analysis_data, indent=2)}
            
            Provide detailed analysis including:
            - Phishing sophistication level
            - Social engineering techniques used
            - Target profile analysis
            - Campaign attribution indicators
            - Infrastructure analysis
            - Credential harvesting mechanisms
            - Advanced evasion techniques
            - Business email compromise indicators
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert social engineering and phishing analyst specializing in sophisticated campaigns and business email compromise attacks."
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
                
                logger.info("Mistral advanced phishing analysis completed")
                return result
                
        except Exception as e:
            logger.error(f"Error in Mistral phishing analysis: {str(e)}")
            return {
                "error": str(e),
                "is_phishing": False,
                "confidence": 0.0,
                "sophistication": "unknown"
            }
    
    async def analyze_network_anomaly(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze network anomalies for advanced threats using Mistral.
        
        Args:
            network_data: Network traffic and anomaly data
            
        Returns:
            Network anomaly analysis results
        """
        try:
            prompt = f"""
            Analyze network anomalies for advanced persistent threats and sophisticated attacks:
            
            Network Data: {json.dumps(network_data, indent=2)}
            
            Focus on:
            - Advanced C2 communication patterns
            - Covert channel detection
            - Data exfiltration indicators
            - Lateral movement patterns
            - Zero-day exploitation network signatures
            - Nation-state attack patterns
            - Supply chain compromise indicators
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a network security expert specializing in advanced threat detection and APT network analysis."
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
                
                logger.info("Mistral network anomaly analysis completed")
                return result
                
        except Exception as e:
            logger.error(f"Error in Mistral network analysis: {str(e)}")
            return {
                "error": str(e),
                "anomaly_type": "unknown",
                "threat_level": "unknown"
            }
    
    async def generate_apt_report(self, analysis_results: Dict[str, Any]) -> str:
        """
        Generate comprehensive APT analysis report using Mistral.
        
        Args:
            analysis_results: Combined analysis results
            
        Returns:
            Detailed APT analysis report
        """
        try:
            prompt = f"""
            Generate a comprehensive APT (Advanced Persistent Threat) analysis report based on the following analysis results:
            
            Analysis Results: {json.dumps(analysis_results, indent=2)}
            
            The report should be suitable for executive briefing and include:
            - Executive summary of the threat
            - Technical analysis details
            - Attribution assessment
            - Impact analysis
            - Recommended countermeasures
            - Strategic implications
            
            Focus on APT sophistication and nation-state implications.
            """
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a senior cybersecurity analyst specializing in APT reporting for executive audiences. Write comprehensive, professional reports."
                    },
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.2
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                report = data["choices"][0]["message"]["content"]
                
                logger.info("Mistral APT report generated")
                return report
                
        except Exception as e:
            logger.error(f"Error generating APT report: {str(e)}")
            return f"Error generating APT report: {str(e)}"