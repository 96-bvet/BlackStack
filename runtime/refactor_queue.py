# runtime/refactor_queue.py

import os, hashlib
from datetime import datetime
from registry import resolve_persona_by_module
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check
from models.qwen_wrapper import QwenModel

ROOT_PATH = os.path.expanduser("~/BlackStack/BlackStack")
SNAPSHOT_DIR = os.path.join(ROOT_PATH, "audit/snapshots")
LOG_PATH = os.path.join(ROOT_PATH, "audit/refactor_queue.md")

TASKS = [
    {
        "module": "runtime/router/tone_router.py",
        "goal": "fallback logic, persona escalation, audit logging"
    },
    {
        "module": "runtime/finalize_ai.py",
        "goal": "rollback hooks, persona resolution, audit traceability"
    },
    {
        "module": "models/qwen_wrapper.py",
        "goal": "refactor mode injection, reference module loading, audit trace logging"
    }
]

def hash_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def snapshot_file(path):
    if not os.path.exists(SNAPSHOT_DIR):
        os.makedirs(SNAPSHOT_DIR)
    filename = os.path.basename(path)
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"{filename}.bak")
    with open(path, "rb") as src, open(snapshot_path, "wb") as dst:
        dst.write(src.read())
    return snapshot_path

def log_queue_event(module, goal, old_hash, new_hash, status):
    with open(LOG_PATH, "a") as log:
        log.write(f"{datetime.now().isoformat()} | {module} | {goal} | {old_hash} → {new_hash} | {status}\n")

def run_refactor_queue():
    qwen = QwenModel()

    for task in TASKS:
        module_path = task["module"]
        goal = task["goal"]
        abs_path = os.path.join(ROOT_PATH, module_path)

        try:
            if not gatekeeper_check(module_path):
                log_queue_event(module_path, goal, "N/A", "N/A", "BLOCKED")
                continue

            prompt = f"Refactor {module_path} for {goal}. Inject audit logging, persona escalation, fallback logic, and gatekeeper enforcement. Return full code only."
            response = qwen.generate(prompt)[0]["generated_text"]

            old_hash = hash_file(abs_path)
            snapshot_file(abs_path)

            with open(abs_path, "w") as f:
                f.write(response)

            new_hash = hash_file(abs_path)
            log_queue_event(module_path, goal, old_hash, new_hash, "APPLIED")
            print(f"[✓] Refactor applied: {module_path}")

        except Exception as e:
            log_queue_event(module_path, goal, "N/A", "N/A", f"ERROR: {type(e).__name__} — {str(e)}")
            print(f"[✗] Refactor failed: {module_path} — {e}")

if __name__ == "__main__":
    run_refactor_queue()
