import yaml
import os
import datetime

REGISTRY_PATH = os.path.expanduser("~/BlackStack/WachterEID/registry/persona_registry.yaml")
LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/persona_router.log")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def load_registry():
    try:
        with open(REGISTRY_PATH, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        log_event(f"Failed to load persona registry: {e}")
        return {}

def match_persona(tool_data):
    registry = load_registry()
    tags = tool_data.get("tags", [])
    logic_type = tool_data.get("logic_type", "")
    hint = tool_data.get("persona_hint", "")

    # Priority: hint > logic_type > tags
    if hint in registry:
        log_event(f"Matched via hint: {hint}")
        return hint

    if logic_type in registry:
        log_event(f"Matched via logic_type: {logic_type}")
        return logic_type

    for tag in tags:
        if tag in registry:
            log_event(f"Matched via tag: {tag}")
            return tag

    log_event(f"No match found. Routing to 'unassigned'")
    return "unassigned"
