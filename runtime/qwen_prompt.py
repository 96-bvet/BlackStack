# runtime/qwen_prompt.py

import os, sys, hashlib, ast
from datetime import datetime
from models.qwen_wrapper import QwenModel
from registry import resolve_persona_by_module
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check

ROOT = os.path.expanduser("~/BlackStack/BlackStack")
SNAPSHOT_DIR = os.path.join(ROOT, "audit/snapshots")
LOG_PATH = os.path.join(ROOT, "audit/qwen_batch_log.md")

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

def log_mutation(module, goal, old_hash, new_hash, status="APPLIED"):
    with open(LOG_PATH, "a") as log:
        log.write(f"{datetime.now().isoformat()} | {module} | {goal} | {old_hash} → {new_hash} | {status}\n")

def is_valid_python(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"[✗] Syntax error in generated code for {code[:40]}...: {e}")
        return False

def run_batch_refactor(folder, goal):
    qwen = QwenModel()
    folder_path = os.path.join(ROOT, folder)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".py"):
            continue

        rel_path = os.path.join(folder, filename)
        abs_path = os.path.join(ROOT, rel_path)

        if not gatekeeper_check(rel_path):
            print(f"[✗] Mutation blocked: {rel_path}")
            log_mutation(rel_path, goal, "N/A", "N/A", "BLOCKED")
            continue

        prompt = f"Refactor {rel_path} for {goal}. Inject audit logging, persona routing, fallback logic, and gatekeeper enforcement. Return full code only. Ensure all syntax is valid Python 3.11+ and passes ast.parse()."
        response = qwen.generate(prompt)[0]["generated_text"]

        if not is_valid_python(response):
            log_mutation(rel_path, goal, "N/A", "N/A", "SYNTAX_ERROR")
            continue

        old_hash = hash_file(abs_path)
        snapshot_file(abs_path)

        with open(abs_path, "w") as f:
            f.write(response)

        new_hash = hash_file(abs_path)
        log_mutation(rel_path, goal, old_hash, new_hash)
        print(f"[✓] Refactor applied: {rel_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: $Qwen <folder> \"<refactor goal>\"")
        sys.exit(1)

    folder = sys.argv[1]
    goal = sys.argv[2]
    run_batch_refactor(folder, goal)
