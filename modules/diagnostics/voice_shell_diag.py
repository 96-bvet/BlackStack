#!/usr/bin/env python3
"""
Diagnostic harness for voice_shell.py
Logs each stage, enumerates sinks, tests playback, and hashes audio buffers.
Safe to run inside Sentinel without mutating core modules.
"""

import sys
import traceback
import hashlib
import importlib
import subprocess
from pathlib import Path

# === CONFIG ===
TEST_PHRASE = "Sentinel voice shell diagnostic test."
DEBUG_MODE = True

# Resolve repo root dynamically (two levels up from this file's parent)
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

print(f"[VOICE_SHELL][DEBUG] Repo root added to sys.path: {REPO_ROOT}")

def stage(msg):
    print(f"[VOICE_SHELL][STAGE] {msg}", file=sys.stderr, flush=True)

def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def list_sinks():
    try:
        out = subprocess.check_output(["pactl", "list", "short", "sinks"], text=True)
        sinks = [line.split("\t")[1] for line in out.strip().split("\n") if line]
        stage(f"Detected sinks: {sinks}")
        return sinks
    except Exception as e:
        stage(f"Sink enumeration failed: {e}")
        return []

def test_tts(tts_engine, phrase, sink=None):
    try:
        stage(f"Synthesizing phrase: '{phrase}'")
        audio_data = tts_engine.tts(phrase) if hasattr(tts_engine, "tts") else None
        if audio_data:
            h = hash_bytes(audio_data)
            stage(f"Audio buffer hash: {h}")
            if sink:
                stage(f"Attempting playback on sink: {sink}")
                # Example: replace with actual playback call
                # play_audio(audio_data, sink)
            else:
                stage("No sink specified, skipping playback")
        else:
            stage("TTS engine returned no audio data")
    except Exception as e:
        stage(f"TTS test failed: {e}")
        traceback.print_exc()

def main():
    stage("Starting voice shell diagnostic harness")

    # 1. Enumerate sinks
    sinks = list_sinks()

    # 2. Import voice_shell
    try:
        stage("Importing voice_shell module")
        voice_shell = importlib.import_module("BlackStack.modules.voice.voice_shell")
    except Exception as e:
        stage(f"Import failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 3. Init TTS engine
    try:
        stage("Initializing TTS engine from voice_shell")
        tts_engine = getattr(voice_shell, "init_tts", lambda: None)()
        if not tts_engine:
            stage("No TTS engine returned from init_tts()")
    except Exception as e:
        stage(f"TTS init failed: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 4. Test phrase on each sink
    for sink in sinks or [None]:
        test_tts(tts_engine, TEST_PHRASE, sink)

    stage("Diagnostic complete")

if __name__ == "__main__":
    main()
