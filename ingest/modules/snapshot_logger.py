import os
import yaml
import datetime
import hashlib

SNAPSHOT_ROOT = os.path.expanduser("~/BlackStack/WachterEID/snapshots/")
LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/snapshot_logger.log")

def log_event(message):
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a") as log:
        log.write(f"[{timestamp}] {message}\n")

def get_snapshot_folder():
    now = datetime.datetime.now()
    folder_name = f"{now.day:02d}_{now.strftime('%b').upper()}_{now.year}"
    folder_path = os.path.join(SNAPSHOT_ROOT, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

def generate_filename(tool_name):
    timestamp = datetime.datetime.now().isoformat().replace(":", "-")
    return f"{tool_name}_{timestamp}.yaml"

def log_snapshot(tool_data, persona):
    folder = get_snapshot_folder()
    filename = generate_filename(tool_data["tool_name"])
    snapshot_path = os.path.join(folder, filename)

    snapshot = {
        "tool_name": tool_data["tool_name"],
        "tags": tool_data["tags"],
        "logic_type": tool_data["logic_type"],
        "persona": persona,
        "manifest_hash": tool_data["manifest_hash"],
        "source_path": tool_data["source_path"],
        "timestamp": datetime.datetime.now().isoformat(),
        "rollback_id": hashlib.sha256(filename.encode()).hexdigest()
    }

    try:
        with open(snapshot_path, "w") as f:
            yaml.dump(snapshot, f, sort_keys=False)
        log_event(f"Snapshot saved: {snapshot_path}")
    except Exception as e:
        log_event(f"Snapshot failed for {tool_data['tool_name']}: {e}")
