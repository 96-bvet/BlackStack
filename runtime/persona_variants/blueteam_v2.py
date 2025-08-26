def run_deepseek_v2(persona, task, input_text):
    if task == "refactor":
        return input_text.replace("print(", "log_blue(")
    elif task == "analyze":
        return f"# BlueTeam Audit Summary\n" + "\n".join(f"# {i+1}: {line}" for i, line in enumerate(input_text.splitlines()))
    elif task == "inject":
        return f"# Injected by BlueTeam with full traceability\n{input_text}"
    else:
        return f"# Unsupported task: {task}\n{input_text}"
