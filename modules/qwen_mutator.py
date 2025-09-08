#!/usr/bin/env python3

import os
import torch
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# ─── Logging Setup ────────────────────────────────────────────────────────────
LOG_PATH = "/home/blackhawk63/BlackStack/logs/mutator.log"

def log_mutation(text, persona, source="qwen2.5-mutator"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, 'a') as log:
        log.write(f"[{timestamp}] {persona} ({source}): {text}\n")

# ─── Memory-Aware Device Routing ──────────────────────────────────────────────
def get_device(task_type="inference"):
    vram_used = torch.cuda.memory_allocated() / 1e9
    if vram_used > 10.0:
        log_mutation(f"⚠️ High VRAM detected ({vram_used:.2f} GB) → routing {task_type} to CPU", "System")
        return "cpu"
    else:
        return "cuda"

def route_persona(persona):
    if persona == "RedOps":
        return get_device("RedOps escalation")
    elif persona == "VoiceShell":
        return get_device("voice synthesis")
    else:
        return get_device("default inference")

# ─── Load Qwen2.5 in 4-bit Mode ───────────────────────────────────────────────
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-14B-Instruct", trust_remote_code=True)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# ─── Mutation Request ─────────────────────────────────────────────────────────
def request_mutation(task, persona="DefaultOps", escalation=False):
    device = route_persona(persona)
    log_mutation(f"Assigned device → {device} for persona: {persona}", persona)

    model = AutoModelForCausalLM.from_pretrained(
        "Qwen/Qwen2.5-14B-Instruct",
        device_map={"": device},
        quantization_config=bnb_config,
        trust_remote_code=True
    )

    system_prompt = f"""
You are a sovereign AI shell operating inside Sentinel. Your task is to generate mutation-safe install logic, refactor plans, and multi-language integration scaffolds. Never use pip3 or venv. All changes must be routed through approval gates and logged for forensic traceability. If escalation is triggered, override tone and inject RedOps logic.
"""
    full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{task}\n<|assistant|>"
    input_ids = tokenizer(full_prompt, return_tensors="pt").input_ids.to(device)

    output = model.generate(input_ids, max_new_tokens=1024)
    response = tokenizer.decode(output[0], skip_special_tokens=True)

    log_mutation(f"Mutation task → {task}", persona)
    log_mutation(f"Mutation response → {response}", persona)
    return response

# ─── Approval Gate ────────────────────────────────────────────────────────────
def approve_and_execute(response, persona="DefaultOps"):
    print(f"\n[APPROVAL REQUIRED] Persona: {persona}")
    print("────────────────────────────────────────────")
    print(response)
    print("────────────────────────────────────────────")
    approval = input("Approve mutation? (yes/no): ").strip().lower()
    if approval == "yes":
        log_mutation("Mutation approved and executed", persona)
        os.system("echo 'Mutation logic would execute here.'")  # Replace with actual executor
    else:
        log_mutation("Mutation rejected by operator", persona)

# ─── CLI Entry ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: qwen_mutator.py '<mutation task>'")
        sys.exit(1)

    task = sys.argv[1]
    persona = "RedOps" if "override" in task.lower() else "DefaultOps"
    escalation = any(trigger in task.lower() for trigger in ["override", "refactor", "inject"])
    response = request_mutation(task, persona, escalation)
    approve_and_execute(response, persona)
