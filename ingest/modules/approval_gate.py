import yaml
import os
import datetime

LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/approval_gate.log")
APPROVAL_DIR = os.path.expanduser("~/BlackStack/WachterEID/approvals/")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def check_external_approval(tool_name):
    approval_file = os.path.join(APPROVAL_DIR, f"{tool_name}.yaml")
    if not os.path.exists(approval_file):
        return False
    try:
        with open(approval_file, "r") as f:
            data = yaml.safe_load(f)
        return data.get("approved", False)
    except Exception as e:
        log_event(f"Error reading approval file for {tool_name}: {e}")
        return False

def trigger_approval(tool_data, persona):
    tool_name = tool_data.get("tool_name", "unknown_tool")
    manifest_flag = tool_data.get("approved", False)
    external_flag = check_external_approval(tool_name)

    if manifest_flag or external_flag:
        log_event(f"Approved: {tool_name} | Persona: {persona}")
        return True

    # Placeholder for GUI/voice shell prompt
    log_event(f"Approval required: {tool_name} | Persona: {persona}")
    return False
