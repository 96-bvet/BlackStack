#!/usr/bin/env python3

import os, socket, hashlib, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import psutil

# ─── Config ─────────────────────────────────────────────────────────────
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"
LOG_PATH = "/mnt/unified/BlackStack/logs/qwen_mutations.log"

# ─── Memory Check ───────────────────────────────────────────────────────
available_ram = psutil.virtual_memory().available
if available_ram < 3 * 1024**3:
    print("[Qwen] Warning: Low RAM. Consider using a smaller model.")

# ─── BitsAndBytes 4-bit Config ──────────────────────────────────────────
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# ─── Load Model ─────────────────────────────────────────────────────────
print(f"[Qwen] Loading 4-bit model: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True
)
model.eval()

# ─── Hash Utility ───────────────────────────────────────────────────────
def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

# ─── Mutation Handler ───────────────────────────────────────────────────
def mutate(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs.input_ids.to(model.device)
    attention_mask = inputs.attention_mask.to(model.device)
    output = model.generate(input_ids, attention_mask=attention_mask, max_new_tokens=1024)
    result = tokenizer.decode(output[0], skip_special_tokens=True)
    log_mutation(prompt, result)
    return result
if is_file_in_use(target_path):
    return f"[Qwen] Skipped {target_path} — file is currently in use."

# ─── Logging ────────────────────────────────────────────────────────────
def log_mutation(prompt, result):
    with open(LOG_PATH, "a") as log:
        log.write(f"\n[🧠 Qwen Mutation]\nHash: {hash_text(prompt)}\nPrompt: {prompt}\nResult:\n{result}\n")

# ─── Socket Server ──────────────────────────────────────────────────────
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.settimeout(10)
server.bind(("localhost", 9090))
server.listen(1)

print("[Qwen] 4-bit daemon active. Awaiting mutation tasks...")

while True:
    try:
        conn, _ = server.accept()
        prompt = conn.recv(8192).decode()
        response = mutate(prompt)
        conn.send(response.encode())
        conn.close()
    except socket.timeout:
        continue
    except Exception as e:
        print(f"[Qwen] Error: {e}")
        continue
