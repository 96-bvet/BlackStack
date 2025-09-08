# runtime/refactor_module.py

import os, sys, argparse, hashlib, ast
from datetime import datetime
from registry import resolve_persona_by_module
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check
from models.qwen_wrapper import QwenModel

ROOT_PATH = os.path.expanduser("~/BlackStack/BlackStack")
SNAPSHOT_DIR = os.path.join(ROOT_PATH, "audit/snapshots")
LOG_PATH = os.path.join(ROOT_PATH, "audit/refactor_log.md")

def is_valid_python(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        print(f"[Syntax Error] {e}")
        return False

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

def log_refactor(module, old_hash, new_hash):
    with open(LOG_PATH, "a") as log:
        log.write(f"{datetime.now().isoformat()} | {module} | {old_hash} → {new_hash}\n")

def apply_refactor(module_path, refactor_goal):
    abs_path = os.path.join(ROOT_PATH, module_path)
    persona_data = resolve_persona_by_module(module_path)
    persona = persona_data["persona"]

    if not is_valid_python(response):
        print (f"[✗] Refactor skipped due to syntax error in: {module_path}")
        log_refactor(module_path, "N/A", "N/A", "SYNTAX_ERROR")
        return

    if not gatekeeper_check(module_path):
        raise PermissionError(f"[Gatekeeper] Mutation blocked for {module_path}")

    qwen = QwenModel()
    prompt = f"Refactor {module_path} for {refactor_goal}. Inject audit logging, persona escalation, fallback logic, and gatekeeper enforcement. Return full code only."
    response = qwen.generate(prompt)[0]["generated_text"]

    old_hash = hash_file(abs_path)
    snapshot_file(abs_path)

    with open(abs_path, "w") as f:
        f.write(response)

    new_hash = hash_file(abs_path)
    log_refactor(module_path, old_hash, new_hash)
    print(f"[Refactor Applied] {module_path} | {old_hash} → {new_hash}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply Qwen-powered refactor to a module.")
    parser.add_argument("--module", required=True, help="Relative path to the module (e.g. runtime/router/tone_router.py)")
    parser.add_argument("--goal", required=True, help="Refactor goal description")
    args = parser.parse_args()

    apply_refactor(args.module, args.goal)
