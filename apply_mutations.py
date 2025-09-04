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

def refactor_deepseek_to_qwen(file_path):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return False

    with open(file_path, "r") as f:
        lines = f.readlines()

    refactored = []
    replaced = False

    for line in lines:
        lower = line.lower()

        # Match DeepSeek logic in any form
        if "deepseek" in lower:
            if "importlib.util.spec_from_file_location" in line:
                refactored.append("# [Qwen Refactor] Replacing dynamic DeepSeek loader\n")
                refactored.append("from transformers import AutoModelForCausalLM, AutoTokenizer\n")
                refactored.append("model_id = \"Qwen/Qwen2.5-14B\"\n")
                refactored.append("tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)\n")
                refactored.append("model = AutoModelForCausalLM.from_pretrained(model_id, device_map=\"auto\", trust_remote_code=True)\n")
                replaced = True
                continue
            elif "run_deepseek_v2" in line or "ds_infer" in line:
                refactored.append("# [Qwen Refactor] Replacing DeepSeek runtime call\n")
                refactored.append("response = model.generate_response(input_text)\n")
                replaced = True
                continue
            elif "argparse" in line and "DeepSeek" in line:
                refactored.append("# [Qwen Refactor] Updating CLI description\n")
                refactored.append("parser = argparse.ArgumentParser(description=\"Qwen Core Refactor Engine\")\n")
                replaced = True
                continue
            elif "variant" in lower and "\"deepseek\"" in lower:
                refactored.append("# [Qwen Refactor] Replacing variant config\n")
                refactored.append("variant = \"qwen\"\n")
                replaced = True
                continue
            else:
                # Generic DeepSeek reference
                refactored.append("# [Qwen Refactor] Legacy DeepSeek reference detected\n")
                refactored.append("from transformers import AutoModelForCausalLM, AutoTokenizer\n")
                refactored.append("model_id = \"Qwen/Qwen2.5-14B\"\n")
                refactored.append("tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)\n")
                refactored.append("model = AutoModelForCausalLM.from_pretrained(model_id, device_map=\"auto\", trust_remote_code=True)\n")
                replaced = True
                continue
        refactored.append(line)

    if not replaced:
        print(f"[-] No DeepSeek logic found in {file_path}. Skipping.")
        return False

    # Backup original
    backup_path = file_path + ".bak"
    with open(backup_path, "w") as f:
        f.writelines(lines)

    # Write refactored
    with open(file_path, "w") as f:
        f.writelines(refactored)

    print(f"[+] Refactored: {file_path}")
    return True

def apply_mutations():
    if not os.path.exists(QUEUE_PATH):
        print("[!] No approval queue found.")
        return

    with open(QUEUE_PATH, "r") as f:
        queue = json.load(f)

    updated_queue = []
    for entry in queue:
        if entry.get("status") != "approved":
            updated_queue.append(entry)
            continue

        module = entry["module"]
        reason = entry["reason"]

        if "deepseek" not in reason.lower():
            updated_queue.append(entry)
            continue

        if not os.path.exists(module):
            print(f"[!] Skipped: {module} not found.")
            log_action(module, reason, "skipped")
            entry["status"] = "skipped"
            updated_queue.append(entry)
            continue

        success = refactor_deepseek_to_qwen(module)
        if success:
            log_action(module, reason, "applied")
            entry["status"] = "completed"
        else:
            log_action(module, reason, "skipped")
            entry["status"] = "skipped"

        updated_queue.append(entry)

    with open(QUEUE_PATH, "w") as f:
        json.dump(updated_queue, f, indent=2)

    print("\n[✓] Mutation cycle complete. All actions logged.")

if __name__ == "__main__":
    apply_mutations()
