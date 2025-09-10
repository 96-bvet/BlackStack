#!/usr/bin/env python3
import os, subprocess, hashlib, time, importlib.util, sys, json
from pathlib import Path
from socket import socket

BASE_DIR = "/home/blackhawk63/BlackStack/BlackStack"
LOG_PATH = "/mnt/unified/BlackStack/logs/mutation_log.json"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def integrity_check():
    print("\n[1] Integrity Sweep")
    if not os.path.isfile(LOG_PATH):
        print("  [WARN] No mutation log found.")
        return
    with open(LOG_PATH) as f:
        lines = f.readlines()
    latest = {}
    for line in lines:
        parts = line.strip().split("|")
        if len(parts) >= 4:
            latest[parts[1]] = parts[3]
    for path, expected_hash in latest.items():
        if os.path.isfile(path):
            current_hash = ssha256(path)
            if current_hash != expected_hash:
                print(f"  [ERROR] Hash mismatch for {path}. Expected {expected_hash}, got {current_hash}")
            else:
                print(f"  [OK] Hash match for {path}")
        else:
            print(f"  [ERROR] File missing: {path}")
    print("\n[2] Persona Check")
    personas = [f.stem for f in Path(BASE_DIR).glob("**/*persona*.json")]
    for persona in personas:
        print(f"  [INFO] Found persona: {persona}")
    print("\n[3] Dependency Check")
    required_modules = ["numpy", "torch", "tensorflow"]
    for module in required_modules:
        spec = importlib.util.find_spec(module)
        if spec is None:
            print(f"  [ERROR] Missing dependency: {module}")
        else:
            print(f"  [OK] Found dependency: {module}")
    print("\n[4] Execution Check")
    for script in ["sentinel_core.py", "mutation_log.json"]:
        try:
            subprocess.run([sys.executable, os.path.join(BASE_DIR, script)], check=True)
            print(f"  [OK] Executed {script} successfully")
        except Exception as e:
            print(f"  [ERROR] Failed to execute {script}: {e}")
    print("\n[5] Socket Check")
    try:
        s = socket()
        s.connect(("localhost", 9090))
        s.close()
        print("  [OK] Connected to daemon socket at localhost:9090")
    except Exception as e:
        print(f"  [ERROR] Daemon socket connection failed: {e}")
    print("\nSelf-check complete.")
