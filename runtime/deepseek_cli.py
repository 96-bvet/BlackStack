import argparse, os, shutil, hashlib, json, subprocess
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# Paths
WACHTER_ROOT = os.path.expanduser("~/BlackStack/WachterEID/")
LOG_PATH = os.path.join(WACHTER_ROOT, "logs/integration_registry.json")

# --- Utility Functions ---

def hash_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def log_action(action, src, dst, persona, src_hash, dst_hash):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "src": src,
        "dst": dst,
        "persona": persona,
        "src_hash": src_hash,
        "dst_hash": dst_hash
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[LOGGED] {action}: {src} → {dst}")

def gui_approval(message):
    root = tk.Tk()
    root.withdraw()
    response = messagebox.askyesno("Wachter Approval", message)
    root.destroy()
    return response

# --- Integration Logic ---

def inject_registry_hooks(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()

    injected = [
        "from wachter.registry import log_action\n",
        "from wachter.persona import route_task\n",
        "from wachter.audit import safe_open\n"
    ]

    # Inject at top if not already present
    if not any("wachter.registry" in line for line in lines):
        lines = injected + lines

    with open(file_path, "w") as f:
        f.writelines(lines)

def integrate_module(src_path, persona):
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            full_src = os.path.join(root, file)
            rel_path = os.path.relpath(full_src, src_path)
            dst_path = os.path.join(WACHTER_ROOT, "modules", rel_path)

            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            src_hash = hash_file(full_src)
            if gui_approval(f"Integrate {file} into WachterEID?"):
                shutil.copy2(full_src, dst_path)
                inject_registry_hooks(dst_path)
                dst_hash = hash_file(dst_path)
                log_action("module_integrated", full_src, dst_path, persona, src_hash, dst_hash)
            else:
                log_action("integration_skipped", full_src, dst_path, persona, src_hash, None)

# --- DeepSeek Task Injection ---

def run_deepseek(persona, task_type, input_path):
    cmd = [
        "python3", os.path.join(WACHTER_ROOT, "runtime/deepseek_core.py"),
        "--persona", persona,
        "--task", task_type,
        "--input", input_path
    ]
    subprocess.run(" ".join(cmd), shell=True)

# --- CLI Entry Point ---

def main():
    parser = argparse.ArgumentParser(description="DeepSeek CLI with Wachter Integration")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--task", choices=["refactor", "analyze", "inject"], help="DeepSeek task type")
    parser.add_argument("--input", help="Path to input file for DeepSeek")
    parser.add_argument("--integrate", help="Path to module or folder to integrate into WachterEID")

    args = parser.parse_args()

    if args.integrate:
        integrate_module(args.integrate, args.persona)

    if args.task and args.input:
        run_deepseek(args.persona, args.task, args.input)

if __name__ == "__main__":
    main()
