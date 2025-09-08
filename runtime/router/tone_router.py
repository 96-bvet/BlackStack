# runtime/router/tone_router.py

import os
from datetime import datetime
from registry import (
    get_active_persona,
    get_capabilities,
    mutation_allowed,
    escalate_persona,
    persona_escalation_check
)
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check

AUDIT_LOG = os.path.expanduser("~/BlackStack/BlackStack/audit/tone_trace.md")
MODULE_PATH = "runtime/router/tone_router.py"

def _log_tone_event(message):
    with open(AUDIT_LOG, "a") as log:
        log.write(f"{datetime.now().isoformat()} | {message}\n")

def inject_tone(prompt, tone_profile):
    style = tone_profile.get("style", "neutral")
    emotion = tone_profile.get("emotional_range", "bounded")
    mode = tone_profile.get("response_mode", "forensic")
    tone_header = f"[Tone: {style}, Emotion: {emotion}, Mode: {mode}]"
    return f"{tone_header}\n{prompt}"

def process_tone(prompt, tone_profile):
    if not tone_profile:
        _log_tone_event("[Fallback] No tone profile provided. Using default.")
        tone_profile = {
            "style": "neutral",
            "emotional_range": "bounded",
            "response_mode": "forensic"
        }

    injected_prompt = inject_tone(prompt, tone_profile)
    _log_tone_event(f"[Injected] {injected_prompt}")
    return injected_prompt

def tone_router(prompt, tone_profile=None):
    persona = get_active_persona()

    if not gatekeeper_check(MODULE_PATH):
        _log_tone_event(f"[Gatekeeper] Mutation blocked for {MODULE_PATH}")
        raise PermissionError(f"[Gatekeeper] Mutation blocked for {MODULE_PATH}")

    if not tone_profile:
        _log_tone_event(f"[Escalation] Tone profile missing for persona '{persona}'. Attempting escalation.")
        if persona_escalation_check(MODULE_PATH):
            escalate_persona("SentinelCore")
            tone_profile = {
                "style": "minimal",
                "emotional_range": "bounded",
                "response_mode": "audit"
            }
            _log_tone_event("[Escalation] Escalated to SentinelCore with fallback tone.")
        else:
            _log_tone_event("[Escalation] Persona escalation denied. Using Observer fallback.")
            tone_profile = {
                "style": "neutral",
                "emotional_range": "bounded",
                "response_mode": "forensic"
            }

    return process_tone(prompt, tone_profile)
