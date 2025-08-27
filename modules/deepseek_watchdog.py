import subprocess, time, os, json, hashlib
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

# Config
WATCHDOG_INTERVAL = 60  # seconds
TIMEOUT_THRESHOLD = 300  # seconds
HEARTBEAT_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/deepseek_heartbeat.json")
PROCESS_NAME = "deepseek_cli.py"
LOG_PATH = os.path.expanduser("~/BlackStack/WachterEID/logs/watchdog_events.json")

def get_gpu_utilization():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, text=True
        )
        gpu_util, mem_used = map(int, result.stdout.strip().split(","))
        return gpu_util, mem_used
    except Exception as e:
        log_event(f"GPU query error: {str(e)}")
        return 0, 0

def get_process_pid():
    result = subprocess.run(["pgrep", "-f", PROCESS_NAME], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip().splitlines()

def is_heartbeat_stale():
    if not os.path.exists(HEARTBEAT_PATH):
        log_event("Heartbeat file missing")
        return True
    try:
        with open(HEARTBEAT_PATH) as f:
            data = json.load(f)
        last_ping = float(data.get("last_ping", 0))
        return (time.time() - last_ping) > TIMEOUT_THRESHOLD
    except Exception as e:
        log_event(f"Heartbeat read error: {str(e)}")
        return True

def log_event(reason):
    timestamp = datetime.utcnow().isoformat()
    hash_input = f"{timestamp}:{reason}".encode()
    event_hash = hashlib.sha256(hash_input).hexdigest()
    log_entry = {
        "timestamp": timestamp,
        "reason": reason,
        "hash": event_hash
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"[WATCHDOG] {reason} | Hash: {event_hash}")

def trigger_approval_gate(reason):
    log_event(f"Approval required: {reason}")
    root = tk.Tk()
    root.withdraw()
    response = messagebox.askyesno("DeepSeek Watchdog", f"Stall detected:\n{reason}\n\nTerminate process?")
    root.destroy()
    return response

def terminate_process(pid):
    subprocess.run(["kill", "-9", pid])
    log_event(f"Terminated hung process PID {pid}")

def watchdog_loop():
    while True:
        pids = get_process_pid()
        gpu_util, mem_used = get_gpu_utilization()
        stale = is_heartbeat_stale()

        if pids and stale and gpu_util < 5 and mem_used > 8000:
            reason = "DeepSeek CLI hung: stale heartbeat + low GPU utilization"
            if trigger_approval_gate(reason):
                for pid in pids:
                    terminate_process(pid)
                # Optional: trigger fallback GPU or rollback ingest here
            else:
                log_event("Approval denied: continuing process")

        time.sleep(WATCHDOG_INTERVAL)

if __name__ == "__main__":
    watchdog_loop()
