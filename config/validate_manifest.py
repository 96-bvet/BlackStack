from pathlib import Path
import hashlib
import yaml
from datetime import datetime

HOME = Path.home()
TOOL_MANIFEST = HOME / "BlackStack" / "WachterEID" / "config" / "tool_manifest.yaml"
AUDIT_DIR = HOME / "BlackStack" / "WachterEID" / "audit"
AUDIT_LOG = AUDIT_DIR / "manifest_validation.log"

def hash_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def validate_manifest():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    issues = []

    # Ensure audit directory and log file exist
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if not AUDIT_LOG.exists():
        AUDIT_LOG.touch()

    with TOOL_MANIFEST.open("r") as f:
        manifest = yaml.safe_load(f)

    tools = manifest.get("tools", [])

    for tool in tools:
        full_path = HOME / "cai" / tool["path"]
        if not full_path.exists():
            issues.append(f"[✗] Missing file: {tool['path']}")
            continue

        actual_hash = hash_file(full_path)
        if actual_hash != tool["hash"]:
            issues.append(f"[⚠] Hash mismatch: {tool['path']}")
        if not tool.get("approved", False):
            issues.append(f"[!] Unapproved tool: {tool['path']}")

    with AUDIT_LOG.open("a") as log:
        log.write(f"\n# Manifest Validation — {timestamp}\n")
        for issue in issues:
            log.write(issue + "\n")

    print(f"[✓] Validation complete. {len(issues)} issues logged to manifest_validation.log")

if __name__ == "__main__":
    validate_manifest()
