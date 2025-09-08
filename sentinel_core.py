import os
import json
import yaml
import hashlib
from datetime import datetime
from transformers import AutoModelForCausalLM, AutoTokenizer
import psutil, os

def is_file_in_use(path):
    for proc in psutil.process_iter(['open_files']):
        try:
            for f in proc.info['open_files'] or []:
                if os.path.samefile(f.path, path):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

# Load Qwen model
model_id = "Qwen/Qwen2.5-14B"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True
)

# Paths
MANIFEST_PATH = "sentinel_manifest.yaml"
LOG_PATH = "action_log.csv"
QUEUE_PATH = "approval_queue.json"

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

def queue_mutation(module, reason, cluster="unassigned", role="unknown"):
    hash_val = hash_file(module)
    entry = {
        "module": module,
        "reason": reason,
        "hash": hash_val,
        "cluster": cluster,
        "role": role,
        "status": "pending"
    }
    if os.path.exists(QUEUE_PATH):
        with open(QUEUE_PATH, "r") as f:
            queue = json.load(f)
    else:
        queue = []
    queue.append(entry)
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f, indent=2)
def enqueue_mutation(file_path, reason, persona):
    log_action(file_path, reason, status="approved", persona=persona)
    run_mutation(file_path, reason)  # directly invoke Qwen

def parse_manifest():
    with open(MANIFEST_PATH, "r") as f:
        manifest = yaml.safe_load(f)

    for mod in manifest.get("modules", []):
        rel_path = mod["path"]
        abs_path = os.path.abspath(rel_path)

        if os.path.exists(abs_path):
            log_action(abs_path, "Context assimilation", "observed")
            queue_mutation(
                module=abs_path,
                reason="Passive refactor proposal",
                cluster=mod.get("cluster", "unassigned"),
                role=mod.get("role", "unknown")
            )
        else:
            print(f"[!] Skipped: {abs_path} not found.")

def generate_response(prompt):
    input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(model.device)
    output = model.generate(input_ids, max_new_tokens=512)
    return tokenizer.decode(output[0], skip_special_tokens=True)
for file_path in target_files:
    if is_file_in_use(file_path):
        log_action(file_path, "Skipped: file in use", status="skipped")
        continue
    run_mutation(file_path, reason)

# Entry point
if __name__ == "__main__":
    print("[Sentinel] Activating Qwen core...")
    parse_manifest()
    print("[Sentinel] Context map parsed. Approval queue populated.")
