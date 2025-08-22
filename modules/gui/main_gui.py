import tkinter as tk
from tkinter import ttk
import sys
import os

# === Canonical Paths ===
AUTONOMY_PATH = os.path.expanduser("~/BlackStack/WachterEID/modules/deepseek/autonomy/")
VOICE_PATH = os.path.expanduser("~/BlackStack/WachterEID/modules/voice/")

# === Import Modules ===
sys.path.append(AUTONOMY_PATH)
sys.path.append(VOICE_PATH)

from autonomy_gui import AutonomyGUI
from audio_shell import AudioShell  # Update this if your voice module uses a different entrypoint

# === Unified GUI Shell ===
class WachterMainGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WachterEID Operator Shell")
        self.build_tabs()

    def build_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        # Autonomy Tab
        autonomy_frame = ttk.Frame(notebook)
        AutonomyGUI(autonomy_frame)
        notebook.add(autonomy_frame, text="Autonomy Queue")

        # Voice Shell Tab
        voice_frame = ttk.Frame(notebook)
        AudioShell(voice_frame)
        notebook.add(voice_frame, text="Voice Shell")

        # Future Tabs (Registry Viewer, Persona Router, etc.)
        # registry_frame = ttk.Frame(notebook)
        # RegistryViewer(registry_frame)
        # notebook.add(registry_frame, text="Registry Index")

# === Launch ===
if __name__ == "__main__":
    root = tk.Tk()
    app = WachterMainGUI(root)
    root.mainloop()
