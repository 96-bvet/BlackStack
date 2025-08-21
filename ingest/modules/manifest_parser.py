import yaml
import hashlib
import os
import datetime

QUARANTINE_DIR = os.path.expanduser("~/BlackStack/WachterEID/quarantine/")
LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/manifest_parser.log")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def hash_file(path):
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        log_event(f"Hashing failed for {path}: {e}")
        return None

def parse_manifest(path):
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        manifest_hash = hash_file(path)
        tool_name = data.get("tool_name", "unknown_tool")
        tags = data.get("tags", [])
        logic_type = data.get("logic_type", "unspecified")
        persona_hint = data.get("persona", "unassigned")

        parsed = {
            "tool_name": tool_name,
            "tags": tags,
            "logic_type": logic_type,
            "persona_hint": persona_hint,
            "manifest_hash": manifest_hash,
            "source_path": path
        }

        log_event(f"Parsed manifest: {tool_name} | Hash: {manifest_hash}")
        return parsed

    except Exception as e:
        log_event(f"Failed to parse manifest at {path}: {e}")
        quarantine_path = os.path.join(QUARANTINE_DIR, os.path.basename(path))
        os.rename(path, quarantine_path)
        log_event(f"Moved to quarantine: {quarantine_path}")
        return None
