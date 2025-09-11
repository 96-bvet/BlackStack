#!/usr/bin/env python3
"""
BlackStack Audio Input Module
Audio capture with audit logging and forensic traceability
"""
import speech_recognition as sr
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_audio_event(event_type, details):
    """Log audio events for audit trail"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] AUDIO {event_type}: {details}")

def capture_audio():
    """
    Capture audio with Depstech microphone preference
    Returns transcribed text or error message
    """
    r = sr.Recognizer()
    mic_list = sr.Microphone.list_microphone_names()
    
    log_audio_event("INIT", f"Found {len(mic_list)} microphones")

    # Locate Depstech mic by name, fallback to default
    depstech_index = next((i for i, name in enumerate(mic_list) if "Depstech" in name), 0)
    
    try:
        with sr.Microphone(device_index=depstech_index) as source:
            log_audio_event("LISTENING", f"Using microphone index {depstech_index}")
            print("🎧 Listening via microphone...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=6, phrase_time_limit=12)
    except Exception as e:
        log_audio_event("ERROR", f"Microphone error: {e}")
        return f"[Mic error: {e}]"

    # Try offline Whisper first, fallback to Google if needed
    try:
        result = r.recognize_whisper(audio)
        log_audio_event("SUCCESS", "Whisper transcription successful")
        return result
    except sr.UnknownValueError:
        log_audio_event("WARN", "Whisper could not understand audio")
        return "[Unrecognized speech]"
    except sr.RequestError:
        try:
            result = r.recognize_google(audio)
            log_audio_event("SUCCESS", "Google transcription successful")
            return result
        except Exception as e:
            log_audio_event("ERROR", f"Transcription error: {e}")
            return f"[Transcription error: {e}]"