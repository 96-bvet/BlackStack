from pathlib import Path
import yaml
from datetime import datetime

HOME = Path.home()
TOOL_MANIFEST = HOME / "BlackStack" / "WachterEID" / "config" / "tool_manifest.yaml"
APPROVAL_LOG = HOME / "BlackStack" / "WachterEID" / "audit" / "approval_routing.log"

# Persona logic map
PERSONA_MAP = {
    "forensic": "DFIR_Agent",
    "cybersecurity": "RedTeamer",
    "misc": "GeneralOps"
}

def route_approvals():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with TOOL_MANIFEST.open("r") as f:  # Open the manifest file
        tools = yaml.safe_load(f).get("tools", [])
    for tool in tools:
        if tool["approved"]:
            continue
        persona = PERSONA_MAP.get(tool["category"], "GeneralOps")
        with APPROVAL_LOG.open("a") as log:
            log.write(f"{timestamp},{tool['path']},{persona}\n")
            print(f"Routing [{tool['path']}]: {persona}")

if __name__ == "__main__":
    route_approvals()
    print("[✓] Approval routing completed.")
