# ~/BlackStack/WachterEID/runtime/persona_variants/auditpersona_v2.py

import os
from registry import get_active_persona, get_capabilities, mutation_allowed

def gatekeeper_check(module_path, action="mutation"):
    persona = get_active_persona()
    capabilities = get_capabilities()

    if action not in capabilities:
        print(f"[Gatekeeper] Persona '{persona}' lacks capability: {action}")
        return False

    if not mutation_allowed(module_path):
        print(f"[Gatekeeper] Mutation not allowed for: {module_path}")
        return False

    print(f"[Gatekeeper] Mutation approved for '{module_path}' by persona '{persona}'")
    return True
