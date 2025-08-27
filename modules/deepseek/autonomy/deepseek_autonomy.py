import os
import json
import hashlib
import datetime
import shutil

# === CONFIG ===
APPROVAL_QUEUE = os.path.expanduser("~/WachterEID/modules/deepseek/autonomy/approval_queue.json")
ACTION_LOG = os.path.expanduser("~/WachterEID/modules/deepseek/autonomy/action_log.csv")
ROLLBACK_DIR = os.path.expanduser("~/WachterEID/modules/deepseek/autonomy/rollback_snapshots/")
REGISTRY_INDEX = os.path.expanduser("~/WachterEID/modules/deepseek/autonomy/registry_index.yaml")

# === CORE ===
def propose_patch(module_name, reason, patch_script):
    timestamp = datetime.datetime.utcnow().isoformat()
    patch_hash = hashlib.sha256(patch_script.encode()).hexdigest()
    entry = {
        "module": module_name,
        "reason": reason,
        "hash": patch_hash,
        "timestamp": timestamp,
        "status": "pending",
        "script": patch_script
    }
    append_to_queue(entry)
    log_action(entry)
    create_snapshot(module_name)

def append_to_queue(entry):
    queue = []
    if os.path.exists(APPROVAL_QUEUE):
        with open(APPROVAL_QUEUE, "r") as f:
            queue = json.load(f)
    queue.append(entry)
    with open(APPROVAL_QUEUE, "w") as f:
        json.dump(queue, f, indent=2)

def log_action(entry):
    header = "timestamp,module,hash,reason,status\n"
    line = f"{entry['timestamp']},{entry['module']},{entry['hash']},{entry['reason']},{entry['status']}\n"
    if not os.path.exists(ACTION_LOG):
        with open(ACTION_LOG, "w") as f:
            f.write(header)
    with open(ACTION_LOG, "a") as f:
        f.write(line)

def create_snapshot(module_name):
    src_path = os.path.expanduser(f"~/WachterEID/modules/{module_name}")
    if os.path.exists(src_path):
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(ROLLBACK_DIR, f"{module_name}_{timestamp}")
        shutil.copytree(src_path, dest_path)

# === EXECUTION ===
def execute_approved_patches():
    if not os.path.exists(APPROVAL_QUEUE):
        return
    with open(APPROVAL_QUEUE, "r") as f:
        queue = json.load(f)
    new_queue = []
    for entry in queue:
        if entry["status"] == "approved":
            apply_patch(entry)
            entry["status"] = "executed"
        new_queue.append(entry)
    with open(APPROVAL_QUEUE, "w") as f:
        json.dump(new_queue, f, indent=2)

def apply_patch(entry):
    module_path = os.path.expanduser(f"~/WachterEID/modules/{entry['module']}/patch.py")
    with open(module_path, "w") as f:
        f.write(entry["script"])
    os.system(f"python3 {module_path}")

# === DIAGNOSTICS ===
def scan_for_missing_modules():
    expected = ["persona_router", "registry_indexer", "rollback_manager"]
    found = os.listdir(os.path.expanduser("~/WachterEID/modules/"))
    missing = [m for m in expected if m not in found]
    for m in missing:
        reason = f"Missing expected module: {m}"
        patch_script = f"# Placeholder for {m} module\nprint('Initializing {m}')"
        propose_patch(m, reason, patch_script)

# === ENTRYPOINT ===
if __name__ == "__main__":
    scan_for_missing_modules()
    execute_approved_patches()
