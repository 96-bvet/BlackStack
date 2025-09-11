import os
import yaml
import json
import importlib.util
import datetime

# Registry paths
YAML_REGISTRY = os.path.expanduser("~/BlackStack/BlackStack/persona/persona_registry.yaml")
JSON_REGISTRY = os.path.expanduser("~/BlackStack/BlackStack/persona/persona_registry.json")

EXCLUDED_MODULES = [
    "runtime/apply_mutations.py"
]

# --- Registry loading ---
def load_registry():
    if not os.path.exists(YAML_REGISTRY):
        raise FileNotFoundError(f"[Registry] YAML not found: {YAML_REGISTRY}")
    with open(YAML_REGISTRY, "r") as f:
        return yaml.safe_load(f)

class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

def sync_json_from_yaml():
    registry = load_registry()
    with open(JSON_REGISTRY, "w") as f:
        json.dump(registry, f, indent=2, cls=SafeEncoder)
    print("[Registry] JSON synced from canonical YAML.")

# --- Active persona resolution ---
def get_active_persona():
    registry = load_registry()
    persona = registry.get("active_persona", "Unknown")
    if persona not in registry.get("personas", {}):
        print(f"[Registry] Active persona '{persona}' not found.")
    return persona

def set_active_persona(name):
    registry = load_registry()
    registry["active_persona"] = name
    with open(YAML_REGISTRY, "w") as f:
        yaml.dump(registry, f)

# --- Persona data access ---
def get_persona_data(persona=None):
    """
    Return persona data for the given persona name, or the active persona if None.
    """
    registry = load_registry()
    if persona is None:
        persona = get_active_persona()
    return registry.get("personas", {}).get(persona, {})

def get_capabilities(persona=None):
    """
    Return capabilities for the given persona name, or the active persona if None.
    """
    return get_persona_data(persona).get("capabilities", [])

def requires_approval(action="mutation", persona=None):
    data = get_persona_data(persona)
    return data.get("approval_gate", False) and action in get_capabilities(persona)

def get_tone(context="default", persona=None):
    return get_persona_data(persona).get("tone_profile", {}).get(context, "neutral")

def get_mutation_hooks(persona=None):
    return get_persona_data(persona).get("mutation_hooks", [])

def get_routing_tags(persona=None):
    return get_persona_data(persona).get("routing_tags", [])

def mutation_allowed(path, persona=None):
    registry = load_registry()
    if persona is None:
        persona = registry.get("active_persona", "")
    hooks = registry.get("personas", {}).get(persona, {}).get("mutation_hooks", [])
    normalized_path = os.path.abspath(path)
    normalized_hooks = [os.path.abspath(hook) for hook in hooks]
    return normalized_path in normalized_hooks

# --- CLI compatibility shims ---
def list_personas():
    """
    Return a list of all persona names in the registry.
    """
    registry = load_registry()
    return list(registry.get("personas", {}).keys())

def get_persona_metadata(persona=None):
    """
    Compatibility wrapper for CLI — returns persona data.
    """
    return get_persona_data(persona)

# --- Persona loading ---
def load_persona(name):
    return load_persona_engine(name)

def load_persona_engine(persona):
    path = os.path.expanduser(f"~/BlackStack/BlackStack/runtime/persona_variants/{persona.lower()}_v2.py")
    if not os.path.exists(path):
        raise FileNotFoundError(f"[Persona] Module not found: {path}")
    spec = importlib.util.spec_from_file_location("persona_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Prefer Qwen-compatible entry point
    if hasattr(module, "run_persona_logic"):
        return module.run_persona_logic
    else:
        raise AttributeError(f"[Persona] No valid entry point in {path}")

# --- Module-based persona resolution ---
def resolve_persona_by_module(module_name):
    registry = load_registry()
    for persona, data in registry.get("personas", {}).items():
        if module_name in data.get("modules", []):
            return {
                "persona": persona,
                "gatekeeper": data.get("gatekeeper"),
                "capabilities": data.get("capabilities", []),
                "inherits": data.get("inherits", []),
                "tone_profile": data.get("tone_profile", {}),
                "status": data.get("status", "❌ Unrouted")
            }
    return {
        "persona": "Unknown",
        "gatekeeper": None,
        "capabilities": [],
        "inherits": [],
        "tone_profile": {},
        "status": "❌ Unrouted"
    }
