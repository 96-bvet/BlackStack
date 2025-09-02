import os, sys, time, torch, hashlib, subprocess
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# ─── CONFIG ─────────────────────────────────────────────────────────────
ROOT_DIR = os.path.expanduser("~/BlackStack")
EXCLUDE_DIRS = {"venv", "logs", "__pycache__"}
PROMPT_PATH = os.path.join(ROOT_DIR, "WachterEID/prompts/final_refactor_prompt.txt")
ETHIC_PATH = os.path.join(ROOT_DIR, "WachterEID/prompts/ethic_prompt.txt")
MODEL_PATH = os.path.join(ROOT_DIR, "DeepSeek")
LOG_DIR = os.path.join(ROOT_DIR, "logs/deepseek_final")
SNAPSHOT_DIR = os.path.join(ROOT_DIR, "snapshots/final")
REQUIREMENTS_PATH = os.path.join(MODEL_PATH, "requirements.txt")
DEFAULT_PERSONA = "default"

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

# ─── SETUP ──────────────────────────────────────────────────────────────
def install_requirements():
    if os.path.exists(REQUIREMENTS_PATH):
        print("[Setup] Installing requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_PATH])

def log_gpu_state():
    free, total = torch.cuda.mem_get_info()
    print(f"[GPU] Free: {free / 1024**2:.2f} MB / Total: {total / 1024**2:.2f} MB")

def load_deepseek():
    print("[Model] Loading DeepSeek...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map="auto",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        local_files_only=True
    )
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_PATH,
        use_fast=True,
        local_files_only=True
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

# ─── REFRACTOR LOGIC ────────────────────────────────────────────────────
def should_refactor(file):
    return file.endswith((
        ".py", ".sh", ".c", ".cpp", ".json", ".yaml", ".toml",
        ".conf", ".ini", ".txt", ".md", ".service", ".desktop", ".xml"
    ))

def hash_file(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def inject_and_overwrite(filepath, filename, context, deepseek, persona):
    with open(filepath, "r", errors="ignore") as f:
        code = f.read()

    prompt = f"{context}\n\nPersona: {persona}\nRefactor the following file: {filename}\n\n{code}"
    output = deepseek(prompt, max_new_tokens=1024, do_sample=True)[0]["generated_text"]

    hash_before = hash_file(filepath)
    snapshot_path = os.path.join(SNAPSHOT_DIR, f"{filename}.{hash_before[:8]}.bak")
    with open(snapshot_path, "w") as f:
        f.write(code)

    with open(filepath, "w") as f:
        f.write(output)

    hash_after = hashlib.sha256(output.encode()).hexdigest()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, f"{filename}.{timestamp}.{hash_after[:8]}.log")
    with open(log_path, "w") as f:
        f.write(output)

    print(f"[Refactored] {filename} → {hash_after[:8]}")

def run_recursive_refactor(persona):
    install_requirements()
    log_gpu_state()
    deepseek = load_deepseek()

    with open(PROMPT_PATH, "r") as f:
        context = f.read().strip()

    if os.path.exists(ETHIC_PATH):
        with open(ETHIC_PATH, "r") as f:
            ethic = f.read().strip()
        context = ethic + "\n\n" + context

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if should_refactor(file):
                filepath = os.path.join(root, file)
                inject_and_overwrite(filepath, file, context, deepseek, persona)

# ─── ENTRY ──────────────────────────────────────────────────────────────
def main():
    persona = DEFAULT_PERSONA
    if "--persona" in sys.argv:
        idx = sys.argv.index("--persona")
        persona = sys.argv[idx + 1]
    run_recursive_refactor(persona)

if __name__ == "__main__":
    main()
