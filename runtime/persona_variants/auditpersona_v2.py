from datetime import datetime
import hashlib

def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()

def run_deepseek_v2(persona, task, input_text):
    timestamp = datetime.utcnow().isoformat()
    input_hash = hash_text(input_text)

    if task == "refactor":
        return f"# AuditPersona Refactor | Hash: {input_hash} | Time: {timestamp}\n" + input_text.replace("print(", "log_audit(")
    elif task == "analyze":
        return f"# AuditPersona Analysis | Lines: {len(input_text.splitlines())} | Hash: {input_hash}\n" + input_text
    elif task == "inject":
        return f"# Injected by AuditPersona | Time: {timestamp} | Hash: {input_hash}\n{input_text}"
    else:
        return f"# Unsupported task: {task}\n{input_text}"
