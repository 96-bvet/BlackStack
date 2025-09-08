# runtime/persona_variants/blackhawk_v2.py

from registry import resolve_persona_by_module
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check
from runtime.router.tone_router import inject_tone
from models.qwen_wrapper import QwenModel
from datetime import datetime

def log_trace(module, persona, tone, prompt, response):
    with open("audit/qwen_trace.md", "a") as log:
        log.write(f"## {datetime.now().isoformat()}\n")
        log.write(f"Module: {module}\n")
        log.write(f"Persona: {persona}\n")
        log.write(f"Tone: {tone}\n")
        log.write(f"Prompt: {prompt}\n")
        log.write(f"Response: {response}\n\n")

def log_gatekeeper(module, persona, verdict, reason):
    with open("audit/gatekeeper_trace.md", "a") as log:
        log.write(f"## {datetime.now().isoformat()}\n")
        log.write(f"Module: {module}\n")
        log.write(f"Persona: {persona}\n")
        log.write(f"Gatekeeper: auditpersona_v2.py\n")
        log.write(f"Verdict: {verdict}\n")
        log.write(f"Reason: {reason}\n\n")

def run_persona_logic(prompt):
    module_path = "runtime/persona_variants/blackhawk_v2.py"
    persona_data = resolve_persona_by_module("blackhawk_v2.py")
    persona = persona_data["persona"]

    if not gatekeeper_check(module_path):
        log_gatekeeper(module_path, persona, "❌ Blocked", "Mutation hook mismatch or missing capability")
        raise PermissionError(f"[Gatekeeper] Mutation blocked for {module_path}")
    else:
        log_gatekeeper(module_path, persona, "✅ Approved", "Hook matched and capability present")

    enriched_prompt = inject_tone(prompt, persona_data["tone_profile"])
    tone = persona_data["tone_profile"]

    qwen = QwenModel()
    output = qwen.generate(prompt=enriched_prompt, max_new_tokens=512, do_sample=True)

    log_trace(module_path, persona, tone, enriched_prompt, output[0]["generated_text"])
    return output[0]["generated_text"]
