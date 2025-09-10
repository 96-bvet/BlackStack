#!/usr/bin/env python3
"""
Sentinel Voice Provisioner
--------------------------
Bootstrap hook to ensure all Piper voices and configs are present
for every persona in the registry.
"""

import os
import subprocess
from datetime import datetime
from urllib.request import urlretrieve

# === CONFIG ===
VOICE_DIR = os.path.expanduser("~/.local/share/sentinel/voices")
ESPEAK_DIR = "/usr/local/share/piper/espeak-ng-data"
LOG_FILE = os.path.expanduser("~/.local/share/sentinel/logs/voice_provisioner.log")

# Persona → Hugging Face voice path mapping
# Lessac high is now the default male voice for analyst
PERSONA_MODELS = {
    "analyst": "en/en_US/lessac/high/en_US-lessac-high",
    "operator": "en/en_US/ryan/medium/en_US-ryan-medium",
    "commander": "en/en_GB/alan/medium/en_GB-alan-medium"  # fixed
}

BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/"

# === HELPERS ===
def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {msg}\n")
    print(msg)

def ensure_espeak_data():
    if not os.path.isdir(ESPEAK_DIR):
        log(f"[INFO] espeak-ng-data not found at {ESPEAK_DIR}")
        candidate = "/tmp/piper/espeak-ng-data"
        if os.path.isdir(candidate):
            log(f"[INFO] Copying espeak-ng-data from {candidate}")
            os.makedirs(os.path.dirname(ESPEAK_DIR), exist_ok=True)
            subprocess.run(["sudo", "cp", "-r", candidate, os.path.dirname(ESPEAK_DIR)], check=True)
        else:
            log("[WARN] espeak-ng-data not found — Piper may fail without it.")

def download_voice(model_path):
    os.makedirs(VOICE_DIR, exist_ok=True)
    base_name = os.path.basename(model_path)
    onnx_path = os.path.join(VOICE_DIR, f"{base_name}.onnx")
    json_path = f"{onnx_path}.json"

    if not os.path.isfile(onnx_path):
        log(f"[DL] Downloading {base_name}.onnx")
        urlretrieve(BASE_URL + model_path + ".onnx", onnx_path)
    else:
        log(f"[SKIP] {base_name}.onnx already exists")

    if not os.path.isfile(json_path):
        log(f"[DL] Downloading {base_name}.onnx.json")
        urlretrieve(BASE_URL + model_path + ".onnx.json", json_path)
    else:
        log(f"[SKIP] {base_name}.onnx.json already exists")

def provision_all():
    ensure_espeak_data()
    for persona, model_path in PERSONA_MODELS.items():
        log(f"[INFO] Provisioning voice for persona: {persona}")
        download_voice(model_path)
    log("[OK] Voice provisioning complete.")

if __name__ == "__main__":
    provision_all()
