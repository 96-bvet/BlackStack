from TTS.api import TTS
import traceback

MODEL = "tts_models/en/ljspeech/tacotron2-DDC"
OUT = "/home/blackhawk63/test.wav"

print("[DEBUG] Initializing TTS…")
try:
    tts = TTS(model_name=MODEL, progress_bar=True, gpu=False)
    print("[DEBUG] Model loaded.")
except Exception as e:
    print("[ERROR] Model init failed:")
    traceback.print_exc()
    exit(1)

print("[DEBUG] Synthesizing…")
try:
    tts.tts_to_file(text="Hello from Sentinel", file_path=OUT)
    print(f"[DEBUG] Wrote file: {OUT}")
except Exception as e:
    print("[ERROR] Synthesis failed:")
    traceback.print_exc()
    exit(1)
