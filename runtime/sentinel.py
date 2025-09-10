#!/usr/bin/env python3
"""
Sentinel client for Qwen daemon + mutator
- Connects to localhost:9090
- Exposes: --mutate, --mutate-tree, --mutate-batched
"""

import sys
import os
import socket
import time

# Path setup for sibling modules/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # up from runtime/ to BlackStack/
MODULES_DIR = os.path.join(BASE_DIR, "modules")
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

try:
    import qwen_mutator
except ImportError as e:
    print(f"[ERROR] Could not import qwen_mutator from {MODULES_DIR}: {e}")
    sys.exit(1)

# Qwen daemon connection
QWEN_HOST = "127.0.0.1"
QWEN_PORT = 9090
CONNECT_TIMEOUT = 5
RECV_TIMEOUT = 180
MAX_RESPONSE_MB = 8

def qwen_mutate(prompt: str) -> str:
    """Send a prompt to the Qwen daemon and return the response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(CONNECT_TIMEOUT)
            s.connect((QWEN_HOST, QWEN_PORT))
            s.sendall(prompt.encode("utf-8", errors="ignore"))

            s.settimeout(RECV_TIMEOUT)
            chunks, total_bytes, start_time = [], 0, time.time()

            while True:
                try:
                    data = s.recv(8192)
                    if not data:
                        break
                    chunks.append(data)
                    total_bytes += len(data)
                    if total_bytes > MAX_RESPONSE_MB * 1024 * 1024:
                        chunks.append(b"\n[WARN] Response truncated: exceeded safety cap.")
                        break
                except socket.timeout:
                    chunks.append(b"\n[ERROR] Timed out waiting for daemon response.")
                    break
                if time.time() - start_time > RECV_TIMEOUT:
                    chunks.append(b"\n[ERROR] Overall receive time exceeded limit.")
                    break

            return b"".join(chunks).decode("utf-8", errors="ignore")

    except ConnectionRefusedError:
        return "[ERROR] Qwen daemon is not running. Start qwen_daemon and retry."
    except ConnectionResetError:
        return "[ERROR] Qwen daemon closed the connection unexpectedly. Check daemon logs."
    except socket.timeout:
        return "[ERROR] Connection attempt to Qwen daemon timed out."
    except Exception as e:
        return f"[ERROR] Unexpected socket error: {e}"

def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--mutate":
        target_file = sys.argv[2]
        instructions = sys.argv[3] if len(sys.argv) > 3 else "Make it audit-safe, ethical, and forensically sound."
        result = qwen_mutator.mutate_code(target_file, instructions)
        print(result)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--mutate-tree":
        instructions = sys.argv[2] if len(sys.argv) > 2 else "Integrate modules, ensure audit safety and forensic traceability."
        qwen_mutator.mutate_tree(instructions)

    elif len(sys.argv) >= 2 and sys.argv[1] == "--mutate-batched":
        instructions = sys.argv[2] if len(sys.argv) > 2 else "Integrate all modules, ensure audit safety and forensic traceability."
        qwen_mutator.mutate_tree_batched(instructions)

    elif len(sys.argv) >= 2:
        prompt = sys.argv[1]
        print(f"[INFO] Sending prompt to Qwen daemon: {prompt!r}")
        result = qwen_mutate(prompt)
        print(result if result.startswith("[ERROR]") else f"[OK] Daemon responded:\n\n{result}")

    else:
        print(f"Usage:\n"
              f"  {sys.argv[0]} '<prompt text>'\n"
              f"  {sys.argv[0]} --mutate <relative_path_to_file> [instructions]\n"
              f"  {sys.argv[0]} --mutate-tree [instructions]\n"
              f"  {sys.argv[0]} --mutate-batched [instructions]")

if __name__ == "__main__":
    main()
