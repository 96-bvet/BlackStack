import os, sys, time, torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

ROOT_DIR = os.path.expanduser("~/BlackStack/WachterEID")
EXCLUDE_DIRS = {"venv", "logs"}
PROMPT_PATH = os.path.expanduser("~/BlackStack/WachterEID/prompts/final_refactor_prompt.txt")
MODEL_PATH = os.path.expanduser("~/BlackStack/DeepSeek")
DEFAULT_PERSONA = "default"

def log_gpu_state():
    free, total = torch.cuda.mem_get_info()
    print(f"[GPU] Free: {free / 1024**2:.2f} MB / Total: {total / 1024**2:.2f} MB")

def load_deepseek():
    start = time.time()
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
    print(f"[Model Load] {time.time() - start:.2f} seconds")
    return pipeline("text-generation", model=model, tokenizer=tokenizer)

def should_refactor(file):
    return file.endswith((
        ".py", ".sh", ".c", ".cpp", ".json", ".yaml", ".toml",
        ".conf", ".ini", ".txt", ".md", ".service", ".desktop", ".xml"
    ))

def inject_and_overwrite(filepath, filename, context, deepseek):
    with open(filepath, "r", errors="ignore") as f:
        code = f.read()

    prompt = f"{context}\n\nPlease refactor the following file: {filename}\n\n{code}"
    output = deepseek(prompt, max_new_tokens=1024, do_sample=True)[0]["generated_text"]

    with open(filepath, "w") as f:
        f.write(output)

    print(f"[Refactored] {filename}")

def run_recursive_refactor(persona):
    log_gpu_state()
    deepseek = load_deepseek()

    with open(PROMPT_PATH, "r") as f:
        context = f.read().strip()

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if should_refactor(file):
                filepath = os.path.join(root, file)
                inject_and_overwrite(filepath, file, context, deepseek)

def main():
    persona = DEFAULT_PERSONA
    if "--persona" in sys.argv:
        idx = sys.argv.index("--persona")
        persona = sys.argv[idx + 1]
    run_recursive_refactor(persona)

if __name__ == "__main__":
    main()
