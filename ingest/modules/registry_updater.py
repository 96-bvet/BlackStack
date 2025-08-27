import yaml
import os
import datetime

REGISTRY_PATH = os.path.expanduser("~/BlackStack/WachterEID/registry/persona_registry.yaml")
LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/registry_updater.log")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        return {}
    try:
        with open(REGISTRY_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        log_event(f"Failed to load registry: {e}")
        return {}

def save_registry(registry):
    try:
        with open(REGISTRY_PATH, "w") as f:
            yaml.dump(registry, f, sort_keys=False)
        log_event("Registry updated successfully.")
    except Exception as e:
        log_event(f"Failed to save registry: {e}")

def update_registry(tool_data, persona):
    registry = load_registry()
    persona_cluster = registry.get(persona, [])

    # Check for existing tool
    existing = [t for t in persona_cluster if t.get("tool_name") == tool_data["tool_name"]]
    if existing:
        log_event(f"Tool already exists in {persona}: {tool_data['tool_name']}. Skipping.")
        return

    persona_cluster.append({
        "tool_name": tool_data["tool_name"],
        "tags": tool_data["tags"],
        "logic_type": tool_data["logic_type"],
        "manifest_hash": tool_data["manifest_hash"],
        "source_path": tool_data["source_path"],
        "timestamp": datetime.datetime.now().isoformat()
    })

    registry[persona] = persona_cluster
    save_registry(registry)
    log_event(f"Tool added to {persona}: {tool_data['tool_name']}")
