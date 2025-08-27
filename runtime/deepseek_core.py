import argparse, os, json, hashlib
from datetime import datetime
import importlib.util

# --- Persona Loader ---
def load_persona_engine(persona):
    base_dir = os.path.dirname(__file__)
    variant_path = os.path.join(base_dir, "persona_variants", f"{persona.lower()}_v2.py")
    if not os.path.exists(variant_path):
        print(f"[Fallback] No variant found for '{persona}', using generic engine.")
        variant_path = os.path.join(base_dir, "deepseek_v2.py")

    spec = importlib.util.spec_from_file_location("deepseek_v2", variant_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_deepseek_v2

# --- Paths ---
WACHTER_ROOT = os.path.expanduser("~/BlackStack/WachterEID/")
LOG_PATH = os.path.join(WACHTER_ROOT, "logs/refactor_registry.json")

def hash_content(content):
    return hashlib.sha256(content.encode()).hexdigest()

def log_refactor(task_type, persona, chunk_id, input_hash, output_hash):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "task": task_type,
        "persona": persona,
        "chunk_id": chunk_id,
        "input_hash": input_hash,
        "output_hash": output_hash
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[LOGGED] Refactor chunk {chunk_id} | Persona: {persona}")

def chunk_input(text, max_lines=50):
    lines = text.splitlines()
    chunks = [lines[i:i+max_lines] for i in range(0, len(lines), max_lines)]
    return ["\n".join(chunk) for chunk in chunks]

def run_refactor(persona, task_type, input_path):
    engine = load_persona_engine(persona)

    if not os.path.exists(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return

    with open(input_path, "r") as f:
        raw = f.read()

    chunks = chunk_input(raw)
    for i, chunk in enumerate(chunks):
        input_hash = hash_content(chunk)
        try:
            output = engine(persona, "refactor", chunk)
        except Exception as e:
            print(f"[ERROR] DeepSeek-V2 failed on chunk {i}: {e}")
            output = f"# ERROR: Refactor failed\n{chunk}"
        output_hash = hash_content(output)

        out_path = os.path.join(WACHTER_ROOT, f"output/refactor_{persona}_{i}.py")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w") as f:
            f.write(output)

        log_refactor(task_type, persona, i, input_hash, output_hash)

def main():
    parser = argparse.ArgumentParser(description="DeepSeek Core Refactor Engine")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--task", choices=["refactor", "analyze", "inject"], required=True)
    parser.add_argument("--input", required=True)

    args = parser.parse_args()
    if args.task == "refactor":
        run_refactor(args.persona, args.task, args.input)
    else:
        print(f"[TODO] Task type '{args.task}' not yet implemented.")

if __name__ == "__main__":
    main()
