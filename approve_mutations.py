import json
import os
import hashlib
from datetime import datetime

QUEUE_PATH = "approval_queue.json"
LOG_PATH = "action_log.csv"

def hash_file(path):
    if not os.path.exists(path):
        return "N/A"
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()

def log_action(module, reason, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hash_val = hash_file(module)
    with open(LOG_PATH, "a") as log:
        log.write(f"{timestamp},{module},{hash_val},{reason},{status}\n")

def approve_queue(auto=True):
    if not os.path.exists(QUEUE_PATH):
        print("No approval queue found.")
        return

    with open(QUEUE_PATH, "r") as f:
        queue = json.load(f)

    if not queue:
        print("Approval queue is empty.")
        return

    for i, entry in enumerate(queue):
        module = entry["module"]
        reason = entry["reason"]
        hash_val = hash_file(module)

        print(f"\n[{i}] Module: {module}")
        print(f"     Reason: {reason}")
        print(f"     Hash: {hash_val}")

        if auto:
            print("     Auto-approving...")
            entry["status"] = "approved"
            log_action(module, reason, "approved")
        else:
            decision = input("Approve this mutation? (y/n): ").strip().lower()
            if decision == "y":
                entry["status"] = "approved"
                log_action(module, reason, "approved")
            else:
                entry["status"] = "rejected"
                log_action(module, reason, "rejected")

    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)

    print("\n[✓] Approval process complete. All decisions logged.")

if __name__ == "__main__":
    approve_queue(auto=True)
