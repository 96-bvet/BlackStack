# runtime/mutation_queue.py

import os, ast
from datetime import datetime
from registry import get_active_persona, get_capabilities
from runtime.persona_variants.auditpersona_v2 import gatekeeper_check
from models.qwen_wrapper import QwenModel
from runtime.router.tone_router import inject_tone

ROOT = os.path.expanduser("~/BlackStack/BlackStack")
QUEUE_PATH = os.path.join(ROOT, "audit/mutation_queue.md")

def is_valid_python(code):
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        return False

def log_queue_event(module, goal, status, reason=""):
    with open(QUEUE_PATH, "a") as log:
        log.write(f"{datetime.now().isoformat()} | {module} | {goal} | {status} | {reason}\n")

def run_mutation_queue(folder, goal):
    qwen = QwenModel()
    folder_path = os.path.join(ROOT, folder)

    for filename in os.listdir(folder_path):
        if not filename.endswith(".py"):
            continue

        rel_path = os.path.join(folder, filename)
        abs_path = os.path.join(ROOT, rel_path)

        if not gatekeeper_check(rel_path):
            log_queue_event(rel_path, goal, "BLOCKED", "Gatekeeper denied")
            continue

        tone_profile = get_capabilities().get("tone_profile", {})
        enriched_prompt = inject_tone(f"Refactor {rel_path} for {goal}", tone_profile)

        try:
            response = qwen.generate(enriched_prompt)[0]["generated_text"]
        except Exception as e:
            log_queue_event(rel_path, goal, "ERROR", str(e))
            continue

        if not is_valid_python(response):
            log_queue_event(rel_path, goal, "SYNTAX_ERROR", "Failed ast.parse()")
            continue

        with open(abs_path, "w") as f:
            f.write(response)

        log_queue_event(rel_path, goal, "APPLIED")

