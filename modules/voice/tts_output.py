import subprocess
from datetime import datetime
import os

VOICE_LOG = "/home/blackhawk63/BlackStack/logs/voice_output.log"

def log_voice(text, persona, source):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(VOICE_LOG, 'a') as log:
        log.write(f"[{timestamp}] {persona} ({source}): {text}\n")

def speak_text(text, persona="DefaultOps"):
    tone_map = {
        "RedOps": {"rate": "180", "pitch": "80", "voice": "en+m3"},
        "CalmOps": {"rate": "120", "pitch": "40", "voice": "en+f3"},
        "DefaultOps": {"rate": "150", "pitch": "60", "voice": "en-us"}
    }
    tone = tone_map.get(persona, tone_map["DefaultOps"])

    try:
        subprocess.run([
            "espeak-ng",
            "-s", tone["rate"],
            "-p", tone["pitch"],
            "-v", tone["voice"],
            "-w", "/tmp/speech.wav",
            text
        ])
        subprocess.run(["aplay", "/tmp/speech.wav"])
        log_voice(text, persona, "espeak-ng")
    except Exception as e:
        log_voice(f"Error: {str(e)}", persona, "fallback")
