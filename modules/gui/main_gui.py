import tkinter as tk
from tkinter import ttk
import sys
import os
import subprocess

# === Canonical Paths ===
WACHTER_HOME = os.environ.get("WACHTER_HOME", os.path.expanduser("~/BlackStack/WachterEID"))
AUTONOMY_PATH = os.path.join(WACHTER_HOME, "modules/deepseek/autonomy")
VOICE_PATH = os.path.join(WACHTER_HOME, "modules/voice")
libcheck_path = os.path.join(WACHTER_HOME, "modules/diagnostics/libcheck.py")
if os.path.exists(libcheck_path):
    subprocess.call(["python3", libcheck_path])
else:
    print(f"[WARN] libcheck.py not found at {libcheck_path}")


# === Import Modules ===
sys.path.append(AUTONOMY_PATH)
sys.path.append(VOICE_PATH)

try:
    from autonomy_gui import AutonomyGUI
except ImportError as e:
    print(f"[ERROR] Failed to import AutonomyGUI: {e}")
    AutonomyGUI = None

try:
    from audio_shell import AudioShell
except ImportError as e:
    print(f"[ERROR] Failed to import AudioShell: {e}")
    AudioShell = None

# === Unified GUI Shell ===
class WachterMainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WachterEID Operator Shell")
        self.build_tabs()

    def build_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        if AutonomyGUI:
            autonomy_frame = ttk.Frame(notebook)
            AutonomyGUI(autonomy_frame)
            notebook.add(autonomy_frame, text="Autonomy Queue")

        if AudioShell:
            voice_frame = ttk.Frame(notebook)
            AudioShell(voice_frame)
            notebook.add(voice_frame, text="Voice Shell")

        # Future Tabs (Registry Viewer, Persona Router, etc.)
        # registry_frame = ttk.Frame(notebook)
        # RegistryViewer(registry_frame)
        # notebook.add(registry_frame, text="Registry Index")

# === Launch ===
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = WachterMainGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"[FALLBACK] GUI failed: {e}")
