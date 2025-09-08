#!/usr/bin/env python3
import os
import psutil
from socket import socket
import hashlib
import time
from pathlib import Path

BASE_DIR = "/home/blackhawk63/BlackStack/BlackStack"
LOG_PATH = "/mnt/unified/BlackStack/logs/mutation_log.json"

def is_file_in_use(path):
    try:
        for proc in psutil.process_iter(['open_files']):
            try:
                for f in proc.info['open_files'] or []:
                    try:
                        # Skip if the reported file no longer exists
                        if not f.path or not os.path.exists(f.path):
                            continue
                        if os.path.samefile(f.path, path):
                            return True
                    except (FileNotFoundError, OSError):
                        # File vanished or can't be stat'ed — ignore
                        continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"[WARN] is_file_in_use check failed: {e}")
    return False

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def qwen_mutate(task: str):
    s = socket()
    s.connect(("localhost", 9090))
    s.send(task.encode())
    response = s.recv(5_000_000).decode(errors="ignore")  # large buffer
    s.close()
    return response

# Step 1: Gather all eligible files into one big context
file_data = []
for root, dirs, files in os.walk(BASE_DIR):
    for fname in files:
        if fname.endswith((".py", ".rs", ".cpp", ".json")):
            fpath = os.path.join(root, fname)
            if is_file_in_use(fpath):
                print(f"[SKIP] {fpath} — file in use")
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                file_data.append(f"--- FILE: {fpath} ---\n{content}")
            except Exception as e:
                print(f"[ERROR] Could not read {fpath}: {e}")

full_context = "\n".join(file_data)

# Step 2: Build holistic mutation prompt
prompt = f"""
You are Qwen, the sovereign mutation agent for Sentinel.
Scan the following complete BlackStack/BlackStack codebase:

{full_context}

Thread all modules together into a finalized Sentinel shell with:
- Fully integrated voice_shell with tone_infer, fallback.rs, and persona_map.json
- Proper Rust/Python/C++ FFI bindings
- Persona routing and escalation logic
- Fallback detection and logging
- No external API calls — local-only execution
- Mutation-safe, audit-logged architecture

Return the FULL patched code for each file in the SAME format:
--- FILE: <absolute path> ---
<patched file content>
"""

print("[Qwen] Sending full codebase to daemon...")
result = qwen_mutate(prompt)

# Step 3: Parse Qwen's output and write back changes
current_file = None
buffer = []

def commit_file(path, content_lines):
    if not path or not os.path.isfile(path):
        print(f"[SKIP WRITE] Invalid or missing file: {path}")
        return
    if not content_lines:
        print(f"[SKIP WRITE] No content for: {path}")
        return
    before_hash = sha256(path)
    with open(path, "w", encoding="utf-8") as out:
        out.write("\n".join(content_lines))
    after_hash = sha256(path)
    with open(LOG_PATH, "a") as log:
        log.write(f"{time.time()}|{path}|{before_hash}|{after_hash}|approved\n")
    print(f"[UPDATED] {path}")

for line in result.splitlines():
    if line.startswith("--- FILE: "):
        # Commit previous file if any
        if current_file and buffer:
            commit_file(current_file, buffer)
        # Start new file
        current_file = line.replace("--- FILE: ", "").strip()
        if current_file.endswith(" ---"):
            current_file = current_file[:-4].strip()
        buffer = []
    else:
        buffer.append(line)

# Commit last file
if current_file and buffer:
    commit_file(current_file, buffer)

print("[DONE] Sentinel shell finalized.")
