import os
import json
import yaml
import argparse
import hashlib
from datetime import datetime

def hash_file(path):
    if not os.path.exists(path):
        return "N/A"
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()

def log_result(manifest_path, status, reason, log_path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hash_val = hash_file(manifest_path)
    with open(log_path, "a") as log:
        log.write(f"{timestamp},{manifest_path},{hash_val},{status},{reason}\n")

def validate_manifest(manifest):
    required_fields = ["name", "persona", "capabilities"]
    for field in required_fields:
        if field not in manifest:
            return False, f"Missing field: {field}"
    return True, "Valid schema"

def scan_directory(input_dir, log_path):
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".yaml") or file.endswith(".json"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r") as f:
                        data = yaml.safe_load(f) if file.endswith(".yaml") else json.load(f)
                    valid, reason = validate_manifest(data)
                    status = "valid" if valid else "invalid"
                    log_result(full_path, status, reason, log_path)
                    print(f"[{status.upper()}] {file}: {reason}")
                except Exception as e:
                    log_result(full_path, "error", str(e), log_path)
                    print(f"[ERROR] {file}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Qwen Registry Builder")
    parser.add_argument("--input", type=str, required=True, help="Directory containing persona manifests")
    parser.add_argument("--log", type=str, default="registry_log.csv", help="Path to output log file")
    args = parser.parse_args()

    scan_directory(args.input, args.log)

if __name__ == "__main__":
    main()
