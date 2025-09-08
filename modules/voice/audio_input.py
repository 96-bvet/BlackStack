import speech_recognition as sr

def capture_audio():
    r = sr.Recognizer()
    mic_list = sr.Microphone.list_microphone_names()

    # Locate Depstech mic by name
    depstech_index = next((i for i, name in enumerate(mic_list) if "Depstech" in name), 0)

    try:
        with sr.Microphone(device_index=depstech_index) as source:
            print("🎧 Listening via Depstech mic...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=6, phrase_time_limit=12)
    except Exception as e:
        return f"[Mic error: {e}]"

    # Try offline Whisper first, fallback to Google if needed
    try:
        return r.recognize_whisper(audio)
    except sr.UnknownValueError:
        return "[Unrecognized speech]"
    except sr.RequestError:
        try:
            return r.recognize_google(audio)
        except Exception as e:
            return f"[Transcription error: {e}]"
