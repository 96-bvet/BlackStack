import time, hashlib
from datetime import datetime

# --- Utility: Hash for traceability ---
def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

# --- Simulated DeepSeek-V2 Engine ---
def run_deepseek_v2(persona, task, input_text):
    timestamp = datetime.utcnow().isoformat()
    input_hash = hash_text(input_text)

    print(f"[DeepSeek-V2] Task: {task} | Persona: {persona} | Hash: {input_hash} | Time: {timestamp}")

    # Simulated persona-aware refactor
    if task == "refactor":
        return refactor_logic(input_text, persona)
    elif task == "analyze":
        return analyze_logic(input_text, persona)
    elif task == "inject":
        return inject_logic(input_text, persona)
    else:
        raise ValueError(f"Unsupported task type: {task}")

# --- Persona-Aware Logic Blocks ---

def refactor_logic(text, persona):
    if persona == "RedTeam":
        return text.replace("print(", "log_red(")
    elif persona == "BlueTeam":
        return text.replace("print(", "log_blue(")
    else:
        return text.replace("print(", "log_generic(")

def analyze_logic(text, persona):
    lines = text.splitlines()
    summary = f"# Analysis by {persona}: {len(lines)} lines, {sum(len(l) for l in lines)} characters\n"
    return summary + "\n".join(f"# {i+1}: {line}" for i, line in enumerate(lines))

def inject_logic(text, persona):
    injected = f"# Injected by {persona} at {datetime.utcnow().isoformat()}\n"
    return injected + text

