#!/usr/bin/env python3

import sys, os, subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# ─── Canonical Path Patch ─────────────────────────────────────────────────────
BLACKSTACK_ROOT = "/home/blackhawk63/BlackStack"
sys.path.append(BLACKSTACK_ROOT)
sys.path.append("/home/blackhawk63/BlackStack/deps/whisper_core")
sys.path.append("/home/blackhawk63/BlackStack/deps/coqui_core")

# ─── Whisper + Coqui + Qwen Load ──────────────────────────────────────────────
import whisper
from TTS.api import TTS
from transformers import AutoTokenizer, AutoModelForCausalLM

whisper_model = whisper.load_model("base")
coqui_model = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-14B-Instruct", trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-14B-Instruct", device_map="auto", trust_remote_code=True)

# ─── Logging Setup ────────────────────────────────────────────────────────────
LOG_PATH = os.path.join(BLACKSTACK_ROOT, "logs", "sentinel_boot.log")
VOICE_LOG = os.path.join(BLACKSTACK_ROOT, "logs", "voice_output.log")

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, 'a') as log:
        log.write(f"[{timestamp}] {message}\n")

def log_voice(text, persona, source):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(VOICE_LOG, 'a') as log:
        log.write(f"[{timestamp}] {persona} ({source}): {text}\n")

# ─── Voice Output ─────────────────────────────────────────────────────────────
def speak_text(text, persona="DefaultOps", escalation=False):
    try:
        if escalation:
            speaker_wav = "/home/blackhawk63/BlackStack/voices/redops.wav"
        else:
            speaker_map = {
                "RedOps": "/home/blackhawk63/BlackStack/voices/redops.wav",
                "CalmOps": "/home/blackhawk63/BlackStack/voices/calmops.wav",
                "DefaultOps": "/home/blackhawk63/BlackStack/voices/defaultops.wav"
            }
            speaker_wav = speaker_map.get(persona, speaker_map["DefaultOps"])

        coqui_model.tts_to_file(text=text, speaker_wav=speaker_wav, file_path="/tmp/speech.wav")
        subprocess.run(["aplay", "/tmp/speech.wav"])
        log_voice(f"TONE → speaker={os.path.basename(speaker_wav)} escalation={escalation}", persona, "coqui")
        log_voice(text, persona, "coqui")
    except Exception as e:
        log_voice(f"Coqui error: {str(e)}", persona, "fallback")

# ─── Qwen Inference ───────────────────────────────────────────────────────────
def generate_response(text, persona="DefaultOps"):
    try:
        system_prompt = f"You are {persona}, operating inside a sovereign AI shell named Sentinel. Respond with clarity, emotional resonance, and escalation awareness."
        full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{text}\n<|assistant|>"

        input_ids = tokenizer(full_prompt, return_tensors="pt").input_ids
        output = model.generate(input_ids, max_new_tokens=512)
        response = tokenizer.decode(output[0], skip_special_tokens=True)

        escalation = any(trigger in text.lower() for trigger in ["override", "refactor", "inject"])
        log_voice(f"Qwen prompt → {full_prompt}", persona, "qwen2.5-input")
        log_voice(f"Qwen response → {response}", persona, "qwen2.5-output")
        return response, escalation
    except Exception as e:
        log_event(f"Qwen error → {str(e)}")
        return f"{persona} encountered an inference error.", False

# ─── Whisper Input ────────────────────────────────────────────────────────────
def listen_and_process(persona="DefaultOps", gui=None):
    try:
        subprocess.run(["arecord", "-d", "5", "-f", "cd", "/tmp/speech.wav"])
        result = whisper_model.transcribe("/tmp/speech.wav")
        text = result["text"].strip()
        response, escalation = generate_response(text, persona)
        speak_text(response, persona, escalation=escalation)
        log_voice(text, persona, "whisper")
        log_voice(response, persona, "inference")
        log_voice(f"Whisper → lang={result['language']} confidence={result.get('avg_logprob', 'N/A')}", persona, "whisper-meta")
        if gui:
            gui.log_output(f"You: {text}", persona)
            gui.log_output(f"Sentinel: {response}", persona)
    except Exception as e:
        speak_text(f"Whisper error: {str(e)}", persona)

# ─── GUI Shell ────────────────────────────────────────────────────────────────
class VoiceShellGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sentinel Voice Shell")
        self.persona = tk.StringVar(value="DefaultOps")

        ttk.Label(root, text="Persona:").grid(row=0, column=0, padx=5, pady=5)
        persona_menu = ttk.Combobox(root, textvariable=self.persona, values=["DefaultOps", "RedOps", "CalmOps"])
        persona_menu.grid(row=0, column=1, padx=5, pady=5)

        self.input_field = tk.Entry(root, width=60)
        self.input_field.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.input_field.bind("<Return>", self.process_input)

        self.output_log = tk.Text(root, height=10, width=60, state='disabled')
        self.output_log.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

        listen_button = ttk.Button(root, text="🎙️ Listen", command=self.listen)
        listen_button.grid(row=3, column=0, columnspan=2, pady=5)

        log_event("Sentinel GUI shell initialized")

    def process_input(self, event=None):
        text = self.input_field.get().strip()
        persona = self.persona.get()
        if text.lower() in ["exit", "quit"]:
            speak_text("Shutting down voice shell", persona)
            self.root.quit()
            return
        if text:
            response, escalation = generate_response(text, persona)
            speak_text(response, persona, escalation=escalation)
            log_voice(text, persona, "input")
            log_voice(response, persona, "inference")
            self.log_output(f"You: {text}", persona)
            self.log_output(f"Sentinel: {response}", persona)
            self.input_field.delete(0, tk.END)

    def listen(self):
        listen_and_process(self.persona.get(), gui=self)

    def log_output(self, text, persona):
        self.output_log.config(state='normal')
        self.output_log.insert(tk.END, f"[{persona}] {text}\n")
        self.output_log.config(state='disabled')

# ─── Launch ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceShellGUI(root)
    root.mainloop()
