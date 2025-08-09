"""
Attribution Analysis module for threat actor identification and analysis.
"""

import re
import hashlib
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ThreatActor:
    """Data class representing a threat actor profile."""
    name: str
    aliases: List[str]
    origin_country: Optional[str]
    motivation: str
    techniques: List[str]
    indicators: List[str]
    confidence_score: float

@dataclass
class AttributionResult:
    """Result of attribution analysis."""
    event_id: str
    suspected_actors: List[ThreatActor]
    attribution_confidence: float
    reasoning: List[str]
    iocs_matched: List[str]
    timestamp: str

class AttributionAnalyzer:
    """Analyzer for threat actor attribution."""
    
    def __init__(self):
        """Initialize the attribution analyzer."""
        self.threat_actor_database = self._load_threat_actor_profiles()
        self.ioc_patterns = self._load_ioc_patterns()
        logger.info("Attribution Analyzer initialized")
    
    def _load_threat_actor_profiles(self) -> List[ThreatActor]:
        """Load known threat actor profiles."""
        return [
            ThreatActor(
                name="APT29",
                aliases=["Cozy Bear", "The Dukes", "CozyDuke"],
                origin_country="Russia",
                motivation="espionage",
                techniques=["spear_phishing", "living_off_land", "credential_harvesting"],
                indicators=["powershell_empire", "cobalt_strike", "specific_malware_families"],
                confidence_score=0.0
            ),
            ThreatActor(
                name="APT28",
                aliases=["Fancy Bear", "Sofacy", "Sednit"],
                origin_country="Russia",
                motivation="espionage",
                techniques=["spear_phishing", "zero_day_exploits", "credential_theft"],
                indicators=["x-agent", "seduploader", "gamefish"],
                confidence_score=0.0
            ),
            ThreatActor(
                name="Lazarus Group",
                aliases=["HIDDEN COBRA", "Guardians of Peace"],
                origin_country="North Korea",
                motivation="financial_cybercrime",
                techniques=["destructive_attacks", "banking_trojans", "cryptocurrency_theft"],
                indicators=["bankshot", "fallchill", "hoplight"],
                confidence_score=0.0
            ),
            ThreatActor(
                name="APT1",
                aliases=["Comment Crew", "PLA Unit 61398"],
                origin_country="China",
                motivation="espionage",
                techniques=["persistent_access", "data_exfiltration", "lateral_movement"],
                indicators=["webc2", "backdoor.apt1", "trojan.ecltys"],
                confidence_score=0.0
            ),
            ThreatActor(
                name="FIN7",
                aliases=["Carbanak Group"],
                origin_country="Unknown",
                motivation="financial_cybercrime",
                techniques=["point_of_sale_malware", "spear_phishing", "fileless_attacks"],
                indicators=["carbanak", "fin7_tools", "bateleur"],
                confidence_score=0.0
            )
        ]
    
    def _load_ioc_patterns(self) -> Dict[str, List[str]]:
        """Load Indicators of Compromise patterns."""
        return {
            "malware_families": [
                r"trojan\.apt1",
                r"backdoor\.apt1",
                r"carbanak",
                r"bankshot",
                r"fallchill",
                r"x-agent",
                r"seduploader"
            ],
            "command_patterns": [
                r"powershell.*-enc.*",
                r"cmd\.exe.*\/c.*echo.*",
                r"wmic.*process.*call.*create",
                r"rundll32.*javascript:",
                r"regsvr32.*\/s.*\/n.*\/u.*\/i:"
            ],
            "network_patterns": [
                r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:443",
                r"[a-zA-Z0-9-]+\.bit",
                r"[a-zA-Z0-9-]+\.onion",
                r"pastebin\.com\/raw\/[a-zA-Z0-9]+",
                r"github\.com\/[^\/]+\/[^\/]+\/raw\/"
            ],
            "file_patterns": [
                r".*\.scr$",
                r".*\.pif$",
                r".*\.com$",
                r"temp\\[a-zA-Z0-9]{8,}\.exe",
                r"appdata\\.*\\[a-zA-Z0-9]{8,}\.dll"
            ]
        }
    
    async def analyze_attribution(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform attribution analysis on security event data.
        
        Args:
            event_data: Security event data
            
        Returns:
            Attribution analysis results
        """
        logger.info("Starting attribution analysis")
        
        try:
            # Extract IOCs from event data
            extracted_iocs = self._extract_iocs(event_data)
            
            # Analyze techniques used
            techniques_detected = self._analyze_techniques(event_data)
            
            # Match against threat actor profiles
            potential_actors = self._match_threat_actors(extracted_iocs, techniques_detected)
            
            # Calculate attribution confidence
            attribution_confidence = self._calculate_attribution_confidence(
                potential_actors, extracted_iocs, techniques_detected
            )
            
            # Generate reasoning
            reasoning = self._generate_attribution_reasoning(
                potential_actors, extracted_iocs, techniques_detected
            )
            
            result = {
                "suspected_actors": [actor.__dict__ for actor in potential_actors],
                "attribution_confidence": attribution_confidence,
                "reasoning": reasoning,
                "iocs_matched": extracted_iocs,
                "techniques_detected": techniques_detected,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            logger.info("Attribution analysis completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in attribution analysis: {str(e)}")
            return {
                "error": str(e),
                "suspected_actors": [],
                "attribution_confidence": 0.0,
                "reasoning": ["Analysis failed due to error"],
                "iocs_matched": [],
                "techniques_detected": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def _extract_iocs(self, event_data: Dict[str, Any]) -> List[str]:
        """Extract Indicators of Compromise from event data."""
        iocs = []
        event_text = str(event_data)
        
        for category, patterns in self.ioc_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, event_text, re.IGNORECASE)
                iocs.extend(matches)
        
        return list(set(iocs))  # Remove duplicates
    
    def _analyze_techniques(self, event_data: Dict[str, Any]) -> List[str]:
        """Analyze attack techniques present in the event."""
        techniques = []
        
        # Check for common attack techniques
        event_text = str(event_data).lower()
        
        technique_indicators = {
            "spear_phishing": ["phishing", "malicious_attachment", "email_link"],
            "powershell_abuse": ["powershell", "-encodedcommand", "-enc"],
            "credential_harvesting": ["mimikatz", "credential_dump", "password_hash"],
            "lateral_movement": ["psexec", "wmi_exec", "remote_login"],
            "data_exfiltration": ["file_transfer", "data_upload", "compression"],
            "persistence": ["scheduled_task", "registry_modification", "service_creation"],
            "privilege_escalation": ["uac_bypass", "token_impersonation", "exploit"],
            "defense_evasion": ["process_injection", "dll_sideloading", "obfuscation"]
        }
        
        for technique, indicators in technique_indicators.items():
            if any(indicator in event_text for indicator in indicators):
                techniques.append(technique)
        
        return techniques
    
    def _match_threat_actors(
        self, 
        iocs: List[str], 
        techniques: List[str]
    ) -> List[ThreatActor]:
        """Match IOCs and techniques against threat actor profiles."""
        matched_actors = []
        
        for actor in self.threat_actor_database:
            confidence_score = 0.0
            
            # Check technique overlap
            technique_matches = len(set(techniques) & set(actor.techniques))
            if technique_matches > 0:
                confidence_score += (technique_matches / len(actor.techniques)) * 0.6
            
            # Check IOC matches
            ioc_matches = 0
            for ioc in iocs:
                for indicator in actor.indicators:
                    if indicator.lower() in ioc.lower():
                        ioc_matches += 1
            
            if ioc_matches > 0:
                confidence_score += min(ioc_matches / len(actor.indicators), 1.0) * 0.4
            
            # Only include actors with meaningful confidence
            if confidence_score > 0.1:
                actor.confidence_score = round(confidence_score, 3)
                matched_actors.append(actor)
        
        # Sort by confidence score
        matched_actors.sort(key=lambda x: x.confidence_score, reverse=True)
        return matched_actors[:5]  # Return top 5 matches
    
    def _calculate_attribution_confidence(
        self, 
        actors: List[ThreatActor], 
        iocs: List[str], 
        techniques: List[str]
    ) -> float:
        """Calculate overall attribution confidence."""
        if not actors:
            return 0.0
        
        # Base confidence on top actor match
        base_confidence = actors[0].confidence_score
        
        # Adjust based on number of IOCs and techniques
        ioc_factor = min(len(iocs) / 10, 1.0) * 0.2
        technique_factor = min(len(techniques) / 5, 1.0) * 0.2
        
        total_confidence = base_confidence + ioc_factor + technique_factor
        return round(min(total_confidence, 1.0), 3)
    
    def _generate_attribution_reasoning(
        self, 
        actors: List[ThreatActor], 
        iocs: List[str], 
        techniques: List[str]
    ) -> List[str]:
        """Generate human-readable attribution reasoning."""
        reasoning = []
        
        if not actors:
            reasoning.append("No significant threat actor matches found")
            return reasoning
        
        top_actor = actors[0]
        reasoning.append(
            f"Primary attribution to {top_actor.name} "
            f"(confidence: {top_actor.confidence_score})"
        )
        
        if top_actor.origin_country:
            reasoning.append(f"Suspected origin: {top_actor.origin_country}")
        
        reasoning.append(f"Motivation likely: {top_actor.motivation}")
        
        if techniques:
            reasoning.append(f"Techniques detected: {', '.join(techniques[:3])}")
        
        if iocs:
            reasoning.append(f"IOCs identified: {len(iocs)} indicators")
        
        if len(actors) > 1:
            reasoning.append(
                f"Alternative attributions: {', '.join([a.name for a in actors[1:3]])}"
            )
        
        return reasoning