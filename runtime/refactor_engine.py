import os
import hashlib
import datetime
from persona_loader import get_active_persona, mutation_allowed
import json
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../mutation_log.json"))

def hash_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def log_mutation(module, status, reason, original_hash, new_hash):
    entry = {
        "module": module,
        "status": status,
        "reason": reason,
        "persona": get_active_persona(),
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "original_hash": original_hash,
        "new_hash": new_hash
    }

    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                log = json.load(f)
        else:
            log = []
    except Exception:
        log = []

    log.append(entry)

    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)

def refactor_module(path, reason="mutation via CLI"):
    if not os.path.exists(path):
        print(f"[!] Refactor failed: {path} not found.")
        return False

    if not mutation_allowed(path):
        print(f"[!] Refactor blocked: persona '{get_active_persona()}' disallows mutation on {path}")
        return False

    original_hash = hash_file(path)

    try:
        with open(path, "r") as f:
            lines = f.readlines()

        mutated_lines = []
        for line in lines:
            if "DeepSeek" in line or "deepseek" in line:
                mutated_lines.append("# [REMOVED] Legacy DeepSeek binding\n")
            else:
                mutated_lines.append(line)

        with open(path, "w") as f:
            f.writelines(mutated_lines)

        new_hash = hash_file(path)

        if original_hash != new_hash:
            print(f"[✓] Mutation complete. Hash changed.")
            log_mutation(path, "mutated", reason, original_hash, new_hash)
            return True
        else:
            print(f"[-] No mutation applied. File unchanged.")
            log_mutation(path, "unchanged", reason, original_hash, new_hash)
            return False

    except Exception as e:
        print(f"[!] Refactor error: {e}")
        log_mutation(path, "error", reason, original_hash, "error")
        return False
