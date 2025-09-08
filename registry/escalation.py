# registry/escalation.py

import os
from datetime import datetime

REGISTRY_PATH = os.path.expanduser("~/BlackStack/BlackStack/persona/persona_registry.yaml")
AUDIT_LOG = os.path.expanduser("~/BlackStack/BlackStack/audit/escalation_trace.md")

def escalate_persona(new_persona):
    # Log escalation event
    with open(AUDIT_LOG, "a") as log:
        log.write(f"{datetime.now().isoformat()} | Escalated to: {new_persona}\n")

    # Optional: mutate registry file (disabled by default)
    print(f"[Escalation] Persona escalated to: {new_persona}")
    # You can later add YAML mutation logic here if needed

# registry/escalation.py

def persona_escalation_check(module_path):
    # Placeholder logic: allow escalation for now
    print(f"[Escalation Check] Persona escalation allowed for: {module_path}")
    return True
