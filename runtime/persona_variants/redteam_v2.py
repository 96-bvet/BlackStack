def run_deepseek_v2(persona, task, input_text):
    if task == "refactor":
        return input_text.replace("print(", "log_red(")
    elif task == "analyze":
        return f"# RedTeam Analysis: {len(input_text.splitlines())} lines\n" + input_text
    elif task == "inject":
        return f"# Injected by RedTeam\n{input_text}"
    else:
        return f"# Unsupported task: {task}\n{input_text}"
