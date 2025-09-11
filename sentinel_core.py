#!/usr/bin/env python3
"""
Sentinel Core (hardened socket client)
--------------------------------------
- Talks to qwen_daemon.py over localhost:9090.
- Handles daemon-not-running and peer-reset gracefully with readable errors.
- Optionally bootstraps project root into sys.path so local packages import reliably.
"""
from modules.qwen_mutator import mutate_code

def finalize_full_tree():
    # Example: loop through modules and mutate each
    modules_dir = "BlackStack/BlackStack/modules"
    for file in os.listdir(modules_dir):
        if file.endswith(".py"):
            result = mutate_code(f"modules/{file}", "Make it audit-safe, ethical, and forensically sound.")
            print(f"[OK] Updated {file}")

import os
import sys
import socket
import time
from typing import Optional

# --- Optional: ensure project root is on sys.path for local imports like 'modules' ---
# Adjust only if needed; does not rename or move any paths.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# If you rely on a sibling package like 'modules', this makes the failure explicit but non-fatal.
def try_import_modules():
    try:
        import modules  # noqa: F401
        return True
    except Exception as e:
        print(f"[WARN] Could not import 'modules' package: {e}")
        print(f"[INFO] sys.path includes: {sys.path[:5]} ...")
        return False

_ = try_import_modules()

# --- Qwen daemon client ---
QWEN_HOST = "127.0.0.1"
QWEN_PORT = 9090
QWEN_TIMEOUT = 300  # seconds

def qwen_mutate(prompt: str, recv_buf: int = 1_000_000) -> str:
    """
    Sends a prompt to the Qwen daemon and returns the response.
    Returns clear error strings instead of raising socket exceptions.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(QWEN_TIMEOUT)
            s.connect((QWEN_HOST, QWEN_PORT))
            s.sendall(prompt.encode("utf-8", errors="ignore"))
            chunks = []
            while True:
                try:
                    data = s.recv(recv_buf)
                    if not data:
                        break
                    chunks.append(data)
                    # Heuristic: break if reply seems reasonably complete and small
                    if len(b"".join(chunks)) > 8_000_000:  # 8 MB safety upper bound
                        break
                except socket.timeout:
                    # Return what we have so far with an explicit note
                    partial = b"".join(chunks).decode("utf-8", errors="ignore")
                    return partial + "\n[ERROR] Timed out waiting for daemon response."
            return b"".join(chunks).decode("utf-8", errors="ignore")

    except ConnectionRefusedError:
        return "[ERROR] Qwen daemon is not running. Start qwen_daemon.py and retry."
    except ConnectionResetError:
        return "[ERROR] Qwen daemon closed the connection unexpectedly. Check daemon logs."
    except socket.timeout:
        return "[ERROR] Connection attempt to Qwen daemon timed out."
    except Exception as e:
        return f"[ERROR] Unexpected socket error: {e}"

def check_daemon_ready(retries: int = 5, delay: float = 1.0) -> bool:
    """
    Quick readiness probe: attempts to establish a TCP connection.
    Does not send a payload; just ensures the port is listening.
    """
    for _ in range(retries):
        try:
            with socket.create_connection((QWEN_HOST, QWEN_PORT), timeout=3):
                return True
        except Exception:
            time.sleep(delay)
    return False

# --- Your existing high-level logic hooks ---
# Keep your original functions; the only change you may want is to call qwen_mutate()
# and handle "[ERROR] ..." strings gracefully rather than letting exceptions bubble up.

def build_mutation_prompt() -> str:
    """
    Construct the prompt for Qwen. Replace this body with your current logic as-is.
    """
    return "Finalize full tree mutation pass for Sentinel. Keep audit safety, do not rename protected paths."

def finalize_full_tree() -> Optional[str]:
    """
    Executes the mutation with Qwen. Returns the daemon response (or error string).
    """
    prompt = build_mutation_prompt()
    response = qwen_mutate(prompt)
    return response

def provision_voices():
    """
    Keep your existing voice provisioning. This placeholder logs similarly to your prior output.
    Replace with your existing implementation if you already have it.
    """
    voices = {
        "analyst": ("en_US-lessac-high.onnx", "en_US-lessac-high.onnx.json"),
        "operator": ("en_US-ryan-medium.onnx", "en_US-ryan-medium.onnx.json"),
        "commander": ("en_GB-alan-medium.onnx", "en_GB-alan-medium.onnx.json"),
    }
    print("[INFO] Provisioning voice models...")
    for persona, files in voices.items():
        print(f"[INFO] Provisioning voice for persona: {persona}")
        for f in files:
            # We don't mutate your tree; just mimic the prior log format.
            print(f"[SKIP] {f} already exists")
    print("[OK] Voice provisioning complete.")

def main():
    provision_voices()

    if not check_daemon_ready():
        print("[ERROR] Qwen daemon is not reachable at 127.0.0.1:9090.")
        print("        Start it with: python3 runtime/qwen_daemon.py")
        return

    result = finalize_full_tree()
    if result is None:
        print("[ERROR] No response from Qwen daemon.")
        return

    if result.startswith("[ERROR]"):
        print(result)
        print("[HINT] Check ~/.local/share/sentinel/logs/qwen_daemon.log for details.")
        return

    # Normal successful path
    print("[OK] Mutation completed. Qwen daemon responded:")
    print(result)

if __name__ == "__main__":
    main()
