import tkinter as tk
from tkinter import messagebox, scrolledtext
import json
import os
import hashlib
import datetime
import subprocess

# === CONFIG ===
BASE_PATH = os.path.expanduser("~/BlackStack/WachterEID/modules/deepseek/autonomy/")
APPROVAL_QUEUE = os.path.join(BASE_PATH, "approval_queue.json")
ACTION_LOG = os.path.join(BASE_PATH, "action_log.csv")
ROLLBACK_DIR = os.path.join(BASE_PATH, "rollback_snapshots/")

class AutonomyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WachterEID Autonomy Shell")
        self.queue = self.load_queue()
        self.build_ui()

    def load_queue(self):
        if os.path.exists(APPROVAL_QUEUE):
            with open(APPROVAL_QUEUE, "r") as f:
                return json.load(f)
        return []

    def build_ui(self):
        for idx, entry in enumerate(self.queue):
            frame = tk.Frame(self.root, bd=2, relief=tk.RIDGE, padx=10, pady=5)
            frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(frame, text=f"Module: {entry['module']}", font=("Arial", 12, "bold")).pack(anchor="w")
            tk.Label(frame, text=f"Reason: {entry['reason']}").pack(anchor="w")
            tk.Label(frame, text=f"Hash: {entry['hash']}").pack(anchor="w")
            tk.Label(frame, text=f"Timestamp: {entry['timestamp']}").pack(anchor="w")

            script_box = scrolledtext.ScrolledText(frame, height=6, width=80)
            script_box.insert(tk.END, entry['script'])
            script_box.configure(state='disabled')
            script_box.pack()

            btn_frame = tk.Frame(frame)
            btn_frame.pack()

            tk.Button(btn_frame, text="Approve", command=lambda i=idx: self.approve_patch(i)).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Reject", command=lambda i=idx: self.reject_patch(i)).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Rollback", command=lambda m=entry['module']: self.rollback_module(m)).pack(side=tk.LEFT, padx=5)

    def approve_patch(self, index):
        self.queue[index]['status'] = "approved"
        self.execute_patch(self.queue[index])
        self.save_queue()
        messagebox.showinfo("Patch Executed", f"Patch for {self.queue[index]['module']} executed.")

    def reject_patch(self, index):
        self.queue[index]['status'] = "rejected"
        self.save_queue()
        messagebox.showinfo("Patch Rejected", f"Patch for {self.queue[index]['module']} rejected.")

    def rollback_module(self, module_name):
        snapshots = [d for d in os.listdir(ROLLBACK_DIR) if d.startswith(module_name)]
        if not snapshots:
            messagebox.showerror("Rollback Failed", f"No snapshots found for {module_name}")
            return
        latest = sorted(snapshots)[-1]
        src = os.path.join(ROLLBACK_DIR, latest)
        dest = os.path.expanduser(f"~/BlackStack/WachterEID/modules/{module_name}")
        subprocess.run(["rm", "-rf", dest])
        subprocess.run(["cp", "-r", src, dest])
        messagebox.showinfo("Rollback Complete", f"Rolled back {module_name} to snapshot {latest}")

    def execute_patch(self, entry):
        module_path = os.path.expanduser(f"~/BlackStack/WachterEID/modules/{entry['module']}/patch.py")
        with open(module_path, "w") as f:
            f.write(entry["script"])
        subprocess.run(["python3", module_path])
        self.log_action(entry)

    def log_action(self, entry):
        line = f"{entry['timestamp']},{entry['module']},{entry['hash']},{entry['reason']},{entry['status']}\n"
        if not os.path.exists(ACTION_LOG):
            with open(ACTION_LOG, "w") as f:
                f.write("timestamp,module,hash,reason,status\n")
        with open(ACTION_LOG, "a") as f:
            f.write(line)

    def save_queue(self):
        with open(APPROVAL_QUEUE, "w") as f:
            json.dump(self.queue, f, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutonomyGUI(root)
    root.mainloop()