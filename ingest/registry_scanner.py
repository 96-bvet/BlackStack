import os
import hashlib
import yaml
from datetime import datetime

SCAN_PATHS = ["/usr/bin", "/opt", "/usr/share"]
OUTPUT_DIR = "WachterEID/manifests/generated/"
LOG_DIR = "WachterEID/logs/registry_scanner/"

RED_TAGS = ["hydra", "sqlmap", "john", "metasploit"]
BLUE_TAGS = ["nmap", "tcpdump", "wireshark", "clamav"]

def hash_file(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def classify_tool(name):
    if name in RED_TAGS:
        return "red_team"
    elif name in BLUE_TAGS:
        return "blue_team"
    return "unknown"

def generate_manifest(tool_path):
    tool_name = os.path.basename(tool_path)
    tool_hash = hash_file(tool_path)
    tag = classify_tool(tool_name)

    manifest = {
        "tool_name": tool_name,
        "source_path": tool_path,
        "tags": [tag],
        "persona_hint": "Exploit" if tag == "red_team" else "Defense",
        "hash": f"sha256:{tool_hash}",
        "description": f"Auto-generated manifest for {tool_name}"
    }

    return manifest

def scan_and_generate():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

    log_file = os.path.join(LOG_DIR, f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    with open(log_file, "w") as log:
        for path in SCAN_PATHS:
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        manifest = generate_manifest(full_path)
                        out_path = os.path.join(OUTPUT_DIR, f"{manifest['tool_name']}.yaml")
                        with open(out_path, "w") as f:
                            yaml.dump(manifest, f)
                        log.write(f"{manifest['tool_name']} → {manifest['hash']}\n")

if __name__ == "__main__":
    scan_and_generate()
