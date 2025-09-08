import os
import yaml
import argparse
import hashlib
from datetime import datetime

def hash_file(path):
    if not os.path.exists(path):
        return "N/A"
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()

def log_result(name, status, reason, registry_path, log_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hash_val = hash_file(registry_path)
    with open(log_path, "a") as log:
        log.write(f"{timestamp},{name},{hash_val},{status},{reason}\n")

def validate_persona(entry):
    required_fields = ["name", "persona", "capabilities"]
    for field in required_fields:
        if field not in entry:
            return False, f"Missing field: {field}"
    return True, "Valid schema"

def scan_registry(registry_path, log_path):
    if not os.path.exists(registry_path):
        print(f"[!] Registry file not found: {registry_path}")
        return

    try:
        with open(registry_path, "r") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse registry: {e}")
        return

    personas = data.get("personas", {})
    if not isinstance(personas, dict):
        print("[!] Registry format invalid: 'personas' should be a dictionary.")
        return

    valid_count = 0
    invalid_count = 0

    for name, entry in personas.items():
        entry["name"] = name  # Inject name for validation
        valid, reason = validate_persona(entry)
        status = "valid" if valid else "invalid"
        log_result(name, status, reason, registry_path, log_path)
        print(f"[{status.upper()}] {name}: {reason}")
        if valid:
            valid_count += 1
        else:
            invalid_count += 1

    print(f"\n[✓] Scan complete: {valid_count} valid, {invalid_count} invalid.")

def main():
    parser = argparse.ArgumentParser(description="Qwen Registry Builder (Centralized)")
    parser.add_argument("--registry", type=str, required=True, help="Path to persona_registry.yaml")
    parser.add_argument("--log", type=str, default="registry_log.csv", help="Path to output log file")
    args = parser.parse_args()

    scan_registry(args.registry, args.log)

if __name__ == "__main__":
    main()
