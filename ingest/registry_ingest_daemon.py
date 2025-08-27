import os
import time
import yaml
from datetime import datetime
from modules.manifest_parser import parse_manifest
from modules.persona_router import match_persona
from modules.approval_gate import trigger_approval
from modules.snapshot_logger import log_snapshot
from modules.refactor_engine import suggest_split
from modules.registry_updater import update_registry

BASE_DIR = "WachterEID"
MANIFEST_DIR = os.path.join(BASE_DIR, "manifests", "generated")
LOG_DIR = os.path.join(BASE_DIR, "logs", "registry_ingest")


def ensure_directories():
    os.makedirs(MANIFEST_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

SCAN_INTERVAL = 300  # seconds

def log_action(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, f"ingest_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_path, "a") as log:
        log.write(f"[{datetime.now().isoformat()}] {message}\n")

def ingest_manifest(manifest_path, dry_run=False):
    tool_data = parse_manifest(manifest_path)
    if not tool_data:
        log_action(f"Failed to parse {manifest_path}")
        return

    persona = match_persona(tool_data)
    approved = trigger_approval(tool_data, persona)

    if not approved:
        log_action(f"Approval denied for {tool_data['tool_name']}")
        return

    refactored_list = suggest_split(tool_data)

    for entry in refactored_list:
        if dry_run:
            log_action(f"[DRY RUN] Would ingest {entry['tool_name']} for {persona}")
        else:
            update_registry(entry, persona)
            log_snapshot(entry, persona)
            log_action(f"Ingested {entry['tool_name']} for {persona}")

def daemon_loop(dry_run=False):
    ensure_directories()
    seen = set()
    while True:
        for file in os.listdir(MANIFEST_DIR):
            path = os.path.join(MANIFEST_DIR, file)
            if path not in seen and file.endswith(".yaml"):
                ingest_manifest(path, dry_run=dry_run)
                seen.add(path)
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    daemon_loop(dry_run=False)
