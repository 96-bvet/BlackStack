import yaml
import os
import datetime

LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/refactor_engine.log")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def suggest_split(tool_data):
    suggestions = []
    tags = tool_data.get("tags", [])
    logic_type = tool_data.get("logic_type", "")
    tool_name = tool_data.get("tool_name", "unknown_tool")

    # Example: split GUI logic from CLI if both are present
    if "gui" in tags and "cli" in tags:
        suggestions.append({
            "tool_name": f"{tool_name}_cli",
            "tags": ["cli"],
            "logic_type": logic_type,
            "persona": tool_data.get("persona_hint", "unassigned")
        })
        suggestions.append({
            "tool_name": f"{tool_name}_gui",
            "tags": ["gui"],
            "logic_type": logic_type,
            "persona": tool_data.get("persona_hint", "unassigned")
        })
        log_event(f"Suggested split for {tool_name}: CLI/GUI separation")

    # Example: flag missing logic_type
    if not logic_type:
        suggestions.append({
            "tool_name": f"{tool_name}_refactor",
            "tags": tags,
            "logic_type": "unspecified",
            "persona": "unassigned"
        })
        log_event(f"Suggested refactor for {tool_name}: missing logic_type")

    return suggestions if suggestions else [tool_data]
