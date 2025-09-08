import os
import json
from persona_loader import get_active_persona, mutation_allowed
from refactor_engine import refactor_module  # Replace with your actual mutation logic

APPROVAL_QUEUE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../approval_queue.json"))

def load_approval_queue():
    try:
        with open(APPROVAL_QUEUE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] approval_queue.json not found.")
        return []

def process_mutations():
    queue = load_approval_queue()
    if not queue:
        print("[Qwen] No approved mutations found.")
        return

    for entry in queue:
        if entry.get("status") != "approved":
            continue

        module = entry.get("module")
        reason = entry.get("reason", "no reason provided")

        if not os.path.exists(module):
            print(f"[!] Skipping: {module} not found.")
            continue

        if not mutation_allowed(module):
            print(f"[!] Skipping: mutation not allowed for {module} under persona {get_active_persona()}")
            continue

        print(f"[Qwen] Applying mutation to {module} — Reason: {reason}")
        success = refactor_module(module)

        if success:
            print(f"[✓] Mutation applied to {module}")
        else:
            print(f"[-] Mutation failed or no changes made to {module}")

if __name__ == "__main__":
    process_mutations()
