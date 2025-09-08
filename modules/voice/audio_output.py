import pyttsx3
import subprocess
import sys
from datetime import datetime

# Optional: log file path
LOG_PATH = "/home/blackhawk63/BlackStack/logs/voice_output.log"

def speak_text(text, persona="DefaultOps"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        engine = pyttsx3.init()
        engine.setProperty('volume', 1.0)

        # Persona-based tone routing
        if persona == "RedOps":
            engine.setProperty('rate', 180)
        elif persona == "CalmOps":
            engine.setProperty('rate', 120)
        else:
            engine.setProperty('rate', 150)

        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)

        engine.say(text)
        engine.runAndWait()

        # Log successful pyttsx3 output
        with open(LOG_PATH, 'a') as log:
            log.write(f"[{timestamp}] {persona} (pyttsx3): {text}\n")

    except Exception as e:
        # Fallback to espeak-ng + aplay
        fallback_cmd = ['espeak-ng', '-s', '150', '-p', '60', '-a', '100', '-v', 'en-us', '-w', '/tmp/speech.wav', text]
        subprocess.run(fallback_cmd)
        subprocess.run(['aplay', '/tmp/speech.wav'])

        # Log fallback usage
        with open(LOG_PATH, 'a') as log:
            log.write(f"[{timestamp}] {persona} (fallback): {text} | pyttsx3 failed: {str(e)}\n")
