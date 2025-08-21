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
    with TOOL_MANIFEST.open("r") as f:
        manifest = yaml.safe_load(f)

    tools = manifest.get("tools", [])
    routed = []

    for tool in tools:
        if not tool.get("approved", False):
            persona = PERSONA_MAP.get(tool.get("category", "misc"), "GeneralOps")
            routed.append({
                "name": tool["name"],
                "path": tool["path"],
                "category": tool["category"],
                "persona": persona,
                "hash": tool["hash"]
            })

    # Log routed approvals
    APPROVAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    with APPROVAL_LOG.open("a") as log:
        log.write(f"\n# Approval Routing — {timestamp}\n")
        for entry in routed:
            log.write(f"[→] {entry['name']} → {entry['persona']} ({entry['category']})\n")

    print(f"[✓] Routed {len(routed)} tools to persona approval queue.")

if __name__ == "__main__":
    route_approvals()
