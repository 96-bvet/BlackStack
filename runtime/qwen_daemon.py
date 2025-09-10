#!/usr/bin/env python3
"""
Qwen Daemon for Sentinel (streaming version)
--------------------------------------------
- Loads Qwen from a local directory in 4-bit quantization.
- Streams generated text to the client as soon as tokens are ready.
- Always sends a final message, even on errors.
"""

import os
import socket
import datetime
import traceback

LOG_FILE = os.path.expanduser("~/.local/share/sentinel/logs/qwen_daemon.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log_event(msg: str):
    ts = datetime.datetime.now().isoformat()
    line = f"{ts} | {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)

# --- Preflight environment report ---
def preflight_report():
    for mod in ("transformers", "huggingface_hub", "torch", "bitsandbytes"):
        try:
            m = __import__(mod)
            log_event(f"{mod}: {getattr(m, '__version__', 'unknown')} @ {getattr(m, '__file__', 'unknown')}")
        except Exception as e:
            log_event(f"{mod}: ERROR - {e}")

# --- Config ---
MODEL_PATH = os.path.expanduser("~/Qwen2.5-14B")
HOST = "127.0.0.1"
PORT = 9090

MODEL = None
TOKENIZER = None
MODEL_READY = False

def load_model():
    global MODEL, TOKENIZER, MODEL_READY
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

        log_event(f"Loading Qwen model from local path: {MODEL_PATH} (4-bit)")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        try:
            TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=True)
            log_event("Tokenizer loaded (fast).")
        except Exception as e_fast:
            log_event(f"[WARN] Fast tokenizer failed, falling back to slow: {e_fast}")
            TOKENIZER = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
            log_event("Tokenizer loaded (slow).")

        MODEL = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            device_map="auto",
            quantization_config=bnb_config,
            torch_dtype="auto"
        )
        MODEL_READY = True
        log_event("Model loaded successfully in 4-bit mode from local directory.")
    except Exception as e:
        MODEL_READY = False
        log_event(f"[ERROR] Model load failed: {e}")
        log_event(traceback.format_exc())

def stream_generate(prompt: str, conn, max_new_tokens: int = 1024):
    """
    Streams generated text to the client in chunks, with repetition control.
    """
    if not MODEL_READY:
        conn.sendall(b"[ERROR] Qwen model is not loaded. Check daemon logs.\n")
        return

    try:
        import torch
        from transformers import TextIteratorStreamer
        streamer = TextIteratorStreamer(TOKENIZER, skip_special_tokens=True)

        inputs = TOKENIZER(prompt, return_tensors="pt").to(MODEL.device)

        # Run generation in a background thread so we can stream
        import threading
        gen_kwargs = dict(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,              # enable sampling
            temperature=0.7,              # lower = more focused, higher = more creative
            top_p=0.9,                     # nucleus sampling
            repetition_penalty=1.15,       # discourage loops
            streamer=streamer
        )
        thread = threading.Thread(target=MODEL.generate, kwargs=gen_kwargs)
        thread.start()

        for new_text in streamer:
            try:
                conn.sendall(new_text.encode("utf-8", errors="ignore"))
            except Exception as e:
                log_event(f"[WARN] Failed to send chunk: {e}")
                break

        thread.join()
    except Exception as e:
        err_msg = f"[ERROR] Inference failed: {e}\n"
        log_event(err_msg)
        log_event(traceback.format_exc())
        try:
            conn.sendall(err_msg.encode("utf-8", errors="ignore"))
        except Exception:
            pass

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(8)
        log_event(f"Qwen daemon listening on {HOST}:{PORT} (MODEL_READY={MODEL_READY})")

        while True:
            try:
                conn, addr = s.accept()
            except Exception as e:
                log_event(f"[ERROR] accept() failed: {e}")
                continue

            with conn:
                try:
                    conn.settimeout(300)
                    log_event(f"Connection from {addr}")
                    data = conn.recv(5_000_000)
                    if not data:
                        log_event("Empty payload; closing connection.")
                        continue
                    prompt = data.decode("utf-8", errors="ignore")
                    log_event(f"Received prompt ({len(data)} bytes)")
                    stream_generate(prompt, conn)
                except ConnectionResetError:
                    log_event("[WARN] Peer reset connection mid-request.")
                except Exception as e:
                    log_event(f"[ERROR] Request handling failed: {e}")
                    log_event(traceback.format_exc())
                    try:
                        conn.sendall(f"[ERROR] {e}".encode("utf-8", errors="ignore"))
                    except Exception:
                        pass

if __name__ == "__main__":
    preflight_report()
    load_model()
    run_server()
