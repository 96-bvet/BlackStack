#!/usr/bin/env python3
"""
Sentinel Voice Shell - Piper Edition (Lessac High, Deeper Pitch)
---------------------------------------------------------------
Offline-first, persona-aware TTS using Piper.
Auto-provisions missing voices, applies conversational phrasing,
and deepens pitch for a richer male tone.
"""

import subprocess
import os
import datetime
from modules import voice_provisioner  # your existing provisioner

# === CONFIG ===

# Path to espeak-ng-data
ESPEAK_DATA = "/usr/local/share/piper/espeak-ng-data"

# Default male voice (Lessac high quality)
DEFAULT_MODEL = os.path.expanduser(
    "~/.local/share/sentinel/voices/en_US-lessac-high.onnx"
)

# Persona → voice model mapping
PERSONA_VOICES = {
    "analyst": "~/.local/share/sentinel/voices/en_US-lessac-high.onnx",
    "operator": "~/.local/share/sentinel/voices/en_US-ryan-medium.onnx",
    "commander": "~/.local/share/sentinel/voices/en_GB-alan-high.onnx"
}

# Pitch shift in semitones (negative = deeper)
PITCH_SHIFT = -3

# Audit log
LOG_FILE = os.path.expanduser("~/.local/share/sentinel/logs/voice_shell.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


# === HELPERS ===

def log_event(persona: str, text: str, output_path: str, pitch: int):
    """Append a synthesis event to the audit log."""
    timestamp = datetime.datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{timestamp} | persona={persona} | pitch={pitch} | output={output_path} | text={text}\n")


def get_model_for_persona(persona: str) -> str:
    """Return the model path for a given persona, or the default."""
    return os.path.expanduser(PERSONA_VOICES.get(persona, DEFAULT_MODEL))


def conversationalize(text: str) -> str:
    """Lightly adjust text for a more natural, conversational delivery."""
    text = text.replace("I am", "I'm").replace("we are", "we're")
    text = text.replace("do not", "don't").replace("cannot", "can't")
    text = text.replace(".", "...")  # subtle pause
    return text


def ensure_voice(model_path: str):
    """Provision the voice if missing."""
    if not os.path.isfile(model_path):
        base_name = os.path.basename(model_path).replace(".onnx", "")
        print(f"[INFO] Voice model {base_name} missing — provisioning...")
        for persona, path in PERSONA_VOICES.items():
            if os.path.expanduser(path) == model_path:
                hf_path = voice_provisioner.PERSONA_MODELS.get(persona)
                if hf_path:
                    voice_provisioner.download_voice(hf_path)
                break


# === CORE FUNCTION ===

def speak(text: str, out_path: str = "output.wav", persona: str = "default"):
    """Synthesize speech from text using Piper and deepen pitch."""
    model_path = get_model_for_persona(persona)
    ensure_voice(model_path)
    text = conversationalize(text)

    # Step 1: Generate raw voice
    subprocess.run([
        "piper",
        "--model", model_path,
        "--espeak-data", ESPEAK_DATA,
        "--output_file", out_path
    ], input=text.encode("utf-8"), check=True)

    # Step 2: Apply pitch shift with SoX
    subprocess.run([
        "sox", out_path, out_path, "pitch", str(PITCH_SHIFT)
    ], check=True)

    log_event(persona, text, out_path, PITCH_SHIFT)


# === CLI ENTRY ===

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: voice_shell.py \"Text to speak\" [persona] [output.wav]")
        sys.exit(1)

    text = sys.argv[1]
    persona = sys.argv[2] if len(sys.argv) >= 3 else "default"
    out_path = sys.argv[3] if len(sys.argv) >= 4 else "output.wav"

    speak(text, out_path, persona)
    print(f"[OK] Voice synthesis complete → {out_path}")
